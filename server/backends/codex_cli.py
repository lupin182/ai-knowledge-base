"""Codex CLI backend.

This backend uses the local logged-in Codex CLI (`codex exec --json`) as a
subscription-style provider, similar to the Claude CLI backend.
"""

import base64
import binascii
import json
import logging
import os
import re
import subprocess
import threading
import time
import uuid
from collections.abc import Generator
from pathlib import Path
from typing import Any

from server.config import (
    DOCS_ROOT,
    MAX_PAGE_CHARS,
    MAX_PDF_CHARS,
    MAX_PDF_INDEX_CHARS,
    PDF_RENDER_DPI,
)
from server.services import kb_service, pdf_render, settings_service

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger.setLevel(logging.INFO)

_CLI_TIMEOUT = 300
_IMG_TMP_DIR = ".tmp_images"
_IMG_MAX_B64 = 7_000_000
_IMG_EXT = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
_DANGEROUS_NAME_RE = re.compile(r"(secret|credential|password|token|api[_-]?key)", re.I)


def _looks_like_windows_sandbox_failure(text: str) -> bool:
    text = text or ""
    lowered = text.lower()
    return (
        "windows sandbox" in lowered
        and (
            "orchestrator_helper_launch_failed" in lowered
            or "sandbox helper failed" in lowered
            or "os error 5" in lowered
            or "拒绝访问" in text
        )
    )


def _sandbox_failure_hint() -> str:
    if settings_service.ai_full_access() and not _bound_to_loopback():
        return (
            "Codex CLI 的 Windows sandbox helper 启动失败（拒绝访问 / os error 5），"
            "而当前服务不是仅绑定本机回环地址，所以 AskMD 已按安全策略降级为受限 sandbox，"
            "无法让 Codex 写入文件。请用 `python run.py --host 127.0.0.1` 启动，"
            "并只在本机私有实例中开启“放开 AI 全部权限”后重试。"
        )
    return (
        "Codex CLI 的 Windows sandbox helper 启动失败（拒绝访问 / os error 5），"
        "当前受限模式无法读写文件。解决方法：在设置页的“对话默认”中勾选"
        "“放开 AI 全部权限”，确认服务只绑定 127.0.0.1/localhost 后保存并重试；"
        "或者修复 Codex CLI 的 Windows sandbox 权限后继续使用受限模式。"
    )


def _build_env() -> dict[str, str]:
    keys = [
        "PATH",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "APPDATA",
        "LOCALAPPDATA",
        "USERPROFILE",
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ]
    env = {k: os.environ.get(k, "") for k in keys if os.environ.get(k, "")}
    env["PATH"] = ";".join(
        [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "OpenAI", "Codex", "bin"),
            os.path.join(os.environ.get("APPDATA", ""), "npm"),
            env.get("PATH", ""),
        ]
    )
    if "HOME" not in env and os.environ.get("USERPROFILE"):
        env["HOME"] = os.environ["USERPROFILE"]
    return env


def _bound_to_loopback() -> bool:
    return os.environ.get("KB_BOUND_HOST", "").strip().lower() in _LOOPBACK_HOSTS


def _is_pdf_extract(page_content: str) -> bool:
    return page_content.lstrip().startswith("---") and "source_pdf:" in page_content[:800]


def _resolve_cwd(kb_slug: str) -> Path:
    if kb_slug:
        try:
            return kb_service.kb_dir(kb_slug)
        except ValueError:
            pass
    return DOCS_ROOT


def _save_temp_images(cwd: Path, images: list[dict[str, Any]] | None) -> tuple[list[Path], list[str]]:
    if not images:
        return [], []
    tmp_dir = cwd / _IMG_TMP_DIR
    tmp_dir.mkdir(exist_ok=True)
    abs_paths: list[Path] = []
    refs: list[str] = []
    for i, img in enumerate(images):
        b64 = img.get("base64", "")
        media = img.get("media_type", "")
        if not b64 or len(b64) > _IMG_MAX_B64:
            logger.warning("[codex img] #%d skipped (size=%d)", i, len(b64))
            continue
        ext = _IMG_EXT.get(media, "png")
        try:
            data = base64.b64decode(b64, validate=True)
        except (ValueError, binascii.Error) as exc:
            logger.warning("[codex img] #%d decode failed: %s", i, exc)
            continue
        path = tmp_dir / f"{uuid.uuid4().hex}.{ext}"
        try:
            path.write_bytes(data)
        except OSError as exc:
            logger.warning("[codex img] #%d write failed: %s", i, exc)
            continue
        abs_paths.append(path)
        refs.append(path.resolve().as_posix())
    return abs_paths, refs


