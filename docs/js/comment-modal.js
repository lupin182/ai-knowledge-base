/* 共享评论模态（OO）：一条标注 = 一个评论线程，可发多条评论，每条带时间、可单独编辑/删除。
   存储无关——只操作传入的 annotation 对象（按引用改其 comments），变更经回调持久化：
     new KBComments.CommentModal({ onChange(){保存}, onCancelEmpty(ann){空标注=取消，移除} })
     modal.open(ann)   // ann = {exact, comments:[{id,text,created,updated}], ...}
   正文页（reading.js）与 PDF 阅读器（pdf-reader.html）共用同一份，避免重复。
   依赖站点 CSS 的 .kb-annot-popup / .kb-cmt-* 类（reading.css 提供）。 */
(function () {
  function uid() { return "a" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }
  function esc(s) { var d = document.createElement("div"); d.textContent = s || ""; return d.innerHTML; }

  function fmtTime(iso) {
    if (!iso) return "";
    var d = new Date(iso); if (isNaN(d.getTime())) return "";
    var diff = (Date.now() - d.getTime()) / 1000; if (diff < 0) diff = 0;
    if (diff < 60) return "刚刚";
    if (diff < 3600) return Math.floor(diff / 60) + " 分钟前";
    if (diff < 86400) return Math.floor(diff / 3600) + " 小时前";
    var pad = function (x) { return (x < 10 ? "0" : "") + x; };
    var md = (d.getMonth() + 1) + "-" + pad(d.getDate());
    if (d.getFullYear() === new Date().getFullYear()) return md + " " + pad(d.getHours()) + ":" + pad(d.getMinutes());
    return d.getFullYear() + "-" + md;
  }

  // 居中模态 + 背景遮罩。open(annotation) 打开；评论的增/改/删全在类内完成，
  // 每次变更调 onChange() 持久化；关闭时若该标注无评论 → 视为取消，回调 onCancelEmpty 移除空标注。
  function CommentModal(opts) {
    opts = opts || {};
    this.onChange = opts.onChange || function () {};
    this.onCancelEmpty = opts.onCancelEmpty || function () {};
    this.ann = null;          // 当前打开的 annotation 对象（按引用直接改其 comments）
    this.editingId = null;    // 正在内联编辑的评论 id（null = 没在编辑）
    this._build();
  }
  CommentModal.prototype._build = function () {
    var self = this;
    this.backdrop = document.createElement("div");
    this.backdrop.className = "kb-annot-backdrop"; this.backdrop.hidden = true;
    this.backdrop.addEventListener("click", function () { self.close(); });
    document.body.appendChild(this.backdrop);

    this.el = document.createElement("div");
    this.el.className = "kb-annot-popup"; this.el.hidden = true;
    document.body.appendChild(this.el);

    document.addEventListener("keydown", function (e) {
      if (!self.el.hidden && e.key === "Escape") self.close();
    });
  };
  CommentModal.prototype.open = function (ann) {
    if (!ann) return;
    this.ann = ann; this.editingId = null;
    if (!Array.isArray(ann.comments)) ann.comments = [];
    this._render();
    this.backdrop.hidden = false; this.el.hidden = false;
    var ta = this.el.querySelector(".kb-cmt-input"); if (ta) ta.focus();
  };
  CommentModal.prototype.close = function () {
    if (this.el.hidden) return;
    var ann = this.ann;
    this.el.hidden = true; this.backdrop.hidden = true;
    this.ann = null; this.editingId = null;
    if (ann && (!ann.comments || !ann.comments.length)) this.onCancelEmpty(ann);  // 空标注 = 取消
  };
  CommentModal.prototype._post = function (text) {
    text = (text || "").trim(); if (!text) return;
    var now = new Date().toISOString();
    this.ann.comments.push({ id: uid(), text: text, created: now, updated: now });
    this.ann.updated = now;
    this.onChange(); this._render();
  };
  CommentModal.prototype._saveEdit = function (cid, text) {
    text = (text || "").trim();
    var c = this.ann.comments.filter(function (x) { return x.id === cid; })[0];
    if (c) {
      if (!text) this.ann.comments = this.ann.comments.filter(function (x) { return x.id !== cid; });  // 清空 = 删除
      else { c.text = text; c.updated = new Date().toISOString(); }
    }
    this.editingId = null; this.onChange(); this._render();
  };
  CommentModal.prototype._del = function (cid) {
    this.ann.comments = this.ann.comments.filter(function (x) { return x.id !== cid; });
    this.onChange(); this._render();
  };
  CommentModal.prototype._render = function () {
    var self = this, ann = this.ann; if (!ann) return;
    var ex = ann.exact || "", cs = ann.comments || [];
    var pageTag = ann.page ? '（第 ' + ann.page + ' 页）' : '';
    var listHtml = cs.length
      ? cs.map(function (c) { return self._commentHtml(c); }).join("")
      : '<div class="kb-cmt-empty">还没有笔记，写下第一条吧</div>';
    this.el.innerHTML =
      '<div class="kb-annot-head"><span class="kb-annot-title">📝 笔记 · ' + cs.length + ' 条' + esc(pageTag) + '</span>' +
      '<button type="button" class="kb-annot-x" title="关闭 (Esc)">✕</button></div>' +
      '<div class="kb-annot-sel">“' + esc(ex.slice(0, 280)) + (ex.length > 280 ? "…" : "") + '”</div>' +
      '<div class="kb-cmt-list">' + listHtml + '</div>' +
      '<div class="kb-cmt-new">' +
        '<textarea class="kb-cmt-input" rows="2" placeholder="写条笔记……（Ctrl+Enter 发布）"></textarea>' +
        '<button type="button" class="kb-cmt-post">发布</button>' +
      '</div>';
    this._bind();
  };
  CommentModal.prototype._commentHtml = function (c) {
    if (c.id === this.editingId) {
      return '<div class="kb-cmt kb-cmt-editing" data-id="' + c.id + '">' +
        '<textarea class="kb-cmt-edit-input" rows="3">' + esc(c.text) + '</textarea>' +
        '<div class="kb-cmt-edit-actions">' +
          '<button type="button" class="kb-cmt-edit-cancel">取消</button>' +
          '<button type="button" class="kb-cmt-edit-save">保存</button>' +
        '</div></div>';
    }
    var edited = (c.updated && c.created && c.updated !== c.created) ? " · 已编辑" : "";
    return '<div class="kb-cmt" data-id="' + c.id + '">' +
      '<div class="kb-cmt-text">' + esc(c.text) + '</div>' +
      '<div class="kb-cmt-meta"><span class="kb-cmt-time">' + esc(fmtTime(c.updated || c.created) + edited) + '</span>' +
        '<span class="kb-cmt-acts">' +
          '<button type="button" class="kb-cmt-act kb-cmt-edit">编辑</button>' +
          '<button type="button" class="kb-cmt-act kb-cmt-del">删除</button>' +
        '</span></div></div>';
  };
  CommentModal.prototype._bind = function () {
    var self = this;
    this.el.querySelector(".kb-annot-x").addEventListener("click", function () { self.close(); });
    var input = this.el.querySelector(".kb-cmt-input");
    var post = this.el.querySelector(".kb-cmt-post");
    var submit = function () {
      var v = input.value;
      if (!v.trim()) return;
      self._post(v);                                  // _post 内会 _render（输入框换成全新的空框）
      var ni = self.el.querySelector(".kb-cmt-input"); // 重新聚焦新框，方便连发
      if (ni) ni.focus();
    };
    post.addEventListener("click", submit);
    input.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") { e.preventDefault(); submit(); }
    });
    this.el.querySelectorAll(".kb-cmt[data-id]").forEach(function (row) {
      var cid = row.getAttribute("data-id");
      var eb = row.querySelector(".kb-cmt-edit");
      var db = row.querySelector(".kb-cmt-del");
      if (eb) eb.addEventListener("click", function () { self.editingId = cid; self._render(); });
      if (db) db.addEventListener("click", function () { self._del(cid); });
      var sv = row.querySelector(".kb-cmt-edit-save");
      var cn = row.querySelector(".kb-cmt-edit-cancel");
      var ei = row.querySelector(".kb-cmt-edit-input");
      if (sv) sv.addEventListener("click", function () { self._saveEdit(cid, ei.value); });
      if (cn) cn.addEventListener("click", function () { self.editingId = null; self._render(); });
      if (ei) { ei.focus(); ei.setSelectionRange(ei.value.length, ei.value.length); }
    });
  };

  window.KBComments = { CommentModal: CommentModal, fmtTime: fmtTime };
})();
