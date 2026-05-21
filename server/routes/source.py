"""读取 docsify 页面的 markdown 源码（给 CodeMirror 编辑器用）。"""

from fastapi import APIRouter, HTTPException, Query

from server.config import DOCS_ROOT
from server.services import kb_service

router = APIRouter()


@router.get("/page-source")
async def get_page_source(path: str = Query(..., description="Docsify page path")):
    try:
        resolved = kb_service.resolve_docsify_page(path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    content = resolved.abs_path.read_text(encoding="utf-8")
    rel_path = resolved.abs_path.relative_to(DOCS_ROOT).as_posix()
    return {"source": content, "file_path": rel_path}
