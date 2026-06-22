<div align="center">

<img src="assets/readme/logo.png" width="110" alt="AI Knowledge Base logo">

<img src="assets/readme/title.png" width="520" alt="AI Knowledge Base">

### Your Markdown notes, with an AI that reads, annotates — and edits the source file for you.

**English** · [简体中文](README.zh-CN.md)

<a href="https://github.com/JZ-Wu/ai-knowledge-base/stargazers"><img src="https://img.shields.io/github/stars/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=github&color=2fbf60" alt="stars"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=opensourceinitiative&logoColor=white&color=2fbf60" alt="license"></a>
<img src="https://img.shields.io/github/last-commit/JZ-Wu/ai-knowledge-base?style=for-the-badge&logo=git&logoColor=white&color=2fbf60" alt="last-commit">
<img src="https://img.shields.io/github/languages/top/JZ-Wu/ai-knowledge-base?style=for-the-badge&color=2fbf60" alt="top-language">

<sub>Built with</sub><br>
<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/FastAPI-009688.svg?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
<img src="https://img.shields.io/badge/Astro-BC52EE.svg?style=flat-square&logo=astro&logoColor=white" alt="Astro">
<img src="https://img.shields.io/badge/TypeScript-3178C6.svg?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript">
<img src="https://img.shields.io/badge/PDF.js-F40F02.svg?style=flat-square" alt="PDF.js">
<img src="https://img.shields.io/badge/KaTeX-2364AA.svg?style=flat-square" alt="KaTeX">

</div>

---

**AI Knowledge Base** turns any folder of Markdown, images and PDFs into a fast, searchable static site — with an AI assistant built right into the page. **Select a passage, ask a question, and the assistant answers _and can edit the underlying `.md` file directly_** — inside a sandboxed tool boundary that never leaves your knowledge base. Everything runs locally behind a single port: one command builds the site and starts the server.

It is **local-first** (your notes stay on your machine), **multi-KB** (each `knowledge_bases/<slug>/` is its own site), and **backend-agnostic** (drive it with a logged-in Claude CLI or any OpenAI-compatible API).

<div align="center">
<img src="assets/readme/workflow.svg" width="92%" alt="How AI Knowledge Base works">
</div>

## ✨ Highlights

|     | Feature | What it does |
| :-: | :--- | :--- |
| 📖 | **Markdown knowledge bases** | Each `knowledge_bases/<slug>/` is an independent KB, published as an Astro static site with auto sidebar, breadcrumbs, TOC and "recent updates" pulled from git history. |
| 🤖 | **AI inside the page** | Select text or send full-page context, then ask through a streaming side panel (SSE: text, thinking, tool calls, usage). Pluggable backends — **Claude CLI** or any **OpenAI-compatible** API, with multiple model profiles. |
| ✍️ | **AI edits the source** | The assistant can `read` / `search` / `replace` / `write` Markdown through a **controlled tool boundary** scoped to the current KB — path-validated, `.md`-only, no hidden dirs, no parent escapes, no secret-looking files. |
| 🧾 | **PDF reading & annotation** | A PDF.js viewer with select-to-ask-AI, geometry-anchored highlights and inline comment threads — persisted without triggering a rebuild. The Claude backend can render pages to images to answer figure/formula questions. |
| 🗃️ | **Multi-KB management** | List, create, rename and delete knowledge bases from the UI. Deletes move to `_trash/` (never hard-deleted); uploads are restricted to safe suffixes inside the KB. |
| 🔐 | **Local-first & safe** | Localhost-only until you set a password (scrypt-hashed, HMAC cookies). Internal paths (`/server/`, `/.git/`, `/knowledge_bases/`…) are blocked; login and chat are rate-limited. |
| ⚙️ | **One command, atomic builds** | `python run.py` auto-installs, syncs content and builds Astro with **build-to-temp + atomic swap**, so the server never serves a half-finished page. |

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

`run.py` is the only entry point: on first launch it runs `npm install`, syncs content and builds the Astro site, then serves the frontend **and** API from one port. Force a fresh build with `python run.py --rebuild`.

**Requirements** — Python 3.11+ · Node.js 18+ (first build only) · one AI backend: a logged-in **Claude CLI** _or_ any **OpenAI-compatible** API key. Windows, macOS and Linux are all supported (Windows console encoding and OneDrive build locks are handled for you).

