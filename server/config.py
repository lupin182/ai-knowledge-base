"""项目级常量。

运行时可变的设置（API key、所选 backend、模型列表、ACCESS_PASSWORD、Claude CLI 路径等）
统一搬到 `server/services/settings_service.py` 持久化到 `server/.settings.json`，
本文件只保留路径、字符上限等真常量。
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# 仓库根目录 (server/ 的父目录) —— Docsify 前端静态资源根。
DOCS_ROOT = Path(__file__).parent.parent.resolve()

# 多知识库根目录：每个子目录 = 一个独立 KB。
KB_ROOT = DOCS_ROOT / "knowledge_bases"

# 默认知识库 slug。当 URL 没有 /kb/<slug>/ 前缀时回退到这个 KB。
DEFAULT_KB_SLUG = os.getenv("DEFAULT_KB_SLUG", "ai-ml-interview")

# 单页 markdown 内容传给 LLM 的最大字符数，防止超出上下文窗口。
MAX_PAGE_CHARS = 50000
# PDF 全文抽取出来的页面通常更长，给它单独的更大阈值。
MAX_PDF_CHARS = 200000
