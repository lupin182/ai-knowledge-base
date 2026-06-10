"""启动知识库 AI 服务器。

用法:
    python run.py              # 一条命令：按需自动构建前端 + 启动 127.0.0.1:8001（仅本机）
    python run.py --port 8080  # 指定端口
    python run.py --host 0.0.0.0  # 对外/局域网可访问（先设密码、关 full-access，自担风险）
    python run.py --rebuild    # 强制重建前端再启动
    python run.py --no-build   # 跳过前端构建检查，直接用现有 dist

首次启动（或内容/前端有更新时）会自动 `npm install` + 走 rebuild_service 的
「构建到临时目录 + 原子换入」（和 /api/rebuild 同一条路径，启动构建中途崩也不会
把现网 dist 弄残）。构建产物在 OneDrive 之外的本机 cache（见 config.WEB_DIST）。需要 Node.js。
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import uvicorn

from server.config import WEB_DIST  # 构建产物在 OneDrive 之外的本机 cache（见 config.py）

# Windows 控制台常是 GBK，遇到非 GBK 字符会 UnicodeEncodeError 崩溃。
# 保留控制台原编码（中文在 GBK 下正常），只把无法编码的字符降级为占位符，绝不崩。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
DIST_INDEX = WEB_DIST / "index.html"


def get_lan_ips():
    """尝试枚举本机所有非回环 IPv4 地址，方便手机接入。"""
    ips = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = info[4][0]
            if ip and not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def ensure_frontend(force: bool = False, skip: bool = False) -> None:
    """保证 dist 是最新的静态站：缺失或源码更新过就 npm install + 走 rebuild_service 构建。

    staleness 判定 + 构建都复用 rebuild_service（单一权威）：避免 run.py 自己一份 mtime 逻辑
    与 /api/rebuild 漂移，也让启动构建走「临时目录 + 原子换入」而非原地 build（原地 build
    astro 先清空 outDir，中途崩会把现网 dist 弄残）。"""
    if skip or not WEB.exists():
        return

    # 延迟 import：避免 server 包在 argparse 之前就被拉起
    from server.services import rebuild_service

    need_build = force or not DIST_INDEX.exists() or rebuild_service.is_stale()
    if not need_build:
        return

    if not shutil.which("npm"):
        if DIST_INDEX.exists():
            print("[!] 未找到 npm，跳过前端构建，沿用现有 dist（内容可能过期）。装 Node.js 后会自动更新。")
            return
        print("[x] 首次启动需要构建前端，但未找到 npm。请先安装 Node.js: https://nodejs.org")
        sys.exit(1)

    on_win = os.name == "nt"
    try:
        if not (WEB / "node_modules").exists():
            print("- 安装前端依赖（npm install，仅首次，约 1-2 分钟）...")
            subprocess.run(["npm", "install"], cwd=WEB, check=True, shell=on_win)
        print(f"- 同步内容 + 构建前端（→ {WEB_DIST}，临时目录原子换入）...")
        rebuild_service._run_build()   # sync + 构建到 dist_new + 原子 swap（不会弄残现网）
        print("[ok] 前端就绪")
    except subprocess.CalledProcessError as e:
        print(f"[x] 前端构建失败（exit {e.returncode}）。可在 web/ 里手动跑 `npm install && npm run build` 看详细报错。")
        if DIST_INDEX.exists():
            print("  沿用现有 dist 继续启动（内容可能过期）。")
        else:
            sys.exit(1)
    except Exception as e:  # _run_build 的 guard/swap 抛 RuntimeError 等
        print(f"[x] 前端构建失败：{e}")
        if DIST_INDEX.exists():
            print("  沿用现有 dist 继续启动（内容可能过期）。")
        else:
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="AI Knowledge Base Server")
    # 默认只绑 127.0.0.1：不暴露到局域网/公网，外部够不到 → 没人能远程调用你的 AI。
    # 真要给同 WiFi 的手机/别的机器访问，显式传 --host 0.0.0.0（且务必先设访问密码、
    # 关掉「放开 AI 全部权限」），自己权衡风险。
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--reload", action="store_true", help="Auto-reload on code changes")
    parser.add_argument("--rebuild", action="store_true", help="强制重建前端再启动")
    parser.add_argument("--no-build", action="store_true", help="跳过前端构建检查，直接用现有 web/dist")
    args = parser.parse_args()

    # 把绑定 host 暴露给后端：claude_cli 的安全联锁据此决定是否真放开 full-access
    # （只有仅绑本机才允许 bypassPermissions；对外暴露时即便设置开着也降级）。
    os.environ["KB_BOUND_HOST"] = args.host

    ensure_frontend(force=args.rebuild, skip=args.no_build)

    print(f"Starting server (binding {args.host}:{args.port})")
    print(f"  Local:   http://localhost:{args.port}/")
    loopback = args.host in ("127.0.0.1", "::1", "localhost")
    if not loopback:
        print("  [!] 已绑非本机：局域网/外部可访问。确保已设访问密码。")
        # full-access 对外暴露是致命组合：联锁会在请求时降级，这里再显式提醒。
        try:
            from server.services import settings_service
            if settings_service.ai_full_access():
                print("  [!!] 检测到「放开 AI 全部权限」开着 + 非仅本机：已自动降级为受限工具集"
                      "（防远程借 AI 跑命令）。要真用全权限请只绑 127.0.0.1。")
        except Exception:
            pass
        for ip in get_lan_ips():
            print(f"  LAN:     http://{ip}:{args.port}/   (手机同 WiFi 可访问)")
    else:
        print("  (仅本机，不暴露到局域网；要对外访问加 --host 0.0.0.0)")
        # 反代部署提示：同机 nginx 转发到 loopback 会让外部访客 peer IP 变 127.0.0.1，
        # 不处理就等于免密 + 可远程 RCE。详见 INSTALL.md「部署给别人用」。
        if os.environ.get("KB_BEHIND_PROXY", "").strip().lower() not in ("1", "true", "yes", "on"):
            print("  [反代提醒] 若前面有 nginx/caddy 反向代理对外暴露：请设 KB_BEHIND_PROXY=1 "
                  "或在代理层转发 X-Forwarded-For，否则外部访客会被当本机免密直通（详见 INSTALL.md）。")
    print("Press Ctrl+C to stop")

    uvicorn.run(
        "server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
