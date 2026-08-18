(function () {
    function normalize(v) {
        return v.replace(/\s+/g, " ").trim().toLowerCase();
    }

    function walk(el, out) {
        for (var node = el.firstChild; node; node = node.nextSibling) {
            if (node.nodeType === 1 && node.matches && node.matches("a.gb-tree-file")) {
                out.push(node);
                continue;
            }
            if (node.nodeType === 1 && node.children && node.children.length) {
                walk(node, out);
            }
        }
        return out;
    }

    function handleSearch(input) {
        var panel = document.getElementById("mw-panel");
        if (!panel) return;
        var query = normalize(input.value);
        var links = walk(panel, []);

        links.forEach(function (link) {
            var text = normalize(link.textContent);
            var match = !query || text.indexOf(query) !== -1;
            link.classList.toggle("gb-search-hidden", !match);
        });

        var visible = panel.querySelectorAll("a.gb-tree-file:not(.gb-search-hidden)").length;

        panel.querySelectorAll("details.gb-tree-dir, details.gb-tree-sub").forEach(function (det) {
            if (query) {
                det.setAttribute("open", "");
            }
        });
        panel.dataset.gbSearchActive = query ? "1" : "0";
        panel.dataset.gbHasResults = visible > 0 ? "1" : "0";
    }

    document.addEventListener("keydown", function (e) {
        var modifier = e.ctrlKey || e.metaKey;
        if (modifier && e.key.toLowerCase() === "k") {
            var input = document.querySelector("#p-search input[data-gb-search]");
            if (input) {
                e.preventDefault();
                input.focus();
                input.select();
            }
        }
        if (e.key === "Escape") {
            var el = document.activeElement;
            if (el && el.matches && el.matches("input[data-gb-search]")) {
                el.value = "";
                handleSearch(el);
                el.blur();
            }
        }
    });

    document.querySelectorAll("input[data-gb-search]").forEach(function (input) {
        input.addEventListener("input", function () { handleSearch(input); });
    });
})();