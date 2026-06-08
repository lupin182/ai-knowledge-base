"""每页的阅读状态(未读/在读/已读) + 行内笔记标注。

- KB 页（kb/<slug>/<rel>）：存该 KB 的 `.kb/reading-state.json`，键 = rel（首页记 "(index)"）。
- 外部挂载页（/external-reports/... 等，不在 kb/ 下）：存全局 `DOCS_ROOT/.reading-external.json`，
  键 = 完整路径。外部内容本就是本机 EXTERNAL_MOUNTS、不入 git，其阅读态也 gitignore。

value = {"status": "unread"|"reading"|"read", "annotations": [{id,exact,prefix,suffix,note,updated}], "updated": iso}
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


def _clean_annotations(annotations) -> list:
    out = []
    for a in (annotations or [])[:_MAX_ANNOTS]:
        if not isinstance(a, dict):
            continue
        out.append({
            "id": str(a.get("id", ""))[:64],
            "exact": str(a.get("exact", ""))[:2000],
            "prefix": str(a.get("prefix", ""))[:200],
            "suffix": str(a.get("suffix", ""))[:200],
            "note": str(a.get("note", ""))[:_NOTE_MAX],
            "updated": str(a.get("updated", ""))[:40] or _now(),
        })
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


def all_for(path: str) -> dict:
    """侧栏标记用：{完整页面路径: {status, notes}}。合并「外部全局库」+「当前页所属 KB 库」，
    都归一成完整路径键（kb/<slug>/<rel> 或 external-reports/...），前端按链接 href 直接查。"""
    out = {}
    for k, e in _load(_EXTERNAL_STORE).items():
        if isinstance(e, dict):
            out[k] = {"status": e.get("status", "unread"), "notes": len(e.get("annotations") or [])}
    slug, _rel = _split(path)
    if slug:
        kb_store = kb_service.kb_dir(slug) / ".kb" / "reading-state.json"
        for k, e in _load(kb_store).items():
            if not isinstance(e, dict):
                continue
            full = f"kb/{slug}" if k == _INDEX_KEY else f"kb/{slug}/{k}"
            out[full] = {"status": e.get("status", "unread"), "notes": len(e.get("annotations") or [])}
    return out
