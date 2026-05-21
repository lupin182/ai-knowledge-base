// 顶栏 KB 切换器：点 KB ▾ 弹下拉，列出所有 KB + 跳设置页入口
(function () {
  "use strict";

  var btn = document.getElementById("kb-switcher-btn");
  var menu = document.getElementById("kb-switcher-menu");
  var label = document.getElementById("kb-switcher-label");
  if (!btn || !menu) return;

  function currentSlug() {
    var hash = window.location.hash || "";
    var path = hash.replace(/^#\/?/, "").split("?")[0];
    try { path = decodeURIComponent(path); } catch (e) {}
    var m = path.match(/^kb\/([^\/]+)/);
    return m ? m[1] : "";
  }

  async function loadAndRender() {
    var slug = currentSlug();
    try {
      var resp = await fetch("/api/kbs");
      var data = await resp.json();
      var items = data.items || [];
      var current = items.find(function (k) { return k.slug === slug; });
      if (current) label.textContent = current.name;
      else if (items.length) label.textContent = items[0].name;

      menu.innerHTML = "";
      items.forEach(function (kb) {
        var a = document.createElement("a");
        a.href = "#/kb/" + encodeURIComponent(kb.slug) + "/";
        a.className = "kb-switcher-item" + (kb.slug === slug ? " active" : "");
        a.innerHTML =
          '<span class="kb-switcher-name"></span>' +
          '<span class="kb-switcher-meta"></span>';
        a.querySelector(".kb-switcher-name").textContent = kb.name;
        a.querySelector(".kb-switcher-meta").textContent = kb.files + " 篇";
        a.addEventListener("click", function () {
          setTimeout(function () { location.reload(); }, 50);
        });
        menu.appendChild(a);
      });
      var divider = document.createElement("div");
      divider.className = "kb-switcher-divider";
      menu.appendChild(divider);
      var settings = document.createElement("a");
      settings.href = "docs/tools/settings.html";
      settings.className = "kb-switcher-item kb-switcher-settings";
      settings.textContent = "⚙️ 管理知识库 / 后端设置";
      menu.appendChild(settings);
    } catch (e) {
      menu.innerHTML = '<div class="kb-switcher-error">加载失败：' + e.message + '</div>';
    }
  }

  function toggleMenu(open) {
    if (open === undefined) open = !menu.classList.contains("open");
    menu.classList.toggle("open", open);
    if (open) loadAndRender();
  }

  btn.addEventListener("click", function (e) {
    e.stopPropagation();
    toggleMenu();
  });

  document.addEventListener("click", function (e) {
    if (!menu.contains(e.target) && e.target !== btn) toggleMenu(false);
  });

  window.addEventListener("hashchange", loadAndRender);
  loadAndRender();
})();
