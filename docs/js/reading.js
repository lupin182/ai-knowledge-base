/* 每页阅读状态(未读/在读/已读) + 行内笔记标注。仅 /kb/ 文档页。
   - 状态栏放在 h1 下面（三选一）。
   - 选中正文文字 → 浮出「✎ 笔记」→ 该段加点状下划线 + 弹出评论模态；点下划线再打开。
   - 一条高亮 = 一个评论线程：可发多条评论，每条带时间、可单独编辑/删除（CommentModal 类）。
   - 侧栏给已读(绿)/在读(橙)的页面打标。
   数据走 /api/reading（PUT 整条 {status, annotations}）→ 各 KB 的 .kb/reading-state.json。
   annotation = {id, exact, prefix, suffix, comments:[{id,text,created,updated}], updated}。 */
(function () {
  function apiBase() { return window.__KB_API_BASE || ""; }
  var path = location.pathname.replace(/^\/+|\/+$/g, "");
  if (!path) return;  // 首页不显示；其它内容页(kb/ 或外部挂载 external-reports/...)在 mount() 里靠 article.article 兜底

  var STATUSES = ["unread", "reading", "read"];
  var LABEL = { unread: "未读", reading: "在读", read: "已读" };
  var state = { status: "unread", annotations: [] };
  var article = null, bar = null, commentModal = null;

  function uid() { return "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function annById(id) { return state.annotations.filter(function (a) { return a.id === id; })[0]; }

  function save() {
    return fetch(apiBase() + "/api/reading", {
      method: "PUT", headers: { "Content-Type": "application/json" }, credentials: "include",
      body: JSON.stringify({ path: path, status: state.status, annotations: cleanAnns() }),
    }).catch(function () {});
  }
  function cleanAnns() {
    return state.annotations.map(function (a) {
      return {
        id: a.id, exact: a.exact, prefix: a.prefix, suffix: a.suffix,
        comments: (a.comments || []).map(function (c) {
          return { id: c.id, text: c.text, created: c.created, updated: c.updated };
        }),
        updated: a.updated,
      };
    });
  }
  // 移除一条标注（撤销空高亮、或删光评论后）：去掉下划线 + 出库。
  function removeAnnotation(ann) {
    if (!ann) return;
    state.annotations = state.annotations.filter(function (a) { return a.id !== ann.id; });
    var s = article.querySelector('span.kb-annot[data-id="' + ann.id + '"]'); if (s) unwrap(s);
    renderStatus(); save();
  }

  // ---------- 状态栏 ----------
  function renderStatus() {
    bar.querySelectorAll(".kb-status-seg button").forEach(function (b) {
      var on = b.getAttribute("data-status") === state.status;
      b.className = on ? "active active-" + state.status : "";
    });
    var n = state.annotations.reduce(function (s, a) { return s + ((a.comments || []).length); }, 0);
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
    span.addEventListener("click", function (ev) { ev.stopPropagation(); commentModal.open(annById(id)); });
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
      var cs = ann.comments || [];
      var first = cs.length ? cs[0].text : "";
      row.innerHTML = '<div class="kb-orphan-q">“' + esc((ann.exact || "").slice(0, 60)) + '”</div>' +
        '<div class="kb-orphan-n">' + esc(first || "(空)") + (cs.length > 1 ? (" …等 " + cs.length + " 条") : "") + '</div>';
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

  // ---------- 评论模态 ----------
  // CommentModal 类已抽到共享模块 docs/js/comment-modal.js（正文页与 PDF 阅读器共用一份，
  // 见 Base.astro 的脚本顺序：comment-modal.js 先于 reading.js）。本页在 mount() 里用
  // window.KBComments.CommentModal 实例化。

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
    var ann = {
      id: id, exact: exact,
      prefix: hay.slice(Math.max(0, off.start - 40), off.start),
      suffix: hay.slice(off.end, off.end + 40),
      comments: [], updated: new Date().toISOString(),
    };
    state.annotations.push(ann);
    renderStatus();
    commentModal.open(ann);   // 不先 save：发第一条评论时才入库；直接关掉(无评论)=取消，移除空高亮
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
    commentModal = new window.KBComments.CommentModal({
      onChange: function () { renderStatus(); save(); },
      onCancelEmpty: function (ann) { removeAnnotation(ann); },
    });
    buildBar();
    load().then(function () { renderStatus(); renderAnnotations(); });
    markSidebar();
    document.addEventListener("mouseup", onMouseUp);
  }
  function load() {
    return fetch(apiBase() + "/api/reading?path=" + encodeURIComponent(path), { credentials: "include" })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        state.status = (d && d.status) || "unread";
        // 归一化：老数据每条标注是单个 note 字段 → 迁成 comments 数组（一条评论）。
        state.annotations = ((d && d.annotations) || []).map(function (a) {
          if (!Array.isArray(a.comments)) {
            a.comments = (a.note && String(a.note).trim())
              ? [{ id: (a.id || "") + "-c0", text: String(a.note), created: a.updated || "", updated: a.updated || "" }]
              : [];
          }
          delete a.note;
          return a;
        });
      })
      .catch(function () {});
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
