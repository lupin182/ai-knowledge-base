[<img src="assets/readme/logo.png" align="right" width="25%" padding-right="350">]()

<p align="left">
	<img src="assets/readme/title.png" width="62%" alt="AI Knowledge Base">
</p>

#### 一个面向 Markdown 多知识库的本地优先 AI 阅读、搜索、批注、编辑与静态发布工作台。

<p align="left">
	<a href="LICENSE"><img src="https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=2fbf60" alt="license"></a>
	<img src="https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=git&logoColor=white&color=2fbf60" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/JZ-Wu/ai-knowledge-base?style=for-the-badge&color=2fbf60" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/JZ-Wu/ai-knowledge-base?style=for-the-badge&color=2fbf60" alt="repo-language-count">
</p>
<p align="left">
		<em>_Built with:_</em>
</p>
<p align="left">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
	<img src="https://img.shields.io/badge/Astro-BC52EE.svg?style=for-the-badge&logo=astro&logoColor=white" alt="Astro">
	<img src="https://img.shields.io/badge/TypeScript-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript">
	<img src="https://img.shields.io/badge/Markdown-000000.svg?style=for-the-badge&logo=markdown&logoColor=white" alt="Markdown">
	<img src="https://img.shields.io/badge/KaTeX-2364AA.svg?style=for-the-badge" alt="KaTeX">
	<img src="https://img.shields.io/badge/PDF.js-F40F02.svg?style=for-the-badge" alt="PDF.js">
	<img src="https://img.shields.io/badge/CodeMirror-1F2937.svg?style=for-the-badge" alt="CodeMirror">
</p>
<br>

## 🔗 目录

