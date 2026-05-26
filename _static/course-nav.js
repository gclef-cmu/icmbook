(function () {
  // Suppress Sphinx's post-search highlighting + "Hide Search Matches"
  // banner. sphinx_highlight.js reads the terms from two places on every
  // page load: localStorage["sphinx_highlight_terms"] (written by the
  // search page and persisting across navigations — this is why the
  // banner appeared even when clicking a sidebar link), and the URL's
  // ?highlight=... fallback. Clearing both synchronously here, before
  // sphinx_highlight.js's DOMContentLoaded handler runs, makes it find
  // no terms and skip rendering the banner. SPHINX_HIGHLIGHT_ENABLED
  // is a `const` so it can't be toggled from another script.
  try {
    window.localStorage.removeItem("sphinx_highlight_terms");
  } catch (e) { /* ignore */ }
  if (window.location.search.includes("highlight=")) {
    const url = new URL(window.location.href);
    url.searchParams.delete("highlight");
    window.history.replaceState(null, "", url.toString());
  }

  // Restrict the theme switcher to light/dark only. The pydata-sphinx-theme
  // switcher is one button that cycles light → dark → auto; we force-skip
  // the auto step so users only ever toggle between sun and moon.
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

  // Rewrite sphinx-proof and sphinx-exercise titles from the default
  // "Definition N (Waveform)" format to "Definition: Waveform". The
  // running counter adds noise without information when every directive
  // already has a meaningful name; the surrounding parens read like a
  // parenthetical aside instead of a proper title.
  //
  // The extension renders the title as
  //   <p class="admonition-title"><span class="caption-number">Definition 2 </span> (Waveform)</p>
  // We extract the type word ("Definition") from caption-number and the
  // title from the parenthesized text node, then rebuild as plain text.
  // If a directive has no title (no parens), we keep just the type word.
  // The caption-number span is also CSS-hidden as a no-JS fallback, so
  // pages remain readable if this script is blocked.
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
