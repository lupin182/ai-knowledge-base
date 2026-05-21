"""统一安全中间件：路径防护 + 速率限制 + 密码认证，合并为单一中间件保证执行顺序。

ACCESS_PASSWORD 从 settings_service 读取（可以从前端设置页改并实时生效）。
"""

import hashlib
import hmac
import os
import pathlib
import re
import secrets
import time
import urllib.parse

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse

from server.services import settings_service

# ── Cookie 签名密钥（持久化，重启后 cookie 仍有效）──
_SECRET_FILE = pathlib.Path(__file__).parent / ".auth_secret"


def _load_or_create_secret() -> str:
    if _SECRET_FILE.exists():
        secret = _SECRET_FILE.read_text().strip()
        if len(secret) >= 32:
            return secret
    secret = secrets.token_hex(32)  # 256-bit
    _SECRET_FILE.write_text(secret)
    try:
        os.chmod(str(_SECRET_FILE), 0o600)
    except OSError:
        pass
    return secret


_SECRET = _load_or_create_secret()

# 只信任直连 socket IP，绝不信任 X-Forwarded-For
_LOCAL_IPS = frozenset({"127.0.0.1", "::1"})

# ── 路径安全 ──
# 直接 URL 访问以下前缀的资源会被拦截：
# - server/ ：后端代码
# - knowledge_bases/ ：必须走 /kb/<slug>/... 路由，禁止暴露真实磁盘前缀
# - _trash/、_backup/、_cli_sandbox/ ：临时/废弃数据
# - .git/, .github/, .claude/, .env, .venv/, .vscode/, .idea/, __pycache__/, .auth_secret
_BLOCKED_PREFIXES = (
    "/server/", "/.claude/", "/.git/", "/.github/", "/.env",
    "/knowledge_bases/", "/_trash/", "/_cli_sandbox/", "/_backup/",
    "/__pycache__/", "/.auth_secret",
    "/.venv/", "/venv/", "/.vscode/", "/.idea/",
)
_DANGEROUS_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def _normalize_path(raw: str) -> str | None:
    if _DANGEROUS_CHARS.search(raw):
        return None
    decoded = urllib.parse.unquote(urllib.parse.unquote(raw))
    if _DANGEROUS_CHARS.search(decoded):
        return None
    decoded = decoded.replace("\\", "/")
    while "//" in decoded:
        decoded = decoded.replace("//", "/")
    parts = decoded.split("/")
    resolved: list[str] = []
    for p in parts:
        if p in ("", "."):
            continue
        elif p == "..":
            if resolved:
                resolved.pop()
        else:
            resolved.append(p.rstrip(". "))
    normalized = "/" + "/".join(resolved)
    return normalized.lower()


def _is_path_blocked(path: str) -> bool:
    for prefix in _BLOCKED_PREFIXES:
        if path.startswith(prefix) or path == prefix.rstrip("/"):
            return True
    if path.endswith(".py") or path.endswith(".pyc"):
        return True
    if "/." in path:
        return True
    if "~" in path:
        return True
    return False


# ── Token 生成与验证（时序安全）──
def _make_token(password: str) -> str:
    return hmac.new(_SECRET.encode(), password.encode(), hashlib.sha256).hexdigest()


def verify_token(token: str) -> bool:
    if not token:
        return False
    password = settings_service.access_password()
    if not password:
        return False
    return hmac.compare_digest(token, _make_token(password))


def verify_password(candidate: str, expected: str | None = None) -> bool:
    if expected is None:
        expected = settings_service.access_password()
    if not candidate or not expected:
        return False
    return hmac.compare_digest(candidate, expected)


# ── 速率限制 ──
_chat_rate: dict[str, list[float]] = {}
_login_rate: dict[str, list[float]] = {}
_MAX_TRACKED_IPS = 10000

CHAT_RATE_WINDOW = 60
CHAT_RATE_MAX = 30
LOGIN_RATE_WINDOW = 300
LOGIN_RATE_MAX = 5


