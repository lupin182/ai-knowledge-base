"""多知识库 API + 动态 sidebar。

注：/kb/<slug>/... 静态文件**不再**由本路由处理——交给 main.py 的 StaticFiles
mount（指向 web/dist/，Astro 静态构建产物）。
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, field_validator

from server.config import DOCS_ROOT
from server.services import kb_service, reading_state, rebuild_service

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


class KbPromptRequest(BaseModel):
    prompt: str = ""


@router.get("/api/kbs/{slug}/prompt")
async def get_kb_prompt(slug: str):
    """读某 KB 的自定义 AI 提示词（追加在基础系统提示词后）。"""
    try:
        kb_service.validate_slug(slug)
        if not kb_service.kb_dir(slug).exists():
            raise FileNotFoundError(slug)
        return {"slug": slug, "prompt": kb_service.read_kb_prompt(slug)}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/api/kbs/{slug}/prompt")
async def put_kb_prompt(slug: str, request: KbPromptRequest):
    """保存某 KB 的自定义 AI 提示词（空串 = 清除，回退到基础提示词）。"""
    try:
        return kb_service.write_kb_prompt(slug, request.prompt)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/prompt/base")
async def get_base_prompt():
    """基础系统提示词（只读）。每次对话默认带，KB 额外提示词追加在它之后。设置页展示用。"""
    from server.backends import claude_cli
    return {"base": claude_cli.base_system_prompt()}


class ReadingRequest(BaseModel):
    path: str
    status: str = "unread"          # unread | reading | read
    annotations: list = []          # 行内笔记标注 [{id, exact, prefix, suffix, note}]


@router.get("/api/reading")
async def get_reading(path: str):
    """读某页的阅读状态 + 行内笔记。path = 归一化 pathname（kb/<slug>/<rel> 或 external-reports/...）。"""
    return reading_state.get(path)


@router.put("/api/reading")
async def put_reading(req: ReadingRequest):
    """存某页的阅读状态 + 行内笔记（status=unread 且无笔记 = 清除该条）。支持 KB 页与外部挂载页。"""
    return reading_state.set_state(req.path, req.status, req.annotations)


@router.get("/api/reading/all")
async def get_reading_all(path: str):
    """侧栏标记用：{完整页面路径: {status, notes}}（外部全局库 + 当前页所属 KB 库）。"""
    return reading_state.all_for(path)


# 同步 def（非 async）→ FastAPI 在 threadpool 里跑，~15s 构建不阻塞事件循环。
@router.post("/api/rebuild")
def rebuild(force: bool = False):
    """按需重建 Astro 静态站。AI / 编辑器改完 .md 后由前端自动调用，让侧栏 + 页面刷新生效。

    force=1：已知发生改动时强制重建，绕开 mtime 竞态误判"不旧"导致刷新仍是旧内容。
    """
    return rebuild_service.rebuild_now(force=force)


@router.get("/api/sidebar")
async def api_sidebar():
    return PlainTextResponse(kb_service.build_sidebar_markdown(), media_type="text/markdown")


@router.get("/_sidebar.md")
async def sidebar():
    """根 sidebar：优先静态 DOCS_ROOT/_sidebar.md，缺失才回退到自动构建。

    设计意图：KB 维护者通常会手写一个简洁的 KB switcher 落地页 sidebar；
    auto-build 那种"把每个 KB 的每个 md 全列出来"的版本只在没人手写时兜底。
    """
    static_sidebar = DOCS_ROOT / "_sidebar.md"
    if static_sidebar.exists():
        return PlainTextResponse(
            static_sidebar.read_text(encoding="utf-8"),
            media_type="text/markdown",
        )
    return PlainTextResponse(kb_service.build_sidebar_markdown(), media_type="text/markdown")


# 注：原 /kb/{slug}/ 和 /kb/{slug}/{file_path:path} 两个 FileResponse 路由
# （直接返回 knowledge_bases/<slug>/... 下的 raw markdown）已删除。
# 它们是 Docsify 时代的产物——Docsify 客户端 fetch 原始 .md 自渲染。
# 现在前端是 Astro 静态构建（web/dist/kb/<slug>/<path>/index.html），
# 这些路由不应再拦截 URL，必须 fall through 到 main.py 的 StaticFiles。
# AI 侧边栏读原文用 /api/page-source（独立路由，仍走 knowledge_bases/）。
