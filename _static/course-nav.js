(function () {
  // Suppress Sphinx's post-search highlighting + "Hide Search Matches"
  // banner. sphinx_highlight.js reads terms from localStorage (persists
  // across navigations) and the ?highlight= URL param; clearing both
  // synchronously, before its DOMContentLoaded handler, makes it find
  // nothing and skip the banner.
  try {
    window.localStorage.removeItem("sphinx_highlight_terms");
  } catch (e) { /* ignore */ }
  if (window.location.search.includes("highlight=")) {
    const url = new URL(window.location.href);
    url.searchParams.delete("highlight");
    window.history.replaceState(null, "", url.toString());
  }

  // Restrict the theme switcher to light/dark only: the theme's one button
  // cycles light → dark → auto, and we force-skip the auto step.
  function restrictThemeToggle() {
    const root = document.documentElement;
    function forceLight() {
      root.dataset.mode = "light";
      root.dataset.theme = "light";
      try {
        window.localStorage.setItem("mode", "light");
      } catch (e) { /* ignore */ }
    }
    if (root.dataset.mode === "auto") {
      forceLight();
    } else if (root.dataset.theme !== root.dataset.mode) {
      // Keep theme in sync with mode on initial load.
      root.dataset.theme = root.dataset.mode;
    }
    const observer = new MutationObserver(() => {
      if (root.dataset.mode === "auto") {
        // Skip auto: go straight to light, completing the light → dark → light cycle.
        forceLight();
      } else if (root.dataset.theme !== root.dataset.mode) {
        root.dataset.theme = root.dataset.mode;
      }
    });
    observer.observe(root, { attributes: true, attributeFilter: ["data-mode"] });
  }

  // Rewrite sphinx-proof / sphinx-exercise titles from "Definition N
  // (Waveform)" to "Definition: Waveform" — the counter is noise when every
  // directive has a name. The type word comes from the caption-number span,
  // the title from the parenthesized text; with no parens, keep just the
  // type word. The span is also CSS-hidden as a no-JS fallback.
  function rewriteAdmonitionTitles() {
    const titles = document.querySelectorAll(
      ".proof > .admonition-title, .exercise > .admonition-title, .solution > .admonition-title"
    );
    titles.forEach((titleEl) => {
      const numSpan = titleEl.querySelector(".caption-number");
      if (!numSpan) return;
      const typeWord = numSpan.textContent.trim().split(/\s+/)[0].replace(/[:.]+$/, "");
      const fullText = titleEl.textContent.trim();
      const parenMatch = fullText.match(/\(([^)]*)\)\s*$/);
      titleEl.textContent = parenMatch ? `${typeWord}: ${parenMatch[1]}` : typeWord;
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", restrictThemeToggle);
    document.addEventListener("DOMContentLoaded", rewriteAdmonitionTitles);
  } else {
    restrictThemeToggle();
    rewriteAdmonitionTitles();
  }
})();
