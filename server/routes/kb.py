"""多知识库 API + 动态 sidebar + /kb/<slug>/... 静态文件。"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, field_validator

from server.config import DOCS_ROOT
from server.services import kb_service

router = APIRouter()

_TRASH_ROOT = DOCS_ROOT / "_trash" / "knowledge_bases"


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    slug: str | None = None

    @field_validator("name")
    @classmethod
    def name_length(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 80:
            raise ValueError("name must be 1-80 chars")
        return value

    @field_validator("slug")
    @classmethod
    def slug_format(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        return kb_service.validate_slug(value.strip())


class RenameKnowledgeBaseRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def name_length(cls, value: str) -> str:
        value = value.strip()
        if not value or len(value) > 80:
            raise ValueError("name must be 1-80 chars")
        return value


@router.get("/api/kbs")
async def list_kbs():
    return {"items": kb_service.list_knowledge_bases()}


@router.post("/api/kbs")
async def create_kb(request: CreateKnowledgeBaseRequest):
    try:
        return kb_service.create_knowledge_base(request.name, request.slug)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/api/kbs/{slug}")
async def rename_kb(slug: str, request: RenameKnowledgeBaseRequest):
    try:
        return kb_service.rename_knowledge_base(slug, request.name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/api/kbs/{slug}")
async def delete_kb(slug: str):
    try:
        return kb_service.delete_knowledge_base(slug, _TRASH_ROOT)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/kbs/{slug}/upload")
async def upload_to_kb(slug: str, request: Request):
    try:
        kb_service.validate_slug(slug)
        form = await request.form()
        return await kb_service.save_uploads(slug, form)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except AssertionError:
        raise HTTPException(
            status_code=500,
            detail="File upload support requires python-multipart. Run: pip install -r requirements.txt",
        )


@router.get("/api/sidebar")
async def api_sidebar():
    return PlainTextResponse(kb_service.build_sidebar_markdown(), media_type="text/markdown")


@router.get("/_sidebar.md")
async def sidebar():
    return PlainTextResponse(kb_service.build_sidebar_markdown(), media_type="text/markdown")


@router.get("/kb/{slug}/")
async def serve_kb_root(slug: str):
    try:
        return FileResponse(kb_service.resolve_static_file(slug, "README.md"))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))


@router.get("/kb/{slug}/{file_path:path}")
async def serve_kb_file(slug: str, file_path: str):
    try:
        return FileResponse(kb_service.resolve_static_file(slug, file_path))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
