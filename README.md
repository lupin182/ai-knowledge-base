# AI 知识库

<div id="kb-stats" class="kb-stats"></div>

> 选中文字 → 问 AI → AI 直接改源文件。多知识库、双 AI 后端、浏览器里建库导入。

一个 **AI 原生**的 Markdown 知识库。不是在笔记里嵌一个聊天框 —— 是 AI 真的能 **读你的笔记、改你的笔记**。

## 它能做什么

### 1. 选中提问，带上下文

选中页面任意一段文字，点浮动按钮，AI 自动带着 **当前页面内容 + 你选中的文字** 回答。不需要复制粘贴。

### 2. AI 直接编辑源文件

对 AI 说 "把这段公式推导补充完整" 或 "帮我加一个对比表格"，它 **直接修改对应的 .md 文件**。刷新页面就能看到更新。

### 3. 多知识库

`knowledge_bases/` 下每个子目录是一个独立知识库。`KB` 按钮可在浏览器里直接 **新建 / 重命名 / 删除 / 上传文件文件夹** 到任意 KB。

### 4. 双 AI 后端，按需切换

- **Claude CLI**（推荐）：用你的 Claude 订阅认证，**不需要 API Key**，安装 `@anthropic-ai/claude-code` 并登录即可。
- **OpenAI 兼容 API**：填 API key（OpenAI / DeepSeek / 任何支持 Chat Completions 协议的服务），适合没订阅或想用更便宜模型的人。

在 `/docs/tools/settings.html` 设置页里随时切换，模型列表也在这里维护。

### 5. 内置源码编辑器

`Ctrl+Shift+E` 打开 CodeMirror，自动定位到你正在阅读的位置。`Ctrl+S` 保存。

### 6. 数学公式 + PDF 阅读

- KaTeX 渲染行内 `$...$` 和行间 `$$...$$`
- 内置 PDF.js 阅读器，PDF 选区可作为上下文传给 AI

## 技术栈

| 层 | 技术 | 作用 |
|----|------|------|
| 渲染 | [Docsify](https://docsify.js.org/) | 零构建，改 `.md` 刷新即生效 |
| 后端 | FastAPI | SSE 流式对话 + 多 KB API + 设置 API |
| AI（默认） | [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) | 子进程，用你的 Claude 订阅认证 |
| AI（可选） | OpenAI-compatible API | httpx 直连，工具调用走服务器侧实现 |
| 编辑器 | CodeMirror 5 | Markdown 语法高亮 + 实时编辑 |
| 公式 | KaTeX | LaTeX 数学公式渲染 |

## 快速开始

```bash
# 1. 装 Claude CLI 并登录（推荐用 Claude CLI 后端，免 API Key）
npm install -g @anthropic-ai/claude-code && claude

# 2. 克隆 + 启动
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
pip install -r server/requirements.txt
python run.py                            # 打开 http://localhost:8000
```

第一次启动会自动探测 `claude` 命令是否可用：可用就默认 Claude CLI 后端，立即就能聊。
没装 Claude CLI 也能跑 —— 顶部会弹横幅引导你去 **⚙️ 设置页** 填 API key。

详细安装/部署 → [INSTALL.md](INSTALL.md)

## 内置知识库内容

本项目自带一套完整的 **AI/ML 面试知识体系**（在 `knowledge_bases/ai-ml-interview/`），涵盖：

| 分支 | 内容 |
|------|------|
| **大模型** | Transformer、Tokenizer、MoE、Scaling Laws、长上下文、SFT/RLHF/DPO/GRPO、推理优化（KV Cache/FlashAttention/量化/vLLM/投机解码）、RAG、VLM |
| **机器学习基础** | 概率统计、线性代数、IML 课程、深度学习基础、KL 散度 |
| **强化学习** | MDP/Bellman、Q-Learning/DQN、策略梯度/PPO/SAC、Model-Based RL、Offline RL |
| **视觉** | 对比学习、CLIP、DINO、生成模型（VAE/Diffusion）、3D 稀疏卷积 |
| **具身智能** | VLA 模型、世界模型、策略学习、机器人操控、运动与导航 |
| **CUDA 编程** / **分布式训练** / **行业动态** / **面试手撕** | 略 |

`KB` 按钮 → **新建知识库** 就能开一个全新主题的 KB，互不干扰。

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+A` | 打开 AI 侧边栏 |
| `Ctrl+Shift+E` | 打开源码编辑器 |
| `Ctrl+S` | 保存编辑 |

## License

MIT
