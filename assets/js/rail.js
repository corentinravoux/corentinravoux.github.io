// Redshift rail and scroll reveal. No dependencies, no scroll listeners:
// both effects run on IntersectionObserver. The rail fill and the mobile
// progress bar are pure CSS (scroll-driven animations).
(function () {
  window.__rail = true;             // tells the inline head script the reveal is handled
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var hasIO = "IntersectionObserver" in window;

  // ---------------------------------------------------------------- rail ticks
  // Highlights the tick of the section crossing the middle of the viewport.
  var ticks = Array.prototype.slice.call(document.querySelectorAll(".rail .tick"));
  if (ticks.length && hasIO) {
    // "#top" points at <main>, which spans the whole page; for highlighting, the
    // z = 0 tick stands for the hero and the about section instead.
    var targets = ticks.map(function (t) {
      var id = t.getAttribute("href").slice(1);
      var els = id === "top" ? [document.querySelector(".hero"), document.getElementById("about")]
                             : [document.getElementById(id)];
      return els.filter(Boolean);
    });
    var visible = new Set();
    var mark = function () {
      var current = -1;
      for (var i = 0; i < targets.length && current < 0; i++) {
        if (targets[i].some(function (el) { return visible.has(el); })) current = i;
      }
      ticks.forEach(function (t, i) { t.setAttribute("aria-current", i === current ? "true" : "false"); });
    };
    var railObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) visible.add(e.target); else visible.delete(e.target);
      });
      mark();
    }, { rootMargin: "-45% 0px -45% 0px" });
    targets.forEach(function (els) { els.forEach(function (el) { railObserver.observe(el); }); });
  }

  // ------------------------------------------------------------- scroll reveal
  // Content enters once, as it reaches the viewport. Without IntersectionObserver
  // or with reduced motion, everything is shown at once.
  var items = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (!hasIO || reduce) {
    items.forEach(function (el) { el.classList.add("is-in"); });
    return;
  }
  var revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add("is-in");
      revealObserver.unobserve(e.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  items.forEach(function (el) { revealObserver.observe(el); });

  // Anything already above the fold on load (deep links, reloads) shows immediately.
  window.addEventListener("load", function () {
    items.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("is-in");
    });
  }, { once: true });
})();
