"""统计 + 模型列表 + 兼容旧的 rate-limits 接口。"""

import time

from fastapi import APIRouter

from server.backends import get_active_backend
from server.services import kb_service, settings_service

router = APIRouter()

_cache = {"data": None, "ts": 0}
_TTL = 60


@router.get("/stats")
def get_stats():
    """统计所有知识库 Markdown 文件数量和总字数（带 60s 缓存）。"""
    now = time.time()
    if _cache["data"] and now - _cache["ts"] < _TTL:
        return _cache["data"]
    result = kb_service.all_kb_stats()
    _cache["data"] = result
    _cache["ts"] = now
    return result


@router.get("/models")
def list_models():
    """前端模型下拉用。返回当前 backend 的可用模型列表。"""
    backend = get_active_backend()
    return {
        "backend": backend.name,
        "models": backend.list_models(),
        "is_configured": settings_service.is_configured(),
    }


@router.get("/rate-limits")
async def rate_limits():
    """老前端会调；返回当前 backend 的简要可用状态。"""
    backend = get_active_backend()
    return {"rate_limits": backend.status()}
