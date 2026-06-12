# Computer Music Principles

Source for the **15-322 / 15-622 Computer Music Principles** textbook at Carnegie
Mellon University, built with [Jupyter Book](https://jupyterbook.org).

Two pinned git submodules keep builds reproducible:

- **`icm-text/`** — ground-truth chapter prose (a private fork). `make split`
  derives the rendered chapters under `content/ch*/` from it.
- **`pyquist/`** — the course audio library
  ([`gclef-cmu/pyquist`](https://github.com/gclef-cmu/pyquist)); the Pyquist
  Overview and API pages are generated from it.

## Build

```sh
git clone --recurse-submodules <repo-url>
# already cloned? plain builds need only the public pyquist submodule:
git submodule update --init pyquist

conda env create -f environment.yml   # first time (installs pyquist from ./pyquist)
conda activate icmbook

make book      # build HTML into _build/html/
make serve     # build + serve at http://localhost:8000
make pdf       # PDF build (needs a LaTeX toolchain)
make clean     # remove build outputs
```

Every `make` target assumes the `icmbook` env is active — it provides
`jupyter-book` and the `python` that `make serve` uses.

`make book` reads the **committed** `content/`, so it doesn't need `icm-text/`.
You only need that (private) submodule to run `make split` / `make merge`.

## Authoring

The book is written in **MyST-native Markdown**. For a live reference of every
directive and feature — admonitions, margin notes, definitions, figures, audio,
citations — see **`content/template-md.md`** (prose) and
**`content/template-notebook.ipynb`** (runnable code, audio, plots).

Each chapter is a folder `content/chNN/` with one file per section (`00.md`,
`01.md`, …); the section number lives in each H1 (e.g. `# 1.2 …`).

## Chapter prose: `icm-text` → `content/`

Chapter prose lives in the **`icm-text/`** submodule (the source of truth).
`make split` regenerates the rendered chapters from it:

```sh
git submodule update --remote icm-text   # pull the latest prose
make split                               # regenerate content/ch*/ and _toc.yml
git add content/ && git commit && git push
```

`content/ch*/` is **committed** to this repo — the build and CI read those files
directly and never fetch the private `icm-text/`. So after a split, commit the
regenerated `content/` for changes to reach the deploy.

`make merge` is the inverse: it re-assembles `content/ch*/` into icm-text-shaped
files (under `icm-text-merged/`) for PR'ing edits upstream, and self-checks that
the rendered site is unchanged.

## Pyquist docs

Everything the book shows about Pyquist is generated from the pinned `pyquist/`
submodule — there are no hand-written API docs:

- `content/pyquist/Overview.md` mirrors `pyquist/README.md` (refreshed each build).
- `content/pyquist/api/*.md` are autodoc shells that introspect the **installed**
  module — the editable install (`-e ./pyquist`) that `conda env create` performs,
  not the `pyquist/` folder itself. If the import fails at build time, these pages
  silently render empty (see Troubleshooting).

Bump the pinned version and push to update:

```sh
git submodule update --remote pyquist
git add pyquist && git commit -m "Bump pyquist" && git push
```

## Live code (in-browser Python)

Notebook pages are **live**: every code cell is an editor the moment the page
opens, and a ▶ Run chip (or Shift-Enter) executes it — Python runs entirely in
the browser via [Pyodide](https://pyodide.org), no server, no Binder. The page
renders exactly like the static build (baked outputs stay until a cell re-runs;
running a cell first runs the not-yet-run cells above it). Prose pages load
none of this.

### How it's achieved

The pipeline has three stages — two at build time, one in the browser:

1. **`make book` builds the runtime artifacts** (both targets are `book`
   prerequisites and run automatically):
   - `make wheels` → `_static/wheels/` + `manifest.json`: a pyquist wheel from
     the pinned submodule, plus two stand-ins from `tools/`: a **sounddevice
     stub** (PortAudio can't exist in WASM; raises a friendly error) and a
     **soundfile stub** (WAV-only via stdlib `wave`; temporary, see below).
     Rebuilt every build so the wheel always matches the submodule pin.
   - `make vendor-thebe` → `vendor/thebe-dist/`: downloads the pinned
     **thebe-lite 0.5.0** and **thebe 0.9.3** npm bundles (the in-browser
     Jupyter server + frontend). Self-hosted because the kernel web worker
     must be **same-origin** — a CDN copy is blocked by the browser. Served
     verbatim via `html_extra_path` (`_config.yml`); it must **never move into
     `_static/`**, where Jupyter Book auto-registers every `.js` as a page
     script and would execute worker-only chunks on page load. Cached behind a
     `.ok` sentinel; `rm -rf vendor/thebe-dist` forces a re-fetch.
2. **Page load — editors, no kernel** (`_static/live-cells.js`): on pages with
   code cells it adds Run chips, restyles outputs (audio → the book's chip
   cards), and at browser idle loads the thebe core bundle and mounts a
   CodeMirror editor into every cell, pixel-matched to the static `<pre>`
   (`_static/live-cells.css`). The kernel does **not** start: bootstrap's
   server connection is parked on a gated `window.thebeLite` stand-in.
3. **First Run — kernel**: loads the thebe-lite server bundle, injects the
   pinned Pyodide URL + self-hosted kernel-wheel URLs (this *must* happen by
   wrapping `startJupyterLiteServer` — thebe forwards no lite config, and
   thebe-lite overwrites the page-level `litePluginSettings`), then releases
   the gate. Pyodide boots in a web worker (~25 MB from the CDN, first visit
   only), the wheels install in manifest order (stubs first, so micropip never
   fetches the real sounddevice/soundfile from PyPI), and the run executes.
   Reload = reset; a floating badge shows kernel state.

The TeachBooks **sphinx-thebe fork** (pinned by commit in `environment.yml`)
supplies the page glue (`text/x-thebe-config` tag, helper script). It has the
same dist name/version as upstream, so pip needs
`--force-reinstall --no-deps` to replace an already-installed upstream copy.

### The version matrix (why each pin exists)

| Pin | Where | Why |
|---|---|---|
| Pyodide **0.27.7** | `pyodideUrl` in `_static/live-cells.js` | pyquist needs numpy ≥ 2 (so Pyodide ≥ 0.27); the bundled pyodide_kernel **0.4.7 crashes on ≥ 0.28** |
| thebe-lite **0.5.0**, thebe **0.9.3** | `Makefile` (`vendor-thebe`) | newest released; embeds pyodide_kernel 0.4.7 (the piplite wheel URL in live-cells.js carries that version too) |
| sphinx-thebe fork @ `1f3a809` | `environment.yml` | fork publishes no tags |
| soundfile stub | `tools/soundfile_stub/` | Pyodide < 0.28 ships no WASM soundfile; PyPI's pure-Python one needs a native lib |

These move **together** — don't bump one alone. The blocked upgrade: Pyodide
0.28 (real soundfile, mp3 decode) needs a thebe-lite release embedding
jupyterlite pyodide-kernel ≥ 0.6. When that ships:

1. Bump both versions in `Makefile` `vendor-thebe`; `rm -rf vendor/thebe-dist`.
2. In `_static/live-cells.js`: bump `pyodideUrl`, and match `pipliteWheelUrl`
   to the piplite wheel inside the new bundle (`vendor/thebe-dist/lite/pypi/`).
3. Delete `tools/soundfile_stub/` and its line in the `wheels` target.
4. `make serve` and smoke-test (below) — expect `Audio.from_file` to handle
   mp3 now.

### Maintaining / testing

- Routine builds need nothing: wheels track the pyquist pin automatically;
  vendor bundles are cached (first build fetches them from npm).
- **Smoke test** after touching any of this: `make serve`, open
  `http://localhost:8000/content/template-notebook.html` (must be `http://` —
  the worker won't start from `file://`). Check: cells are editable
  immediately with no layout shift; ▶ Run on the `pq.play(tone)` cell boots
  the kernel (badge: "● Python connected") and replaces the baked output with
  a working audio card; the hidden-input cell errors with a red ERROR card
  (its old-API code is a known content issue, useful as the error fixture).
- The editors are **CodeMirror 5**; their look (and scroll behavior) is
  pixel-matched against the built static page in `live-cells.css` — if the
  theme or pygments style changes, re-measure. Output styling lives in
  `custom.css` ("response rail") and fights some `!important` rules in the
  fork's `code.css`; keep both in view when restyling outputs.
- `thebe_config.exclude_patterns` in `_config.yml` keeps book sources (and
  dotfiles — `**` alone misses `.git/`!) out of `_build/html`. Don't loosen it.

## Troubleshooting

- **`make: jupyter-book: No such file or directory`** — the `icmbook` conda env
  isn't active. Run `conda activate icmbook` (create it first if needed; see
  Build).

- **Pyquist API pages build, but show no classes or functions** — autodoc
  imports `pyquist` from the environment, and a failed import doesn't fail the
  build. The editable install records an **absolute path**, so it goes stale if
  the repo is moved or re-cloned. Check it, then re-point and rebuild:

  ```sh
  python -c "import pyquist; print(pyquist.__file__)"
  # healthy: a path inside this repo's pyquist/pyquist/
  # stale:   None, an ImportError, or a path elsewhere

  pip install -e ./pyquist
  make clean && make book   # clean first — Sphinx caches the empty pages
  ```

- **Live code: cells never become editable, or Run hangs at "Starting
  Python"** — open the browser console and look for `[live-cells]` lines,
  then check in order: the page is served over `http://` (not `file://`);
  a stale `python -m http.server` isn't serving an old build; hard-reload
  (the JupyterLite service worker caches kernel files); `vendor/thebe-dist/`
  isn't half-fetched (`rm -rf vendor/thebe-dist && make book`). First-ever
  Run downloads ~25 MB from the Pyodide CDN — give it time on slow networks.

## Deploy

Pushing to `main` triggers `.github/workflows/deploy-book.yml`, which builds and
deploys to GitHub Pages. CI fetches only the public `pyquist/` submodule (over
HTTPS) and builds from the committed `content/` — it never runs `make split` or
fetches `icm-text/`. Because CI runs `make book`, the live-code artifacts
(wheels, vendored thebe bundles from the npm registry) are built there too —
nothing live-code-related is committed except the sources under `tools/` and
`_static/`.

## Layout

```
icm-text/    chapter prose (private submodule, source of truth)
pyquist/     audio library (public submodule)
tools/       split_chapters.py / merge_chapters.py + browser-kernel stubs
             (sounddevice_stub/, soundfile_stub/ — see Live code)
content/     rendered book — chNN/, appendix/, pyquist/, reference/, templates
_static/     book JS/CSS — custom.css, audio-chip.js, live-cells.{js,css}
             (live code), wheels/ (generated, gitignored)
_ext/        local Sphinx extensions — {audio}, figures, glossary, roles
vendor/      thebe runtime bundles (generated by make vendor-thebe, gitignored)
_config.yml  Jupyter Book config
_toc.yml     table of contents
Makefile     book / serve / pdf / clean / split / merge / wheels / vendor-thebe
```
