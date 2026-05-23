# Introduction to Computer Music

Source for the **15-322 / 15-622 Introduction to Computer Music** textbook at
Carnegie Mellon University, built with [Jupyter Book](https://jupyterbook.org).

The book includes a reference section for **Pyquist**, the audio library used in
the course, and a placeholder for the course website.

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
        ├── Examples.md
        ├── Installation.md
        ├── Overview.md
        ├── Reference.md
        ├── SoundModel.md
        └── intro.md
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
