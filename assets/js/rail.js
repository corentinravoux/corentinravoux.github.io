// Marks the redshift tick matching the section in view. No dependencies.
(function () {
  var ticks = Array.prototype.slice.call(document.querySelectorAll(".rail .tick"));
  if (!ticks.length || !("IntersectionObserver" in window)) return;

  var byId = {};
  ticks.forEach(function (t) { byId[t.getAttribute("href").slice(1)] = t; });

  var seen = new Set();
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) seen.add(e.target.id); else seen.delete(e.target.id);
    });
    // topmost visible section wins
    var current = Object.keys(byId).filter(function (id) { return seen.has(id); })[0];
    ticks.forEach(function (t) {
      t.setAttribute("aria-current", t.getAttribute("href") === "#" + current ? "true" : "false");
    });
  }, { rootMargin: "-45% 0px -45% 0px" });

  Object.keys(byId).forEach(function (id) {
    var el = document.getElementById(id);
    if (el) observer.observe(el);
  });
})();
