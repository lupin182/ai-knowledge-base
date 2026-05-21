# AI 知识库

<div id="kb-stats" class="kb-stats"></div>

> **选中文字 → 问 AI → AI 直接改源文件。** 不是聊天框，是真协作。

如果你也用 Markdown 写笔记，习惯过 Obsidian / Notion / mdBook，但每次都嫌：
- AI 工具能聊但帮不上忙，答案得我自己复制粘贴回去
- 笔记越积越多，导航越来越乱
- 想接 GPT/Claude，要么贵要么折腾 key
- 部署给同学看一眼都要担心安全

这个项目就是为这几个痛点造的。

## 它和别的工具有什么不一样

| 工具 | AI 真的能改你的文件吗？ | 多知识库 | 不要 API key | 浏览器里就能管 |
|------|----------------------|---------|------------|-------------|
| **本项目** | ✓ AI 调 Read/Edit/Write 工具直接改 .md | ✓ | ✓ Claude 订阅就行 | ✓ |
| Obsidian + AI 插件 | ✗ 大多只能聊，要复制粘贴 | ✓ vault | ✗ | ✗ |
| Notion AI | ✗ 块级 AI 补全，不改源文件 | ✓ page tree | ✗ | ✓ |
| Cursor / VSCode + Continue | ✓ 但定位是编辑器，不是知识库 | ✗ | ✗ | ✗ |
| mdBook / MkDocs | ✗ 没 AI | ✗ | – | ✗ |

简单说：**只有这个项目把 "AI 作为协作者" 当核心，而不是 "知识库 + 聊天 widget"。**

## 30 秒上手

```bash
npm install -g @anthropic-ai/claude-code && claude    # 一次性：用 Claude 订阅登录
git clone https://github.com/JZ-Wu/ai-knowledge-base.git
cd ai-knowledge-base
pip install -r server/requirements.txt
python run.py                                          # 浏览器开 http://localhost:8001
```

没装 Claude CLI 也能跑 —— 顶部会弹横幅引导你去设置页填任意 OpenAI 兼容 API 的 key（GPT / DeepSeek / Qwen / 任何 Chat Completions 协议的服务）。

详细安装 → [INSTALL.md](INSTALL.md)

## 一个真实的工作流

打开一篇你写到一半的笔记，比如 `大模型/MoE.md`，正文里有这句：

> MoE 通过门控网络把 token 路由到不同专家，常见做法是 top-k 选择。

选中这句话 → 点浮动按钮 → 对 AI 说：

> **"在这句话后面加 3 个具体例子：Switch Transformer / Mixtral / DeepSeekMoE，每个写清楚 k 值和总专家数。"**

AI 会先 Read 这个文件，定位你选中的位置，然后用 Edit 工具把这一行扩成你要的格式。窗口右下角会出现 `Edit: 大模型/MoE.md` 提示，你刷新页面就看到新内容。

不需要切窗口、不需要复制粘贴、不需要 prompt 工程让 AI "返回完整文件" 然后你自己合并 —— 它就是直接改了。

## 核心特性

**AI 协作编辑**
- 选中文字浮动按钮：AI 自动带 *当前页面内容 + 选区* 作为上下文
- AI 通过 `Read / Edit / Write / Glob / Grep` 工具直接操作 `.md` 文件
- 工具白名单受控，不会乱跑命令；编辑前自动生成 `.bak` 备份

**多知识库**
- `knowledge_bases/<slug>/` 每个子目录 = 一个独立 KB，URL `/kb/<slug>/`
- 顶栏 `KB ▾` 切换器一键跳转
- 设置页里建 / 改名 / 删除 / 上传文件夹（拖整个文件夹也行，会保留目录结构）
- Sidebar 后端动态生成，加文件不用手维护索引

**双 AI 后端**
- **Claude CLI**（默认）：用 Claude Pro / Max 订阅，*不要 API key*
- **OpenAI 兼容 API**：GPT / DeepSeek / Qwen / 任何 Chat Completions 协议
- 设置页里热切换，多模型并存，前端下拉选用哪个

**内置工具**
- **CodeMirror 编辑器**：`Ctrl+Shift+E` 打开，自动跳到你正读的位置
- **KaTeX 公式**：行内 `$E=mc^2$` 和行间 `$$\int_0^1 x \, dx$$` 都支持
- **PDF 阅读器**：选中 PDF 段落作为上下文传给 AI（适合啃论文）
- **图片上传给 AI 看**：粘贴 / 拖拽截图，AI 直接读

**部署友好**
- **访问密码**：scrypt 哈希存储（不是明文），本机访问免登录，外网登录 5 次 / 5 分钟限速
- **路径白名单**：访问 `/server/`、`/.git/`、`/_trash/` 等敏感路径直接 403
- **EXTERNAL_MOUNTS**：跨盘符内容（Windows junction 不行的情况）也能挂进来

## 自带内容：AI/ML 面试知识库

[knowledge_bases/ai-ml-interview/](knowledge_bases/ai-ml-interview/) —— 一套完整 AI/ML 面试知识体系，全中文，**166 篇 / 121 万字**：

| 分支 | 内容 |
|------|------|
| 大模型 | Transformer / Tokenizer / MoE / Scaling Laws / 长上下文 / SFT-RLHF-DPO-GRPO / 推理优化（KV Cache / FlashAttention / 量化 / vLLM / 投机解码）/ RAG / VLM / 主流模型对比 |
| 机器学习基础 | 概率统计 / 线性代数 / IML / 深度学习基础 / KL 散度 |
| 强化学习 | MDP-Bellman / Q-Learning-DQN / 策略梯度-PPO-SAC / Model-Based / Offline RL |
| 视觉 | 对比学习 / CLIP / DINO / 生成模型（VAE-Diffusion）/ 3D 稀疏卷积 |
| 具身智能 | VLA / 世界模型 / 策略学习 / 机器人操控 / 运动与导航 |
| 其他 | CUDA 编程 / 分布式训练 / 行业动态 / 面试手撕 |

**用作你自己的知识库**：设置页 → KB 卡片 → 删除（搬到 `_trash/` 不丢）→ 创建空 KB → 拖文件夹上传。三分钟搞定。

## 技术栈

| 层 | 技术 | 为什么选它 |
|----|------|-----------|
| 渲染 | [Docsify](https://docsify.js.org/) | 零构建，改 `.md` 刷新即生效 |
| 后端 | FastAPI | SSE 流式 + 现代 Python typing |
| AI（默认） | [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) | 用订阅，免 API key |
| AI（可选） | OpenAI-compatible API | httpx 直连，工具调用走服务器侧 |
| 编辑器 | CodeMirror 5 | Markdown 高亮 + 多文件类型 |
| 公式 | KaTeX | LaTeX 数学公式，纯前端 |
| 密码 | Python stdlib `scrypt` | 不引新依赖 |

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+Shift+A` | 打开 AI 侧边栏 |
| `Ctrl+Shift+E` | 打开源码编辑器 |
| `Ctrl+S` | 保存编辑（编辑器内） |
| `Ctrl+F` | 搜索（编辑器内） |
| `Escape` | 关闭当前面板 |

## 想参与？

欢迎 PR。仓库已经开了分支保护：

1. Fork 或 clone 仓库
2. `git checkout -b feature/your-thing`
3. 改完 `git push -u origin feature/your-thing`
4. 在 GitHub 上开 PR，base 是 `master`
5. Review 通过后 squash 合入

直接 push master 会被挡 —— 这是有意的，所有改动留个 PR 记录。

## License

MIT