def _default_model() -> str:
    cfg = settings_service.codex_cli_config()
    default_key = cfg.get("default_model_key", "")
    for profile in cfg.get("models") or []:
        if profile.get("key") == default_key:
            return profile.get("model", "")
    profiles = cfg.get("models") or []
    return profiles[0].get("model", "") if profiles else ""


def _resolve_model(selection: str) -> str:
    requested = (selection or "").strip()
    cfg = settings_service.codex_cli_config()
    for profile in cfg.get("models") or []:
        if requested in {profile.get("key"), profile.get("name"), profile.get("model")}:
            return (profile.get("model") or "").strip()
    return requested or _default_model()


def _markdown_snapshot(root: Path) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    if not root.exists():
        return out
    for path in root.rglob("*.md"):
        try:
            rel_parts = path.relative_to(root).parts
            if any(part.startswith(".") for part in rel_parts):
                continue
            if _DANGEROUS_NAME_RE.search(path.name):
                continue
            st = path.stat()
            out[path.resolve().as_posix()] = (st.st_mtime_ns, st.st_size)
        except OSError:
            continue
    return out


def _changed_markdown(root: Path, before: dict[str, tuple[int, int]]) -> list[str]:
    after = _markdown_snapshot(root)
    changed = []
    for abs_path, sig in after.items():
        if before.get(abs_path) != sig:
            try:
                rel = Path(abs_path).relative_to(root.resolve()).as_posix()
            except ValueError:
                rel = abs_path
            changed.append(rel)
    return sorted(changed)


def _strip_code_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _build_prompt(
    *,
    page_path: str,
    page_content: str,
    selected_text: str,
    messages: list[dict[str, Any]],
    kb_slug: str,
    rel_path: str,
    cwd: Path,
) -> str:
    is_pdf = _is_pdf_extract(page_content)
    pdf_pages = None
    if is_pdf and rel_path:
        stem = Path(rel_path).stem
        pdf_abs = cwd / "papers" / f"{stem}.pdf"
        count = pdf_render.ensure_pages(pdf_abs, cwd / "papers" / ".pages" / stem, PDF_RENDER_DPI)
        if count:
            pdf_pages = (f"papers/.pages/{stem}", count, f"papers/{stem}.md")

    max_chars = MAX_PDF_CHARS if is_pdf else MAX_PAGE_CHARS
    content = page_content
    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n... (content truncated)"

    parts = [
        "你是一个本地 Markdown 知识库助手，通过 Codex CLI 在当前知识库目录内工作。",
        "请用中文回答，使用清晰的 Markdown。",
        "",
        "## 安全与文件访问规则",
        "1. 默认只回答问题，不要修改文件；只有用户明确要求修改、添加、删除或整理知识库内容时才可以编辑文件。",
        "2. 只允许读取、搜索、创建或修改当前工作目录内的 Markdown (.md) 文件。",
        "3. 禁止访问 ../、绝对路径、隐藏目录、server/、docs/、.git/、.claude/、.codex/ 或任何知识库外路径。",
        "4. 禁止读取或修改文件名包含 secret、credential、password、token、api_key、key 的文件。",
        "5. 如需编辑当前页面，优先使用提示中的当前页面相对路径。",
        "6. 修改完成后说明改了哪些文件，并提醒用户刷新页面查看。",
        "",
        "## 当前上下文",
        f"- 工作目录: `{cwd.as_posix()}`",
        f"- 页面路径: `{page_path or 'README.md'}`",
    ]
    if kb_slug:
        parts.extend([
            f"- 知识库 slug: `{kb_slug}`",
            f"- 当前页相对路径: `{rel_path or 'README.md'}`",
        ])

    kb_prompt = kb_service.read_kb_prompt(kb_slug) if kb_slug else ""
    if kb_prompt:
        parts.extend(["", "## 本知识库额外提示", kb_prompt])

    if pdf_pages:
        pages_rel, page_count, md_rel = pdf_pages
        index_excerpt = content[:MAX_PDF_INDEX_CHARS]
        parts.extend([
            "",
            "## PDF 阅读模式",
            f"当前页面来自一篇 PDF，共 {page_count} 页。",
            f"- 文字索引: `{md_rel}`",
            f"- 每页图片: `{pages_rel}/pNNN.png`，例如 `{pages_rel}/p001.png`",
            "回答时先用文字索引定位；涉及图表、公式、版面或具体数值时，按需查看对应页图。不要直接读取 .pdf 文件。",
            "",
            "### 文字索引开头",
            index_excerpt,
        ])
    elif is_pdf:
        parts.extend([
            "",
            "## PDF 阅读模式",
            "当前页面是 PDF 自动抽取全文。请严格基于本文回答并尽量标注页码；不要修改文件。",
        ])

    parts.extend(["", "## 当前页面内容", content])
    if selected_text:
        parts.extend(["", "## 用户选中的文字", selected_text])
    if len(messages) > 1:
        parts.append("")
        parts.append("## 对话历史")
        for msg in messages[:-1]:
            role = "用户" if msg.get("role") == "user" else "助手"
            parts.append(f"\n**{role}**: {msg.get('content', '')}")
    if messages:
        parts.extend(["", "## 当前问题", messages[-1].get("content", "")])
    return "\n".join(parts)


