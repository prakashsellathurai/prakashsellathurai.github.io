(function () {
    "use strict";

    var STORAGE_KEY = "theme";
    var DARK = "dark";
    var LIGHT = "light";

    function getPreferred() {
        var stored = null;
        try { stored = localStorage.getItem(STORAGE_KEY); } catch (e) { /* noop */ }
        if (stored === DARK || stored === LIGHT) return stored;
        if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
            return DARK;
        }
        return LIGHT;
    }

    function apply(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        var btn = document.getElementById("theme-toggle");
        if (btn) {
            btn.setAttribute("aria-label", theme === DARK ? "Switch to light mode" : "Switch to dark mode");
            btn.textContent = theme === DARK ? "\u2600\uFE0F" : "\uD83C\uDF19";
        }
    }

    function toggle() {
        var current = document.documentElement.getAttribute("data-theme") || LIGHT;
        var next = current === DARK ? LIGHT : DARK;
        apply(next);
        try { localStorage.setItem(STORAGE_KEY, next); } catch (e) { /* noop */ }
    }

    /* Apply on load (the inline script in <head> already set data-theme,
       but we update the button state here). */
    apply(getPreferred());

    function init() {
        var btn = document.getElementById("theme-toggle");
        if (btn) {
            btn.addEventListener("click", toggle);
            /* Re-apply so button label is correct */
            apply(getPreferred());
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }

    /* Listen for OS theme changes */
    if (window.matchMedia) {
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", function (e) {
            var stored = null;
            try { stored = localStorage.getItem(STORAGE_KEY); } catch (ex) { /* noop */ }
            if (!stored) {
                apply(e.matches ? DARK : LIGHT);
            }
        });
    }
})();
