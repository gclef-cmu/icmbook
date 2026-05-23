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
_config.yml          Jupyter Book configuration (metadata, extensions, LaTeX)
_toc.yml             Table of contents — defines parts, chapters, sections
Makefile             Build targets
environment.yml      Conda environment
Alon.cls             LaTeX document class for the PDF build
epigrafica.sty       LaTeX font package for the PDF build
colormap.tex.txt     Colored-math macros shared by HTML and PDF
_static/custom.css   Site styling
content/             All book content
  intro.md             Preface / landing page
  chNN-*/              One folder per chapter (intro + sections + exercises)
  pyquist/             Pyquist documentation
  course/              Course website placeholder
  appendix/            Supplementary material
  references.bib       BibTeX bibliography
  references.md        Rendered reference list
  errata.md            Post-publication corrections
  bauhaus.mplstyle     Matplotlib style for consistent figures
  images/              Figures and chapter cover art
```

## Authoring notes

- Each chapter folder has an `intro.md` (chapter landing page) plus one file per
  section. Add or remove sections by editing both the folder and `_toc.yml`.
- Pages that need runnable code/audio should be Jupyter notebooks (`.ipynb`) or
  MyST-Markdown notebooks (see `content/ch03-getting-started/HelloSound.md`).
- Notebook execution is disabled in `_config.yml` while content is being drafted.
  Set `execute_notebooks: 'auto'` once notebooks contain real, runnable code.