class CodexCLIBackend:
    name = "codex_cli"

    def list_models(self) -> list[dict[str, Any]]:
        cfg = settings_service.codex_cli_config()
        default_key = cfg.get("default_model_key", "")
        return [
            {
                "value": p.get("model") or p.get("key"),
                "label": p.get("name") or p.get("model") or "Codex default",
                "model": p.get("model") or p.get("key"),
                "context": p.get("context", 200000),
                "is_default": p.get("key") == default_key,
                "configured": True,
            }
            for p in cfg.get("models") or []
        ]

    def status(self) -> dict[str, Any]:
        cli_path = settings_service.codex_cli_path()
        return {
            "backend": self.name,
            "cli_path": cli_path,
            "available": bool(cli_path),
        }

    def stream_chat(
        self,
        *,
        page_path: str,
        page_content: str,
        selected_text: str,
        messages: list[dict[str, Any]],
        model: str = "",
        thinking: bool = False,
        effort: str = "",
        enable_tools: bool = True,
        images: list[dict[str, Any]] | None = None,
        session_id: str = "",
    ) -> Generator[dict[str, Any], None, None]:
        del thinking, effort, session_id
        kb_slug, rel_path = kb_service.split_docsify_path(page_path or "")
        kb_slug = kb_slug or ""
        cwd = _resolve_cwd(kb_slug)
        cwd.mkdir(parents=True, exist_ok=True)

        img_paths, img_refs = _save_temp_images(cwd, images)
        prompt = _build_prompt(
            page_path=page_path,
            page_content=page_content,
            selected_text=selected_text,
            messages=messages,
            kb_slug=kb_slug,
            rel_path=rel_path,
            cwd=cwd,
        )
        if img_refs:
            prompt = (
                f"用户随本次消息上传了 {len(img_refs)} 张图片。图片已通过 Codex CLI 的 --image 参数附加；"
                "请把这些图片视为用户输入的一部分。\n\n" + prompt
            )

        cli = settings_service.codex_cli_path()
        cmd = [cli, "--ask-for-approval", "never", "exec", "--json", "--skip-git-repo-check", "-C", str(cwd)]
        if enable_tools:
            if settings_service.ai_full_access() and _bound_to_loopback():
                cmd.append("--dangerously-bypass-approvals-and-sandbox")
            else:
                if settings_service.ai_full_access():
                    logger.warning(
                        "ai_full_access is enabled but KB_BOUND_HOST=%r is not loopback; Codex is downgraded to workspace-write.",
                        os.environ.get("KB_BOUND_HOST"),
                    )
                cmd.extend(["--sandbox", "workspace-write"])
        else:
            cmd.extend(["--sandbox", "read-only"])
        resolved_model = _resolve_model(model)
        if resolved_model:
            cmd.extend(["--model", resolved_model])
        for path in img_paths:
            cmd.extend(["--image", str(path)])
        cmd.append("-")

        before = _markdown_snapshot(cwd) if enable_tools else {}
        logger.info(
            "codex_cli call: kb=%s model=%s prompt=%dB images=%d cwd=%s",
            kb_slug or "(none)", resolved_model or "(codex default)",
            len(prompt.encode("utf-8")), len(img_paths), cwd,
        )

        try:
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd),
                env=_build_env(),
            )
        except Exception:
            for path in img_paths:
                try:
                    path.unlink()
                except OSError:
                    pass
            raise

        timed_out = [False]

        def _kill_on_timeout():
            timed_out[0] = True
            try:
                proc.kill()
            except OSError:
                pass

        timeout_timer = threading.Timer(_CLI_TIMEOUT, _kill_on_timeout)
        timeout_timer.start()
        stderr_chunks: list[str] = []

        def _read_stderr():
            try:
                for line in proc.stderr:
                    stderr_chunks.append(line.decode("utf-8", errors="replace"))
            except Exception:
                pass

        def _write_stdin():
            try:
                proc.stdin.write(prompt.encode("utf-8"))
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass

        stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
        stdin_thread = threading.Thread(target=_write_stdin, daemon=True)
        stderr_thread.start()
        stdin_thread.start()

        got_text = False
        sandbox_failed = False
        started = time.time()
        try:
            for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug("Ignoring non-json Codex stdout line: %s", line[:200])
                    continue

                event_type = event.get("type", "")
                if event_type == "thread.started":
                    thread_id = event.get("thread_id", "")
                    if thread_id:
                        yield {"type": "session_id", "session_id": thread_id}
                elif event_type == "error":
                    msg = event.get("message", "")
                    if msg:
                        if msg.startswith("Reconnecting..."):
                            logger.info("Codex CLI transient stream reconnect: %s", msg)
                            continue
                        yield {"type": "error", "content": msg}
                elif event_type == "item.completed":
                    item = event.get("item") or {}
                    item_type = item.get("type", "")
                    if _looks_like_windows_sandbox_failure(item.get("aggregated_output", "")):
                        sandbox_failed = True
                    if item_type == "agent_message" and item.get("text"):
                        got_text = True
                        yield {"type": "text", "content": item["text"]}
                    elif item_type == "file_change" and item.get("status") == "failed":
                        sandbox_failed = True
                    elif item_type in {"command_execution", "tool_call", "file_change"}:
                        name = item.get("name") or item_type
                        file_path = item.get("path") or item.get("file") or ""
                        if file_path:
                            yield {"type": "tool", "tool": name, "file": file_path}
                elif event_type == "turn.completed":
                    usage = event.get("usage") or {}
                    if usage:
                        yield {
                            "type": "usage",
                            "input_tokens": usage.get("input_tokens", 0),
                            "output_tokens": usage.get("output_tokens", 0),
                            "cache_read": usage.get("cached_input_tokens", 0),
                            "cache_create": 0,
                        }
                    yield {"type": "duration", "ms": int((time.time() - started) * 1000)}

            proc.wait(timeout=10)
            stderr_thread.join(timeout=5)
            if timed_out[0]:
                yield {"type": "error", "content": f"Codex CLI timed out after {_CLI_TIMEOUT} seconds."}
            elif proc.returncode != 0 and not got_text:
                detail = "".join(stderr_chunks).strip() or f"exit code {proc.returncode}"
                logger.error("Codex CLI error: %s", detail)
                yield {"type": "error", "content": "Codex CLI encountered an error. Please try again."}

            if enable_tools and sandbox_failed:
                yield {"type": "error", "content": _sandbox_failure_hint()}

            if enable_tools and proc.returncode == 0:
                for rel in _changed_markdown(cwd, before):
                    yield {"type": "tool", "tool": "Codex", "file": rel}
        finally:
            timeout_timer.cancel()
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)
            for path in img_paths:
                try:
                    path.unlink()
                except OSError:
                    pass

    def suggest_edit(
        self,
        *,
        page_content: str,
        instruction: str,
        chat_context: str = "",
    ) -> str:
        prompt = (
            "请根据用户指令修改下面的 Markdown。\n"
            "只输出完整修改后的 Markdown 内容，不要解释，不要使用代码围栏。\n\n"
            f"## 用户指令\n\n{instruction}\n\n"
            f"## 对话上下文\n\n{chat_context or '(无)'}\n\n"
            f"## 原始 Markdown\n\n{page_content}"
        )
        cli = settings_service.codex_cli_path()
        cmd = [
            cli, "--ask-for-approval", "never",
            "exec", "--json", "--skip-git-repo-check", "--sandbox", "read-only", "-C", str(DOCS_ROOT),
        ]
        model = _default_model()
        if model:
            cmd.extend(["--model", model])
        cmd.append("-")
        proc = subprocess.run(
            cmd,
            input=prompt.encode("utf-8"),
            capture_output=True,
            cwd=str(DOCS_ROOT),
            env=_build_env(),
            timeout=_CLI_TIMEOUT,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeError(err or f"Codex CLI exited with {proc.returncode}")
        last_text = ""
        for raw in proc.stdout.decode("utf-8", errors="replace").splitlines():
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if event.get("type") == "item.completed":
                item = event.get("item") or {}
                if item.get("type") == "agent_message" and item.get("text"):
                    last_text = item["text"]
        return _strip_code_fence(last_text)
