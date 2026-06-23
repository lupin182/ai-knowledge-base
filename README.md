<img src="assets/readme/cover.png" width="300" alt="AskMD">

# 欢迎使用 **AskMD**！

> 选中即问 · AI 帮你改原文 —— 一个本地优先、AI 原生的 Markdown 知识库。

[![GitHub stars](https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base.svg?style=social&label=Star)](https://github.com/JZ-Wu/ai-knowledge-base) [![GitHub watchers](https://img.shields.io/github/watchers/JZ-Wu/ai-knowledge-base.svg?style=social&label=Watch)](https://github.com/JZ-Wu/ai-knowledge-base) [![License](https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=flat-square&color=7c3aed)](LICENSE) [![Last commit](https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=flat-square&color=7c3aed)](https://github.com/JZ-Wu/ai-knowledge-base/commits)

简体中文 · [English](README.en.md)

* * *

## 简介

**AskMD** 是一个本地部署并运行的知识库系统，支持对包含 Markdown、图片与 PDF 格式文件的任意文件夹进行**检索**与**智能问答/修改**。在阅读文件过程中，可对任意文本段落进行选取，并直接调用 AI 模型进行即时问答，同时可选择让 AI 将生成结果直接写回原始文件，实现续写、改写、内容整理及多语言翻译等操作，全程无需借助外部编辑工具进行复制粘贴。本项目兼容 Claude 及 OpenAI API 接口，可使用自有模型密钥，所有数据与敏感信息都留存于本地设备。

<div align="center">
<img src="assets/readme/demo.gif" width="90%" alt="选中文字 → 问 AI → AI 改写源文件">
</div>

* * *

## 功能

- 📚 **多知识库** —— 将任意包含 Markdown 文件的目录结构构建为具备全文检索功能的知识库，所有建库、文件上传等操作均可在浏览器图形界面中完成。
- 🤖 **选中即问** —— 阅读时选中任意段落，一键问 AI，回答在页面右侧流式弹出。
- ✍️ **AI 帮你改原文** —— 让 AI 续写、改写、整理、翻译，它会**直接修改你的 Markdown 源文件**。
- 🔎 **全站搜索与自动导航** —— 侧栏、目录、面包屑、最近更新全部自动生成。
- 🧾 **PDF 阅读与批注** —— 内置 PDF 阅读器：选中文字问 AI、高亮、写行内评论，还帮你记着读到哪。
- 🧮 **公式 · 代码 · 图片** —— 原生支持 KaTeX 数学公式、代码高亮和图片。
- 🔌 **接你自己的模型** —— 支持 Claude 与任意 OpenAI 兼容 API，全部本地运行。
- ⚡ **一条命令启动** —— `python run.py`，自动构建并打开浏览器即可使用。

<div align="center">
<img src="assets/readme/home.png" width="88%" alt="AskMD 主页：搜索、专题卡片、统计">
<br><br>
<img src="assets/readme/api-config.png" width="62%" alt="后端 / API 配置：Claude CLI 或任意 OpenAI 兼容 API">
</div>

* * *

## 快速开始

```bash
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
pip install -r server/requirements.txt
python run.py            # → http://localhost:8001
```

**环境要求**：Python 3.11+ · Node.js 18+（仅首次构建需要）· 一个 AI 后端：已登录的 **Claude CLI** 或任意 **OpenAI 兼容** API key。Windows / macOS / Linux 均可。

打开 `http://localhost:8001` 即可开始使用。如果想创建一个新知识库，可以在浏览器界面中直接新建知识库，然后上传所需文件即可，或者手动操作目录，在 `knowledge_bases/<名字>/` 里放 Markdown 即可成为一个新知识库；模型、密码等都可以在浏览器的设置页里点选。更多见 [INSTALL.md](INSTALL.md)。

### 快捷键

| 按键 | 操作 |
| :--- | :--- |
| `Ctrl+Shift+A` | 打开 / 关闭 AI 侧栏 |
| `Ctrl+Shift+E` | 打开 / 关闭源码编辑器 |
| `Ctrl+S` | 保存 |

* * *

## 许可证

基于 [MIT 许可证](LICENSE) 开源，欢迎提 issue 和 PR。

如果觉得 **AskMD** 对你有用的话，欢迎点一个 ⭐ Star以表达对项目的支持！！！
