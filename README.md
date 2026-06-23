<img src="assets/readme/cover.png" width="300" alt="AskMD">

# 欢迎使用 **AskMD**！

> 选中即问 · AI 帮你改原文 —— 一个本地优先、AI 原生的 Markdown 知识库。

[![GitHub stars](https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base.svg?style=social&label=Star)](https://github.com/JZ-Wu/ai-knowledge-base) [![GitHub watchers](https://img.shields.io/github/watchers/JZ-Wu/ai-knowledge-base.svg?style=social&label=Watch)](https://github.com/JZ-Wu/ai-knowledge-base) [![License](https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=flat-square&color=7c3aed)](LICENSE) [![Last commit](https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=flat-square&color=7c3aed)](https://github.com/JZ-Wu/ai-knowledge-base/commits)

简体中文 · [English](README.en.md)

* * *

## 简介

**AskMD** 把任意一个装着 Markdown、图片和 PDF 的文件夹，变成一个**可搜索、带 AI 助手**的本地知识库网站。

它最特别的地方是：阅读时**选中任意一段文字就能直接问 AI**，而且可以让 AI 把答案**直接写回你的源文件**——续写、改写、整理、翻译都不用再复制粘贴。一切都在本地运行，接你自己的 Claude 或 OpenAI 兼容模型，笔记不出本机。一条命令就能跑起来。

<div align="center">
<img src="assets/readme/demo.gif" width="90%" alt="选中文字 → 问 AI → AI 改写源文件">
</div>

* * *

## 功能

- 📚 **多知识库** —— 把任意 Markdown 文件夹变成可搜索、可导航的知识库网站，想建几个建几个，界面里就能新建 / 重命名 / 上传。
- 🤖 **选中即问** —— 阅读时选中任意段落，一键问 AI，回答在页面右侧流式弹出。
- ✍️ **AI 帮你改原文** —— 让 AI 续写、改写、整理、翻译，它会**直接改好你的 Markdown 源文件**。
- 🔎 **全站搜索与自动导航** —— 侧栏、目录、面包屑、最近更新全部自动生成。
- 🧾 **PDF 阅读与批注** —— 内置 PDF 阅读器：选中文字问 AI、高亮、写行内评论，还帮你记着读到哪。
- 🧮 **公式 · 代码 · 图片** —— 原生支持 KaTeX 数学公式、代码高亮和图片。
- 🔌 **接你自己的模型** —— 支持 Claude 与任意 OpenAI 兼容 API，全部本地运行。
- ⚡ **一条命令启动** —— `python run.py`，自动构建并打开浏览器即可使用。

<div align="center">
<img src="assets/readme/preview1.png" width="86%" alt="阅读页与 AI 侧栏">
<br><br>
<img src="assets/readme/preview2.png" width="86%" alt="PDF 阅读与批注">
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

打开 `http://localhost:8001` 就能开始用。在 `knowledge_bases/<名字>/` 里放 Markdown 即可成为一个新知识库；模型、密码等都在浏览器的设置页里点选。更多见 [INSTALL.md](INSTALL.md)。

### 快捷键

| 按键 | 操作 |
| :--- | :--- |
| `Ctrl+Shift+A` | 打开 / 关闭 AI 侧栏 |
| `Ctrl+Shift+E` | 打开 / 关闭源码编辑器 |
| `Ctrl+S` | 保存 |

* * *

## 许可证

基于 [MIT 许可证](LICENSE) 开源，欢迎提 issue 和 PR。

如果 **AskMD** 帮到了你，欢迎点一个 ⭐ Star——这是对项目最简单也最有力的支持。
