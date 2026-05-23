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
icmbook/
├── _config.yml              Jupyter Book configuration (metadata, extensions, LaTeX)
├── _toc.yml                 Table of contents — parts, chapters, sections
├── Makefile                 Build targets: book / pdf / serve / clean
├── README.md                This file
├── environment.yml          Conda environment for building the book
├── .gitignore
│
├── _static/
│   └── custom.css           Site styling (Carnegie Mellon palette, typography)
│
├── Alon.cls                 LaTeX document class for the PDF build
├── epigrafica.sty           LaTeX font package for the PDF build
├── colormap.tex.txt         Colored-math macros shared by HTML and PDF
│
└── content/                 All book content
    ├── intro.md             Preface / landing page (book root)
    ├── Template.ipynb       Feature-reference notebook (every directive demoed)
    │
    ├── ch01-introduction/
    │   ├── intro.md
    │   ├── WhatIsComputerMusic.md
    │   ├── AShortHistory.md
    │   └── Exercises.md
    ├── ch02-digital-audio/         Sound / Sampling / Quantization
    ├── ch03-getting-started/       Installation / HelloSound / Exercises
    ├── ch04-oscillators/           Oscillators / Additive synthesis
    ├── ch05-envelopes/             Amplitude / ADSR
    ├── ch06-modulation/            AM / FM
    ├── ch07-subtractive/           Noise / Filters
    ├── ch08-wavetable/             Sample playback / Wavetables
    ├── ch09-granular-physical/     Granular synthesis / Physical modeling
    ├── ch10-midi/                  MIDI / Control signals
    ├── ch11-scores/                Music representation / Sequencing
    ├── ch12-algorithmic/           Randomness / Generative methods
    ├── ch13-effects/               Delays / Reverberation
    ├── ch14-spectral/              STFT / Spectral processing
    │
    ├── pyquist/                    Pyquist library documentation
    │   ├── intro.md
    │   ├── Overview.md
    │   ├── Installation.md
    │   ├── SoundModel.md
    │   ├── Reference.md
    │   └── Examples.md
    ├── course/                     Course website placeholder
    │   └── website.md
    ├── appendix/                   Math & Python background
    │   ├── intro.md
    │   ├── Math.md
    │   └── Python.md
    │
    ├── references.bib              BibTeX bibliography
    ├── references.md               Rendered reference list
    ├── errata.md                   Post-publication corrections
    ├── bauhaus.mplstyle            Matplotlib style for notebook figures
    └── images/                     Figures and chapter cover art
```

Every `chNN-*/` folder follows the shape shown for `ch01-introduction/`: a chapter
`intro.md`, one file per section, and an `Exercises.md` at the end.

## Authoring notes

- Each chapter folder has an `intro.md` (chapter landing page) plus one file per
  section. Add or remove sections by editing both the folder and `_toc.yml`.
- Pages that need runnable code, audio, or plots should be Jupyter notebooks
  (`.ipynb`) or MyST-Markdown notebooks. See `content/Template.ipynb` for a
  live demo of every directive and feature available to authors.
- Notebooks execute at build time (`execute_notebooks: 'auto'` in `_config.yml`);
  outputs — text, audio players, Matplotlib plots — are baked into the rendered
  HTML. Pyquist is installed from `environment.yml`.
