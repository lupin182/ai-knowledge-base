# Harness 详解：Agent 的工程基座

> 写于 2026-05。配合 [/kb/ai-ml-interview/大模型/外部增强与Agent/Agent框架详解/](/kb/ai-ml-interview/大模型/外部增强与Agent/Agent框架详解/) 看：那篇讲 "Agent 长什么样"，这篇讲 "Agent 在代码里到底长什么样、由谁负责跑起来"。

## 一、为什么单独讲 harness

讨论 Coding Agent 时常常听到三个词：**model、agent、harness**。

| 词 | 重点 |
|---|------|
| **model** | 跑在远端的 LLM（Claude / GPT / DeepSeek …），只输入输出文字 |
| **harness** | 跑在本地的"外壳"：循环、工具分发、安全边界、错误处理 |
| **agent** | model + harness + tools 组合起来、会自主多步完成任务的东西 |

业界讨论 "Claude Code agent" / "Cursor agent" / "Devin" / "Manus" 之间的差异，**主要不在模型**（大家都用 Claude / GPT 那几款），**主要在 harness 设计**：工具集是什么、循环怎么终止、安全怎么管、上下文怎么压缩。

所以 "agent" 是抽象 / 产品概念，"harness" 是工程实现。看一个 agent 产品做得好不好，要看 harness。

## 二、从一次 tool call 到 agent 循环

工具调用（[/kb/ai-ml-interview/大模型/外部增强与Agent/工具调用与MCP/](/kb/ai-ml-interview/大模型/外部增强与Agent/工具调用与MCP/)）是最小积木：模型返回一段 JSON 说"我想调函数 X、参数是 Y"，本地执行，把结果交回去。

一次性是 function call，多次循环才是 agent：

```
[起点] 用户消息
   ↓
模型 → 返回 tool_call: replace_markdown(file=..., old=..., new=...)
   ↓
harness → 执行替换 → 拿到结果 {ok: true, file: ...}
   ↓
模型 ← 看到结果，决定下一步：要不要再 call 别的工具？
   ↓
   ├─ 是 → 回到上一步，再循环
   └─ 否（输出普通文字） → 跳出循环 → 文字直接给用户
```

**Agent 就是这个循环 + 几个保险**。下面以本项目的 `server/backends/openai_api.py` 为例，看一个真 harness 长什么样。

## 三、拆开一个真 harness（本项目代码）

本项目的 [`server/backends/openai_api.py`](/server/backends/openai_api.py) 是一个完整的 harness，约 500 行。核心是这个循环：

```python
# server/backends/openai_api.py: stream_chat()
for round_idx in range(max_rounds + 1):
    tool_calls_acc = {}
    content_parts = []

    # 1. 调 LLM（流式）
    for event in _stream_completion(api_messages, profile, tools=enable_tools):
        # 边收 SSE 边累积 text / tool_calls
        delta = (event["choices"][0].get("delta") or {})
        if delta.get("content"):
            content_parts.append(delta["content"])
            yield {"type": "text", "content": delta["content"]}
        for tool_delta in delta.get("tool_calls") or []:
            _accumulate_tool_call(tool_calls_acc, tool_delta)

    # 2. 这一轮模型没调工具 = 任务结束，return 跳出循环
    tool_calls = _completed_tool_calls(tool_calls_acc)
    if not tool_calls:
        return

    # 3. 超过最大轮数 = 强制中止
    if round_idx >= max_rounds:
        yield {"type": "error", "content": "Tool call limit exceeded."}
        return

    # 4. 把"模型说要调什么"这条 assistant 消息塞回历史
    api_messages.append({
        "role": "assistant",
        "content": "".join(content_parts) or None,
        "tool_calls": tool_calls,
    })

    # 5. 本地执行每个工具调用，把结果作为 tool message 塞回历史
    for call in tool_calls:
        name = call["function"]["name"]
        args = call["function"]["arguments"]
        result, edited_file = _execute_tool(name, args, default_kb_slug)
        api_messages.append({
            "role": "tool",
            "tool_call_id": call["id"],
            "content": json.dumps(result, ensure_ascii=False),
        })
```

这就是 harness 全部的本质 —— 把 `_stream_completion`（调模型）和 `_execute_tool`（执行工具）用一个 `for` 循环串起来，中间维护 `api_messages` 历史。

## 四、Harness 的五件套

任何 harness 都能拆出这五块：