def _check_rate(store: dict, ip: str, window: int, limit: int) -> bool:
    now = time.time()
    if len(store) > _MAX_TRACKED_IPS:
        expired = [k for k, v in store.items() if not v or now - v[-1] > window]
        for k in expired:
            del store[k]
    if ip not in store:
        store[ip] = []
    store[ip] = [t for t in store[ip] if now - t < window]
    if len(store[ip]) >= limit:
        return True
    store[ip].append(now)
    return False


def _is_local(request: Request) -> bool:
    client = request.client
    if not client:
        return False
    return client.host in _LOCAL_IPS


# ── 登录页 ──
LOGIN_PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>登录 - AI 知识库</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    display: flex; align-items: center; justify-content: center;
    min-height: 100vh; background: #f0f2f5; font-family: -apple-system, sans-serif;
  }
  .login-card {
    background: #fff; border-radius: 12px; padding: 40px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.1); width: 360px; text-align: center;
  }
  .login-card h1 { font-size: 22px; color: #333; margin-bottom: 8px; }
  .login-card p { font-size: 14px; color: #888; margin-bottom: 24px; }
  .login-card input {
    width: 100%; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px;
    font-size: 15px; outline: none; transition: border-color 0.2s;
  }
  .login-card input:focus { border-color: #3F51B5; }
  .login-card button {
    width: 100%; padding: 12px; margin-top: 16px; border: none; border-radius: 8px;
    background: #3F51B5; color: #fff; font-size: 15px; cursor: pointer;
    transition: background 0.2s;
  }
  .login-card button:hover { background: #303F9F; }
  .error { color: #e53935; font-size: 13px; margin-top: 10px; display: none; }
</style>
</head>
<body>
<div class="login-card">
  <h1>AI 知识库</h1>
  <p>请输入访问密码</p>
  <form id="f">
    <input type="password" id="pw" placeholder="密码" autofocus>
    <button type="submit">登录</button>
    <div class="error" id="err">密码错误</div>
  </form>
</div>
<script>
document.getElementById('f').onsubmit = function(e) {
  e.preventDefault();
  fetch('/api/login', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({password: document.getElementById('pw').value})
  }).then(function(r) { return r.json(); }).then(function(d) {
    if (d.ok) { location.reload(); }
    else { document.getElementById('err').style.display = 'block'; }
  });
};
</script>
</body>
</html>"""


# 未启用密码也允许访问的诊断/设置接口（让首次启动能进设置页）
_OPEN_PATHS = frozenset({"/api/login", "/api/settings/check"})


class SecurityMiddleware(BaseHTTPMiddleware):
    """合并路径防护 + 速率限制 + 认证，保证执行顺序。"""

    async def dispatch(self, request: Request, call_next):
        normalized = _normalize_path(request.url.path)
        if normalized is None:
            return JSONResponse({"error": "Bad request"}, status_code=400)
        if _is_path_blocked(normalized):
            return JSONResponse({"error": "Forbidden"}, status_code=403)

        client_ip = request.client.host if request.client else "unknown"
        if normalized == "/api/login":
            if _check_rate(_login_rate, client_ip, LOGIN_RATE_WINDOW, LOGIN_RATE_MAX):
                return JSONResponse(
                    {"error": "Too many login attempts. Try again later."},
                    status_code=429,
                    headers={"Retry-After": str(LOGIN_RATE_WINDOW)},
                )
        elif normalized.startswith("/api/chat"):
            if _check_rate(_chat_rate, client_ip, CHAT_RATE_WINDOW, CHAT_RATE_MAX):
                return JSONResponse(
                    {"error": "Rate limit exceeded. Try again later."},
                    status_code=429,
                )

        password = settings_service.access_password()
        if not password:
            return await call_next(request)
        if _is_local(request):
            return await call_next(request)
        if normalized in _OPEN_PATHS:
            return await call_next(request)

        token = request.cookies.get("kb_auth", "")
        if verify_token(token):
            return await call_next(request)

        if normalized.startswith("/api/"):
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        return HTMLResponse(LOGIN_PAGE)
