(function () {
    "use strict";

    var MAX_RESULTS = 8;
    var TYPE_LABELS = ["Essay", "Note", "Experiment", "Book", "Project", "Quote", "LeetCode"];
    var TYPE_BOOST = [3, 3, 2.5, 1.5, 1.5, 1, 1];

    var INDEX = null;
    var docs = [];
    var chars = [];
    var kids = [];
    var weights = [];
    var indexLoading = false;
    var indexQueue = [];

    function setIndexData() {
        INDEX = window.__SEARCH__ || null;
        docs = INDEX ? INDEX.d : [];
        chars = INDEX ? INDEX.c : [];
        kids = INDEX ? INDEX.k : [];
        weights = INDEX ? INDEX.w : [];
    }

    function ensureIndex(cb) {
        if (INDEX) {
            cb();
            return;
        }
        indexQueue.push(cb);
        if (indexLoading) return;
        indexLoading = true;
        var s = document.createElement("script");
        s.src = "/static/search-index.js";
        s.onload = function () {
            setIndexData();
            indexLoading = false;
            var queue = indexQueue;
            indexQueue = [];
            for (var i = 0; i < queue.length; i++) queue[i]();
        };
        s.onerror = function () {
            indexLoading = false;
            indexQueue = [];
        };
        document.head.appendChild(s);
    }

    function normalizeQuery(q) {
        return (q || "").toLowerCase().replace(/\s+/g, " ").trim();
    }

    function queryTerms(q) {
        var m = q.match(/[a-z0-9]+/g);
        return m || [];
    }

    function findNode(term) {
        var node = 0;
        var i = 0;
        while (i < term.length) {
            var seg = chars[node];
            var j = 0;
            while (j < seg.length && i < term.length && seg[j] === term[i]) { j++; i++; }
            if (i === term.length) return node;
            if (j < seg.length) return -1;
            var found = -1;
            var k = kids[node];
            for (var m = 0; m < k.length; m++) {
                if (chars[k[m]].charAt(0) === term[i]) { found = k[m]; break; }
            }
            if (found === -1) return -1;
            node = found;
        }
        return node;
    }

    function collect(node, out) {
        if (node < 0 || out.count >= 60) return;
        var w = weights[node];
        for (var i = 0; i < w.length; i++) {
            var docId = w[i] >> 4;
            out.docs[docId] = (out.docs[docId] || 0) + (w[i] & 15);
            out.count++;
        }
        var k = kids[node];
        for (var j = 0; j < k.length; j++) {
            collect(k[j], out);
        }
    }

    function rank(query) {
        var q = normalizeQuery(query);
        var terms = queryTerms(q);
        var agg = {};
        for (var t = 0; t < terms.length; t++) {
            var node = findNode(terms[t]);
            var collector = { docs: {}, count: 0 };
            collect(node, collector);
            for (var d in collector.docs) {
                agg[d] = (agg[d] || 0) + collector.docs[d];
            }
        }

        var ql = q.length;
        var results = [];
        for (var did in agg) {
            var title = docs[did][0].toLowerCase();
            var score = agg[did];
            if (title.indexOf(q) === 0) score += 6;
            else if (title.indexOf(q) !== -1) score += 3;
            score += TYPE_BOOST[docs[did][2]] || 0;
            results.push({ id: +did, score: score });
        }
        results.sort(function (a, b) {
            return b.score - a.score || a.id - b.id;
        });
        return results.slice(0, MAX_RESULTS);
    }

    function highlight(title, q) {
        if (!q) return title;
        var i = title.toLowerCase().indexOf(q);
        if (i === -1) return title;
        return (
            title.slice(0, i) +
            "<mark>" + title.slice(i, i + q.length) + "</mark>" +
            title.slice(i + q.length)
        );
    }

    function escapeHtml(s) {
        return s.replace(/[&<>"']/g, function (c) {
            return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
        });
    }

    function init() {
        var form = document.querySelector("#p-search form");
        if (!form) return;
        var input = form.querySelector("input[data-gb-search]");
        if (!input) return;

        var domain = form.getAttribute("data-site-domain") || "";
        var wrap = document.createElement("div");
        wrap.className = "sb-wrap";
        form.parentNode.insertBefore(wrap, form);
        wrap.appendChild(form);

        var dropdown = document.createElement("div");
        dropdown.className = "sb-dropdown";
        dropdown.setAttribute("role", "listbox");
        wrap.appendChild(dropdown);

        var items = [];
        var activeIndex = -1;
        var timer = null;
        var googleRow = null;

        function googleUrl(q) {
            return "https://www.google.com/search?q=" +
                encodeURIComponent("site:" + domain + " " + q);
        }

        function closeDropdown() {
            dropdown.classList.remove("open");
            dropdown.innerHTML = "";
            items = [];
            activeIndex = -1;
        }

        function render(q) {
            var results = rank(q);
            if (!results.length) {
                closeDropdown();
                return;
            }
            var html = "";
            items = [];
            for (var i = 0; i < results.length; i++) {
                var d = docs[results[i].id];
                items.push(d);
                html +=
                    '<div class="sb-item" role="option" data-idx="' + results[i].id + '">' +
                    '<span class="sb-title">' + highlight(escapeHtml(d[0]), q) + "</span>" +
                    '<span class="sb-type">' + TYPE_LABELS[d[2]] + "</span>" +
                    "</div>";
            }
            html +=
                '<div class="sb-google" role="option" data-idx="google">' +
                'Search Google for <strong>"' + escapeHtml(q) + '"</strong> on ' +
                escapeHtml(domain) + "</div>";
            dropdown.innerHTML = html;
            googleRow = dropdown.lastElementChild;
            dropdown.classList.add("open");
            activeIndex = -1;
            setActive(-1);
        }

        function setActive(idx) {
            var rows = dropdown.querySelectorAll(".sb-item, .sb-google");
            for (var i = 0; i < rows.length; i++) {
                rows[i].classList.toggle("active", i === idx);
            }
            activeIndex = idx;
        }

        function navigate(idx) {
            var row = dropdown.querySelectorAll(".sb-item, .sb-google")[idx];
            if (!row) return;
            if (row.classList.contains("sb-google")) {
                window.location.href = googleUrl(normalizeQuery(input.value));
            } else {
                window.location.href = docs[+row.getAttribute("data-idx")][1];
            }
        }

        function handleInput() {
            var q = normalizeQuery(input.value);
            if (!q) {
                closeDropdown();
                return;
            }
            clearTimeout(timer);
            timer = setTimeout(function () {
                ensureIndex(function () { render(q); });
            }, 120);
        }

        dropdown.addEventListener("mousedown", function (e) {
            e.preventDefault();
            var row = e.target.closest(".sb-item, .sb-google");
            if (!row) return;
            var all = dropdown.querySelectorAll(".sb-item, .sb-google");
            navigate(Array.prototype.indexOf.call(all, row));
        });

        dropdown.addEventListener("mousemove", function (e) {
            var row = e.target.closest(".sb-item, .sb-google");
            if (row) {
                var all = dropdown.querySelectorAll(".sb-item, .sb-google");
                setActive(Array.prototype.indexOf.call(all, row));
            }
        });

        input.addEventListener("input", handleInput);
        input.addEventListener("focus", function () {
            if (normalizeQuery(input.value)) handleInput();
        });

        input.addEventListener("blur", function () {
            setTimeout(closeDropdown, 120);
        });

        input.addEventListener("keydown", function (e) {
            if (e.key === "ArrowDown") {
                e.preventDefault();
                var total = dropdown.querySelectorAll(".sb-item, .sb-google").length;
                if (total) setActive((activeIndex + 1) % total);
            } else if (e.key === "ArrowUp") {
                e.preventDefault();
                var totalUp = dropdown.querySelectorAll(".sb-item, .sb-google").length;
                if (totalUp) setActive((activeIndex - 1 + totalUp) % totalUp);
            } else if (e.key === "Enter") {
                var q = normalizeQuery(input.value);
                if (!q) return;
                e.preventDefault();
                if (activeIndex >= 0) navigate(activeIndex);
                else window.location.href = googleUrl(q);
            } else if (e.key === "Escape") {
                input.value = "";
                closeDropdown();
                input.blur();
            }
        });

        document.addEventListener("keydown", function (e) {
            var modifier = e.ctrlKey || e.metaKey;
            if (modifier && e.key.toLowerCase() === "k") {
                e.preventDefault();
                input.focus();
                input.select();
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();