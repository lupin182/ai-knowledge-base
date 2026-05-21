from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from server.auth import SecurityMiddleware
from server.config import DOCS_ROOT, EXTERNAL_MOUNTS
from server.routes import chat, edit, kb, settings, source, stats

app = FastAPI(
    title="AI Knowledge Base Server",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# 单一安全中间件：路径防护 + 速率限制 + 认证（顺序敏感）。
app.add_middleware(SecurityMiddleware)

# API 路由
app.include_router(settings.router, prefix="/api")  # 含 /api/login + /api/settings/*
app.include_router(source.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(edit.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(kb.router)                       # 含 /api/kbs/* + /_sidebar.md + /kb/<slug>/...

# EXTERNAL_MOUNTS：在 catch-all 静态文件之前注册，让 URL 前缀优先匹配。
for _prefix, _fs_path in EXTERNAL_MOUNTS.items():
    app.mount(
        f"/{_prefix}",
        StaticFiles(directory=str(_fs_path), html=True),
        name=f"ext-{_prefix}",
    )

# 静态文件 (docs/ 等)。必须最后挂载，作为 catch-all。
app.mount("/", StaticFiles(directory=str(DOCS_ROOT), html=True), name="static")
