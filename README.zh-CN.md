<div align="center">

<img src="assets/readme/logo.png" width="110" alt="AI Knowledge Base logo">

<img src="assets/readme/title.png" width="520" alt="AI Knowledge Base">

### 你的 Markdown 笔记，配一个能阅读、批注、还能直接帮你改源文件的 AI。

[English](README.md) · **简体中文**

<a href="https://github.com/JZ-Wu/ai-knowledge-base/stargazers"><img src="https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=github&color=2fbf60" alt="stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=2fbf60" alt="license"></a>
<img src="https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=git&logoColor=white&color=2fbf60" alt="last-commit">
<img src="https://img.shields.io/github/languages/top/JZ-Wu/ai-knowledge-base?style=for-the-badge&color=2fbf60" alt="top-language">

<sub>技术栈</sub><br>
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Astro-BC52EE.svg?style=flat-square&logo=astro&logoColor=white" alt="Astro">
<img src="https://img.shields.io/badge/TypeScript-3178C6.svg?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
<img src="https://img.shields.io/badge/PDF.js-F40F02.svg?style=flat-square" alt="PDF.js">
<img src="https://img.shields.io/badge/KaTeX-2364AA.svg?style=flat-square" alt="KaTeX">

</div>

---

**AI Knowledge Base** 把任意一个装着 Markdown、图片和 PDF 的文件夹，发布成一个快速、可搜索的静态站点 —— 并在页面里内置了一个 AI 助手。**选中一段文字、提一个问题，助手不仅会回答，还能直接改写背后的 `.md` 源文件** —— 全程在一个受控的工具边界内，绝不越出你的知识库。一切都跑在本地、单端口之后：一条命令即可构建站点并启动服务。

它是 **本地优先**（笔记不出本机）、**多知识库**（每个 `knowledge_bases/<slug>/` 都是独立站点）、**后端无关**（用已登录的 Claude CLI 或任意 OpenAI 兼容 API 驱动）。

<div align="center">
<img src="assets/readme/workflow.svg" width="92%" alt="AI Knowledge Base 工作流">
</div>

## ✨ 核心特性

|     | 特性 | 说明 |
| :-: | :--- | :--- |
| 📖 | **Markdown 知识库阅读** | 每个 `knowledge_bases/<slug>/` 是一个独立 KB，由 Astro 发布成静态站，自动生成侧栏、面包屑、TOC 与「最近更新」（来自本地 git 历史）。 |
| 🤖 | **页面内置 AI** | 选中文本或带整页上下文，通过流式侧栏提问（SSE：文本、思考、工具调用、用量）。后端可插拔 —— **Claude CLI** 或任意 **OpenAI 兼容** API，支持多个模型 profile。 |
| ✍️ | **AI 直接改源文件** | 助手可通过**受控工具边界**对 Markdown 执行 `read` / `search` / `replace` / `write`，作用域锁定当前 KB —— 路径校验、仅限 `.md`、拒绝隐藏目录 / 上级路径 / 疑似密钥文件。 |
| 🧾 | **PDF 阅读与批注** | 基于 PDF.js 的阅读器：选区问 AI、几何锚定高亮、行内评论线程，且持久化时**不触发重建**。Claude 后端可把页面渲染成图片，回答图表 / 公式类问题。 |
| 🗃️ | **多知识库管理** | 在界面里列出、新建、重命名、删除 KB。删除会移入 `_trash/`（绝不物理删除）；上传限制在 KB 内、仅放行安全后缀。 |
| 🔐 | **本地优先且安全** | 未设密码时仅允许本机访问（scrypt 哈希、HMAC cookie）。内部路径（`/server/`、`/.git/`、`/knowledge_bases/`…）被拦截；登录与聊天均有速率限制。 |
| ⚙️ | **一条命令，原子构建** | `python run.py` 自动安装依赖、同步内容、构建 Astro，采用 **build-to-temp + 原子换入**，服务器永远不会吐出构建到一半的页面。 |

<div align="center">
<img src="assets/readme/preview1.png" width="88%" alt="阅读页与 AI 侧栏">
<br><br>
<img src="assets/readme/preview2.png" width="88%" alt="PDF 阅读与批注">
</div>

## 🚀 快速开始

```bash
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
pip install -r server/requirements.txt
python run.py            # → http://localhost:8001
```

`run.py` 是唯一入口：首次启动会自动 `npm install`、同步内容、构建 Astro 站点，然后在同一个端口同时托管前端**与** API。强制重建用 `python run.py --rebuild`。

**环境要求** —— Python 3.11+ · Node.js 18+（仅首次构建需要）· 二选一的 AI 后端：已登录的 **Claude CLI** 或任意 **OpenAI 兼容** API key。Windows / macOS / Linux 均支持（Windows 控制台编码与 OneDrive 构建占用已为你处理好）。

