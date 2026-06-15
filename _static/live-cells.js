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
      ensureMounted().catch(function () {});
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
    chip.title = "Run this cell (runs the cells above it first) — Shift-Enter works too";
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

  // ----- status pill / connected badge ----------------------------------

  var statusEl = null;
  var startedAt = 0;
  var ticker = null;
  var lastMsg = "";

  function elapsed() {
    return Math.round((Date.now() - startedAt) / 1000);
  }

  function status(msg, kind) {
    if (!statusEl) {
      statusEl = document.createElement("div");
      statusEl.className = "live-status";
      document.body.appendChild(statusEl);
    }
    lastMsg = msg;
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
    if (!kernelPromise) {
      kernelRequested = true;
      startedAt = Date.now();
      kernelPromise = startKernel().catch(function (err) {
        reportError(err);
        throw err;
      });
    }
    return kernelPromise;
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

    // Leaving the page now would lose kernel state; the built page returns
    // on reload, so make that an informed choice instead of an accident.
    window.addEventListener("beforeunload", function (e) {
      e.preventDefault();
      e.returnValue = "";
    });

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
      // pq.record(..., browser=True) / browseraudio: in-browser mic recording.
      { pkg: "browseraudio", when: ["browseraudio", "browser=True"] },
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
    setChip(cell, kernelPromise ? "running" : "starting");
    runQueue = runQueue
      .then(function () {
        return runChain(cell);
      })
      .catch(function () {
        /* reported by the pipeline; keep the queue alive */
      });
  }

  async function runChain(target) {
    try {
      await ensureKernel();
      var chain = codeCells();
      for (var i = 0; i < chain.length; i++) {
        var cell = chain[i];
        var isTarget = cell === target;
        var nb = nbCellOf(cell);
        if (!nb) continue;
        if (isTarget || !ranIds.has(nb.id)) {
          dropBakedOutput(cell);
          setChip(cell, "running");
          await nb.execute();
          ranIds.add(nb.id);
          freshenOutput(cell);
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