Runtime settings live in the browser — no config files to hand-edit:

```text
http://localhost:8001/docs/tools/settings.html
```

Pick the backend, model profiles, access password, default context/tool behavior and external mounts there — saved to a git-ignored `server/.settings.json`. See [INSTALL.md](INSTALL.md) for deployment and reverse-proxy notes.

### ⌨️ Shortcuts

| Keys | Action |
| :--- | :--- |
| `Ctrl+Shift+E` | Toggle the Markdown source editor |
| `Ctrl+Shift+A` | Toggle the AI side panel |
| `Ctrl+S` | Save in the editor |
| `Esc` | Close the current panel |

## 🗂️ How it's organized

All content lives in `knowledge_bases/<slug>/` (slug matches `[A-Za-z0-9_-]{1,64}`) and is served at `/kb/<slug>/...`. Drop in a `README.md` as the KB home; add an optional `_sidebar.md` to hand-order navigation, or let the folder structure build a collapsible tree automatically. Homepage cards and the top/side KB lists auto-discover every folder — zero config to add a new KB.

```text
ai-knowledge-base/
├── run.py                 # single entry: build + serve on one port
├── server/                # FastAPI app, auth, routes, services, backends
│   ├── main.py            # app + security middleware + static hosting
│   ├── backends/          # claude_cli.py · openai_api.py
│   └── services/          # KB CRUD, sidebar, build-to-temp + atomic swap
├── web/                   # Astro static site (content, layouts, search index)
├── docs/tools/            # PDF reader, settings page
├── scripts/               # sync_core.py · extract_pdf.py
└── knowledge_bases/       # your KBs (ships with ai-ml-interview)
```

The bundled **`ai-ml-interview`** KB covers LLMs, ML foundations, RL, vision, embodied AI, CUDA, distributed training, industry news and interview coding.

## 🛣️ Roadmap

- [x] Multi-KB foundation — create / rename / delete / upload / stats
- [x] Astro static build — content sync, asset mirroring, link rewriting, search index
- [x] AI reading & editing — Claude CLI + OpenAI-compatible, scoped tool calls, page context
- [x] PDF reading & annotation — PDF.js, ask-AI selections, inline threads, persisted state
- [x] Security boundary — localhost-by-default, scrypt passwords, path blocking, rate limits
- [ ] Automated test coverage — routes, path safety, sync/build, annotations, frontend
- [ ] Performance benchmarks — large KBs, external mounts, image/PDF-heavy builds
- [ ] More docs — real screenshots, deployment recipes, reverse-proxy templates

## 🤝 Contributing

Issues and PRs are welcome — for new features, AI-editing boundaries, the PDF reader, or local-deployment experience. Please include a minimal repro (startup command, browser path, backend log, screenshot) for bugs, and the motivation + verification commands for PRs.

<details>
<summary><b>Local setup</b></summary>

```bash
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
git checkout -b feature/your-change

# verify before pushing
python -m compileall run.py server scripts
cd web && npm run build
```

Shared-framework code (`server/`, `web/src/`, skills…) is mirrored from [kb-core](https://github.com/JZ-Wu/kb-core); see [CLAUDE.md](CLAUDE.md) before editing it.
</details>

<details>
<summary><b>Recent updates</b></summary>

- **2026-06-19** 🧭 Cleaner PDF reader navigation (removed a redundant back button).
- **2026-06-18** 📄 PDF auto-fit via `ResizeObserver` — re-layouts on zoom / container change.
- **2026-06-17** 💬 Inline PDF comment threads anchored to page geometry (survive refresh).
- **2026-06-17** 📚 Merged whole-library read state — external pages show read / reading / note marks.
- **2026-06-11** 🛡️ `no-cache` revalidation for HTML/CSS/JS so browsers don't run stale scripts.
</details>

## 📄 License

Released under the [MIT License](LICENSE).

## 🙏 Acknowledgments

Built on **FastAPI**, **Uvicorn**, **Astro**, **MDX**, **KaTeX**, **PDF.js**, **CodeMirror** and **Marked**, with **Claude CLI** and **OpenAI-compatible** Chat Completions powering Q&A, rewriting and tool calls.

<div align="center"><sub>If this saves you time, a ⭐ helps others find it.</sub></div>
