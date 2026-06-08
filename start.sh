#!/bin/bash
# 一条命令启动：run.py 会按需自动构建前端(web/dist)再起服务。
cd "$(dirname "$0")"

if lsof -i :8001 &>/dev/null; then
    echo "Server already running on port 8001"
    exit 0
fi

# 后台启动；run.py 在 web/dist 缺失或源码更新时会自动 npm install + build（日志见下）。
nohup python3 run.py --host 0.0.0.0 --port 8001 > /tmp/knowledge-base.log 2>&1 &
echo "AI Knowledge Base started (run.py auto-builds web/dist if needed):"
echo "  Local:   http://localhost:8001/"
echo "Log: /tmp/knowledge-base.log"
