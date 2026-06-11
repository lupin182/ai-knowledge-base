"""按需重建 Astro 静态站（web/dist），供 AI / 编辑器改完内容后自动刷新。

设计：
- **单飞**：一个 threading.Lock 串行化所有重建请求。并发调用会排队；排到时若已
  不再 stale（前一次已经把更新构建进去了），直接返回 rebuilt=False，自然合并。
- **staleness**：构建前比对源文件 mtime 与 web/dist/index.html，不旧就跳过（秒级 stat）。
- **build-to-temp + swap**：先构建到 web/dist_new，再原子换进 web/dist，避免构建期间
  serve 到半成品（Astro build 会先清空 outDir，in-place 构建会有十几秒 404 窗口）。
"""
import logging
import os
import shutil
import subprocess
import threading
import time

from server.config import DOCS_ROOT, EXTERNAL_MOUNTS, WEB_DIST

logger = logging.getLogger(__name__)

WEB = DOCS_ROOT / "web"            # npm cwd（源码仍在仓库）
# dist 及其换入临时目录都在 OneDrive 之外（WEB_DIST 在 %LOCALAPPDATA%\kb-build\...）：
# 构建 + swap 全在本机盘，OneDrive 够不到 → 永不被同步占用锁住。
DIST = WEB_DIST
DIST_INDEX = DIST / "index.html"
DIST_NEW = WEB_DIST.parent / "dist_new"
DIST_OLD = WEB_DIST.parent / "dist_old"

_ON_WIN = os.name == "nt"
_build_lock = threading.Lock()
_last_error = ""


def _decode(b: bytes) -> str:
    """子进程输出解码：Windows 的 npm/npx 常输出 GBK，强按 UTF-8 解会乱码。"""
    if not b:
        return ""
    for enc in (("utf-8", "gbk") if _ON_WIN else ("utf-8",)):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            continue
    return b.decode("utf-8", "replace")


def _recover_dist(include_dist_new: bool = True) -> None:
    """崩在 swap 的两次 rename 之间会让 DIST 缺失、上一份好站停在 DIST_OLD（或新构建在 DIST_NEW）。
    启动时 + 每次 swap 前自愈：DIST 不存在但有完整备份就补回，绝不让现网空着。"""
    if DIST.exists():
        return
    candidates = (DIST_OLD, DIST_NEW) if include_dist_new else (DIST_OLD,)
    for cand in candidates:
        if cand.exists() and (cand / "index.html").exists():
            try:
                os.replace(cand, DIST)
                logger.warning("rebuild_service: dist 缺失，已从 %s 自愈恢复", cand.name)
                return
            except OSError:
                pass


# knowledge_bases 下不算"源"的运行时/可再生子目录（按路径段名跳过）：
# .kb=运行时元数据/阅读态(改它绝不该触发重建)、.pages=PDF 页图、raw/_extracted=PDF 抽取产物。
_SOURCE_SKIP_PARTS = {".kb", ".pages", "raw", "_extracted", "node_modules"}


def _newest_source_mtime() -> float:
    """内容(knowledge_bases 下 .md + 图片/PDF 等资源) + 前端源(web/src，去生成的 content) + docs/ 最新 mtime。

    注意 knowledge_bases 用 "*"（不再只 "*.md"）：只加一张图片/一个 PDF（不动 .md）也得能触发重建，
    否则 /api/rebuild 误判不 stale → 新资源发不出去。但跳过 .kb/.pages/raw 等运行时目录
    （尤其 .kb/reading-state.json，改阅读态不该触发重建）。
    """
    newest = 0.0
    roots = [(DOCS_ROOT / "knowledge_bases", "*"), (WEB / "src", "*"), (DOCS_ROOT / "docs", "*")]
    # 外部挂载（env 的 EXTERNAL_MOUNTS + 设置页管理的 external_mounts）也纳入：否则只在那边
    # 加/改文章时 staleness 察觉不到 → /api/rebuild 与启动检查都不重建 → 外部更新一直不生效。
    from pathlib import Path as _Path
    from server.services import settings_service as _ss
    ext = list(EXTERNAL_MOUNTS.values()) + [_Path(p) for p in _ss.external_mounts().values()]
    roots += [(m, "*") for m in ext]
    skips = [WEB / "src" / "content", DIST, DIST_NEW, DIST_OLD, WEB / "node_modules"]
    for base, pattern in roots:
        if not base.exists():
            continue
        for p in base.rglob(pattern):
            if not p.is_file():
                continue
            if _SOURCE_SKIP_PARTS.intersection(p.parts):
                continue
            if any(s == p or s in p.parents for s in skips):
                continue
            try:
                newest = max(newest, p.stat().st_mtime)
            except OSError:
                pass
    return newest


def is_stale() -> bool:
    if not DIST_INDEX.exists():
        return True
    try:
        return _newest_source_mtime() > DIST_INDEX.stat().st_mtime
    except OSError:
        return True


