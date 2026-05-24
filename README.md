# Introduction to Computer Music

Source for the **15-322 / 15-622 Introduction to Computer Music** textbook at
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
├── tools/                    Build-time scripts
│   └── fetch_pyquist_readme.py   Mirrors the Pyquist README into Overview.md
└── content/                  Book, course, appendix, and reference content
    ├── Template.ipynb        Feature-reference notebook
    ├── bauhaus.mplstyle      Matplotlib style for notebook figures
    ├── errata.md             Post-publication corrections
    ├── intro.md              Preface / landing page
    ├── references.bib        BibTeX bibliography
    ├── references.md         Rendered reference list
    ├── appendix/             Math and Python background
    │   ├── Math.md
    │   ├── Python.md
    │   └── intro.md
    ├── ch01-introduction/    What is computer music, history, exercises
    ├── ch02-digital-audio/   Sound, sampling, quantization, exercises
    ├── ch03-getting-started/ Installation, HelloSound, exercises
    ├── ch04-oscillators/     Oscillators, additive synthesis, exercises
    ├── ch05-envelopes/       Amplitude, ADSR, exercises
    ├── ch06-modulation/      Amplitude and frequency modulation, exercises
    ├── ch07-subtractive/     Noise, spectra, filters, exercises
    ├── ch08-wavetable/       Sampling, wavetables, exercises
    ├── ch09-granular-physical/
    │                         Granular synthesis, physical modeling, exercises
    ├── ch10-midi/            MIDI basics, control signals, exercises
    ├── ch11-scores/          Music representation, sequencing, exercises
    ├── ch12-algorithmic/     Randomness, generative methods, exercises
    ├── ch13-effects/         Delays, reverberation, exercises
    ├── ch14-spectral/        STFT, spectral processing, exercises
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
as `.claude/`. Every `chNN-*/` folder contains a chapter `intro.md`, one file
per section, and an `Exercises.md` at the end.

## Authoring notes

- Each chapter folder has an `intro.md` (chapter landing page) plus one file per
  section. Add or remove sections by editing both the folder and `_toc.yml`.
- Pages that need runnable code, audio, or plots should be Jupyter notebooks
  (`.ipynb`) or MyST-Markdown notebooks. See `content/Template.ipynb` for a
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
| `Overview.md` | `README.md` | `tools/fetch_pyquist_readme.py`, invoked by `make book` |
| `api/audio.md` | `docs/api/audio.rst` | [Sphinx autodoc][autodoc] against `pyquist.audio` |
| `api/score.md` | `docs/api/score.rst` | autodoc against `pyquist.score` |
| `api/plot.md` | `docs/api/plot.rst` | autodoc against `pyquist.plot` |
| `api/device.md` | `docs/api/device.rst` | autodoc against `pyquist.device` |
| `api/helper.md` | `docs/api/helper.rst` | autodoc against `pyquist.helper` |
| `api/web.md` | `docs/api/web.rst` | autodoc against `pyquist.web.{freesound,theorytab}` |

### Overview (README mirror)

`content/pyquist/Overview.md` is a **verbatim** mirror of the Pyquist
README, including the `# pyquist` title and the full `## Installation`
section. The flow:

1. `make book` runs `make sync-pyquist-readme`, which invokes
   `tools/fetch_pyquist_readme.py`.
2. The script downloads
   `https://raw.githubusercontent.com/gclef-cmu/pyquist/main/README.md`
   and rewrites relative links (e.g. `examples/HelloPyquist.ipynb`) to
   absolute GitHub URLs so they resolve from the book.
3. It writes the result to `content/pyquist/_pyquist_readme.md`, which
   is git-ignored.
4. `Overview.md` pulls that file in with `{include} _pyquist_readme.md`.

The script is **offline-tolerant**: if the fetch fails and a previous
copy exists on disk, it warns and reuses it; only an empty cache + a
failed fetch causes the build to exit non-zero. So a network blip on CI
won't deploy a half-rendered Overview, and local builds without internet
still work as long as you have built at least once.

To preview a README change before it lands on Pyquist's `main`:

```sh
python3 tools/fetch_pyquist_readme.py    # refresh the snapshot manually
make book                                # rebuild
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

`.github/workflows/deploy-book.yml` triggers a rebuild on **four** events:

| Trigger | Fires when… | Typical latency |
|---|---|---|
| `push` to `main` | You push to this repo | seconds |
| `repository_dispatch` (`pyquist-updated`) | Pyquist's `main` notifies us | seconds |
| `schedule` (`17 7 * * *` UTC) | Nightly safety net | up to 24 h |
| `workflow_dispatch` | You click "Run workflow" in the Actions tab | seconds |

Inside the job, a dedicated **"Refresh Pyquist from latest source"** step runs
before `make book`:

```sh
pip install --upgrade --force-reinstall --no-deps \
  git+https://github.com/gclef-cmu/pyquist.git
```

`environment.yml` already pins Pyquist to that git URL, but pip caches built
wheels keyed by source URL — the force-reinstall guarantees the runner picks
up the latest commit even when the URL string is unchanged. Without this
step a dispatch or nightly run could re-deploy yesterday's docstrings.

### Setting up the dispatch trigger (one-time, on the Pyquist repo)

The `repository_dispatch` trigger is what makes the book update within
**seconds** of an upstream commit (the nightly cron is just a safety net).
It is half wired on the book side; the other half lives in the Pyquist repo.

1. **Create a token.** On the GitHub account that owns the Pyquist repo,
   create a fine-grained personal access token scoped to **this repo only**
   (`jiaweil6/icmbook`) with the permission `Actions: Read and write`. A
   classic PAT with `repo` scope also works.
2. **Store it on the Pyquist repo** as a secret named
   `ICMBOOK_DISPATCH_TOKEN` (Settings → Secrets and variables → Actions).
3. **Add a workflow** to `gclef-cmu/pyquist` at
   `.github/workflows/notify-icmbook.yml`:

   ```yaml
   name: notify-icmbook
   on:
     push:
       branches: [main]
   jobs:
     dispatch:
       runs-on: ubuntu-latest
       steps:
         - name: Tell icmbook to rebuild
           run: |
             curl -X POST \
               -H "Authorization: Bearer ${{ secrets.ICMBOOK_DISPATCH_TOKEN }}" \
               -H "Accept: application/vnd.github+json" \
               https://api.github.com/repos/jiaweil6/icmbook/dispatches \
               -d '{"event_type":"pyquist-updated"}'
   ```

After this, every push to `pyquist/main` posts the event, GitHub fires the
`repository_dispatch` listener here, and the book redeploys.

### Verifying / troubleshooting

- **Did the dispatch fire?** On the Pyquist repo, check the Actions tab for
  the `notify-icmbook` run.
- **Did this repo receive it?** On `icmbook`, check the Actions tab for a
  `deploy-book` run whose triggering event is `repository_dispatch`.
- **Did the build see the latest Pyquist?** The "Refresh Pyquist from latest
  source" step prints the install path — its log line also indirectly
  confirms a fresh download via pip.
- **An API entry is missing.** Check that the symbol is exported and has a
  docstring in its module. If both are true and it still doesn't render,
  add it explicitly to the matching `content/pyquist/api/<module>.md`.
- **A new module landed in Pyquist.** Add a matching shell page under
  `content/pyquist/api/` and register it in `_toc.yml` — see how the
  existing six files are written.
- **Token rotated / dispatch silently broken.** The nightly cron at 07:17 UTC
  will catch the change within a day; meanwhile you can re-run manually from
  the Actions tab via "Run workflow".

[autodoc]: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