| 块 | 本项目实现 | 干嘛 |
|---|----------|------|
| **循环** | `for round_idx in range(max_rounds + 1)` | 让模型能多次调工具 |
| **模型调用** | `_stream_completion()` → httpx 流式打 chat/completions | 把累积的对话历史发给 LLM |
| **工具分发** | `_execute_tool(name, args, ...)` → 5 个 `_tool_*` 函数 | 把模型的 JSON 翻译成真实的 IO 副作用 |
| **结果回灌** | `api_messages.append({"role": "tool", ...})` | 让模型看到上一次工具的结果，继续推理 |
| **退出条件** | `if not tool_calls: return` 或 `round_idx >= max_rounds` | 知道什么时候停 |

Claude CLI 的 harness（[`server/backends/claude_cli.py`](/server/backends/claude_cli.py)）只是把 `_stream_completion` 换成"启动 `claude` 子进程读 stdin 写 stdout"，五件套结构完全一样。

## 五、Harness 的"保险丝"

光有循环还不够，agent 一旦能调工具就能搞破坏。**Harness 的安全层**是 agent 工程的核心。看一下本项目都做了什么：

```python
# server/backends/openai_api.py: _resolve_markdown_path()
def _resolve_markdown_path(file_path, kb_slug, default_kb_slug, must_exist):
    slug, rel = _split_tool_file_path(file_path, kb_slug or default_kb_slug)
    resolved = kb_service.resolve_kb_path(slug, rel, must_exist=must_exist)
    if resolved.suffix.lower() != ".md":             # ← 只允许 .md
        raise ValueError("only Markdown files can be accessed")
    if _DANGEROUS_NAME_RE.search(resolved.name):     # ← 拒含 secret/key/token/password 的文件名
        raise ValueError("sensitive-looking filenames are not allowed")
    return resolved
```

`kb_service.resolve_kb_path()` 再做第二层：

```python
# server/services/kb_service.py: resolve_kb_path()
def resolve_kb_path(slug, rel_path="", must_exist=False):
    root = kb_dir(slug).resolve()
    clean = _clean_rel_path(rel_path)           # ← 拒 .. / 隐藏文件 / NTFS 设备名
    resolved = (root / clean).resolve() if clean else root
    if not resolved.is_relative_to(root):       # ← 即使绕过 _clean 也用绝对路径再 check
        raise ValueError("Path must stay inside the knowledge base")
    ...
```

总结起来 harness 的"保险丝"通常有以下这些：

| 保险丝 | 实现思路 | 防什么 |
|-------|---------|-------|
| **工具白名单** | 只在 `_TOOLS` 列里塞 read/replace/write/search/list 五个 | 防模型乱调危险工具（比如 Bash） |
| **路径沙箱** | `_resolve_markdown_path` + `resolve_kb_path` 双重校验 | 防越权访问 KB 之外的文件 |
| **后缀白名单** | 强制 `.md` | 防写入 .py / .env / .json 等敏感文件 |
| **文件名黑名单** | 正则匹配 `secret/key/token/credential/password` | 防泄露密钥 |
| **最大轮数** | `AI_MAX_TOOL_ROUNDS = 5`，超过就报错退出 | 防 agent 无限循环烧 token |
| **超时** | Claude CLI backend 里 `_CLI_TIMEOUT = 300s` + `threading.Timer(kill)` | 防子进程挂死 |
| **速率限制** | `server/auth.py` 里 `CHAT_RATE_MAX = 30 / 60s` | 防被滥用 |
| **审批门**（更激进） | 工具调用前先 prompt 用户 yes/no | Claude Code `.claude/settings.local.json` 的 `ask: [...]` 做的 |

## 六、业界 harness 对照

不同 agent 产品的差异**几乎全在 harness 设计**：

| 产品 | model 在哪 | harness 在哪 | 工具集 | 退出条件 |
|------|----------|-------------|-------|---------|
| **Claude Code** | Anthropic 云 | 本地 `claude` CLI（Node.js 进程） | Read/Edit/Write/Glob/Grep/Bash/WebFetch/NotebookEdit/Task/... | 模型说停 或 用户 Ctrl+C |
| **Cursor** | OpenAI / Anthropic 云 | 本地 Cursor 编辑器进程（Electron） | Read/Edit/Apply/Terminal/... + IDE 自己的 LSP | 同上 |
| **Aider** | 任意 LLM API | 本地 `aider` Python 进程 | git diff / git commit / 文件读写 | 单轮居多，agent 模式才循环 |
| **Cline** | 任意 LLM API | 本地 VSCode 扩展 | Read/Write/Execute/Browser/... | 模型说停 |
| **Devin** | 自家模型 + 第三方 | 云端 Linux VM + 浏览器 + Slack 通知 | 终端 / 浏览器 / 编辑器 / git | 任务声明完成 |
| **Manus** | 多模型集合 | 云端 sandbox + 多 agent 协作 | 同 Devin + 更多浏览 / 表格 / 长程任务 | 同上 |
| **本项目** | Claude CLI 或 OpenAI 兼容 API | 本地 FastAPI server (`server/backends/`) | 5 个 markdown 工具 | 模型说停 或 5 轮上限 |

