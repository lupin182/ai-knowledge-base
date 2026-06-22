<div align="center">

<img src="assets/readme/logo.png" width="110" alt="AI Knowledge Base logo">

<img src="assets/readme/title.png" width="500" alt="AI Knowledge Base">

### A local Markdown knowledge base — select any text to ask AI, and let it edit the source for you.

[简体中文](README.md) · **English**

<a href="https://github.com/JZ-Wu/ai-knowledge-base/stargazers"><img src="https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=github&color=2fbf60" alt="stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=2fbf60" alt="license"></a>
<img src="https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=git&logoColor=white&color=2fbf60" alt="last-commit">

</div>

<div align="center">
<img src="assets/readme/demo.gif" width="92%" alt="AI Knowledge Base demo">
</div>

> Turn any folder of Markdown, images and PDFs into a **searchable, AI-powered** local knowledge base. Select a passage while reading to ask AI — and have it **write the answer straight back into your source file**.

## ✨ Features

- 📚 **Multiple knowledge bases** — turn any Markdown folder into a searchable, navigable site; create, rename and upload right from the UI.
- 🤖 **Select to ask** — highlight any passage while reading and ask AI; the answer streams into a side panel.
- ✍️ **AI edits your files** — let AI continue, rewrite, reorganize or translate, and it **edits your Markdown source directly** — no copy-paste back.
- 🔎 **Search & auto-navigation** — sidebar, TOC, breadcrumbs and "recent updates" are generated for you.
- 🧾 **PDF reading & annotation** — built-in PDF reader: ask AI about a selection, highlight, leave inline comments, and it remembers what you've read.
- 🧮 **Math · code · images** — native KaTeX formulas, code highlighting and images.
- 🔌 **Bring your own model** — works with Claude and any OpenAI-compatible API, all running locally — your notes never leave your machine.
- ⚡ **One command** — `python run.py` builds everything and opens in your browser.

<div align="center">
<img src="assets/readme/preview1.png" width="88%" alt="Reading with the AI side panel">
<br><br>
<img src="assets/readme/preview2.png" width="88%" alt="PDF reading and annotation">
</div>

## 🚀 Quick start

```bash
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
pip install -r server/requirements.txt
python run.py            # → http://localhost:8001
```

**Requirements**: Python 3.11+ · Node.js 18+ (first build only) · one AI backend: a logged-in **Claude CLI** or any **OpenAI-compatible** API key. Works on Windows, macOS and Linux.

Open `http://localhost:8001` and you're in. Drop Markdown into `knowledge_bases/<name>/` to add a knowledge base; pick your model, password and more from the in-browser settings page. See [INSTALL.md](INSTALL.md).

### ⌨️ Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+Shift+A` | Toggle the AI side panel |
| `Ctrl+Shift+E` | Toggle the source editor |
| `Ctrl+S` | Save |

## 📄 License

[MIT](LICENSE). Issues and PRs welcome.

<div align="center"><sub>If this helps you, a ⭐ helps others find it.</sub></div>
