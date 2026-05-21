(function () {
  "use strict";

  var openBtn = document.getElementById("kb-manager-btn");
  if (!openBtn) return;

  var state = {
    kbs: [],
    currentSlug: "",
  };

  function getCurrentSlug() {
    var hash = window.location.hash || "";
    var path = hash.replace(/^#\/?/, "").split("?")[0];
    try { path = decodeURIComponent(path); } catch (_) {}
    var m = path.match(/^kb\/([^\/]+)/);
    return m ? m[1] : "";
  }

  function createPanel() {
    var panel = document.createElement("div");
    panel.id = "kb-manager-panel";
    panel.className = "kb-manager-panel";
    panel.innerHTML =
      '<div class="kb-manager-header">' +
        '<div class="kb-manager-title">知识库管理</div>' +
        '<button class="kb-manager-close" id="kb-manager-close">&times;</button>' +
      '</div>' +
      '<div class="kb-manager-body">' +
        '<div class="kb-section">' +
          '<h3>知识库</h3>' +
          '<div class="kb-list" id="kb-list"></div>' +
        '</div>' +
        '<div class="kb-section">' +
          '<h3>新建知识库</h3>' +
          '<input id="kb-new-name" type="text" placeholder="名称，例如：强化学习论文">' +
          '<input id="kb-new-slug" type="text" placeholder="slug，可选：rl-papers">' +
          '<div class="kb-action-row">' +
            '<button id="kb-create-btn">新建</button>' +
          '</div>' +
        '</div>' +
        '<div class="kb-section">' +
          '<h3>导入到知识库</h3>' +
          '<select id="kb-upload-target"></select>' +
          '<div class="kb-action-row">' +
            '<label class="kb-upload-btn">选择文件' +
              '<input id="kb-file-input" type="file" multiple style="display:none">' +
            '</label>' +
            '<label class="kb-upload-btn secondary">选择文件夹' +
              '<input id="kb-folder-input" type="file" webkitdirectory multiple style="display:none">' +
            '</label>' +
          '</div>' +
          '<div class="kb-status" id="kb-status"></div>' +
        '</div>' +
        '<div class="kb-section">' +
          '<a class="kb-settings-link" href="docs/tools/settings.html" target="_blank">⚙️ 后端 / API key 设置</a>' +
        '</div>' +
      '</div>';
    document.body.appendChild(panel);
    return panel;
  }

  var panel = createPanel();
  var closeBtn = document.getElementById("kb-manager-close");
  var listEl = document.getElementById("kb-list");
  var nameInput = document.getElementById("kb-new-name");
  var slugInput = document.getElementById("kb-new-slug");
  var createBtn = document.getElementById("kb-create-btn");
  var uploadTarget = document.getElementById("kb-upload-target");
  var fileInput = document.getElementById("kb-file-input");
  var folderInput = document.getElementById("kb-folder-input");
  var statusEl = document.getElementById("kb-status");

  function setStatus(text, isError) {
    statusEl.textContent = text || "";
    statusEl.classList.toggle("error", !!isError);
  }

  function openPanel() {
    panel.classList.add("open");
    document.body.classList.add("kb-manager-open");
    loadKbs();
  }

  function closePanel() {
    panel.classList.remove("open");
    document.body.classList.remove("kb-manager-open");
  }

  function renderKbs() {
    state.currentSlug = getCurrentSlug();
    listEl.innerHTML = "";
    uploadTarget.innerHTML = "";
    state.kbs.forEach(function (kb) {
      var item = document.createElement("div");
      item.className = "kb-list-item" + (kb.slug === state.currentSlug ? " active" : "");
      item.innerHTML =
        '<div class="kb-list-main">' +
          '<div class="kb-list-name"></div>' +
          '<div class="kb-list-meta"></div>' +
        '</div>' +
        '<div class="kb-list-actions">' +
          '<button class="kb-open-btn">打开</button>' +
          '<button class="kb-rename-btn secondary" title="重命名">改名</button>' +
          '<button class="kb-delete-btn danger" title="移到 _trash/">删</button>' +
        '</div>';
      item.querySelector(".kb-list-name").textContent = kb.name;
      item.querySelector(".kb-list-meta").textContent =
        kb.slug + " · " + (kb.files || 0) + " 篇 · " + ((kb.chars || 0) / 10000).toFixed(1) + " 万字";
      item.querySelector(".kb-open-btn").addEventListener("click", function () {
        window.location.hash = "#/kb/" + encodeURIComponent(kb.slug) + "/";
        closePanel();
        setTimeout(function () { location.reload(); }, 50);
      });
      item.querySelector(".kb-rename-btn").addEventListener("click", function () {
        var nv = prompt("新的知识库名称：", kb.name);
        if (nv && nv.trim() && nv.trim() !== kb.name) {
          renameKb(kb.slug, nv.trim());
        }
      });
      item.querySelector(".kb-delete-btn").addEventListener("click", function () {
        if (confirm("把知识库「" + kb.name + "」整个目录搬到 _trash/？\n（_trash/ 在 .gitignore 内，不会推到远端，本地也不会自动清空。）")) {
          deleteKb(kb.slug);
        }
      });
      listEl.appendChild(item);

      var opt = document.createElement("option");
      opt.value = kb.slug;
      opt.textContent = kb.name + " (" + kb.slug + ")";
      if (kb.slug === state.currentSlug) opt.selected = true;
      uploadTarget.appendChild(opt);
    });
    if (!state.kbs.length) {
      listEl.innerHTML = '<div class="kb-list-meta">暂无知识库</div>';
    }
  }

  async function loadKbs() {
    try {
      var resp = await fetch("/api/kbs");
      if (!resp.ok) throw new Error("加载失败：" + resp.status);
      var data = await resp.json();
      state.kbs = data.items || [];
      renderKbs();
    } catch (err) {
      setStatus(err.message, true);
    }
  }

  async function createKb() {
    var name = nameInput.value.trim();
    var slug = slugInput.value.trim();
    if (!name) {
      setStatus("请输入知识库名称", true);
      return;
    }
    setStatus("正在创建...");
    try {
      var resp = await fetch("/api/kbs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, slug: slug || null }),
      });
      var data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "创建失败");
      nameInput.value = "";
      slugInput.value = "";
      setStatus("已创建：" + data.name);
      await loadKbs();
      window.location.hash = "#/kb/" + encodeURIComponent(data.slug) + "/";
      setTimeout(function () { location.reload(); }, 80);
    } catch (err) {
      setStatus(err.message, true);
    }
  }

  async function renameKb(slug, newName) {
    setStatus("正在重命名...");
    try {
      var resp = await fetch("/api/kbs/" + encodeURIComponent(slug), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName }),
      });
      var data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "重命名失败");
      setStatus("已重命名为：" + data.name);
      await loadKbs();
      setTimeout(function () { location.reload(); }, 400);
    } catch (err) {
      setStatus(err.message, true);
    }
  }

  async function deleteKb(slug) {
    setStatus("正在搬到 _trash/...");
    try {
      var resp = await fetch("/api/kbs/" + encodeURIComponent(slug), { method: "DELETE" });
      var data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "删除失败");
      setStatus("已搬到：" + data.trashed_at);
      await loadKbs();
      if (state.currentSlug === slug) {
        window.location.hash = "#/";
        setTimeout(function () { location.reload(); }, 400);
      }
    } catch (err) {
      setStatus(err.message, true);
    }
  }

  async function uploadFiles(fileList, fromFolder) {
    var slug = uploadTarget.value || state.currentSlug;
    if (!slug) {
      setStatus("请先选择目标知识库", true);
      return;
    }
    var files = Array.from(fileList || []);
    if (!files.length) return;

    var form = new FormData();
    files.forEach(function (file) {
      form.append("files", file, file.name);
      form.append("relative_paths", fromFolder ? (file.webkitRelativePath || file.name) : file.name);
    });

    setStatus("正在上传 " + files.length + " 个文件...");
    try {
      var resp = await fetch("/api/kbs/" + encodeURIComponent(slug) + "/upload", {
        method: "POST",
        body: form,
      });
      var data = await resp.json();
      if (!resp.ok) throw new Error(data.detail || "上传失败");
      var msg = "已导入 " + (data.saved || []).length + " 个文件";
      if (data.errors && data.errors.length) {
        msg += "\n失败 " + data.errors.length + " 个：" +
          data.errors.slice(0, 5).map(function (e) { return "\n- " + e.path + ": " + e.error; }).join("");
      }
      setStatus(msg, !!(data.errors && data.errors.length));
      await loadKbs();
      setTimeout(function () { location.reload(); }, 600);
    } catch (err) {
      setStatus(err.message, true);
    }
  }

  openBtn.addEventListener("click", openPanel);
  closeBtn.addEventListener("click", closePanel);
  createBtn.addEventListener("click", createKb);
  fileInput.addEventListener("change", function () {
    uploadFiles(fileInput.files, false);
    fileInput.value = "";
  });
  folderInput.addEventListener("change", function () {
    uploadFiles(folderInput.files, true);
    folderInput.value = "";
  });
  window.addEventListener("hashchange", renderKbs);
})();
