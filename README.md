<div align="center">

<img src="assets/readme/logo.png" width="110" alt="AI Knowledge Base logo">

<img src="assets/readme/title.png" width="500" alt="AI Knowledge Base">

### 一个本地运行的 Markdown 知识库 —— 选中任意文字就能问 AI，还能让它直接帮你改原文。

**简体中文** · [English](README.en.md)

<a href="https://github.com/JZ-Wu/ai-knowledge-base/stargazers"><img src="https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=github&color=2fbf60" alt="stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=2fbf60" alt="license"></a>
<img src="https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=git&logoColor=white&color=2fbf60" alt="last-commit">

</div>

<div align="center">
<img src="assets/readme/demo.gif" width="92%" alt="AI Knowledge Base 演示">
</div>

> 把任意一个装着 Markdown、图片和 PDF 的文件夹，变成一个**可搜索、带 AI 助手**的本地知识库网站。阅读时选中一段文字就能直接问 AI，还能让它把答案**直接写回你的源文件**。

## ✨ 功能

- 📚 **多知识库** —— 把任意 Markdown 文件夹变成可搜索、可导航的知识库网站，想建几个建几个，界面里就能新建 / 重命名 / 上传。
- 🤖 **选中即问** —— 阅读时选中任意段落，一键问 AI，回答就在页面右侧流式弹出。
- ✍️ **AI 帮你改原文** —— 让 AI 续写、改写、整理、翻译，它会**直接改好你的 Markdown 源文件**，不用再复制粘贴回来。
- 🔎 **全站搜索与自动导航** —— 侧栏、目录、面包屑、最近更新全部自动生成，开箱即用。
- 🧾 **PDF 阅读与批注** —— 内置 PDF 阅读器，选中文字问 AI、高亮、写行内评论，读到哪、读没读都帮你记着。
- 🧮 **公式 · 代码 · 图片** —— 原生支持 KaTeX 数学公式、代码高亮和图片。
- 🔌 **接你自己的模型** —— 支持 Claude 与任意 OpenAI 兼容 API，全部在本地运行，笔记不出本机。
- ⚡ **一条命令启动** —— `python run.py`，自动构建并打开浏览器即可使用。

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

**环境要求**：Python 3.11+ · Node.js 18+（仅首次构建需要）· 一个 AI 后端：已登录的 **Claude CLI** 或任意 **OpenAI 兼容** API key。Windows / macOS / Linux 均可。

打开 `http://localhost:8001` 就能开始用。在 `知识库/<名字>/` 里放 Markdown 即可成为一个新知识库；模型、密码等都在浏览器的设置页里点选。详见 [INSTALL.md](INSTALL.md)。

### ⌨️ 快捷键

| 按键 | 操作 |
| :--- | :--- |
| `Ctrl+Shift+A` | 打开 / 关闭 AI 侧栏 |
| `Ctrl+Shift+E` | 打开 / 关闭源码编辑器 |
| `Ctrl+S` | 保存 |

## 📄 许可证

[MIT](LICENSE) 开源。问题与 PR 都欢迎。

<div align="center"><sub>如果它帮到你，点个 ⭐ 能让更多人发现它。</sub></div>