可以看到差异点几乎都是 harness 选择题：

- **工具集大小**：Claude Code 给 Bash（强大但要严管）；本项目只给 5 个 markdown 工具（弱但绝对安全）
- **执行环境**：本地 vs 云端 sandbox（Devin / Manus 是云）
- **用户介入粒度**：每次工具调用都问 / 只问破坏性的 / 全自动
- **上下文管理**：超长后自动压缩（Claude Code）/ 让 agent 自己 handoff（Manus）/ 直接报错（朴素实现）

## 七、为什么 harness 是壁垒

2025-2026 这两年模型公司打得火热（Claude 4 / GPT-5 / Gemini 3 / DeepSeek V4），但用户层产品差异化的**核心战场是 harness**：

- 模型 commoditize 速度极快，每隔几个月就有新一代
- 但 harness 的设计决定了"agent 用起来稳不稳、敢不敢托付重要任务"
- 比如 Claude Code 的成功不是因为 Claude 模型独家（它能换 GPT），而是因为 `.claude/settings.json` 的权限分层、`/compact` 上下文压缩、subagent 隔离机制、CLAUDE.md 自动加载等一整套 harness 设计

具体哪些 harness 设计点决定体验：

| 设计点 | 决定什么 |
|-------|---------|
| 工具描述质量 | 模型能不能选对工具 |
| 上下文压缩策略 | 长会话还能不能继续 |
| 工具调用并行度 | agent 任务跑得快不快 |
| 错误恢复策略 | 工具失败后 agent 会卡死还是 retry |
| 安全边界粒度 | 用户敢不敢让它跑 `rm` |
| 用户审批入口 | 用户参与感 vs 自动化 trade-off |

## 八、常见工程权衡

写 harness 时绕不开的几个选择：

### 8.1 一次性多工具 vs 串行单工具

OpenAI / Anthropic 都支持一次返回多个 `tool_calls`（一次模型调用，并行执行多个工具）。

```python
# 本项目代码：一次返回多个就并行执行
for call in tool_calls:           # ← tool_calls 可能有多个
    result, edited_file = _execute_tool(name, args, default_kb_slug)
    api_messages.append({"role": "tool", "tool_call_id": call["id"], ...})
```

- **并行**：省时间（Read 三个文件并发），但工具之间不能依赖结果
- **串行**：保证顺序，但同样三个 Read 要等三次模型调用

实务：读类（Read / Glob / Grep）尽量让模型一次返回多个并行；写类（Edit / Write）建议串行（写完看结果再决定下一步）。

### 8.2 流式 vs 阻塞

本项目用 SSE 流式（`_stream_completion` 一边读一边 yield），用户能看到模型边想边说话。代价是工程复杂度：要边收边累积 `tool_calls_acc`、断流要处理。

如果只做后台 agent（比如 schedule cron），阻塞拿完整 response 简单很多。

### 8.3 用户在哪个环节介入

| 模式 | 介入时机 | 适合 |
|------|---------|------|
| **全自动** | 不介入，agent 跑完看结果 | 简单明确的任务（修一个 typo） |
| **每次工具前问** | 每个 tool call 弹确认 | 高风险操作（写关键文件 / 跑命令） |
| **只问破坏性** | 删 / 写 / 跑命令时才问 | Claude Code 默认 |
| **失败时介入** | 工具报错时让用户决定 retry / 跳过 | 长程任务 |

本项目目前是"全自动 + 严格白名单"，因为工具集只覆盖 .md 文件，破坏性上限很低。如果以后把 Bash 加进来，必须切到"每次工具前问"或"只问破坏性"。

## 九、和站内其它笔记的关系

- 抽象层 / 算法层：[/kb/ai-ml-interview/大模型/外部增强与Agent/Agent框架详解/](/kb/ai-ml-interview/大模型/外部增强与Agent/Agent框架详解/) 讲 ReAct / 规划 / 记忆 / 反思
- 协议层：[/kb/ai-ml-interview/大模型/外部增强与Agent/工具调用与MCP/](/kb/ai-ml-interview/大模型/外部增强与Agent/工具调用与MCP/) 讲 function call / MCP 协议怎么定
- **工程层（本篇）**：把上面两层接起来真的跑起来的代码 / 安全 / 权衡

下次再有人问"agent 和 harness 有什么区别"，把这三篇连起来读一遍就够。

---
[返回上级](/kb/ai-ml-interview/大模型/外部增强与Agent/) · [返回大模型](/kb/ai-ml-interview/大模型/) · [返回总目录](/kb/ai-ml-interview/)
