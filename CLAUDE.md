# Claude Code 项目规则

## 项目说明

这是一个 **Markdown 多知识库** 项目，前后端一体（Docsify + FastAPI）。
内容在 `knowledge_bases/<slug>/`；后端 / 前端代码与内容分离。

### 操作权限

- 允许所有文件的读取、编辑、创建、搜索
- 允许使用 Glob、Grep、Read、Edit、Write 工具，无需额外确认
- 允许使用 Bash 执行 ls、mkdir、git mv 等文件管理命令
- **禁止** `rm -rf` 或任何删除文件/目录的命令；要"删"就 `git mv` 到 `_trash/`

### 内容规范

- 知识库 .md 全部用中文，Markdown 格式
- 新增 .md 后更新所在目录的 `README.md` 索引
- **不要**手动维护根目录 `_sidebar.md` —— sidebar 由 `server/services/kb_service.build_sidebar_markdown()` 动态生成
- 单目录文件超过 15 个时拆子目录
- 交叉引用用相对路径
- 涉及版本/时间敏感内容标注日期

### 后端架构（修改后端代码时务必读懂）

- 两个 backend 实现 `server/backends/__init__.py` 里的 `Backend` Protocol，路由层只调接口
- 运行时设置（API key / 默认 backend / ACCESS_PASSWORD）走 `server/services/settings_service.py`，**不要再加 env var 配置项**，全部走 `.settings.json`
- 多 KB CRUD / 路径解析 / sidebar 生成都在 `server/services/kb_service.py`
- 路径安全永远在 `server/auth.py` 的中间件里做（已拦 `/server/`、`/knowledge_bases/`、`/_trash/` 等）

### Git 规范

- 每完成一组修改后自动 `git add` + `git commit` + `git push`，不等用户要求
- commit message 用英文，简洁描述改动
- 每次修改主动告知改了哪些文件
