/* Negative Aura - Officer Hub : shared helpers (no dependencies) */
(function (global) {
  "use strict";

  var CLASS_COLORS = {
    "death knight": "#C41E3A",
    "demon hunter": "#A330C9",
    "druid": "#FF7C0A",
    "evoker": "#33937F",
    "hunter": "#AAD372",
    "mage": "#3FC7EB",
    "monk": "#00FF98",
    "paladin": "#F48CBA",
    "priest": "#E6E6E6",
    "rogue": "#FFF468",
    "shaman": "#0070DD",
    "warlock": "#8788EE",
    "warrior": "#C69B6D"
  };

  function classColor(cls) {
    return CLASS_COLORS[String(cls || "").toLowerCase()] || "var(--text)";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function timeAgo(iso) {
    if (!iso) return "unknown";
    var then = new Date(iso).getTime();
    if (isNaN(then)) return "unknown";
    var s = Math.max(0, (Date.now() - then) / 1000);
    if (s < 90) return "just now";
    var m = s / 60;
    if (m < 60) return Math.round(m) + " min ago";
    var h = m / 60;
    if (h < 24) return Math.round(h) + " hour" + (Math.round(h) === 1 ? "" : "s") + " ago";
    var d = Math.round(h / 24);
    return d + " day" + (d === 1 ? "" : "s") + " ago";
  }

  function fmtDateFromEpoch(ms) {
    if (!ms) return "";
    var d = new Date(ms);
    if (isNaN(d.getTime())) return "";
    return d.toISOString().slice(0, 10);
  }

  // fetch JSON relative to the page; works from file:// too when the file exists
  function loadJSON(path) {
    return fetch(path, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(path + " -> HTTP " + r.status);
      return r.json();
    });
  }

  // Standard page bootstrap: set the "updated" stamp from meta.json, run render()
  function boot(opts) {
    var updatedEl = document.querySelector(".page-head .updated");
    loadJSON("../data/meta.json")
      .then(function (meta) {
        if (updatedEl) {
          updatedEl.textContent = "data as of " + timeAgo(meta.generatedAt);
          updatedEl.title = meta.generatedAt || "";
        }
        return meta;
      })
      .catch(function () { return {}; })
      .then(function (meta) {
        try { opts.render(meta); } catch (e) {
          console.error(e);
          var host = document.querySelector(opts.errorInto || "#content");
          if (host) host.innerHTML = '<div class="notice err">Failed to render: ' + esc(e.message) + "</div>";
        }
      });
  }

  global.NAHub = {
    CLASS_COLORS: CLASS_COLORS,
    classColor: classColor,
    esc: esc,
    timeAgo: timeAgo,
    fmtDateFromEpoch: fmtDateFromEpoch,
    loadJSON: loadJSON,
    boot: boot
  };
})(window);
