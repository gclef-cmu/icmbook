---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

(hello-sound)=
# Your First Sound

```{note}
This page is a **MyST-Markdown notebook**: a `.md` file with a `{code-cell}`
directive for runnable code. Notebook execution is disabled in `_config.yml`
while the book is a template, so the cells below render as code without output.
Set `execute_notebooks: 'auto'` and install Pyquist to run them at build time.

You can also write pages as regular `.ipynb` notebooks — both appear in the table
of contents the same way.
```

The traditional first program prints `hello, world`. Ours plays a tone.

```{code-cell} ipython3
:tags: [remove-stderr]
import pyquist

# A 440 Hz sine tone (concert A), one second long.
tone = pyquist.osc(freq=440, dur=1.0)
tone.play()
```

## What just happened?

- `pyquist.osc(...)` built an **oscillator** — a signal that varies over time.
- `freq` set the pitch and `dur` set the length.
- `.play()` sent the samples to your speakers.

```{admonition} The core loop
:class: tip
Write code, run it, *listen*, change a number, run it again. This loop is how you
will learn every technique in the book.
```

## Try it

Change the frequency and hear the pitch move:

```{code-cell} ipython3
for freq in [262, 330, 392]:   # a C major triad
    pyquist.osc(freq=freq, dur=0.5).play()
```

```{warning}
The Pyquist function names used here (`osc`, `play`, ...) are **illustrative**.
Replace them with the real API once the library is finalized, and keep the
{doc}`Pyquist reference <../pyquist/Overview>` in sync.
```