def _swap() -> None:
    """dist_new -> dist 事务式替换：失败可回滚，绝不让现网 web/dist 变空。

    1) 校验新构建有 index.html；2) dist -> dist_old 备份（带锁重试）；
    3) dist_new -> dist，失败则把备份移回去；4) 清理备份。window 仅一次 rename（毫秒级）。
    """
    # 先自愈：万一上次崩在两次 rename 之间(DIST 缺失)，这里只从 dist_old 补回。
    # 此时 dist_new 是本次刚构建出的候选产物，不能提前搬走，否则后续校验会误判缺 index.html。
    _recover_dist(include_dist_new=False)

    # 完整性校验：缺 index.html(或空)/缺 docs/js（前端脚本 + PDF 阅读器全在 docs/ 下）就是坏构建
    # （多因 OneDrive 锁住 web/public/docs 导致 sync 漏拷）→ 拒绝换入，保住现网，绝不拿坏构建顶替好站。
    idx = DIST_NEW / "index.html"
    if not idx.exists() or idx.stat().st_size == 0:
        raise RuntimeError("构建未产出有效 index.html，拒绝换入")
    if not (DIST_NEW / "docs" / "js").is_dir():
        raise RuntimeError("构建缺 docs/（前端脚本/PDF 阅读器），疑似 sync 被占用漏拷 → 拒绝换入，保留现网")
    # 只在 DIST 存在时清理旧备份；若 DIST 缺失而 DIST_OLD 在，_recover_dist 已把它移回 DIST，
    # 这里不会误删唯一好副本。
    if DIST.exists() and DIST_OLD.exists():
        shutil.rmtree(DIST_OLD, ignore_errors=True)

    # 2) 备份现网：os.replace 是原子整目录改名——要么成功、要么 PermissionError，绝不半删。
    # Windows 下 StaticFiles / OneDrive 可能正占用 → 重试 ~10s。
    # 关键：**绝不 rmtree(DIST)**——之前那个"原地替换"退路在 OneDrive 锁住时会把现网 dist
    # 删一半（部分文件被锁删不掉→报错），导致刷新渲染失败。占用拿不到就安全放弃，dist 原封不动。
    if DIST.exists():
        moved = False
        for _ in range(40):  # ~20s：足够熬过 OneDrive 一次同步占用
            try:
                os.replace(DIST, DIST_OLD)
                moved = True
                break
            except PermissionError:
                time.sleep(0.5)
        if not moved:
            raise RuntimeError("web/dist 被占用(多为 OneDrive 同步)，本次放弃换入；现网保持不变，稍后会再试")

    # 3) 换入新构建；失败则回滚备份，保证现网不空
    try:
        os.replace(DIST_NEW, DIST)
    except Exception:
        if DIST_OLD.exists() and not DIST.exists():
            try:
                os.replace(DIST_OLD, DIST)
            except Exception:
                logger.error("rebuild_service: swap 失败且回滚失败，web/dist 可能缺失！")
        raise

    # 4) 清理备份
    shutil.rmtree(DIST_OLD, ignore_errors=True)


def _run_build() -> None:
    if shutil.which("npm") is None:
        raise RuntimeError("未找到 npm，无法自动重建（装 Node.js 后生效）")
    DIST_NEW.parent.mkdir(parents=True, exist_ok=True)
    if DIST_NEW.exists():
        shutil.rmtree(DIST_NEW, ignore_errors=True)
    # stdout+stderr 合并捕获：Astro/Vite 的构建错误（坏 MDX、import 失败）主要打在 **stdout**，
    # 只收 stderr 会拿到空错误信息，用户看不出为什么失败。合并后报错可读。
    # 1) 同步内容（knowledge_bases -> web/src/content，docs -> web/public/docs）
    subprocess.run(
        ["npm", "run", "sync"], cwd=str(WEB), check=True, shell=_ON_WIN,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180,
    )
    # 2) 构建到临时目录
    subprocess.run(
        ["npx", "astro", "build", "--outDir", str(DIST_NEW)], cwd=str(WEB), check=True,
        shell=_ON_WIN, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600,
    )
    # 3) 原子换入
    _swap()


def rebuild_now(force: bool = False) -> dict:
    """同步重建（被 FastAPI 放进 threadpool，不阻塞事件循环）。单飞 + staleness 合并。

    force=True：跳过 staleness 直接重建。AI/编辑器改完是"已知发生了改动"，但 mtime 竞态下
    is_stale() 可能误判不旧 → 直接返回 rebuilt:False、dist 仍是旧的 → 刷新看到旧内容。
    已知改动就强制重建，绕开这个竞态。
    """
    global _last_error
    with _build_lock:
        if not force and not is_stale():
            return {"ok": True, "rebuilt": False}
        try:
            _run_build()
            _last_error = ""
            logger.info("rebuild_service: web/dist rebuilt + swapped")
            return {"ok": True, "rebuilt": True}
        except subprocess.CalledProcessError as e:
            # stderr 已合并进 stdout（见 _run_build）；按平台编码解码，取尾部 1200 字。
            err = _decode(e.stdout or e.stderr or b"")[-1200:]
            _last_error = f"build exit {e.returncode}: {err}"
            logger.error("rebuild_service build failed: %s", _last_error)
            return {"ok": False, "rebuilt": False, "error": _last_error}
        except Exception as e:  # noqa: BLE001
            _last_error = str(e)[:800]
            logger.exception("rebuild_service failed")
            return {"ok": False, "rebuilt": False, "error": _last_error}


# 进程启动(import 本模块)即自愈一次：若上次崩在 swap 中途导致 dist 缺失，从备份补回。
_recover_dist()
