"""suggest-edit (生成 diff 预览) + apply-edit (落盘)。两者都走 kb_service 解析路径。"""

import difflib
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from server.backends import get_active_backend
from server.config import DOCS_ROOT
from server.models import SuggestEditRequest, ApplyEditRequest
from server.services import kb_service

router = APIRouter()


def _write_with_backup(path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    path.write_text(content, encoding="utf-8")


@router.post("/suggest-edit")
async def suggest_edit(request: SuggestEditRequest):
    try:
        resolved = kb_service.resolve_docsify_page(request.page_path)
        original = resolved.abs_path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    backend = get_active_backend()
    try:
        modified = backend.suggest_edit(
            page_content=original,
            instruction=request.instruction,
            chat_context=request.chat_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile="original",
        tofile="modified",
    )
    diff_text = "".join(diff)
    rel_path = str(resolved.abs_path.relative_to(DOCS_ROOT))
    return {"original": original, "modified": modified, "diff": diff_text, "file_path": rel_path}


@router.post("/apply-edit")
async def apply_edit(request: ApplyEditRequest):
    try:
        path = kb_service.validate_path(request.file_path)
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    if path.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="Only .md files can be edited")
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    _write_with_backup(path, request.modified_content)
    # 触发对应 KB 的 updated_at 更新（如果文件在某个 KB 内）。
    for item in kb_service.list_knowledge_bases():
        try:
            path.resolve().relative_to(kb_service.kb_dir(item["slug"]).resolve())
            meta_path = kb_service.meta_path(item["slug"])
            if meta_path.exists():
                import json
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                meta["updated_at"] = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
                meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            break
        except ValueError:
            continue
    return {"success": True, "file_path": request.file_path}
