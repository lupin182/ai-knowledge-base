"""每页的阅读状态(未读/在读/已读) + 行内笔记标注。

- KB 页（kb/<slug>/<rel>）：存该 KB 的 `.kb/reading-state.json`，键 = rel（首页记 "(index)"）。
- 外部挂载页（/external-reports/... 等，不在 kb/ 下）：存全局 `DOCS_ROOT/.reading-external.json`，
  键 = 完整路径。外部内容本就是本机 EXTERNAL_MOUNTS、不入 git，其阅读态也 gitignore。

value = {"status": "unread"|"reading"|"read",
         "annotations": [{id,exact,prefix,suffix,comments:[{id,text,created,updated}],updated}],
         "updated": iso}
一条高亮 = 一个评论线程（comments 多条）。老数据每条标注只有单个 note 字段，读/写时兼容迁移成一条评论。
PDF 标注额外带 page（页码）+ rects（[{x,y,w,h}] scale=1 PDF 点坐标），正文标注则带 prefix/suffix。
用户态、不进静态构建（前端动态读写），改它不触发重建。
"""
import json
import os
import threading
from datetime import datetime, timezone

from server.config import DOCS_ROOT
from server.services import kb_service

_lock = threading.Lock()
_NOTE_MAX = 20000
_MAX_ANNOTS = 500
_MAX_COMMENTS = 200
_MAX_RECTS = 64          # PDF 高亮一条选区的矩形数上限（跨行选区 = 多个矩形）
_INDEX_KEY = "(index)"
_STATUSES = ("unread", "reading", "read")
_EXTERNAL_STORE = DOCS_ROOT / ".reading-external.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _split(path: str):
    try:
        slug, rel = kb_service.split_docsify_path(path or "")
    except ValueError:
        slug, rel = None, (path or "")
    return slug, rel


def _resolve(path: str):
    """(store_file, key) —— KB 页落各 KB .kb/reading-state.json(键=rel)，外部页落全局(键=完整路径)。"""
    slug, rel = _split(path)
    if slug:
        return kb_service.kb_dir(slug) / ".kb" / "reading-state.json", (rel or _INDEX_KEY)
    key = (path or "").strip().strip("/") or _INDEX_KEY
    return _EXTERNAL_STORE, key


def _load(store) -> dict:
    if store.exists():
        try:
            data = json.loads(store.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def _save(store, data: dict) -> None:
    # 原子写：先写同目录临时文件，再 os.replace 覆盖。直接 write_text 写一半崩 →
    # 整份 JSON 损坏 → _load 静默吞掉 → 该 KB 全部阅读态+笔记丢失。
    store.parent.mkdir(parents=True, exist_ok=True)
    tmp = store.with_name(store.name + f".tmp{os.getpid()}")
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    try:
        tmp.write_text(payload, encoding="utf-8")
        os.replace(tmp, store)  # 同目录、原子；要么旧内容、要么新内容，绝不半截
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def _entry_view(e: dict) -> dict:
    if not isinstance(e, dict):
        return {"status": "unread", "annotations": []}
    return {"status": e.get("status", "unread"), "annotations": e.get("annotations", []) or []}


def _clean_rects(rects) -> list:
    """PDF 标注的几何锚点：每个矩形 {x,y,w,h} 为 scale=1 的 PDF 点坐标（页内、缩放无关）。
    正文（markdown）标注没有 rects，返回空列表。"""
    out = []
    if not isinstance(rects, list):
        return out
    for r in rects[:_MAX_RECTS]:
        if not isinstance(r, dict):
            continue
        try:
            out.append({
                "x": round(float(r.get("x", 0)), 2),
                "y": round(float(r.get("y", 0)), 2),
                "w": round(float(r.get("w", 0)), 2),
                "h": round(float(r.get("h", 0)), 2),
            })
        except (TypeError, ValueError):
            continue
    return out


def _clean_comment(c) -> dict | None:
    if not isinstance(c, dict):
        return None
    text = str(c.get("text", ""))[:_NOTE_MAX]
    if not text.strip():
        return None
    created = str(c.get("created", ""))[:40] or _now()
    return {
        "id": str(c.get("id", ""))[:64],
        "text": text,
        "created": created,
        "updated": str(c.get("updated", ""))[:40] or created,
    }


def _clean_annotations(annotations) -> list:
    out = []
    for a in (annotations or [])[:_MAX_ANNOTS]:
        if not isinstance(a, dict):
            continue
        comments = []
        raw = a.get("comments")
        if isinstance(raw, list):
            for c in raw[:_MAX_COMMENTS]:
                cc = _clean_comment(c)
                if cc:
                    comments.append(cc)
        elif str(a.get("note", "")).strip():
            # 向后兼容：老数据每条标注只有单个 note → 迁成一条评论
            ts = str(a.get("updated", ""))[:40] or _now()
            comments.append({
                "id": (str(a.get("id", "")) + "-c0")[:64],
                "text": str(a.get("note", ""))[:_NOTE_MAX],
                "created": ts,
                "updated": ts,
            })
        if not comments:
            continue  # 无评论 = 空高亮，丢弃
        ann = {
            "id": str(a.get("id", ""))[:64],
            "exact": str(a.get("exact", ""))[:2000],
            "prefix": str(a.get("prefix", ""))[:200],
            "suffix": str(a.get("suffix", ""))[:200],
            "comments": comments,
            "updated": str(a.get("updated", ""))[:40] or _now(),
        }
        # PDF 标注：额外存页码 + 几何矩形（正文标注没有这两项）
        try:
            page = int(a.get("page", 0) or 0)
        except (TypeError, ValueError):
            page = 0
        if page > 0:
            ann["page"] = page
            ann["rects"] = _clean_rects(a.get("rects"))
        out.append(ann)
    return out


def get(path: str) -> dict:
    store, key = _resolve(path)
    return _entry_view(_load(store).get(key) or {})


def set_state(path: str, status: str, annotations) -> dict:
    status = status if status in _STATUSES else "unread"
    anns = _clean_annotations(annotations)
    store, key = _resolve(path)
    with _lock:
        data = _load(store)
        if status != "unread" or anns:
            data[key] = {"status": status, "annotations": anns, "updated": _now()}
        else:
            data.pop(key, None)  # 未读且无笔记 → 删条目
        _save(store, data)
    return {"status": status, "annotations": anns}


def all_for(path: str | None = None) -> dict:
    """侧栏标记用：{完整页面路径: {status, notes}}。合并「外部全局库」+「所有 KB 库」，
    都归一成完整路径键（kb/<slug>/<rel> 或 external-reports/...），前端按链接 href 直接查。

    早先只并「当前页所属 KB」，导致外部挂载页（不属任何 KB）拿不到任何 KB 阅读态，
    其侧栏里的 KB 链接全无已读标记；跨库链接同理。改为合并全部 KB——数据量很小
    （只存非 unread 条目），每库一个小 JSON，标记得以在任意页面（含外部页）保持一致。"""
    out = {}
    for k, e in _load(_EXTERNAL_STORE).items():
        if isinstance(e, dict):
            out[k] = {"status": e.get("status", "unread"), "notes": len(e.get("annotations") or [])}
    for slug in kb_service.list_slugs():
        kb_store = kb_service.kb_dir(slug) / ".kb" / "reading-state.json"
        for k, e in _load(kb_store).items():
            if not isinstance(e, dict):
                continue
            full = f"kb/{slug}" if k == _INDEX_KEY else f"kb/{slug}/{k}"
            out[full] = {"status": e.get("status", "unread"), "notes": len(e.get("annotations") or [])}
    return out