I. [📰 最新动态](#news)
II. [📍 项目概览](#overview)
III. [🕹️ 功能特性](#features)
IV. [🗂️ 项目结构](#structure)
V. [🚀 快速开始](#quick-start)
VI. [📊 项目路线图](#roadmap)
VII. [🤝 参与贡献](#contributing)
VIII. [🎫 许可证](#license)
IX. [🙏 致谢](#acknowledgments)

---

<a id="news"></a>

## 📰 最新动态

- **2026-06-19** 🧭 优化 PDF 阅读器导航：移除冗余的返回按钮，让阅读页操作更聚焦。
- **2026-06-18** 📄 改进 PDF 自动适配：接入 ResizeObserver，页面缩放和容器变化后能自动重新排版。
- **2026-06-18** 🧰 统一 PDF 选区工具条：合并“问 AI”和“笔记”入口，减少选中文本后的按钮冲突。
- **2026-06-17** 💬 新增 PDF 行内评论线程：评论锚定到页面几何选区，刷新后仍能定位。
- **2026-06-17** 📝 完善高亮批注模型：每条高亮支持多条 comments，笔记弹窗改为居中 modal。
- **2026-06-17** 📚 合并全库阅读状态：外部页面也能显示所有 KB 文章的已读、在读和笔记标记。
- **2026-06-16** 🗂️ 优化外部内容卡片：新增外部卡片会进入已有 curated 分组，不再生成孤立自动分组。
- **2026-06-11** 🛡️ 改进静态缓存策略：HTML、CSS、JS 使用 no-cache 重新验证，避免前端更新后浏览器继续运行旧脚本。

---

<a id="overview"></a>

## 📍 项目概览

AI Knowledge Base 把 `knowledge_bases/<slug>/` 下的 Markdown、图片、PDF 和结构化资料发布成可搜索的 Astro 静态站，并由 FastAPI 在同一个端口托管前端与 API。用户可以在浏览器里阅读、搜索、标注、编辑源码，也可以让 Claude CLI 或 OpenAI 兼容 API 在受控工具边界内读取、搜索和修改知识库 Markdown。

根入口是 [`run.py`](run.py)。它会按需执行前端同步和 Astro 构建，然后启动 `server.main:app`，默认监听 `127.0.0.1:8001`。

<p align="center">
	<img src="assets/readme/workflow.svg" width="92%" alt="AI Knowledge Base workflow">
</p>

---

<a id="features"></a>

## 🕹️ 功能特性

|      | 功能 | 说明 |
| :--- | :---: | :--- |
| 📖 | **Markdown 知识库阅读** | <ul><li>每个 `knowledge_bases/<slug>/` 目录都是一个独立 KB。</li><li>Astro 将 `README.md` 归一成目录页，并把相对 Markdown 链接改写为稳定的绝对站内路径。</li><li>内置 `ai-ml-interview` 覆盖大模型、机器学习基础、强化学习、视觉、具身智能、CUDA、分布式训练、行业动态和面试手撕等主题。</li></ul> |
| 🔎 | **静态搜索与目录导航** | <ul><li>`web/src/pages/search-index.json.ts` 在构建期生成全站搜索索引。</li><li>侧栏、面包屑、TOC 和最近更新均来自内容集合与本地 git 历史。</li><li>缺少手写 `_sidebar.md` 时，后端可按 KB 目录自动构建 Markdown 侧栏。</li></ul> |
| 🤖 | **AI 侧边栏与模型选择** | <ul><li>`/api/chat` 使用 SSE 流式输出文本、思考、工具调用、用量和会话信息。</li><li>支持 Claude CLI 和 OpenAI 兼容 Chat Completions，可在设置页维护多个模型 profile。</li><li>支持选中文本、页面全文上下文、图片输入、KB 级附加提示词和 CLI session resume。</li></ul> |
| ✍️ | **受控文件编辑** | <ul><li>OpenAI 后端提供 `read_markdown`、`replace_markdown`、`write_markdown`、`search_markdown`、`list_markdown_files`。</li><li>Claude CLI 默认只放行 `Read/Edit/Write/Glob/Grep`，并把工作目录限制到当前 KB。</li><li>路径校验拒绝隐藏目录、上级路径、绝对路径、非 `.md` 写入和疑似密钥文件名。</li></ul> |
| 🗃️ | **多知识库管理** | <ul><li>`/api/kbs` 支持列出、新建、重命名和删除 KB。</li><li>删除会移动到 `_trash/knowledge_bases/`，不会直接物理删除。</li><li>上传支持 Markdown、PDF、图片、CSV、TSV、JSON 等安全后缀。</li></ul> |
| 🧾 | **PDF 阅读与批注** | <ul><li>`docs/tools/pdf-reader.html` 基于 PDF.js，支持选区问 AI、页面适配和几何锚定高亮。</li><li>阅读状态与批注保存到 `.kb/reading-state.json` 或 `.reading-external.json`，不触发静态重建。</li><li>Claude CLI 后端可把论文 PDF 按页渲染为图片，回答图表、公式和版面相关问题时按需读取。</li></ul> |
| 🔐 | **本地优先安全边界** | <ul><li>未设置访问密码时只允许本机访问；远程请求会被拒绝。</li><li>访问密码使用 stdlib scrypt 哈希存储，cookie 使用 HMAC token。</li><li>中间件拦截 `/server/`、`/.git/`、`/knowledge_bases/`、`/_trash/` 等内部路径，并对登录和聊天做速率限制。</li></ul> |
| ⚙️ | **按需构建与原子换入** | <ul><li>`run.py` 首启或源内容更新时自动 `npm install`、同步内容并构建 Astro。</li><li>`rebuild_service` 构建到临时目录，再原子替换 dist，避免服务半成品页面。</li><li>构建产物默认放在同盘 `.kb-build/<repo-hash>/dist`，避开 OneDrive 占用。</li></ul> |

<p align="center">
	<img src="assets/readme/preview1.png" width="88%" alt="AI Knowledge Base preview 1">
</p>
<p align="center">
	<img src="assets/readme/preview2.png" width="88%" alt="AI Knowledge Base preview 2">
</p>

---

<a id="structure"></a>

## 🗂️ 项目结构

```text
ai-knowledge-base/
|-- README.md
|-- LICENSE
|-- INSTALL.md
|-- CLAUDE.md
|-- run.py
|-- start_server.bat
|-- start.sh
|-- assets/
|   `-- readme/
|       |-- logo.png
|       |-- title.png
|       |-- workflow.svg
|       |-- preview1.png
|       `-- preview2.png
|-- server/
|   |-- main.py
|   |-- auth.py
|   |-- config.py
|   |-- models.py
|   |-- routes/
|   |-- services/
|   |-- backends/
|   `-- .env.example
|-- web/
|   |-- package.json
|   |-- astro.config.mjs
|   |-- scripts/
|   `-- src/
|-- docs/
|   |-- css/
|   |-- js/
|   |-- tools/
|   `-- vendor/
|-- scripts/
|   |-- sync_core.py
|   `-- extract_pdf.py
`-- knowledge_bases/
    `-- ai-ml-interview/
        |-- README.md
        |-- 大模型/
        |-- 机器学习基础/
        |-- 强化学习/
        |-- 视觉/
        |-- 具身智能/
        |-- CUDA编程/
        |-- 分布式训练/
        |-- 行业动态/
        `-- 面试手撕/
```

### 📇 项目索引

<details open>
	<summary><b><code>server/</code></b></summary>
	<blockquote>
		<table>
		<tr>
			<td><b><a href="server/main.py">server/main.py</a></b></td>
			<td>FastAPI 应用入口，注册安全中间件、API 路由和静态站点托管。</td>
		</tr>
		<tr>
			<td><b><a href="server/auth.py">server/auth.py</a></b></td>
			<td>路径防护、速率限制、访问密码、登录 cookie 和反向代理安全判定。</td>
		</tr>
		<tr>
			<td><b><a href="server/services/kb_service.py">server/services/kb_service.py</a></b></td>
			<td>KB CRUD、slug 校验、路径解析、上传保存、侧栏生成和统计。</td>
		</tr>
		<tr>
			<td><b><a href="server/services/rebuild_service.py">server/services/rebuild_service.py</a></b></td>
			<td>按需重建 Astro 静态站，使用 build-to-temp + atomic swap。</td>
		</tr>
		<tr>
			<td><b><a href="server/backends/claude_cli.py">server/backends/claude_cli.py</a></b></td>
			<td>通过 Claude CLI 调用模型，提供受限工具集、图片输入、PDF 按页视觉读取和 session resume。</td>
		</tr>
		<tr>
			<td><b><a href="server/backends/openai_api.py">server/backends/openai_api.py</a></b></td>
			<td>OpenAI 兼容 Chat Completions 后端，服务器侧执行受控 Markdown 工具。</td>
		</tr>
		</table>
	</blockquote>
</details>

<details open>
	<summary><b><code>web/</code></b></summary>
	<blockquote>
		<table>
		<tr>
			<td><b><a href="web/scripts/sync-content.mjs">web/scripts/sync-content.mjs</a></b></td>
			<td>把 KB 内容同步到 Astro content collection，重写链接并镜像图片、PDF、JSON、CSV 等静态资源。</td>
		</tr>
		<tr>
			<td><b><a href="web/src/pages/index.astro">web/src/pages/index.astro</a></b></td>
			<td>首页统计、专题卡片和最近更新，数据来自内容集合与 git 历史。</td>
		</tr>
		<tr>
			<td><b><a href="web/src/pages/[...slug].astro">web/src/pages/[...slug].astro</a></b></td>
			<td>知识库文档页，渲染正文、面包屑和创建/更新时间。</td>
		</tr>
		<tr>
			<td><b><a href="web/src/pages/search-index.json.ts">web/src/pages/search-index.json.ts</a></b></td>
			<td>构建期生成搜索索引，供前端即时搜索使用。</td>
		</tr>
		</table>
	</blockquote>
</details>

---

<a id="quick-start"></a>

## 🚀 快速开始

### ☑️ 环境要求

- **Python:** 3.11+
- **Node.js:** 18+，首次构建前端时需要 `npm`
- **AI 后端二选一:** 已登录的 Claude CLI，或任意 OpenAI 兼容 API key
- **推荐系统:** Windows、macOS、Linux 均可；Windows 下项目已处理控制台编码和 OneDrive 构建占用问题

### ⚙️ 安装

1. 克隆仓库：

```powershell
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
```

2. 安装 Python 依赖：

```powershell
pip install -r server/requirements.txt
```

3. 启动单端口服务：

```powershell
python run.py
```

启动后访问：

```text
http://localhost:8001/
```

### 🛠️ 配置

运行时设置主要通过浏览器设置页管理：

```text
http://localhost:8001/docs/tools/settings.html
```

设置会保存到 `server/.settings.json`，该文件已被 `.gitignore` 排除。可配置内容包括：

```text
backend = claude_cli | openai_api
Claude CLI 路径与模型列表
OpenAI 兼容 API base_url / api_key / 模型 profile
访问密码
默认是否带页面全文
默认是否允许 AI 工具调用
外部目录挂载
```

`.env` 只保留启动期常量示例：

```powershell
Copy-Item server/.env.example server/.env
```

可选项包括 `DEFAULT_KB_SLUG` 和 `EXTERNAL_MOUNTS`。API key、访问密码和模型列表不要写进 `.env`。

### 🧪 使用方式

常用启动参数：

```powershell
python run.py --port 8080
python run.py --rebuild
python run.py --no-build
python run.py --reload
```

前端开发模式：

```powershell
python run.py --no-build
cd web
npm install
npm run dev
```

打开源码编辑器和 AI 侧边栏：

```text
Ctrl+Shift+E  打开或关闭 Markdown 源码编辑器
Ctrl+Shift+A  打开或关闭 AI 侧边栏
Ctrl+S        在编辑器中保存
Esc           关闭当前面板
```

### 🗄️ 数据准备

新增知识库有两种方式：

```text
1. 在设置页 / KB 管理面板中新建或上传目录。
2. 手动创建 knowledge_bases/<slug>/README.md，然后重新构建。
```

`slug` 必须匹配 `[A-Za-z0-9_-]{1,64}`。上传文件会限制在 KB 内部，并只允许安全后缀。删除 KB 时会移动到 `_trash/knowledge_bases/`。

### ✅ 验证

静态语法检查：

```powershell
python -m compileall run.py server scripts
```

同步并构建前端：

```powershell
cd web
npm run sync
npm run build
```

如需只验证启动链路，可执行：

```powershell
python run.py --no-build
```

---

<a id="roadmap"></a>

## 📊 项目路线图

- [x] **`多知识库基础结构`**: 使用 `knowledge_bases/<slug>/` 管理独立 KB，并提供创建、重命名、删除、上传和统计接口。
- [x] **`Astro 静态站构建`**: 同步 Markdown 内容、镜像资源、重写链接、生成搜索索引和目录式路由。
- [x] **`AI 阅读与编辑`**: 支持 Claude CLI 与 OpenAI 兼容 API，提供受限工具调用和页面上下文注入。
- [x] **`PDF 阅读与批注`**: 集成 PDF.js、选区问 AI、行内评论线程和阅读状态持久化。
- [x] **`安全边界`**: 本机免密、远程需密码、scrypt 哈希、路径拦截、速率限制和 full-access 联锁降级。
- [ ] **`自动化测试覆盖`**: 扩展后端路由、路径安全、同步构建、PDF 批注和前端交互的回归测试。
- [ ] **`性能基准`**: 记录大 KB、外部挂载、大量图片/PDF 和不同构建环境下的同步与构建耗时。
- [ ] **`文档素材`**: 增补更多真实使用截图、部署示例、反向代理模板和自定义 KB 教程。

---

<a id="contributing"></a>

## 🤝 参与贡献

- **讨论:** 欢迎围绕 Markdown 知识库工作流、AI 编辑边界、PDF 阅读和本地部署体验提出建议。
- **问题反馈:** 请附带最小复现步骤、启动命令、浏览器路径、后端日志摘要和必要截图。
- **合并请求:** 建议在 PR 中说明改动动机、涉及文件、验证命令和对知识库内容或构建产物的影响。

<details closed>
<summary>贡献指南</summary>

1. Fork 仓库。
2. 克隆到本地：
   ```powershell
   git clone https://github.com/JZ-Wu/ai-knowledge-base.git
   ```
3. 创建分支：
   ```powershell
   git checkout -b feature/your-change
   ```
4. 保持改动聚焦；框架共享代码请先阅读 [`CLAUDE.md`](CLAUDE.md) 中关于 `kb-core` 同步的说明。
5. 运行至少一组检查：
   ```powershell
   python -m compileall run.py server scripts
   cd web
   npm run build
   ```
6. 提交并推送：
   ```powershell
   git commit -m "feat: describe your change"
   git push origin feature/your-change
   ```
7. 创建 Pull Request，并说明验证结果。

</details>

---

<a id="license"></a>

## 🎫 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

---

<a id="acknowledgments"></a>

## 🙏 致谢

- FastAPI、Uvicorn、Astro、MDX、KaTeX、PDF.js、CodeMirror 和 Marked 支撑了本项目的阅读、构建、编辑与渲染链路。
- Claude CLI 与 OpenAI 兼容 Chat Completions 为知识库问答、改写和工具调用提供后端能力。

---
