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

  // ---- reusable sortable / filterable / paginated table -------------------
  // renderTable(hostEl, {
  //   columns: [{ key, label, sort:'text'|'num'|'date', render:fn(val,row), cls }],
  //   rows: [...], filter:true, pageSize:50, emptyText:'…',
  //   controls: '<extra html injected into the toolbar>'
  // })
  function renderTable(host, opts) {
    var cols = opts.columns;
    var allRows = opts.rows || [];
    var pageSize = opts.pageSize == null ? 50 : opts.pageSize;
    var state = {
      sortKey: opts.defaultSortKey || null, dir: opts.defaultSortDir || 1,
      q: "", page: 0, extra: (typeof opts.extraFilter === "function" ? opts.extraFilter : null)
    };

    host.innerHTML =
      '<div class="tbl-tools">' +
        (opts.filter ? '<input type="text" class="tbl-filter" placeholder="Filter…">' : '') +
        '<span class="tbl-extra"></span>' +
        '<span class="tbl-count faint"></span>' +
      '</div>' +
      '<div class="table-scroll"><table class="grid"><thead><tr>' +
        cols.map(function (c) {
          return '<th data-k="' + esc(c.key) + '"' + (c.sort ? ' class="sortable"' : '') + '>' +
                 esc(c.label) + '<span class="sar"></span></th>';
        }).join("") +
      '</tr></thead><tbody></tbody></table></div>' +
      (pageSize ? '<div class="tbl-pager"></div>' : '');

    var tbody = host.querySelector("tbody");
    var countEl = host.querySelector(".tbl-count");
    var pagerEl = host.querySelector(".tbl-pager");
    var filterEl = host.querySelector(".tbl-filter");
    if (opts.controls) host.querySelector(".tbl-extra").innerHTML = opts.controls;

    function cmp(a, b, c) {
      var x = a[c.key], y = b[c.key];
      if (c.sort === "num") { x = parseFloat(x) || 0; y = parseFloat(y) || 0; return x - y; }
      if (c.sort === "date") { x = Date.parse(x) || 0; y = Date.parse(y) || 0; return x - y; }
      return String(x == null ? "" : x).localeCompare(String(y == null ? "" : y), undefined, { numeric: true });
    }

    function view() {
      var rows = allRows;
      if (state.extra) rows = rows.filter(state.extra);
      if (state.q) {
        var q = state.q.toLowerCase();
        rows = rows.filter(function (r) {
          return cols.some(function (c) { return String(r[c.key] == null ? "" : r[c.key]).toLowerCase().indexOf(q) !== -1; });
        });
      }
      if (state.sortKey) {
        var c = cols.filter(function (x) { return x.key === state.sortKey; })[0];
        if (c) rows = rows.slice().sort(function (a, b) { return cmp(a, b, c) * state.dir; });
      }
      return rows;
    }

    function draw() {
      var rows = view();
      var total = rows.length;
      var pages = pageSize ? Math.max(1, Math.ceil(total / pageSize)) : 1;
      if (state.page >= pages) state.page = pages - 1;
      var slice = pageSize ? rows.slice(state.page * pageSize, state.page * pageSize + pageSize) : rows;

      tbody.innerHTML = slice.length ? slice.map(function (r) {
        return "<tr>" + cols.map(function (c) {
          var v = r[c.key];
          var cell = c.render ? c.render(v, r) : esc(v == null ? "" : v);
          return "<td" + (c.cls ? ' class="' + c.cls + '"' : "") + ">" + cell + "</td>";
        }).join("") + "</tr>";
      }).join("") : '<tr><td colspan="' + cols.length + '" class="faint" style="padding:20px;text-align:center">' +
        esc(opts.emptyText || "No rows.") + "</td></tr>";

      countEl.textContent = total + (total === 1 ? " row" : " rows");

      host.querySelectorAll("th").forEach(function (th) {
        var s = th.querySelector(".sar");
        s.textContent = th.dataset.k === state.sortKey ? (state.dir > 0 ? " ▲" : " ▼") : "";
      });

      if (pagerEl) {
        pagerEl.innerHTML = pages > 1
          ? '<button class="tbl-pg" data-d="-1"' + (state.page === 0 ? " disabled" : "") + ">‹ Prev</button>" +
            '<span class="faint">Page ' + (state.page + 1) + " / " + pages + "</span>" +
            '<button class="tbl-pg" data-d="1"' + (state.page >= pages - 1 ? " disabled" : "") + ">Next ›</button>"
          : "";
      }
    }

    host.querySelectorAll("th.sortable").forEach(function (th) {
      th.addEventListener("click", function () {
        var k = th.dataset.k;
        if (state.sortKey === k) state.dir = -state.dir; else { state.sortKey = k; state.dir = 1; }
        draw();
      });
    });
    if (filterEl) filterEl.addEventListener("input", function () { state.q = filterEl.value; state.page = 0; draw(); });
    if (pagerEl) pagerEl.addEventListener("click", function (e) {
      var b = e.target.closest(".tbl-pg"); if (!b || b.disabled) return;
      state.page += parseInt(b.dataset.d, 10); draw();
    });

    draw();
    return {
      redraw: draw,
      host: host,
      setFilter: function (fn) { state.extra = fn || null; state.page = 0; draw(); }
    };
  }

  global.NAHub = {
    CLASS_COLORS: CLASS_COLORS,
    classColor: classColor,
    esc: esc,
    timeAgo: timeAgo,
    fmtDateFromEpoch: fmtDateFromEpoch,
    loadJSON: loadJSON,
    boot: boot,
    renderTable: renderTable
  };
})(window);
