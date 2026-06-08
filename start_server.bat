@echo off
chcp 65001 >nul
rem 一条命令启动：run.py 会按需自动构建前端再起服务。%~dp0 = 本脚本目录(可移植)。
cd /d "%~dp0"
echo Starting AI Knowledge Base on http://localhost:8001  (run.py auto-builds web/dist if needed)
python run.py %*
pause
