// live-cells.js — button-free live code for notebook pages.
//
// The page is born editable: as soon as the DOM is ready (and the browser is
// idle), the vendored thebe core bundle replaces every code cell's static
// <pre> with a CodeMirror editor styled to be pixel-identical, so students
// can click in and type immediately — no activation step, no visible mode
// switch. Nothing Python-related runs yet: thebelab.bootstrap() is called at
// mount time, but the JupyterLite server it tries to start is a gated
// stand-in (window.thebeLite placeholder) whose promise we only release on
// the first Run. That first Run loads the thebe-lite server bundle, boots
// Pyodide (pinned below), micropip-installs the wheels listed in
// _static/wheels/manifest.json, then executes the requested cell — running
// any not-yet-run cells above it first (a fresh kernel can't satisfy a
// mid-page cell otherwise). Baked outputs stay in place inside their cells
// until that cell first re-executes. While the kernel comes up, the status
// pill ticks elapsed seconds; once it's ready, a compact "Python connected"
// badge stays on screen.
//
// Cost when dormant: this file plus live-cells.css; on pages without code
// cells it exits immediately. On notebook pages the editor mount costs one
// cached fetch + parse of thebe-dist/core/index.js (~1.4 MB, idle-time);
// the heavy stack (thebe-lite server, Pyodide CDN, wheels, ~25 MB first
// visit) still loads only when a student actually runs something. Page
// reload restores the pristine built page — that IS the reset affordance.
//
// Also owns the output "beautifier": <audio> elements inside cell outputs
// (baked at build time or freshly produced by pq.play in the live kernel)
// are swapped for the book's round audio-chip card (see _ext/icm_audio.py /
// _static/audio-chip.js), so code-produced audio looks native to the book
// instead of the browser's default widget.
//
// Deliberately self-contained: no globals from the sphinx-thebe page glue
// are required (its initThebe()/modifyDOMForThebe() are coupled to the
// launch button and delete baked outputs), and the config tag is parsed
// leniently — so the layer still works on a page built with UPSTREAM
// sphinx-thebe instead of the TeachBooks fork (see readThebeConfig).
(function () {
  "use strict";

  // Same contract as the fork's loadScriptAsync, owned here so the layer
  // doesn't depend on which sphinx-thebe build emitted the page.
  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = resolve;
      s.onerror = function () {
        reject(new Error("failed to load " + src));
      };
      document.head.appendChild(s);
    });
  }

  var SEL_CELL = typeof thebe_selector !== "undefined" ? thebe_selector : ".thebe,.cell";
  var SEL_INPUT = typeof thebe_selector_input !== "undefined" ? thebe_selector_input : "pre";
  var SEL_OUTPUT = typeof thebe_selector_output !== "undefined" ? thebe_selector_output : ".output, .cell_output";

  // Current thebe stack (thebe-lite 0.5.0 / thebe 0.9.3), self-hosted under
  // vendor/thebe-dist by `make vendor-thebe` — the kernel web worker must
  // be same-origin, so a CDN copy cannot be used.

  var thebeConfig = null; // parsed + patched text/x-thebe-config
  var mountPromise = null; // single-flight: editors mounted into the DOM
  var bootPromise = null; // thebelab.bootstrap() result (resolves kernel-up)
  var kernelPromise = null; // single-flight: first Run -> kernel ready
  var kernelRequested = false; // gates status UI (mount itself is silent)
  var openGate = null; // releases the JupyterLite server start
  var runQueue = Promise.resolve(); // serializes run requests
  var ranIds = new Set(); // thebe cell ids executed since kernel start
  var nbRef = null; // ThebeNotebook from bootstrap
  var sessionRef = null; // ThebeSession from bootstrap
  var activationDone = false; // silences boot narration after connect
  var pendingFocus = null; // cell clicked before its editor existed

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);

  function init() {
    var cells = codeCells();
    if (!cells.length) return; // prose page: do nothing, load nothing
    // The rocket launcher is redundant once cells self-activate, and the
    // fork's initThebe() path (which it triggers) breaks our kept outputs.
    var rocket = document.querySelector(".dropdown-launch-buttons");
    if (rocket) rocket.remove();
    cells.forEach(addChip);
    beautifyOutputs(document); // baked audio outputs -> book audio chips
    watchDynamicAudio(); // catch the recorder's player (added on click) too
    watchRecordButtons(); // turn pq.record()'s button into a ring + countdown
    // Editors normally exist before a student can reach them; this covers a
    // click in the brief window before the idle mount finishes (the static
    // pre is gone once the editor mounts, so these listeners die with it).
    cells.forEach(function (cell) {
      var pre = cell.querySelector(".cell_input " + SEL_INPUT);
      if (!pre) return;
      pre.addEventListener("pointerdown", function () {
        pendingFocus = cell;
        ensureMounted().then(focusPending).catch(function () {});
      });
    });
    // Mount as soon as the page settles. A mount failure leaves the static
    // page fully intact, so it only reports to the console — the status
    // pill appears solely for things a student explicitly asked for.
    var kick = function () {
      ensureMounted().then(schedulePrewarm).catch(function () {});
    };
    if ("requestIdleCallback" in window) requestIdleCallback(kick, { timeout: 1500 });
    else setTimeout(kick, 250);
  }

  function focusPending() {
    if (!pendingFocus) return;
    // thebe 0.9.3 mounts CodeMirror 5: the instance hangs off the wrapper.
    var el = pendingFocus.querySelector(".CodeMirror");
    pendingFocus = null;
    if (el && el.CodeMirror) el.CodeMirror.focus();
  }

  // Real, runnable cells only: skip the extension's hidden init cell and
  // anything tagged as not executable. Before the mount a cell holds a
  // static `pre`; after thebe mounts, that pre is replaced by an editor
  // carrying data-thebe-id — accept either form.
  function codeCells() {
    return Array.prototype.slice
      .call(document.querySelectorAll(SEL_CELL))
      .filter(function (c) {
        return (
          (c.querySelector(".cell_input " + SEL_INPUT) ||
            c.querySelector("[data-thebe-id]")) &&
          !c.classList.contains("tag_thebe-remove-input-init") &&
          !c.classList.contains("tag_disable-execution-cell")
        );
      });
  }

  // ----- per-cell Run chips ---------------------------------------------

  function addChip(cell) {
    var input = cell.querySelector(".cell_input");
    var chip = document.createElement("button");
    chip.className = "live-run-chip";
    chip.type = "button";
    chip.title = "Run this cell (its setup cells above run first) — Shift-Enter works too";
    chip.textContent = "▶ Run";
    chip.addEventListener("click", function () {
      enqueueRun(cell);
    });
    input.appendChild(chip);
  }

  function setChip(cell, state) {
    var chip = cell.querySelector(".live-run-chip");
    if (!chip) return;
    chip.classList.toggle("live-busy", state !== "idle");
    chip.textContent =
      state === "starting" ? "starting…" : state === "running" ? "running…" : "▶ Run";
  }

  // ----- per-cell execution state + timing (VSCode-notebook style) --------
  // A cell the student runs gets a colored left bar — amber while running,
  // green on success, red on error — and a small time badge that ticks up
  // while it runs and freezes at the final duration. A cell that has only its
  // default (built-in) output keeps the neutral iron bar and shows no time.

  var cellTimers = new WeakMap(); // cell -> { start, iv }

  function execBadge(cell) {
    var input = cell.querySelector(".cell_input");
    if (!input) return null;
    var el = input.querySelector(".live-exec-time");
    if (!el) {
      el = document.createElement("span");
      el.className = "live-exec-time";
      input.appendChild(el);
    }
    return el;
  }

  function fmtSecs(ms) {
    var s = ms / 1000;
    return (s < 10 ? s.toFixed(1) : Math.round(s)) + "s";
  }

  // idle | running | ran | failed — drives the left-bar color (live-cells.css).
  function setCellState(cell, state) {
    cell.classList.remove("live-running", "live-ran", "live-failed");
    if (state === "running") cell.classList.add("live-running");
    else if (state === "ran") cell.classList.add("live-ran");
    else if (state === "failed") cell.classList.add("live-failed");
  }

  function clearTimerInterval(cell) {
    var t = cellTimers.get(cell);
    if (t) {
      clearInterval(t.iv);
      cellTimers.delete(cell);
    }
    return t;
  }

  // Begin timing: amber "running" bar, a ticking bottom-right badge, and a
  // live elapsed readout in the Run chip (visible up top while it runs).
  function startTimer(cell) {
    clearTimerInterval(cell);
    setCellState(cell, "running");
    var badge = execBadge(cell);
    var chip = cell.querySelector(".live-run-chip");
    var start = Date.now();
    if (badge) badge.textContent = "0.0s";
    var iv = setInterval(function () {
      var txt = fmtSecs(Date.now() - start);
      if (badge) badge.textContent = txt;
      if (chip && chip.classList.contains("live-busy")) chip.textContent = "running " + txt;
    }, 100);
    cellTimers.set(cell, { start: start, iv: iv });
  }

  // Freeze the timer at the final duration and record the outcome.
  function stopTimer(cell, errored) {
    var t = clearTimerInterval(cell);
    var badge = execBadge(cell);
    if (badge && t) badge.textContent = fmtSecs(Date.now() - t.start);
    setCellState(cell, errored ? "failed" : "ran");
  }

  // A run errored if its output carries a traceback (tagged by freshenOutput)
  // or a Jupyter error mime.
  function cellErrored(cell) {
    return !!cell.querySelector(
      '.cell_output .live-error, .cell_output [data-mime-type="application/vnd.jupyter.error"]'
    );
  }

  // ----- status pill / connected badge ----------------------------------

  var statusEl = null;
  var startedAt = 0;
  var ticker = null;
  var lastMsg = "";
  var lastKind = null;
  var leaveGuardArmed = false;

  function elapsed() {
    return Math.round((Date.now() - startedAt) / 1000);
  }

  function status(msg, kind) {
    lastMsg = msg;
    lastKind = kind || null;
    // The background prewarm is silent — the pill appears only for things a
    // student explicitly asked for. ensureKernel replays the latest state
    // when the first Run flips kernelRequested.
    if (!kernelRequested) return;
    if (!statusEl) {
      statusEl = document.createElement("div");
      statusEl.className = "live-status";
      document.body.appendChild(statusEl);
    }
    statusEl.className = "live-status live-status-" + (kind || "busy");
    if (kind === "busy" || !kind) {
      statusEl.textContent = msg + " · " + elapsed() + " s";
      if (!ticker) {
        ticker = setInterval(function () {
          statusEl.textContent = lastMsg + " · " + elapsed() + " s";
        }, 1000);
      }
    } else {
      if (ticker) {
        clearInterval(ticker);
        ticker = null;
      }
      statusEl.textContent = msg;
    }
  }

  function reportError(err) {
    console.error("[live-cells]", err);
    status(
      "Live code failed: " + (err && err.message ? err.message : err) + " — reload the page to try again.",
      "error"
    );
  }

  // ----- editor mount (page load, silent) --------------------------------

  function ensureMounted() {
    if (!mountPromise) {
      mountPromise = mountEditors().catch(function (err) {
        console.error("[live-cells] editor mount failed:", err);
        throw err;
      });
    }
    return mountPromise;
  }

  // The text/x-thebe-config tag. The TeachBooks fork emits strict JSON, but
  // a build that silently got UPSTREAM sphinx-thebe (same dist name AND
  // version — see check-thebe-fork in the Makefile) emits a JS object
  // literal with unquoted keys, which JSON.parse rejects. That exact mixup
  // took down the first deploy, so parse leniently and then force every
  // setting our self-hosted runtime needs: the result is byte-identical on
  // fork-built pages and repairs upstream-built ones (which would otherwise
  // point thebe at BINDER with a dark editor theme and no rootPath).
  function readThebeConfig() {
    var tag = document.querySelector('script[type="text/x-thebe-config"]');
    var config = {};
    if (tag) {
      try {
        config = JSON.parse(tag.text);
      } catch (e) {
        try {
          config = new Function("return (" + tag.text + ");")() || {};
        } catch (e2) {
          console.warn("[live-cells] unparseable thebe config tag:", e2);
        }
      }
    }
    config.useJupyterLite = true;
    config.useBinder = false;
    config.requestKernel = true;
    config.kernelOptions = Object.assign({}, config.kernelOptions, { path: "/" });
    if (!config.rootPath) {
      // The fork writes the docs root (e.g. ".."); derive it from our own
      // script tag otherwise. Root-level pages get "." ("" would resolve
      // subsequent "/thebe-dist/…" paths to the DOMAIN root).
      var me = document.querySelector('script[src*="live-cells.js"]');
      var prefix = me ? me.getAttribute("src").replace(/_static\/live-cells\.js.*$/, "") : "";
      config.rootPath = prefix ? prefix.replace(/\/$/, "") : ".";
    }
    return config;
  }

  async function mountEditors() {
    var config = readThebeConfig();
    // Our chips are the single execution path (they own run-above
    // semantics), so suppress thebe's own buttons. Restart keys in both
    // spellings: the extension's config tag uses "mountRestartallButton",
    // which thebe 0.9.3 ignores (it reads camel-case "All").
    config.mountRunButton = false;
    config.mountRunAllButton = false;
    config.mountRestartButton = false;
    config.mountRestartallButton = false;
    config.mountRestartAllButton = false;
    // Static code blocks have no gutters and the book is a light theme;
    // keep the editors identical (upstream-built pages say theme "abcdef").
    config.codeMirrorConfig = Object.assign({}, config.codeMirrorConfig, {
      lineNumbers: false,
      theme: "default",
      mode: "python",
    });
    thebeConfig = config;

    // The gate: bootstrap() below calls connectToJupyterLiteServer(), which
    // requires window.thebeLite and invokes its startJupyterLiteServer right
    // away. This stand-in satisfies the check but parks the server start on
    // a promise that startKernel() resolves on the first Run — so the mount
    // is free of Pyodide, the service worker, and all network weight. The
    // real thebe-lite bundle later Object.assign()s itself over this object,
    // which is fine: the parked call already captured the gate.
    var gate = new Promise(function (resolve) {
      openGate = resolve;
    });
    window.thebeLite = {
      startJupyterLiteServer: function (cfg) {
        return gate.then(function (start) {
          return start(cfg);
        });
      },
    };

    await loadScript(config.rootPath + "/thebe-dist/core/index.js");

    prepareCells();
    // Gates the editor-parity styling in live-cells.css.
    document.body.classList.add("live-active");

    thebelab.on("status", function (evt, data) {
      // The gated server emits a "launching" event at mount time, and kernel
      // busy/idle events keep firing during normal use; only narrate while a
      // student is actually waiting for the runtime to come up.
      if (!kernelRequested || activationDone) return;
      if (data.status === "ready" || data.status === "attached") return;
      status("Starting Python (" + data.status + ") — first visit downloads ~25 MB");
    });

    // thebe 0.9.x renders all editors synchronously-ish inside bootstrap,
    // then awaits the (gated) server — so the promise resolves only after
    // the first Run opens the gate, but the editors exist right away.
    bootPromise = thebelab.bootstrap(config);
    bootPromise.catch(function (err) {
      if (kernelRequested) reportError(err);
      else console.error("[live-cells]", err);
    });

    await waitForEditors();
    relocateLiveOutputs();
    bindEditors();
    focusPending();
  }

  function waitForEditors() {
    var want = codeCells().length;
    return new Promise(function (resolve, reject) {
      var t0 = Date.now();
      (function poll() {
        if (document.querySelectorAll(".thebe-cell .CodeMirror").length >= want)
          return resolve();
        if (Date.now() - t0 > 10000)
          return reject(new Error("editors did not mount"));
        setTimeout(poll, 50);
      })();
    });
  }

  // Per-editor wiring once CodeMirror exists: notebook keybindings, copy
  // buttons, and a refresh for editors revealed by <details> (hide-input
  // cells mount while collapsed, so CodeMirror measures them at zero width).
  function bindEditors() {
    codeCells().forEach(function (cell) {
      var el = cell.querySelector(".CodeMirror");
      if (!el || !el.CodeMirror) return;
      var cm = el.CodeMirror;
      var run = function () {
        enqueueRun(cell);
      };
      cm.setOption(
        "extraKeys",
        Object.assign({}, cm.getOption("extraKeys") || {}, {
          "Shift-Enter": run,
          "Cmd-Enter": run,
          "Ctrl-Enter": run,
        })
      );
      // The theme's copy button reads the static <pre> the editor replaced;
      // re-point it at the editor's current text (clone drops old handlers).
      cell.querySelectorAll("button.copybtn").forEach(function (b) {
        var fresh = b.cloneNode(true);
        b.parentNode.replaceChild(fresh, b);
        fresh.addEventListener("click", function (e) {
          e.preventDefault();
          navigator.clipboard.writeText(cm.getValue()).then(function () {
            var was = fresh.innerHTML;
            fresh.innerHTML =
              '<span style="font-size:0.9em;color:#2e8b57;">✓</span>';
            setTimeout(function () {
              fresh.innerHTML = was;
            }, 1200);
          });
        });
      });
    });
    document.querySelectorAll("details").forEach(function (d) {
      d.addEventListener("toggle", function () {
        d.querySelectorAll(".CodeMirror").forEach(function (el) {
          if (el.CodeMirror) el.CodeMirror.refresh();
        });
      });
    });
  }

  // Mark inputs executable for thebe. Baked outputs are left exactly where
  // they are: thebe only adopts elements marked data-output, which ours
  // never get. Each is tagged so the cell's first re-execution removes it
  // (the live output area takes its place inside the same cell).
  function prepareCells() {
    codeCells().forEach(function (cell, i) {
      if (!cell.id) cell.id = "livecell" + i;
      var input = cell.querySelector(".cell_input " + SEL_INPUT);
      input.setAttribute("data-language", "python");
      input.setAttribute("data-executable", "true");
      var output = cell.querySelector(SEL_OUTPUT);
      if (output) output.classList.add("live-baked-output");
    });
  }

  function dropBakedOutput(cell) {
    var baked = cell.querySelector(".live-baked-output");
    if (baked) baked.remove();
  }

  // Thebe renders each cell's live output area INSIDE .cell_input (inside
  // the gray code box). The static page puts outputs outside the box in a
  // .cell_output container, so move each live area into one of those —
  // the theme then styles live results identically to baked ones. Moving
  // the node is safe: thebe keeps a reference to the same element. (This
  // also covers hide-input cells, whose live output would otherwise be
  // stuck inside the collapsed <details>.)
  function relocateLiveOutputs() {
    codeCells().forEach(function (cell) {
      var area = cell.querySelector(".cell_input .jp-OutputArea");
      if (!area) return;
      var wrap = document.createElement("div");
      wrap.className = "cell_output docutils container live-output";
      wrap.appendChild(area);
      cell.appendChild(wrap);
    });
  }

  // ----- kernel start (first Run) ----------------------------------------

  function ensureKernel() {
    if (!kernelRequested) {
      kernelRequested = true;
      // A prewarm may already be underway (or done): surface its state.
      if (lastMsg) status(lastMsg, lastKind);
    }
    if (!kernelPromise) {
      startedAt = Date.now();
      kernelPromise = startKernel().catch(function (err) {
        reportError(err);
        throw err;
      });
    }
    return kernelPromise;
  }

  // Pre-boot the kernel and install the wheels in the background once the
  // page has gone idle: installation always completed, execution only on
  // click — the first ▶ Run then pays just its own cells. Silent (status()
  // is gated on kernelRequested) and free of user code (no init cells in
  // this book). Skipped for readers who asked to save data; on failure the
  // page simply returns to the boot-on-first-Run path.
  function schedulePrewarm() {
    if (navigator.connection && navigator.connection.saveData) return;
    var warm = function () {
      if (kernelPromise) return;
      startedAt = Date.now();
      kernelPromise = startKernel().catch(function (err) {
        console.warn("[live-cells] kernel prewarm failed; Run will retry:", err);
        if (kernelRequested) reportError(err);
        kernelPromise = null;
        throw err;
      });
      kernelPromise.catch(function () {}); // nobody awaits a prewarm
    };
    if ("requestIdleCallback" in window) requestIdleCallback(warm, { timeout: 6000 });
    else setTimeout(warm, 3000);
  }

  async function startKernel() {
    await ensureMounted();
    status("Starting Python — first visit downloads ~25 MB");
    await loadScript(thebeConfig.rootPath + "/thebe-dist/lite/thebe-lite.min.js");

    // Pin the kernel's runtime stack. Pyodide 0.27.7 is the sweet spot:
    // pyquist needs numpy>=2.0 (so >= 0.27), and the pyodide_kernel 0.4.7
    // inside thebe-lite 0.5.0 (the newest released) crashes on >= 0.28
    // (NoGilError / importlib API changes). 0.27 lacks the real WASM
    // soundfile, which is why tools/soundfile_stub exists — when the
    // thebe-lite/pyodide_kernel stack catches up to 0.28, bump this URL
    // and delete that stub. The piplite URLs self-host the kernel wheels
    // (vendored next to the bundle) instead of thebe-lite's unpkg
    // defaults. This must be passed through startJupyterLiteServer's own
    // config merge: thebe 0.9.3 never forwards a lite config, and
    // thebe-lite overwrites the page-level litePluginSettings PageConfig
    // unconditionally.
    var liteSettings = {
      "@jupyterlite/pyodide-kernel-extension:kernel": {
        pyodideUrl: "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js",
        pipliteUrls: [
          new URL(thebeConfig.rootPath + "/thebe-dist/lite/pypi/all.json", document.baseURI).href,
        ],
        pipliteWheelUrl: new URL(
          thebeConfig.rootPath + "/thebe-dist/lite/pypi/piplite-0.4.7-py3-none-any.whl",
          document.baseURI
        ).href,
      },
    };
    // The lite bundle just merged the real startJupyterLiteServer over our
    // placeholder; releasing the gate hands the parked mount-time call this
    // wrapper, which injects the pinned settings into the real start.
    var realStart = window.thebeLite.startJupyterLiteServer;
    openGate(function (cfg) {
      cfg = Object.assign({}, cfg);
      cfg.litePluginSettings = Object.assign({}, cfg.litePluginSettings, liteSettings);
      return realStart.call(window.thebeLite, cfg);
    });

    // thebe 0.9.x resolves bootstrap with { server, session, notebook }.
    var boot = await bootPromise;
    nbRef = boot.notebook;
    sessionRef = boot.session;

    status("Installing pyquist…");
    await installWheels(thebeConfig);
    await runInitCells_();

    activationDone = true;
    status("● Python connected — ready in " + elapsed() + " s. Reload page to reset.", "connected");
  }

  async function installWheels(config) {
    var base = new URL(config.rootPath + "/_static/wheels/", document.baseURI);
    var manifest = await (await fetch(new URL("manifest.json", base))).json();
    var lines = [
      // Load pyquist's compiled/dist dependencies straight from the Pyodide
      // distribution FIRST. micropip resolves bare dependency names to the
      // newest compatible wheel across its indexes, and PyPI sometimes
      // carries newer pure-Python wheels that need native libraries the
      // browser doesn't have. Pre-loading pins these to the WASM builds.
      // (soundfile is deliberately absent: not in the 0.27 distribution —
      // the manifest's stub wheel stands in for it.)
      "import pyodide_js",
      "from pyodide.ffi import to_js",
      'await pyodide_js.loadPackage(to_js(["numpy", "matplotlib", "soxr", "requests", "tqdm"]))',
      "import micropip",
    ];
    manifest.forEach(function (name) {
      lines.push('await micropip.install("' + new URL(name, base).href + '")');
    });
    // Optional features pulled from PyPI, but only when a code cell on THIS
    // page actually uses them — so prose/plotting pages don't pay for heavy
    // extras (e.g. anywidget, which browseraudio's recorder pulls in). Keyed
    // on strings that appear in the page's code.
    var pageCode = Array.prototype.map
      .call(document.querySelectorAll(".cell_input"), function (e) {
        return e.textContent;
      })
      .join("\n");
    var pypiFeatures = [
      // pq.record() / browseraudio: in-browser mic recording. record() now
      // auto-detects the browser, so any page that records needs browseraudio.
      { pkg: "browseraudio", when: ["browseraudio", "pq.record"] },
    ];
    pypiFeatures.forEach(function (f) {
      if (f.when.some(function (s) { return pageCode.indexOf(s) !== -1; })) {
        lines.push('await micropip.install("' + f.pkg + '")');
      }
    });
    // Browser-kernel shims: a no-op myst_nb.glue (build-time-only library)
    // and the RcParams patch the TeachBooks extension applies for matplotlib.
    lines.push(
      "import sys, types",
      'if "myst_nb" not in sys.modules:',
      '    _m = types.ModuleType("myst_nb"); _m.glue = lambda *a, **k: None; sys.modules["myst_nb"] = _m',
      "import matplotlib",
      'if not hasattr(matplotlib.RcParams, "_get"):',
      "    matplotlib.RcParams._get = dict.get"
    );
    // The inlined chapter scripts (the {interactive} directive — see
    // _ext/icm_interactive.py) are standalone files that locate their output
    // folder as `Path(__file__).parent.parent / "assets"` and write WAVs there.
    // A notebook cell has no __file__, so those scripts NameError on Run. Define
    // one pointing under the kernel's CWD: the assets dir then mkdir()s and the
    // soundfile stub writes WAVs into the in-memory FS harmlessly. The writes
    // are silent by design — readers hear the chapter's audio through the page's
    // {audio} chips (preserved from the prose), and can add pq.play(...) to hear
    // their own edits. setdefault so a genuine __file__ (if any) always wins.
    lines.push(
      "import os as _os",
      'if "__file__" not in globals():',
      '    __file__ = _os.path.join(_os.getcwd(), "code", "inlined_script.py")'
    );
    var fut = sessionRef.kernel.requestExecute({ code: lines.join("\n") });
    var kernelErr = null;
    fut.onIOPub = function (m) {
      var c = m.content || {};
      if (c.ename) {
        kernelErr = c.ename + ": " + c.evalue;
        console.error("[live-cells] kernel:", kernelErr);
      }
    };
    var reply = await fut.done;
    var st = reply && reply.content && reply.content.status;
    if (st && st !== "ok") {
      throw new Error("environment setup failed — " + (kernelErr || "see browser console"));
    }
  }

  // The extension injects hidden cells tagged thebe-init (e.g. its
  // matplotlib patch) that expect to run right after the kernel is up.
  // They are display:none and never thebe-mounted (codeCells() skips them),
  // so run their SOURCE directly on the kernel — output is irrelevant.
  async function runInitCells_() {
    var initCells = document.querySelectorAll(".thebe-init, .tag_thebe-init");
    for (var i = 0; i < initCells.length; i++) {
      var pre = initCells[i].querySelector("pre");
      if (pre && pre.textContent.trim()) {
        await sessionRef.kernel.requestExecute({ code: pre.textContent }).done;
      }
    }
  }

  // The thebe notebook cell backing a DOM cell, via the data-thebe-id the
  // mount stamps on the editor. Null for unmounted cells.
  function nbCellOf(cell) {
    var marked = cell.querySelector("[data-thebe-id]");
    if (!marked || !nbRef) return null;
    var id = marked.getAttribute("data-thebe-id");
    return nbRef.cells.find(function (c) {
      return c.id === id;
    }) || null;
  }

  // ----- execution --------------------------------------------------------

  // Serialize runs: clicking several chips queues them instead of
  // interleaving kernel requests.
  function enqueueRun(cell) {
    if (!leaveGuardArmed) {
      leaveGuardArmed = true;
      // Leaving would lose kernel state the student built by RUNNING cells;
      // the built page returns on reload, so make that an informed choice.
      // Armed on the first Run, not at boot — a prewarmed kernel with
      // nothing run isn't state worth nagging about.
      window.addEventListener("beforeunload", function (e) {
        e.preventDefault();
        e.returnValue = "";
      });
    }
    setChip(cell, kernelPromise ? "running" : "starting");
    runQueue = runQueue
      .then(function () {
        return runChain(cell);
      })
      .catch(function () {
        /* reported by the pipeline; keep the queue alive */
      });
  }

  // A split page interleaves several self-contained companion notebooks;
  // the splitter tags each one's code cells `icm-run-group-N` (rendered as
  // a `tag_…` class). Scope a Run's setup chain to the clicked cell's own
  // notebook. Pages without groups (ordinary notebook pages, where every
  // cell shares one namespace arc) keep the whole-page chain.
  function runGroupOf(cell) {
    for (var i = 0; i < cell.classList.length; i++) {
      if (cell.classList[i].indexOf("tag_icm-run-group-") === 0)
        return cell.classList[i];
    }
    return null;
  }

  async function runChain(target) {
    try {
      await ensureKernel();
      var chain = codeCells();
      var group = runGroupOf(target);
      if (group) {
        chain = chain.filter(function (c) {
          return c.classList.contains(group);
        });
      }
      for (var i = 0; i < chain.length; i++) {
        var cell = chain[i];
        var isTarget = cell === target;
        var nb = nbCellOf(cell);
        if (!nb) continue;
        if (isTarget || !ranIds.has(nb.id)) {
          dropBakedOutput(cell);
          setChip(cell, "running");
          startTimer(cell);
          try {
            await nb.execute();
          } catch (e) {
            stopTimer(cell, true); // kernel-level failure → red bar
            throw e;
          }
          ranIds.add(nb.id);
          freshenOutput(cell);
          stopTimer(cell, cellErrored(cell)); // green, or red on a Python traceback
          if (!isTarget) setChip(cell, "idle");
        }
        if (isTarget) break;
      }
    } finally {
      setChip(target, "idle");
    }
  }

  // Post-execution polish for one cell: convert any audio the run produced
  // into the book's chip card, tell tracebacks apart from ordinary stderr,
  // and pulse the output rail so the fresh result is findable without
  // being loud.
  function freshenOutput(cell) {
    beautifyOutputs(cell);
    // thebe's rendermime emits tracebacks under the stderr mime type — the
    // same one tqdm progress bars use — so the red error treatment can't
    // hang off the mime type alone (live-cells.css styles .live-error).
    cell
      .querySelectorAll('[data-mime-type="application/vnd.jupyter.stderr"]')
      .forEach(function (el) {
        if (el.textContent.indexOf("Traceback (most recent call last)") !== -1) {
          el.classList.add("live-error");
        }
      });
    var out = cell.querySelector(".cell_output.live-output");
    if (!out) return;
    out.classList.remove("live-fresh");
    void out.offsetWidth; // restart the rail-pulse animation
    out.classList.add("live-fresh");
  }

  // ----- output beautifier ------------------------------------------------
  //
  // pq.play emits IPython.display.Audio: a bare browser <audio controls>
  // (no autoplay), which looks nothing like the book. Swap each one — baked
  // at build time or just produced by the live kernel — for the same round
  // play/pause chip card the {audio} directive renders (markup mirrors
  // _ext/icm_audio.py's _chip_button; behavior shared via the wiring hook
  // audio-chip.js exposes). The WAV header inside the data URI is parsed
  // for a "1.00 s · 44.1 kHz · mono" caption.

  var CHIP_MARKUP =
    '<svg class="audio-chip-ring" viewBox="0 0 36 36" aria-hidden="true">' +
    '<circle class="acr-track" cx="18" cy="18" r="15.9155"></circle>' +
    '<circle class="acr-fill" cx="18" cy="18" r="15.9155"></circle>' +
    "</svg>" +
    '<svg class="audio-chip-icon" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path class="ac-play" d="M8 5v14l11-7z"></path>' +
    '<g class="ac-pause"><rect x="7" y="5" width="3.5" height="14"></rect>' +
    '<rect x="13.5" y="5" width="3.5" height="14"></rect></g>' +
    "</svg>";

  // Download icon for the audio-output card, matching the {audio} directive's
  // control (_ext/icm_audio.py) so authored and code-produced audio look alike.
  var DOWNLOAD_MARKUP =
    '<svg class="audio-download-icon" viewBox="0 0 24 24" aria-hidden="true">' +
    '<path d="M12 16l-5-5h3V4h4v7h3l-5 5zm-7 2h14v2H5z"></path></svg>';

  function beautifyOutputs(root) {
    root.querySelectorAll(".cell_output audio").forEach(function (audio) {
      var src = audio.getAttribute("src");
      if (!src) {
        var sourceEl = audio.querySelector("source");
        src = sourceEl && sourceEl.getAttribute("src");
      }
      if (!src) return; // nothing playable; leave the native element

      var card = document.createElement("div");
      card.className = "audio-block audio-output";
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "audio-chip audio-chip-lg";
      chip.setAttribute("data-audio-src", src);
      chip.setAttribute("aria-label", "Play audio output");
      chip.title = "Play audio output";
      chip.innerHTML = CHIP_MARKUP;
      var body = document.createElement("div");
      body.className = "audio-block-body";
      var name = document.createElement("span");
      name.className = "audio-output-name";
      name.textContent = "Audio output";
      body.appendChild(name);
      card.appendChild(chip);
      card.appendChild(body);
      // Trailing download control — saves the produced clip (a data:/blob: URL,
      // both of which honor the `download` attribute).
      var dl = document.createElement("a");
      dl.className = "audio-download";
      dl.href = src;
      dl.setAttribute("download", "audio-output.wav");
      dl.setAttribute("aria-label", "Download audio output");
      dl.title = "Download audio output";
      dl.innerHTML = DOWNLOAD_MARKUP;
      card.appendChild(dl);
      audio.replaceWith(card);
      setAudioMeta(body, src); // "1.00 s · 44.1 kHz · mono"
      if (window.icmWireAudioChip) window.icmWireAudioChip(chip);
    });
  }

  // The recorder's inline player is added to the DOM when the student clicks
  // Record — after the cell finished running, so freshenOutput never sees it.
  // Watch for any <audio> appearing in an output and give it the chip card too,
  // so recorded and played audio look identical.
  function watchDynamicAudio() {
    new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var nodes = records[i].addedNodes;
        for (var j = 0; j < nodes.length; j++) {
          var n = nodes[j];
          if (n.nodeType !== 1) continue;
          if (n.tagName === "AUDIO" || (n.querySelector && n.querySelector("audio"))) {
            beautifyOutputs(document);
            return;
          }
        }
      }
    }).observe(document.body, { childList: true, subtree: true });
  }

  // pq.record() renders a plain ipywidgets button ("● Record 3s"). Wrap it in a
  // card that echoes the audio-output card (live-cells.css): a round record
  // control with a draining ring + a caption that counts the seconds down.
  // Driven by the widget's own duration label and status text — the browseraudio
  // widget itself stays untouched.
  function enhanceRecordButton(origBtn) {
    if (origBtn.dataset.baRing) return; // idempotent
    var text = origBtn.textContent || "";
    if (!/Record/i.test(text)) return; // only the record button
    var m = text.match(/([\d.]+)\s*s/);
    var duration = m ? parseFloat(m[1]) : 3;
    var durLabel = (duration % 1 === 0 ? duration.toFixed(0) : duration.toFixed(1)) + " s";
    origBtn.dataset.baRing = "1";

    // Hide the ipywidgets button + its status span and render our own card —
    // forwarding clicks — so none of the widget's button CSS reaches our UI.
    origBtn.style.display = "none";
    var status = origBtn.nextElementSibling;
    if (status && status.tagName === "SPAN") status.style.display = "none";

    // Reuse the book's audio-chip ring (viewBox 36, r=15.9155, dasharray 100)
    // so the control is identical in size/weight to a pq.play() output chip.
    var NS = "http://www.w3.org/2000/svg";
    function circle(cls) {
      var c = document.createElementNS(NS, "circle");
      c.setAttribute("class", cls);
      c.setAttribute("cx", "18");
      c.setAttribute("cy", "18");
      c.setAttribute("r", "15.9155");
      return c;
    }
    var ring = document.createElementNS(NS, "svg");
    ring.setAttribute("class", "audio-chip-ring");
    ring.setAttribute("viewBox", "0 0 36 36");
    var fill = circle("acr-fill"); // dasharray 100, offset 100 (empty) via custom.css
    fill.style.transition = "stroke-dashoffset 0.1s linear";
    ring.append(circle("acr-track"), fill);
    var dot = document.createElement("span");
    dot.className = "ba-dot";

    var ctrl = document.createElement("button");
    ctrl.type = "button";
    ctrl.className = "audio-chip audio-chip-lg ba-record";
    ctrl.title = "Record " + durLabel;
    ctrl.append(ring, dot);

    var card = document.createElement("div");
    card.className = "audio-block audio-output";
    var body = document.createElement("div");
    body.className = "audio-block-body";
    var label = document.createElement("span");
    label.className = "audio-output-name";
    body.append(label);
    card.append(ctrl, body);
    origBtn.parentNode.insertBefore(card, origBtn);

    function setLabel(main, sub) {
      label.textContent = main + " ";
      var s = document.createElement("span");
      s.className = "ba-sub";
      s.textContent = "· " + sub;
      label.append(s);
    }
    setLabel("Record", durLabel);

    var timer = null;
    function stop() {
      if (timer) {
        clearInterval(timer);
        timer = null;
      }
      fill.style.strokeDashoffset = "100"; // empty ring
    }

    ctrl.addEventListener("click", function () {
      if (timer) return;
      origBtn.click(); // trigger the widget's capture, within this user gesture
      var startedAt = performance.now();
      fill.style.strokeDashoffset = "0"; // full ring at the start
      timer = setInterval(function () {
        var elapsed = (performance.now() - startedAt) / 1000;
        var left = Math.max(0, duration - elapsed);
        fill.style.strokeDashoffset = String(100 * Math.min(1, elapsed / duration));
        setLabel("Recording", left.toFixed(1) + " s left");
        // Stop when the widget reports the take is done or failed (status text),
        // or as a safety a couple seconds past the requested duration.
        var s = status ? status.textContent : "";
        if (/error/i.test(s)) {
          stop();
          setLabel("Couldn't record", "check mic access");
        } else if (/recorded/i.test(s) || elapsed > duration + 2) {
          stop();
          setLabel("Recorded", durLabel);
        }
      }, 100);
    });
  }

  function watchRecordButtons() {
    function scan(root) {
      if (!root || root.nodeType !== 1) return;
      if (root.matches && root.matches(".jupyter-button")) enhanceRecordButton(root);
      if (root.querySelectorAll) {
        root.querySelectorAll(".jupyter-button").forEach(enhanceRecordButton);
      }
    }
    new MutationObserver(function (records) {
      for (var i = 0; i < records.length; i++) {
        var nodes = records[i].addedNodes;
        for (var j = 0; j < nodes.length; j++) scan(nodes[j]);
      }
    }).observe(document.body, { childList: true, subtree: true });
    document.querySelectorAll(".jupyter-button").forEach(enhanceRecordButton);
  }

  // Append a "1.00 s · 44.1 kHz · mono" caption parsed from the WAV header.
  // pq.play uses a data: URI (parsed synchronously); the recorder's preview
  // uses a blob: URL (fetched, so the caption fills in a moment later).
  function setAudioMeta(body, src) {
    function append(text) {
      if (!text) return;
      var line = document.createElement("span");
      line.className = "audio-output-meta";
      line.textContent = text;
      body.appendChild(line);
    }
    var dataPrefix = "data:audio/wav;base64,";
    if (src.indexOf(dataPrefix) === 0) {
      try {
        var head = atob(src.substr(dataPrefix.length, 96));
        var bytes = new Uint8Array(head.length);
        for (var i = 0; i < head.length; i++) bytes[i] = head.charCodeAt(i);
        append(captionFromWavBytes(bytes));
      } catch (e) {
        /* no caption */
      }
    } else if (src.indexOf("blob:") === 0) {
      fetch(src)
        .then(function (r) { return r.arrayBuffer(); })
        .then(function (buf) { append(captionFromWavBytes(new Uint8Array(buf))); })
        .catch(function () {});
    }
  }

  // Parse a canonical 44-byte RIFF/WAV PCM header into the caption string.
  // Any surprise -> null (no caption), never an error.
  function captionFromWavBytes(bytes) {
    if (bytes.length < 44) return null;
    var str = function (i, n) {
      var r = "";
      for (var k = 0; k < n; k++) r += String.fromCharCode(bytes[i + k]);
      return r;
    };
    if (str(0, 4) !== "RIFF" || str(8, 4) !== "WAVE") return null;
    var u16 = function (i) { return bytes[i] | (bytes[i + 1] << 8); };
    var u32 = function (i) { return u16(i) + u16(i + 2) * 65536; };
    var channels = u16(22);
    var rate = u32(24);
    var bytesPerSecond = u32(28);
    var dataBytes = str(36, 4) === "data" ? u32(40) : bytes.length - 44;
    if (!bytesPerSecond || !rate || !channels) return null;
    var dur = dataBytes / bytesPerSecond;
    var durTxt =
      dur >= 60
        ? Math.floor(dur / 60) + ":" + String(Math.round(dur % 60)).padStart(2, "0") + " min"
        : dur.toFixed(2) + " s";
    var rateTxt = (rate % 1000 === 0 ? rate / 1000 : (rate / 1000).toFixed(1)) + " kHz";
    var chTxt = channels === 1 ? "mono" : channels === 2 ? "stereo" : channels + " channels";
    return durTxt + " · " + rateTxt + " · " + chTxt;
  }
})();
