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

(pyquist-examples)=
# Examples

```{note}
This page is a MyST-Markdown notebook. The code cells use the **placeholder**
Pyquist API and are not executed while the book is a template. Once the real API
exists and `execute_notebooks` is enabled, they will run and produce audio.
```

A few short, complete recipes. Each is meant to be copied, run, and modified.

## A note with an envelope

```{code-cell} ipython3
import pyquist

tone = pyquist.osc(freq=440, dur=2.0, wave='saw')
env = pyquist.adsr(attack=0.01, decay=0.2, sustain=0.6, release=0.5)
(tone * env).play()
```

## A simple melody

```{code-cell} ipython3
notes = [262, 294, 330, 349, 392]   # C D E F G
melody = pyquist.seq(*[pyquist.osc(freq=f, dur=0.4) for f in notes])
melody.play()
```

## Subtractive synthesis with an effect

```{code-cell} ipython3
source = pyquist.noise(dur=2.0, color='white')
filtered = pyquist.lowpass(source, cutoff=800, resonance=0.7)
pyquist.delay(filtered, time=0.25, feedback=0.4).play()
```

```{seealso}
Each technique above is explained in depth in the chapters: oscillators in
{numref}`Chapter %s <oscillators>`, envelopes in
{numref}`Chapter %s <envelopes>`, filtering in
{numref}`Chapter %s <subtractive>`, and delays in
{numref}`Chapter %s <effects>`.
```
