# Computer Music Principles

Source for the **15-322 / 15-622 Computer Music Principles** textbook at
Carnegie Mellon University, built with [Jupyter Book](https://jupyterbook.org).

The book includes a reference section for **Pyquist**, the audio library used in
the course, and a placeholder for the course website. The Pyquist **API
Reference** page is generated automatically from the installed Pyquist package
and refreshes whenever upstream changes — see [Pyquist sync](#pyquist-sync)
below.

## Building the book

```sh
conda env create -f environment.yml   # first time only
conda activate icmbook

make book      # build the HTML book into _build/html/
make serve     # build, then serve locally at http://localhost:8000
make pdf       # build a PDF via xelatex (requires a LaTeX toolchain)
make clean     # remove generated outputs
```

## Repository layout

```
icmbook-demo/
├── .gitignore                Ignored build outputs, notebook checkpoints, and local tooling files
├── Alon.cls                  LaTeX document class for the PDF build
├── Makefile                  Build targets: book / pdf / serve / clean
├── README.md                 This file
├── _build/                   Generated book output (ignored)
├── _config.yml               Jupyter Book configuration
├── _static/                  Static assets included in the rendered site
│   ├── course-nav.js         Course navigation behavior
│   └── custom.css            Site styling
├── _toc.yml                  Jupyter Book table of contents
├── colormap.tex.txt          Colored-math macros shared by HTML and PDF
├── environment.yml           Conda environment for building the book
├── epigrafica.sty            LaTeX font package for the PDF build
└── content/                  Book, course, appendix, and reference content
    ├── about.md              Landing page (title, author, AI disclaimer, license)
    ├── template.ipynb        Feature-reference notebook
    ├── bauhaus.mplstyle      Matplotlib style for notebook figures
    ├── errata.md             Post-publication corrections
    ├── references.bib        BibTeX bibliography
    ├── references.md         Rendered reference list
    ├── appendix/             Math and Python background
    │   ├── Math.md
    │   ├── Python.md
    │   └── intro.md
    ├── ch00/                 Computer music — numbered section files (00.md – 03.md)
    ├── ch01/                 Sound and digital audio — numbered section files (00.md – 07.md)
    ├── ch02/                 Synthesis and vectorized computation — numbered section files (00.md – 06.md)
    ├── course/               Course website pages
    │   ├── about.md
    │   ├── projects.md
    │   ├── resources.md
    │   ├── schedule.md
    │   ├── showcase.md
    │   └── website.md
    ├── images/               Figures and image assets
    │   └── template-waveform.png
    └── pyquist/              Pyquist library documentation
        │                         (mirrors the upstream pyquist/docs layout)
        ├── Overview.md       Verbatim mirror of pyquist's README (auto-fetched)
        └── api/              Per-module API reference (autodoc)
            ├── audio.md
            ├── device.md
            ├── helper.md
            ├── plot.md
            ├── score.md
            └── web.md
```

The listing omits Git metadata, OS files, and local-only tooling settings such
as `.claude/`, plus the local `pure-md/` reference folder. Each `chNN/` folder
contains numbered section files (`01.md`, `02.md`, …) plus an `assets/` folder
for figures and audio.

## Authoring notes

- Each chapter folder has one file per section, numbered (`01.md`, `02.md`, …).
  Section numbering is baked into each file's H1 (e.g. `# 1.3 From analog to
  digital`); auto-numbering is off in `_toc.yml` so the sidebar matches the
  page headings. Add or remove sections by editing both the folder and
  `_toc.yml`.
- Pages that need runnable code, audio, or plots should be Jupyter notebooks
  (`.ipynb`) or MyST-Markdown notebooks. See `content/template.ipynb` for a
  live demo of every directive and feature available to authors.
- Notebooks execute at build time (`execute_notebooks: 'auto'` in `_config.yml`);
  outputs — text, audio players, Matplotlib plots — are baked into the rendered
  HTML. Pyquist is installed from `environment.yml`.

## Pyquist sync

The `content/pyquist/` section deliberately mirrors the
[upstream Pyquist `docs/` layout](https://github.com/gclef-cmu/pyquist/tree/main/docs):
one landing page (`Overview.md`, the README itself) and per-module API
pages under `api/`. Both are kept in sync with the upstream repo
**automatically** — there are no hand-maintained Pyquist docs in this
book.

| Page | Mirrors upstream | Mechanism |
|---|---|---|
| `Overview.md` | `README.md` | `curl` + `sed` step in `make sync-pyquist-readme` |
| `api/audio.md` | `docs/api/audio.rst` | [Sphinx autodoc][autodoc] against `pyquist.audio` |
| `api/score.md` | `docs/api/score.rst` | autodoc against `pyquist.score` |
| `api/plot.md` | `docs/api/plot.rst` | autodoc against `pyquist.plot` |
| `api/device.md` | `docs/api/device.rst` | autodoc against `pyquist.device` |
| `api/helper.md` | `docs/api/helper.rst` | autodoc against `pyquist.helper` |
| `api/web.md` | `docs/api/web.rst` | autodoc against `pyquist.web.{freesound,theorytab}` |

### Overview (README mirror)

`content/pyquist/Overview.md` is a **verbatim** mirror of the Pyquist
README, including the `# pyquist` title and the full `## Installation`
section. The plumbing is a three-line `sync-pyquist-readme` target in
the [Makefile](Makefile):

1. `curl` downloads
   `https://raw.githubusercontent.com/gclef-cmu/pyquist/main/README.md`
   to `content/pyquist/_pyquist_readme.md` (git-ignored).
2. `sed` rewrites relative `examples/…` links to absolute GitHub URLs
   so they resolve from the book site.
3. `Overview.md` pulls that file in with `{include} _pyquist_readme.md`.

`make book` depends on `sync-pyquist-readme`, so every build refreshes
the snapshot. If `curl` fails, the build fails — there's no offline
fallback, so building requires network access.

To refresh the snapshot without rebuilding the book:

```sh
make sync-pyquist-readme
```

### API pages (autodoc)

The six files under `content/pyquist/api/` are **not hand-written
prose** — they are thin shells of `{eval-rst}` blocks that invoke
autodoc against each module of the installed `pyquist` package. Each
build, autodoc imports the module, reads its docstrings, and renders
them as the API entries you see on the page.

Practical consequences:

- **Adding an API entry to the book = adding a docstring upstream.** If
  a new Pyquist function ships with a docstring, it appears in the next
  book build with no edit here. If it has no docstring, it shows up with
  an empty body — the fix is in the Pyquist repo, not here.
- **Mirror upstream when adding new modules.** If Pyquist adds a new
  module documented in `pyquist/docs/api/`, add a matching shell file in
  `content/pyquist/api/` and register it in `_toc.yml`.
- **The visual styling lives in `_static/custom.css`** under the
  "Auto-generated API reference" block. Autodoc emits standard
  `dl.py` / `dl.field-list` markup; the CSS rebrands it to match the
  rest of the textbook (Carnegie Red signatures, Palatino body,
  theme-aware card).

### How the rebuild pipeline works

`.github/workflows/deploy-book.yml` triggers a rebuild on **three** events:

| Trigger | Fires when… | Typical latency |
|---|---|---|
| `push` to `main` | You push to this repo | seconds |
| `schedule` (`22 8 * * *` UTC) | Nightly, automatic | up to 24 h |
| `workflow_dispatch` | You click "Run workflow" in the Actions tab | seconds |

The nightly cron is what picks up changes from the upstream Pyquist repo
without any manual action — a daily rebuild against `pyquist/main`'s HEAD.
If you need faster propagation, raise the cron frequency (e.g.
`"17 */6 * * *"` for every six hours, `"17 * * * *"` for hourly) — GitHub
Actions minutes are free on public repos, so this is cheap.

Inside the job, a dedicated **"Refresh Pyquist from latest source"** step
runs before `make book`:

```sh
pip install --upgrade --force-reinstall --no-deps \
  git+https://github.com/gclef-cmu/pyquist.git
```

`environment.yml` already pins Pyquist to that git URL, but pip caches built
wheels keyed by source URL — the force-reinstall guarantees the runner picks
up the latest commit even when the URL string is unchanged. Without this
step a nightly run could re-deploy yesterday's docstrings.

### Verifying / troubleshooting

- **Did the rebuild run?** Check the Actions tab on `icmbook` for the
  most recent `deploy-book` run — its triggering event tells you whether
  it came from a push, the schedule, or a manual dispatch.
- **Did the build see the latest Pyquist?** The "Refresh Pyquist from
  latest source" step prints the install path and forces a fresh pip
  download, so its log line confirms the commit hash that was fetched.
- **An API entry is missing.** Check that the symbol is exported and has
  a docstring in its module. If both are true and it still doesn't
  render, add it explicitly to the matching
  `content/pyquist/api/<module>.md`.
- **A new module landed in Pyquist.** Add a matching shell page under
  `content/pyquist/api/` and register it in `_toc.yml` — see how the
  existing six files are written.
- **You need an immediate refresh.** Open the Actions tab and click
  "Run workflow" on `deploy-book`; it rebuilds against the current
  Pyquist HEAD in a couple of minutes.

[autodoc]: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
