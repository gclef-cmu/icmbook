(pyquist-sound-model)=
# The Sound Model

```{note}
Placeholder. Document precisely how Pyquist represents and computes audio.
```

This page should give a precise account of Pyquist's core abstraction, so that
the {doc}`API reference <Reference>` can refer back to it.

## Topics to document

- **The `Sound` object** — what it represents (samples? a function of time?),
  its sample rate, duration, and channel count.
- **Evaluation** — when computation happens: eagerly on creation, or lazily on
  playback/render.
- **Sample format and range** — floating point, nominal range $[-1, 1]$, and
  what happens on overflow.
- **Combining sounds** — how `+`, `*`, sequencing, and mixing behave.
- **Audio rate vs. control rate** — whether the same object serves both.

```{admonition} Why this page matters
:class: tip
A clear, shared mental model of "what a sound *is*" in Pyquist makes every other
page in this reference shorter and less ambiguous.
```
