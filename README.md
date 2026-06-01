# Computer Music Principles

Source for the **15-322 / 15-622 Computer Music Principles** textbook at
Carnegie Mellon University, built with [Jupyter Book](https://jupyterbook.org).

This repo pulls from two **pinned git submodules**, so builds are reproducible:

- **`icm-text/`** — the ground-truth prose for the chapters (see
  [icm-text sync](#icm-text-sync)). `make split` derives the per-section files
  under `content/ch*/` from it.
- **`pyquist/`** — the course audio library; both the Pyquist Overview and the
  **API Reference** pages are generated from this checkout (see
  [Pyquist sync](#pyquist-sync)).

The book also includes a placeholder for the course website.

## Building the book

This repo has two git submodules — `pyquist/` and `icm-text/`. Clone with
`--recurse-submodules`, or initialize them after the fact:

```sh
git clone --recurse-submodules <repo-url>
# already cloned without it?
git submodule update --init                 # both submodules
git submodule update --init pyquist         # or just the one the build needs
```

> **Note:** `icm-text/` points at a **private** fork
> (`git@github.com:jiaweil6/icm-text.git`), so fetching it needs access to that
> repo. You only need `icm-text/` to run `make split`/`make merge` — a plain
> `make book` works with just `pyquist/`, since the prose is already committed
> under `content/ch*/`.

```sh
conda env create -f environment.yml   # first time only (installs pyquist from ./pyquist)
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
├── .gitmodules               Declares the pinned `pyquist/` and `icm-text/` submodules
├── Alon.cls                  LaTeX document class for the PDF build
├── Makefile                  Build targets: book / pdf / serve / clean / split / merge
├── README.md                 This file
├── icm-text/                 Ground-truth chapter prose — pinned git submodule (source for content/ch*/)
├── pyquist/                  Pyquist library source — pinned git submodule (gclef-cmu/pyquist)
├── tools/                    split_pure_md.py / merge_pure_md.py — sync content/ch*/ with icm-text/
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
        ├── Overview.md       Verbatim mirror of pyquist's README (copied from the submodule)
        └── api/              Per-module API reference (autodoc)
            ├── audio.md
            ├── device.md
            ├── helper.md
            ├── plot.md
            ├── score.md
            └── web.md
```

The listing omits Git metadata, OS files, and local-only tooling settings such
as `.claude/`. The `content/ch*/` folders are **gitignored-by-design generated
output** of `make split` (see [icm-text sync](#icm-text-sync)); each `chNN/`
folder holds numbered section files (`01.md`, `02.md`, …) plus an `assets/`
folder for figures and audio.

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
  HTML. Pyquist is installed editable from the `pyquist/` submodule via
  `environment.yml`.

## icm-text sync

The chapter prose is **not authored in this repo**. It lives in the
[`icm-text`](https://github.com/chrisdonahue/icm-text) repo and is vendored here
as a pinned git submodule at `icm-text/` (declared in `.gitmodules`). That
submodule is the **ground truth** for chapter content.

### Where the submodule points

| | Value |
|---|---|
| URL | `git@github.com:jiaweil6/icm-text.git` (SSH, **private** fork) |
| Branch | `david-content-edits` |

For now the pin tracks **our fork** on the `david-content-edits` branch, because
that's where active content edits live. Once those edits are merged upstream,
repoint the submodule at the canonical
[`chrisdonahue/icm-text`](https://github.com/chrisdonahue/icm-text) so the
professor's repo becomes ground truth:

```sh
git submodule set-url icm-text git@github.com:chrisdonahue/icm-text.git
git config -f .gitmodules submodule.icm-text.branch main
git submodule sync icm-text
git submodule update --init --remote icm-text
git add .gitmodules icm-text && git commit -m "Track upstream icm-text"
```

### From icm-text to the rendered chapters (`make split`)

`tools/split_pure_md.py` (via `make split`) turns each
`icm-text/{n}-{slug}/index.md` chapter into the per-section files Jupyter Book
renders:

- splits the chapter body on `## ` headings into `content/ch{nn}/{ii}.md`,
  demoting headings one level and prefixing the section number (`1.3 …`);
- writes `content/ch{nn}/index.md` with the chapter intro;
- copies `assets/`, `code/`, `figures/` across;
- regenerates the chapter block of `_toc.yml`.

> ⚠️ **`make split` wipes `content/ch*/` and regenerates it.** Those folders
> also carry **local styling overrides** (figure refactors, admonition
> wrappers, margin notes) layered on top of the raw prose. Splitting drops
> them. After a split, run `git diff content/` to review and re-apply your
> styling. (This is why `content/ch*/` is committed *and* gitignored: it's
> generated, but the committed copy preserves the styling between splits.)

To pull newer prose, bump the submodule first, then split:

```sh
git submodule update --remote icm-text   # advance the pin to the branch tip
make split                               # regenerate content/ch*/
git diff content/                        # re-apply styling as needed
```

### From the rendered chapters back to icm-text (`make merge`)

`tools/merge_pure_md.py` (via `make merge`) is the inverse: it re-assembles
`content/ch{nn}/` into chapter-level `icm-text-merged/{n}-{slug}/index.md`
files matching the icm-text layout, so you can diff them against `icm-text/` and
PR your edits upstream. It runs a **round-trip self-check**
(`split(merge(content)) == content`, byte for byte) and fails loudly if the
rendered site would change. Output goes to `icm-text-merged/` (gitignored);
compare with `diff -ruN icm-text/ icm-text-merged/`.

### Not needed at book-build time

`make book` reads the committed `content/ch*/` files, **not** the submodule, so
a plain build doesn't need `icm-text/` checked out at all. The submodule is only
required to run `make split` / `make merge`. This is also why CI doesn't fetch
it (see [the rebuild pipeline](#how-the-rebuild-pipeline-works) — the private
fork would be unreachable from the deploy repo's token anyway).

## Pyquist sync

Pyquist is vendored as a **pinned git submodule** at `pyquist/` (declared in
`.gitmodules`, pointing at
[`gclef-cmu/pyquist`](https://github.com/gclef-cmu/pyquist)). Everything the
book shows about Pyquist is generated from that one checkout — **no network
fetch at build time, and no hand-maintained Pyquist docs** in this repo. The
`content/pyquist/` section deliberately mirrors the upstream `docs/` layout:
one landing page (`Overview.md`, the README itself) and per-module API pages
under `api/`.

| Page | Source in the submodule | Mechanism |
|---|---|---|
| `Overview.md` | `pyquist/README.md` | `cp` + `sed` step in `make sync-pyquist-readme` |
| `api/audio.md` | `pyquist.audio` | [Sphinx autodoc][autodoc] against the installed module |
| `api/score.md` | `pyquist.score` | autodoc |
| `api/plot.md` | `pyquist.plot` | autodoc |
| `api/device.md` | `pyquist.device` | autodoc |
| `api/helper.md` | `pyquist.helper` | autodoc |
| `api/web.md` | `pyquist.web.{freesound,theorytab}` | autodoc |

### Forking & first-time setup

When you fork this book, the `pyquist/` submodule keeps pointing at the
canonical [`gclef-cmu/pyquist`](https://github.com/gclef-cmu/pyquist) repo
(that's what `.gitmodules` records) — you track upstream Pyquist, you don't
fork it too. To get a working clone of your fork:

```sh
# clone your fork AND pull the submodule in one step
git clone --recurse-submodules git@github.com:<you>/<your-fork>.git
cd <your-fork>

# already cloned without --recurse-submodules? initialize it now:
git submodule update --init pyquist
```

Then build as usual:

```sh
conda env create -f environment.yml   # installs pyquist editable from ./pyquist
conda activate icmbook
make book
```

**SSH key required.** `.gitmodules` uses an SSH URL
(`git@github.com:gclef-cmu/pyquist.git`), so fetching the submodule needs an
SSH key registered with your GitHub account — verify with
`ssh -T git@github.com`. If you'd rather use HTTPS (no key needed), override
the URL **locally** without editing the tracked file:

```sh
git submodule set-url pyquist https://github.com/gclef-cmu/pyquist.git
git submodule sync pyquist
git submodule update --init pyquist
```

CI doesn't need an SSH key either — the workflow overrides this same URL to
HTTPS and fetches only `pyquist/` (see
[the rebuild pipeline](#how-the-rebuild-pipeline-works)).

### Bumping the pinned version

The submodule stays at whatever commit it's pinned to until you deliberately
move it. To pull the latest upstream Pyquist and re-pin:

```sh
git submodule update --remote pyquist
git add pyquist                      # record the new commit
git commit -m "Bump pyquist submodule"
```

Pushing that commit triggers the `deploy-book` workflow, which rebuilds and
redeploys.

### Overview (README mirror)

`content/pyquist/Overview.md` is a **verbatim** mirror of the Pyquist
README, including the `# pyquist` title and the full `## Installation`
section. The `sync-pyquist-readme` target in the [Makefile](Makefile):

1. `cp` copies `pyquist/README.md` (from the submodule checkout) to
   `content/pyquist/_pyquist_readme.md` (git-ignored). If the submodule
   isn't initialized the target fails with a clear hint to run
   `git submodule update --init pyquist`.
2. `sed` rewrites relative `examples/…` links to absolute GitHub URLs
   so they resolve from the book site.
3. `Overview.md` pulls that file in with `{include} _pyquist_readme.md`.

`make book` depends on `sync-pyquist-readme`, so every build refreshes the
snapshot from the pinned commit. No network access is required.

To refresh the snapshot without rebuilding the book:

```sh
make sync-pyquist-readme
```

### API pages (autodoc)

The six files under `content/pyquist/api/` are **not hand-written
prose** — they are thin shells of `{eval-rst}` blocks that invoke
autodoc against each module of the installed `pyquist` package. Because
`environment.yml` installs Pyquist editable from the submodule
(`-e ./pyquist`), autodoc introspects the exact checked-out commit. Each
build, autodoc imports the module, reads its docstrings, and renders
them as the API entries you see on the page.

Practical consequences:

- **Adding an API entry to the book = adding a docstring upstream, then
  bumping the submodule.** A new Pyquist function with a docstring appears
  in the book once you `git submodule update --remote pyquist`. With no
  docstring it shows up with an empty body — the fix is in the Pyquist
  repo, not here.
- **Mirror upstream when adding new modules.** If Pyquist adds a new
  module documented in `pyquist/docs/api/`, add a matching shell file in
  `content/pyquist/api/` and register it in `_toc.yml`.
- **The visual styling lives in `_static/custom.css`** under the
  "Auto-generated API reference" block. Autodoc emits standard
  `dl.py` / `dl.field-list` markup; the CSS rebrands it to match the
  rest of the textbook (Carnegie Red signatures, Palatino body,
  theme-aware card).

### How the rebuild pipeline works

`.github/workflows/deploy-book.yml` builds and deploys to GitHub Pages. It runs
on two triggers:

| Trigger | Fires when… | Typical latency |
|---|---|---|
| `push` to `main` | You push to this repo (content edits **or** a submodule bump) | seconds |
| `workflow_dispatch` | You click "Run workflow" in the Actions tab | seconds |

The build is **fully deterministic**: it produces the same output until you
change the repo. Upstream Pyquist changes reach the book only when you bump the
submodule (see [Bumping the pinned version](#bumping-the-pinned-version)) and
push — there is no scheduled job and nothing fetches Pyquist over the network.

The job does **not** use `submodules: true`. This repo has two submodules and
`icm-text/` is a private fork in a different repo, which the deploy repo's
`GITHUB_TOKEN` can't read — so a blanket submodule fetch would fail. Instead a
dedicated step overrides the `pyquist/` URL to HTTPS and inits **only** that
(public) submodule:

```sh
git config submodule.pyquist.url https://github.com/gclef-cmu/pyquist.git
git submodule update --init pyquist
```

`conda env create` then installs Pyquist editable via `environment.yml`, and a
**"Verify Pyquist resolves to the submodule"** step prints the import path as a
sanity check before `make book` runs. `icm-text/` is never fetched in CI — the
build only reads the committed `content/ch*/` files.

### Verifying / troubleshooting

- **`pyquist/` is empty / build can't find the README.** The submodule
  isn't checked out. Run `git submodule update --init pyquist` (locally)
  — in CI this is handled by the dedicated pyquist-fetch step.
- **Did the rebuild run?** Check the Actions tab for the most recent
  `deploy-book` run — its triggering event tells you whether it came
  from a push or a manual dispatch.
- **The book shows stale Pyquist docs.** The submodule is pinned to an
  older commit. Bump it with `git submodule update --remote pyquist`,
  commit, and push.
- **An API entry is missing.** Check that the symbol is exported and has
  a docstring in its module at the pinned commit. If both are true and it
  still doesn't render, add it explicitly to the matching
  `content/pyquist/api/<module>.md`.
- **A new module landed in Pyquist.** Bump the submodule, add a matching
  shell page under `content/pyquist/api/`, and register it in `_toc.yml`.

[autodoc]: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
