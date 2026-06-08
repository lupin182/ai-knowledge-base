# 外部增强与 Agent

LLM 本身只会"生成文本"。要让它真正有用，需要外挂各种外部能力：

| 能力 | 方式 | 类比 |
|------|------|------|
| **知识** | RAG（检索增强生成） | 给 LLM 一本参考书 |
| **技能** | Tool Calling / MCP | 给 LLM 一套工具箱 |
| **自主性** | Agent（规划 + 循环执行） | 给 LLM 大脑 + 手脚 |
| **工程基座** | Harness（运行时 + 安全边界） | 把上面这些拼起来真的跑起来 |

四者不互斥 —— 一个 agent 产品通常同时用 RAG + Tool Calling + 自己的 harness 把它们粘起来。

## 知识点索引

- [RAG详解](/kb/ai-ml-interview/大模型/外部增强与Agent/RAG详解/) — 完整流程、分块策略、Embedding、向量数据库、Reranker、混合检索、高级技巧
- [工具调用与MCP](/kb/ai-ml-interview/大模型/外部增强与Agent/工具调用与MCP/) — Function Calling、Tool Use 范式、MCP 协议详解
- [Agent框架详解](/kb/ai-ml-interview/大模型/外部增强与Agent/Agent框架详解/) — ReAct、规划与记忆、Coding Agent、2025-2026 Agent 爆发的原因
- [Harness详解：Agent的工程基座](/kb/ai-ml-interview/大模型/外部增强与Agent/Harness详解：Agent的工程基座/) — Agent 循环的代码长什么样、五件套 + 保险丝、业界 harness 对照、工程权衡

---
[返回上级](/kb/ai-ml-interview/大模型/) · [返回总目录](/kb/ai-ml-interview/)
