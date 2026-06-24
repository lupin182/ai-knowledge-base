# 安装与配置

## 环境要求

- Python 3.11+
- Node.js 18+ —— 前端是 Astro 静态站，`python run.py` 首次启动会自动 `npm install` + 构建（需要 npm）
- AI 后端三选一：
  - （推荐）[Claude CLI](https://docs.anthropic.com/en/docs/claude-code)：用 Claude 订阅，无需 API Key
  - [Codex CLI](https://developers.openai.com/codex)：用 ChatGPT/Codex 登录，无需 API Key；先运行 `codex login`，可用 `codex doctor` 检查状态
  - 或任意 OpenAI 兼容 API 的 Key（OpenAI / DeepSeek / Qwen 等）

## 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base

# 2. 装 Python 依赖
pip install -r server/requirements.txt

# 3. 启动（一条命令：首次会自动构建前端，需 Node.js）
python run.py
```

浏览器打开 http://localhost:8001 即可。

`run.py` 启动前会检查 `web/dist`：**缺失、或内容 / 前端源有更新时自动重建**（首次含 `npm install`，约 1–2 分钟），之后正常启动只是秒级的 stat 检查。想用 Claude CLI 但没装：`npm i -g @anthropic-ai/claude-code && claude` 登录一次即可。想用 Codex CLI：安装后运行 `codex login`，再用 `codex doctor` 确认已登录和网络可用。

> 改内容、日常使用都只用上面这一条命令即可。**仅当你要改 Astro 前端代码本身、想要热更新**时，才需要单独的 dev server（`cd web && npm run dev`，端口 4321）—— 见 [web/README.md](web/README.md)。

### 启动参数

```bash
python run.py --port 8080        # 指定端口
python run.py --rebuild          # 强制重建前端再启动
python run.py --no-build         # 跳过构建检查，直接用现有 web/dist
python run.py --reload           # 开发模式，后端代码改动自动重启
```

### 首次启动流程

1. 服务起来后会自动探测 `claude` / `codex` 命令是否可用：
   - 可用 → backend 默认为 `claude_cli`，**直接能用**，不用碰任何配置
   - `claude` 不可用但 `codex` 可用 → backend 默认为 `codex_cli`
   - 都不可用 → backend 默认为 `openai_api`，但 API key 为空，顶部会弹横幅
2. 点横幅或访问 `http://localhost:8001/docs/tools/settings.html` 进入设置页
3. 选 backend、填 API key / 改默认模型、（可选）设访问密码 → 保存
4. 回到首页即可使用

设置存到 `server/.settings.json`（已 gitignored），重启后保留。

## 项目结构

```
ai-knowledge-base/
├── run.py                      # 启动脚本（按需自动构建前端 + 起服务）
├── server/
│   ├── main.py                 # FastAPI 应用，挂中间件 + 路由
│   ├── auth.py                 # 安全中间件：路径防护 + 速率限制 + 密码认证
│   ├── config.py               # 真常量（路径、字符上限）
│   ├── models.py               # Pydantic 请求模型
│   ├── routes/
│   │   ├── kb.py               # /api/kbs CRUD + /_sidebar.md 动态生成 + /kb/<slug>/...
│   │   ├── chat.py             # /api/chat SSE 流式对话
│   │   ├── source.py           # /api/page-source 读源码
│   │   ├── edit.py             # /api/suggest-edit + /api/apply-edit
│   │   ├── stats.py            # /api/stats + /api/models + /api/rate-limits
│   │   └── settings.py         # /api/settings + /api/login
│   ├── services/
│   │   ├── kb_service.py       # 多 KB CRUD + 路径解析 + sidebar 生成 + 上传
│   │   └── settings_service.py # .settings.json IO + Claude/Codex CLI 自动探测
│   └── backends/
│       ├── __init__.py         # Backend 抽象 + 工厂
│       ├── claude_cli.py       # Claude CLI 子进程实现
│       ├── codex_cli.py        # Codex CLI 子进程实现
│       └── openai_api.py       # OpenAI 兼容 API 实现（带服务器侧工具调用）
├── web/                        # Astro 前端（源码）；构建产物 web/dist 由 run.py/npm 生成
│   ├── src/                    # 页面 / 组件 / 布局 / 内容配置
│   ├── scripts/sync-content.mjs # 把 knowledge_bases/ 同步进 src/content/ + 重写链接
│   └── dist/                   # 静态构建产物（gitignored，FastAPI 在 / 托管）
├── docs/                       # 前端复用资源池（Astro 直接加载）
│   ├── js/                     # ai-sidebar / editor / settings 运行时脚本
│   ├── css/                    # ai-sidebar / pdf-reader / settings 样式
│   ├── tools/
│   │   ├── pdf-reader.html     # PDF.js 阅读器（iframe 内嵌）
│   │   └── settings.html       # 设置 / KB 管理页
│   └── vendor/                 # KaTeX / CodeMirror / PDF.js / marked 本地资源
├── knowledge_bases/            # 多知识库内容目录
│   └── ai-ml-interview/
│       ├── .kb/meta.json       # KB 元数据（名称、时间戳）
│       ├── README.md
│       └── 大模型/、机器学习基础/...
└── _trash/                     # 内部"回收站"（gitignored，删除的 KB / 旧文件都进这里）
```

## 架构

```
浏览器 (localhost:8001)
  ├── Astro 静态站（web/dist），路由 /kb/<slug>/<path>/
  ├── AI 侧边栏（选中 → 对话 → 编辑文件）
  ├── KB 按钮 → 浮窗管理面板（新建/改名/删/上传 KB）
  ├── 编辑器（CodeMirror，Ctrl+Shift+E）
  └── fetch → /api/*

FastAPI 后端（同一端口）
  ├── 中间件 SecurityMiddleware：路径防护 + 速率限制 + ACCESS_PASSWORD 认证
  ├── /api/settings        GET/PUT 运行时设置（脱敏后暴露给前端）
  ├── /api/settings/check  GET     未登录也能访问，用于首次启动检测
  ├── /api/login           POST    登录
  ├── /api/kbs             GET/POST/PATCH/DELETE 多 KB CRUD
  ├── /api/kbs/<slug>/upload POST  上传文件/文件夹
  ├── /api/chat            POST    SSE 流式对话 → 走当前 backend
  ├── /api/page-source     GET     读 markdown 源码
  ├── /api/apply-edit      POST    保存源码编辑器修改
  ├── /api/stats           GET     总文件数 + 总字数
  ├── /api/models          GET     当前 backend 的模型列表
  ├── /kb/<slug>/...       GET     Astro 构建产物（web/dist，StaticFiles 托管）
  └── /*                   静态站（web/dist，catch-all；docs/ 资源同源托管）
```

### Backend 切换

三个 backend 都实现同一个 Protocol（`server/backends/__init__.py`）：

```python
class Backend(Protocol):
    name: str
    def list_models(self) -> list[dict]: ...
    def status(self) -> dict: ...
    def stream_chat(self, *, page_path, page_content, selected_text, messages,
                    model="", thinking=False, images=None, session_id="") -> Generator: ...
    def suggest_edit(self, *, page_content, instruction, chat_context="") -> str: ...
```

`get_active_backend()` 按 `settings_service.active_backend_name()` 返回 `ClaudeCLIBackend()`、`CodexCLIBackend()` 或 `OpenAIAPIBackend()`，路由层只调 backend 接口。

`claude_cli`：工作目录切到具体 KB 根，CLI 工具白名单只放 `Read,Edit,Write,Glob,Grep`，图片上传走 `.tmp_images/` 中转。

`codex_cli`：工作目录同样切到具体 KB 根，默认使用 `codex exec --json` 和用户 Codex 配置里的默认模型；设置页会从本机 `~/.codex/models_cache.json` 自动列出当前账号可见的 Codex 模型供选择。受限模式用 `read-only` / `workspace-write` sandbox；只有本机 loopback 绑定且开启 full access 时才会使用 Codex 的 bypass 模式。

Windows 注意：如果 Codex CLI 在编辑时提示 `windows sandbox` / `codex-windows-sandbox-setup.exe` / `拒绝访问 (os error 5)`，说明 Codex 的受限 sandbox helper 没能启动，受限模式下无法写入文件。只在本机私有实例使用时，可在设置页“对话默认”里勾选“放开 AI 全部权限”，并确保服务绑定 `127.0.0.1` 后重试；公开部署不要开启。

`openai_api`：服务器侧实现 `read_markdown / replace_markdown / write_markdown / search_markdown / list_markdown_files`，路径强制限制在 `knowledge_bases/<slug>/` 内、仅 `.md` 后缀、文件名不含 secret/key/token 等字段。

## 用作自己的知识库

1. Fork 或 clone 本项目
2. KB 按钮 → 新建一个空知识库（或保留 `ai-ml-interview` 当 demo）
3. 拖文件夹到 KB Manager 上传
4. `python run.py` 启动即可

如果想清空内置的 `ai-ml-interview` 改成自己的：直接在 KB 管理面板点"删"，整个目录会被搬到 `_trash/`（gitignored，不会推到远端）。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+A` | 打开/关闭 AI 侧边栏 |
| `Ctrl+Shift+E` | 打开/关闭源码编辑器 |
| `Ctrl+S`（编辑器内） | 保存文件 |
| `Escape` | 关闭当前面板 |
| `Ctrl+F`（编辑器内） | 搜索 |

## 部署给别人用

1. 设访问密码：设置页底部填密码 → 保存。本机访问仍直通，外网访问会跳登录页。
2. **反向代理必读（安全）**：后端用 `request.client.host == 127.0.0.1` 判定"本机直通免密"。
   同机反代（nginx/caddy 把外部请求转发到 loopback）会让**每个外部访客的 peer IP 都变成 127.0.0.1**，
   若不处理就等于**绕过密码、且能远程改 `cli_path` → 任意命令执行（RCE）**。二选一（建议都做）：
   - **设环境变量 `KB_BEHIND_PROXY=1` 再启动**（`KB_BEHIND_PROXY=1 python run.py`）：声明"我在反代后面"，
     后端不再信任 peer IP，外网一律走密码；本机配置高危设置时直连 uvicorn 端口（绕过反代）即可。
   - **在反代转发真实客户端 IP**：nginx 加 `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;`
     （uvicorn 默认 `forwarded_allow_ips=127.0.0.1` 会据此还原真实 IP，免密判定就会正确放行/拦截）。
   - 另外**别把 `/server/`、`/knowledge_bases/`、`/_trash/`、`/_backup/` 暴露给外网**（中间件已拦，反代层再加白名单更稳）；
     对外务必上 HTTPS（鉴权 cookie 在 HTTPS 下才带 Secure）。
3. 不要把 `server/.settings.json` 和 `server/.auth_secret` 推到 git（已在 `.gitignore`）。
