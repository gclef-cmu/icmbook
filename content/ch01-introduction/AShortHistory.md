(short-history)=
# A short history

```{note}
This section is a brief sketch, not a complete history. Expand it with the
periods, people, and works you want to emphasize in lecture.
```

Computer music sits at the intersection of several older traditions: acoustics,
electronic instruments, and algorithmic composition. A few milestones worth
knowing:

- **1957** — Max Mathews creates **MUSIC I** at Bell Labs, the first program to
  generate sound directly from a digital computer.
- **1960s** — The **MUSIC-N** family establishes the *unit generator* model:
  patch small signal-processing blocks together to build instruments.
- **1973** — John Chowning publishes **FM synthesis**, a way to produce rich,
  evolving timbres from very little computation {cite}`chowning1973synthesis`.
- **1980s** — **MIDI** standardizes communication between instruments and
  computers; digital synthesizers become widely available.
- **1980s–1990s** — Real-time languages and environments appear, including
  **Csound**, **Max**, **Pure Data**, and Roger Dannenberg's **Nyquist**
  {cite}`dannenberg1997machine`.
- **2000s–present** — Audio synthesis runs comfortably on laptops and phones;
  the field expands into web audio, live coding, and machine learning.

```{admonition} The unit-generator idea endures
:class: tip
The MUSIC-N model — building instruments by connecting reusable signal blocks —
still shapes how modern tools, including Pyquist, are designed.
```

For a thorough history and technique survey, see {cite}`roads1996computer` and
{cite}`dodge1997computer`.
