/* 每页阅读状态(未读/在读/已读) + 行内笔记标注。仅 /kb/ 文档页。
   - 状态栏放在 h1 下面（三选一）。
   - 选中正文文字 → 浮出「＋笔记」→ 该段加点状下划线 + 弹框写笔记；点下划线再弹出编辑。
   - 侧栏给已读(绿)/在读(橙)的页面打标。
   数据走 /api/reading（PUT 整条 {status, annotations}）→ 各 KB 的 .kb/reading-state.json。 */
(function () {
  function apiBase() { return window.__KB_API_BASE || ""; }
  var path = location.pathname.replace(/^\/+|\/+$/g, "");
  if (!path) return;  // 首页不显示；其它内容页(kb/ 或外部挂载 external-reports/...)在 mount() 里靠 article.article 兜底

  var STATUSES = ["unread", "reading", "read"];
  var LABEL = { unread: "未读", reading: "在读", read: "已读" };
  var state = { status: "unread", annotations: [] };
  var article = null, bar = null, popup = null, openId = null;

  function uid() { return "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

  function save() {
    return fetch(apiBase() + "/api/reading", {
      method: "PUT", headers: { "Content-Type": "application/json" }, credentials: "include",
      body: JSON.stringify({ path: path, status: state.status, annotations: cleanAnns() }),
    }).catch(function () {});
  }
  function cleanAnns() {
    return state.annotations.map(function (a) {
      return { id: a.id, exact: a.exact, prefix: a.prefix, suffix: a.suffix, note: a.note, updated: a.updated };
    });
  }

  // ---------- 状态栏 ----------
  function renderStatus() {
    bar.querySelectorAll(".kb-status-seg button").forEach(function (b) {
      var on = b.getAttribute("data-status") === state.status;
      b.className = on ? "active active-" + state.status : "";
    });
    var n = state.annotations.length;
    bar.querySelector(".kb-note-count").textContent = n ? (n + " 条笔记") : "";
  }
  function buildBar() {
    bar = document.createElement("div");
    bar.className = "kb-reading-bar";
    bar.innerHTML =
      '<div class="kb-status-seg">' +
      STATUSES.map(function (s) { return '<button type="button" data-status="' + s + '">' + LABEL[s] + '</button>'; }).join("") +
      '</div><span class="kb-note-count"></span>';
    var h1 = article.querySelector("h1");
    if (h1 && h1.parentNode) h1.parentNode.insertBefore(bar, h1.nextSibling);
    else article.insertBefore(bar, article.firstChild);
    bar.querySelectorAll(".kb-status-seg button").forEach(function (b) {
      b.addEventListener("click", function () {
        state.status = b.getAttribute("data-status"); renderStatus(); save(); markSidebar();
      });
    });
    renderStatus();
  }

  // ---------- 标注定位 ----------
  function rangeFromOffset(start, len) {
    var walker = document.createTreeWalker(article, NodeFilter.SHOW_TEXT, null);
    var node, pos = 0, started = false, range = document.createRange(), end = start + len;
    while ((node = walker.nextNode())) {
      var nlen = node.nodeValue.length;
      if (!started && pos + nlen > start) { range.setStart(node, start - pos); started = true; }
      if (started && pos + nlen >= end) { range.setEnd(node, end - pos); return range; }
      pos += nlen;
    }
    return null;
  }
  function locate(ann) {
    var hay = article.textContent || "";
    if (!ann.exact) return null;
    var pre = ann.prefix || "", suf = ann.suffix || "", idx = -1, p;
    // 逐级消歧：正文里同一段文字可能多处出现，光靠 prefix+exact（prefix 也重复时）会定位到
    // 错误的那一处并把笔记悄悄搬走。优先用 prefix+exact+suffix 锁死上下文，再逐级放宽。
    if (pre || suf) { p = hay.indexOf(pre + ann.exact + suf); if (p >= 0) idx = p + pre.length; }
    if (idx < 0 && pre) { p = hay.indexOf(pre + ann.exact); if (p >= 0) idx = p + pre.length; }
    if (idx < 0 && suf) { p = hay.indexOf(ann.exact + suf); if (p >= 0) idx = p; }
    if (idx < 0) idx = hay.indexOf(ann.exact);  // 兜底：裸 exact 首次出现
    if (idx < 0) return null;
    return rangeFromOffset(idx, ann.exact.length);
  }
  function offsetsOfRange(range) {
    var pre = document.createRange();
    pre.selectNodeContents(article); pre.setEnd(range.startContainer, range.startOffset);
    var start = pre.toString().length;
    return { start: start, end: start + range.toString().length };
  }
  function wrap(range, id) {
    var span = document.createElement("span");
    span.className = "kb-annot"; span.setAttribute("data-id", id);
    try { range.surroundContents(span); }
    catch (e) { try { span.appendChild(range.extractContents()); range.insertNode(span); } catch (e2) { return null; } }
    span.addEventListener("click", function (ev) { ev.stopPropagation(); openPopup(id, span); });
    return span;
  }
  function unwrap(span) {
    var p = span.parentNode; if (!p) return;
    while (span.firstChild) p.insertBefore(span.firstChild, span);
    p.removeChild(span); if (p.normalize) p.normalize();
  }
  function renderAnnotations() {
    article.querySelectorAll("span.kb-annot").forEach(unwrap);
    var orphans = [];
    state.annotations.forEach(function (ann) {
      var r = locate(ann);
      var s = r ? wrap(r, ann.id) : null;
      if (!s) orphans.push(ann);
    });
    renderOrphans(orphans);
  }
  function renderOrphans(orphans) {
    var old = document.querySelector(".kb-orphan-panel"); if (old) old.remove();
    if (!orphans.length) return;
    var box = document.createElement("details");
    box.className = "kb-orphan-panel";
    box.innerHTML = "<summary>" + orphans.length + " 条笔记未能定位（正文已改）</summary>";
    orphans.forEach(function (ann) {
      var row = document.createElement("div"); row.className = "kb-orphan-row";
      row.innerHTML = '<div class="kb-orphan-q">“' + esc((ann.exact || "").slice(0, 60)) + '”</div>' +
        '<div class="kb-orphan-n">' + esc(ann.note || "(空)") + '</div>';
      var del = document.createElement("button"); del.textContent = "删除"; del.className = "kb-orphan-del";
      del.addEventListener("click", function () {
        state.annotations = state.annotations.filter(function (a) { return a.id !== ann.id; });
        renderStatus(); save(); renderAnnotations();
      });
      row.appendChild(del); box.appendChild(row);
    });
    bar.parentNode.insertBefore(box, bar.nextSibling);
  }
  function esc(s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }

  // ---------- 弹框（居中模态 + 背景遮罩，像评论框）----------
  var backdrop = null;
  function hidePopup() {
    if (popup) popup.hidden = true;
    if (backdrop) backdrop.hidden = true;
  }
  function ensurePopup() {
    if (popup) return;
    backdrop = document.createElement("div");
    backdrop.className = "kb-annot-backdrop"; backdrop.hidden = true;
    backdrop.addEventListener("click", closePopup);  // 点遮罩 = 保存并关闭
    document.body.appendChild(backdrop);

    popup = document.createElement("div"); popup.className = "kb-annot-popup"; popup.hidden = true;
    popup.innerHTML =
      '<div class="kb-annot-head"><span class="kb-annot-title">📝 笔记</span>' +
      '<button type="button" class="kb-annot-x" title="关闭">✕</button></div>' +
      '<div class="kb-annot-sel"></div>' +
      '<textarea class="kb-annot-text" placeholder="对选中段落写点笔记……（保存后在原文标出下划线，点下划线可再编辑）"></textarea>' +
      '<div class="kb-annot-actions"><button type="button" class="kb-annot-del">删除</button>' +
      '<button type="button" class="kb-annot-done">保存</button></div>';
    document.body.appendChild(popup);
    popup.querySelector(".kb-annot-done").addEventListener("click", closePopup);
    popup.querySelector(".kb-annot-x").addEventListener("click", closePopup);
    popup.querySelector(".kb-annot-del").addEventListener("click", function () {
      state.annotations = state.annotations.filter(function (a) { return a.id !== openId; });
      var s = article.querySelector('span.kb-annot[data-id="' + openId + '"]'); if (s) unwrap(s);
      hidePopup(); openId = null; renderStatus(); save();
    });
    document.addEventListener("keydown", function (e) {
      if (popup && !popup.hidden && e.key === "Escape") closePopup();
    });
  }
  function openPopup(id, anchor) {
    void anchor;  // 居中模态，不再按选区定位
    ensurePopup();
    var ann = state.annotations.filter(function (a) { return a.id === id; })[0]; if (!ann) return;
    openId = id;
    var ex = ann.exact || "";
    popup.querySelector(".kb-annot-sel").textContent = "“" + ex.slice(0, 280) + (ex.length > 280 ? "…" : "") + "”";
    popup.querySelector(".kb-annot-text").value = ann.note || "";
    backdrop.hidden = false;
    popup.hidden = false;   // 居中由 CSS（fixed + transform）负责
    popup.querySelector(".kb-annot-text").focus();
  }
  function closePopup() {
    if (!popup || popup.hidden) return;
    var ann = state.annotations.filter(function (a) { return a.id === openId; })[0];
    if (ann) {
      ann.note = popup.querySelector(".kb-annot-text").value;
      ann.updated = new Date().toISOString();
      if (!ann.note.trim()) {
        // 空笔记 = 取消：去掉这条标注 + 撤掉下划线
        state.annotations = state.annotations.filter(function (a) { return a.id !== ann.id; });
        var s = article.querySelector('span.kb-annot[data-id="' + ann.id + '"]'); if (s) unwrap(s);
      }
    }
    hidePopup(); openId = null; renderStatus(); save();
  }

  // ---------- 选区 → 「✎ 笔记」（注入 AI 选区工具条 #ai-float-bar，和「问AI」并排）----------
  function noteAction() {
    var fb = document.getElementById("ai-float-bar");
    if (!fb) return null;
    var b = fb.querySelector("#kb-note-action");
    if (!b) {
      b = document.createElement("button");
      b.id = "kb-note-action"; b.type = "button"; b.className = "ai-float-action"; b.textContent = "✎ 笔记";
      b.addEventListener("mousedown", function (e) { e.preventDefault(); });
      b.addEventListener("click", function (e) {
        e.preventDefault(); e.stopPropagation(); fb.style.display = "none"; createFromSelection();
      });
      fb.appendChild(b);
    }
    return b;
  }
  function articleSelected() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return false;
    return article.contains(sel.getRangeAt(0).commonAncestorContainer) && !!sel.toString().trim();
  }
  function onMouseUp() {
    setTimeout(function () {
      var b = noteAction();           // 只在正文选区时显示「笔记」，其它选区只剩「问AI」
      if (b) b.style.display = articleSelected() ? "" : "none";
    }, 12);
  }
  function createFromSelection() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return;
    var range = sel.getRangeAt(0);
    if (!article.contains(range.commonAncestorContainer)) return;
    var exact = sel.toString(); if (!exact.trim()) return;
    var hay = article.textContent || "";
    var off = offsetsOfRange(range);
    var id = uid();
    var span = wrap(range, id);
    sel.removeAllRanges();
    if (!span) return;
    state.annotations.push({
      id: id, exact: exact,
      prefix: hay.slice(Math.max(0, off.start - 40), off.start),
      suffix: hay.slice(off.end, off.end + 40),
      note: "", updated: new Date().toISOString(),
    });
    renderStatus(); save(); openPopup(id, span);
  }

  // ---------- 侧栏标记 ----------
  function markSidebar() {
    fetch(apiBase() + "/api/reading/all?path=" + encodeURIComponent(path), { credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (map) {
        document.querySelectorAll(".sidebar nav a[href]").forEach(function (a) {
          // map 的键 = 完整页面路径(kb/<slug>/<rel> 或 external-reports/...)；按链接 href 直接查。
          var full = (a.getAttribute("href") || "").split("?")[0].split("#")[0].replace(/^\/+|\/+$/g, "");
          var info = map[full];
          a.classList.remove("kb-sb-read", "kb-sb-reading", "kb-sb-noted");
          if (info) {
            if (info.status === "read") a.classList.add("kb-sb-read");
            else if (info.status === "reading") a.classList.add("kb-sb-reading");
            if (info.notes) a.classList.add("kb-sb-noted");
          }
        });
      }).catch(function () {});
  }

  function mount() {
    article = document.querySelector("article.article");
    if (!article) return;
    buildBar();
    load().then(function () { renderStatus(); renderAnnotations(); });
    markSidebar();
    document.addEventListener("mouseup", onMouseUp);
  }
  function load() {
    return fetch(apiBase() + "/api/reading?path=" + encodeURIComponent(path), { credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (d) { state.status = (d && d.status) || "unread"; state.annotations = (d && d.annotations) || []; })
      .catch(function () {});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
