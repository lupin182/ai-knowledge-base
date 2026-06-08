/* 正文图片单击放大（lightbox）。仅 .article 内、未被 <a> 包裹的图片
   （链接里的图点了应跟随链接，不放大）。放大后等比 fit-to-screen，再点遮罩 / 按 Esc 关闭。
   Astro 是整页加载，挂载一次即可；笔记下划线(reading.js)不动图片，无需观察器。 */
(function () {
  function mount() {
    var article = document.querySelector("article.article");
    if (!article) return;

    var overlay = null;

    function onKey(e) { if (e.key === "Escape") close(); }

    function close() {
      if (!overlay) return;
      var o = overlay;
      overlay = null;
      o.classList.remove("show");
      setTimeout(function () { if (o && o.parentNode) o.parentNode.removeChild(o); }, 160);
      document.removeEventListener("keydown", onKey);
    }

    function open(src, alt) {
      close();
      overlay = document.createElement("div");
      overlay.className = "kb-img-overlay";
      var big = document.createElement("img");
      big.src = src;
      big.alt = alt || "";
      overlay.appendChild(big);
      overlay.addEventListener("click", close);
      document.body.appendChild(overlay);
      requestAnimationFrame(function () { if (overlay) overlay.classList.add("show"); });
      document.addEventListener("keydown", onKey);
    }

    function bind(img) {
      if (img.dataset.kbZoom) return;        // 防重复绑定
      if (img.closest("a")) return;          // 链接里的图：跟随链接，不放大
      img.dataset.kbZoom = "1";
      img.style.cursor = "zoom-in";
      img.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        open(img.currentSrc || img.src, img.alt);
      });
    }

    Array.prototype.forEach.call(article.querySelectorAll("img"), bind);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
