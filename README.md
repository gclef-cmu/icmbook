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

## Deploy

Pushing to `main` triggers `.github/workflows/deploy-book.yml`, which builds and
deploys to GitHub Pages. CI fetches only the public `pyquist/` submodule (over
HTTPS) and builds from the committed `content/` — it never runs `make split` or
fetches `icm-text/`.

## Layout

```
icm-text/    chapter prose (private submodule, source of truth)
pyquist/     audio library (public submodule)
tools/       split_chapters.py / merge_chapters.py
content/     rendered book — chNN/, course/, appendix/, pyquist/, templates
_config.yml  Jupyter Book config
_toc.yml     table of contents
Makefile     book / serve / pdf / clean / split / merge
```
