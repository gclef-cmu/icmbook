(pyquist-overview)=
# Overview

```{note}
Placeholder. Describe Pyquist's design, scope, and lineage.
```

**Pyquist** is a Python audio library for the computer music course. It draws on
the tradition of **Nyquist** {cite}`dannenberg1997machine` and the MUSIC-N
*unit-generator* model: build sound by connecting small, composable signal
blocks.

## Design goals

- **Approachable** — readable Python, minimal boilerplate.
- **Composable** — small pieces combine into instruments and pieces.
- **Notebook-friendly** — every sound is easy to plot and play inline.

## How it is organized

```{list-table}
:header-rows: 1

* - Area
  - Purpose
* - Generators
  - Oscillators, noise, samplers — sources of sound.
* - Envelopes
  - Time-varying control signals.
* - Processors
  - Filters and effects that transform sound.
* - Scores
  - Representing and scheduling musical events.
* - I/O
  - Playback, and reading/writing audio files.
```

## To develop

- The relationship (if any) to the original Nyquist language.
- Versioning and compatibility policy.
- A diagram of the signal-flow model.