运行期设置全部在浏览器里管理，无需手改配置文件：

```text
http://localhost:8001/docs/tools/settings.html
```

在那里选择后端、模型 profile、访问密码、默认上下文 / 工具行为、外部挂载 —— 保存到已被 gitignore 的 `server/.settings.json`。部署与反向代理见 [INSTALL.md](INSTALL.md)。

### ⌨️ 快捷键

| 按键 | 操作 |
| :--- | :--- |
| `Ctrl+Shift+E` | 打开 / 关闭 Markdown 源码编辑器 |
| `Ctrl+Shift+A` | 打开 / 关闭 AI 侧栏 |
| `Ctrl+S` | 在编辑器中保存 |
| `Esc` | 关闭当前面板 |

## 🗂️ 内容组织方式

所有内容放在 `knowledge_bases/<slug>/`（slug 匹配 `[A-Za-z0-9_-]{1,64}`），URL 入口为 `/kb/<slug>/...`。放一个 `README.md` 作为 KB 首页；可选加 `_sidebar.md` 手工精排导航，或让文件夹结构自动生成可折叠树。首页卡片与顶栏 / 侧栏的 KB 列表会自动发现每个目录 —— 新增一个 KB **零配置**。

```text
ai-knowledge-base/
├── run.py                 # 单一入口：一条命令构建 + 托管
├── server/                # FastAPI 应用、鉴权、路由、服务、后端
│   ├── main.py            # 应用 + 安全中间件 + 静态托管
│   ├── backends/          # claude_cli.py · openai_api.py
│   └── services/          # KB CRUD、侧栏、build-to-temp + 原子换入
├── web/                   # Astro 静态站（内容、布局、搜索索引）
├── docs/tools/            # PDF 阅读器、设置页
├── scripts/               # sync_core.py · extract_pdf.py
└── knowledge_bases/       # 你的 KB（内置 ai-ml-interview）
```

内置的 **`ai-ml-interview`** 知识库覆盖大模型、机器学习基础、强化学习、视觉、具身智能、CUDA 编程、分布式训练、行业动态与面试手撕。

## 🛣️ 路线图

- [x] 多知识库基础 —— 新建 / 重命名 / 删除 / 上传 / 统计
- [x] Astro 静态构建 —— 内容同步、资源镜像、链接重写、搜索索引
- [x] AI 阅读与编辑 —— Claude CLI + OpenAI 兼容、受限工具调用、页面上下文
- [x] PDF 阅读与批注 —— PDF.js、选区问 AI、行内线程、阅读状态持久化
- [x] 安全边界 —— 本机免密、scrypt 密码、路径拦截、速率限制
- [ ] 自动化测试覆盖 —— 路由、路径安全、同步构建、批注、前端
- [ ] 性能基准 —— 大 KB、外部挂载、大量图片 / PDF 构建
- [ ] 更多文档 —— 真实截图、部署示例、反向代理模板

## 🤝 参与贡献

欢迎围绕新功能、AI 编辑边界、PDF 阅读器、本地部署体验提 issue 与 PR。Bug 请附最小复现（启动命令、浏览器路径、后端日志、截图）；PR 请说明动机与验证命令。

<details>
<summary><b>本地开发</b></summary>

```bash
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
git checkout -b feature/your-change

# 推送前自检
python -m compileall run.py server scripts
cd web && npm run build
```

框架共享代码（`server/`、`web/src/`、skills…）由 [kb-core](https://github.com/JZ-Wu/kb-core) 镜像而来，改动前请先读 [CLAUDE.md](CLAUDE.md)。
</details>

<details>
<summary><b>最近更新</b></summary>

- **2026-06-19** 🧭 优化 PDF 阅读器导航（移除冗余返回按钮）。
- **2026-06-18** 📄 PDF 自动适配接入 `ResizeObserver`，缩放 / 容器变化后自动重排版。
- **2026-06-17** 💬 PDF 行内评论线程锚定到页面几何选区，刷新后仍能定位。
- **2026-06-17** 📚 合并全库阅读状态，外部页面也显示已读 / 在读 / 笔记标记。
- **2026-06-11** 🛡️ HTML/CSS/JS 改用 `no-cache` 重新验证，避免浏览器跑旧脚本。
</details>

## 📄 许可证

基于 [MIT 许可证](LICENSE) 开源。

## 🙏 致谢

构建于 **FastAPI**、**Uvicorn**、**Astro**、**MDX**、**KaTeX**、**PDF.js**、**CodeMirror**、**Marked**，由 **Claude CLI** 与 **OpenAI 兼容** Chat Completions 提供问答、改写与工具调用能力。

<div align="center"><sub>如果它帮你省了时间，点个 ⭐ 能让更多人发现它。</sub></div>
