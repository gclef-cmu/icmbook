# Template - Markdown 

This page is a **living template** for **MyST Markdown** pages (`.md`). It
demonstrates every feature available when authoring a prose-only chapter —
formatting, math, admonitions, exercises, figures, cross-references, and
tables — but excludes notebook-only features (executable code cells, `glue`,
and cell tags). For those, see the {doc}`notebook template <template>`.

Use it two ways:

1. **As a reference** — skim the rendered page to see what is available.
2. **As a starting point** — copy `template.md`, rename it, and replace the
   content with your own.

(why-markdown)=
## 1. Markdown pages vs. notebooks

Every page in this book is one of two file types:

`.md` — a **MyST Markdown** file (this page)
: Prose, math, and directives. Best for chapters that are mostly explanation.
  Code blocks are displayed but **not executed**.

`.ipynb` — a **Jupyter notebook**
: Markdown cells *and* code cells. Code runs when the book is built, and its
  output — numbers, plots, audio players — is captured into the page. Best for
  anything that should *demonstrate running code*.

Markdown cells inside a notebook understand the **same MyST syntax** as a `.md`
file, so a notebook is a strict superset: everything in this template also
works inside a notebook.

```{important}
If your page needs to *execute* {{ pyquist }} code, author it as a notebook
instead. See the {doc}`notebook template <template>` for the full set of
notebook-only features.
```

## 2. Text formatting

**Bold**, *italic*, ***bold italic***, `inline code`, <del>strikethrough</del>,
H<sub>2</sub>O, x<sup>2</sup>, and a [hyperlink](https://pyquist.org). Press
{kbd}`Shift` + {kbd}`Enter` to run a cell. The {abbr}`DFT (Discrete Fourier Transform)`
abbreviation shows its meaning on hover.

> A blockquote — use it for short asides or quotations.

A horizontal rule follows:

---

Inline math such as $f = 440\,\text{Hz}$ flows inside running text.

## 3. Lists

Unordered, ordered, and nested:

- First item
- Second item
  - Nested item
  - Another nested item
- Third item

1. Step one
2. Step two
3. Step three

A **task list** (the `tasklist` extension):

- [x] Install Pyquist
- [x] Write the template
- [ ] Write Chapter 1

A **definition list** (the `deflist` extension):

Sample rate
: The number of audio samples stored per second, in hertz.

Nyquist frequency
: Half the sample rate; the highest representable frequency.

## 4. Admonitions

Admonitions are colored callout boxes. The syntax is:

````markdown
```{note}
Your text here.
```
````

Swap `note` for any type below:

```{note}
A **note** — neutral, supporting information.
```

```{tip}
A **tip** — practical advice.
```

```{important}
**Important** — do not miss this.
```

```{warning}
A **warning** — something that can go wrong.
```

```{seealso}
A **see-also** — a pointer to related material, e.g. the
{doc}`Pyquist reference <pyquist/Overview>`.
```

```{admonition} Custom title
:class: hint
The generic `{admonition}` directive takes a custom title and any color class.
```

A **collapsible** admonition (`:class: dropdown`):

```{admonition} Click to expand
:class: dropdown note
Hidden until the reader clicks.
```

### 4.1 Audio examples — the `listen` pattern

For short audio clips shipped alongside a chapter (a recorded sample, a pre-rendered WAV), wrap an `<audio>` tag in a custom `{admonition}` with `:class: note listen`. The book ships dedicated CSS for the `listen` class — it swaps the theme's default info glyph for the 🔊 emoji you put in the title, reclaims the icon's reserved left padding, and balances the vertical spacing around the audio player.

Source:

````markdown
```{admonition} 🔊 Listen
:class: note listen
<audio controls src="./assets/your-clip.wav"></audio>

Caption text with `code`, $math$, and [links](https://example.com) — markdown works inside admonitions.
```
````

Rendered (using `./ch01/assets/audio-sine-440.wav`):

```{admonition} 🔊 Listen
:class: note listen
<audio controls src="./ch01/assets/audio-sine-440.wav"></audio>

A 440 Hz sine tone, one second long, at $f_s = 44{,}100$ Hz.
```

For audio *generated* at build time by executable Pyquist code, use a notebook
page with `pq.play(audio)` — see the {doc}`notebook template <template>`.

## 5. Mathematics

Inline math: the angular frequency is $\omega = 2\pi f$.

Display math:

$$
x(t) = A \sin(2\pi f t + \phi)
$$

A **labeled, numbered** equation — source:

````markdown
```{math}
:label: eq-euler-md
e^{i\pi} + 1 = 0
```
````

renders as:

```{math}
:label: eq-euler-md
e^{i\pi} + 1 = 0
```

and is referenced inline with `` {eq}`eq-euler-md` `` → see equation {eq}`eq-euler-md`.

Aligned, multi-line math:

$$
\begin{aligned}
X[k] &= \sum_{n=0}^{N-1} x[n]\, e^{-i 2\pi k n / N} \\
     &= \sum_{n=0}^{N-1} x[n]\,\big(\cos\theta - i\sin\theta\big)
\end{aligned}
$$

Colored terms, using the macros defined in `_config.yml`:
$\blue{a} + \red{b} = \green{c}$.

## 6. Code blocks (not executed)

A plain fenced block is shown with syntax highlighting but **not run**:

```python
# Illustration only — this block does not execute.
import pyquist as pq
audio = pq.Audio(samples, sample_rate=44100)
```

The `{code-block}` directive adds line numbers and line emphasis:

```{code-block} python
:linenos:
:emphasize-lines: 2

def gain(audio, factor):
    audio.samples *= factor      # the emphasized line
    return audio
```

```{important}
In a `.md` file, code blocks are **always** display-only. To run code at build
time, author the page as a notebook instead.
```

## 7. Figures and images

The `{figure}` directive adds a caption and a label you can cross-reference.
Source:

````markdown
```{figure} images/template-waveform.png
:name: fig-waveform-md
:width: 80%

A caption. Reference it with `{numref}` for an auto-numbered link.
```
````

renders as:

```{figure} images/template-waveform.png
:name: fig-waveform-md
:width: 80%
:align: center

A sine waveform — a static image stored in `content/images/`.
```

See {numref}`fig-waveform-md` for an auto-numbered link.

## 8. Tables

A plain Markdown table:

| Waveform | Harmonic content |
| -------- | ---------------- |
| Sine     | Fundamental only |
| Square   | Odd harmonics |
| Sawtooth | All harmonics |

The `{list-table}` directive (easier for long cell text; supports a caption and
label):

```{list-table} Synthesis methods
:header-rows: 1
:name: tbl-methods-md

* - Method
  - Idea
* - Additive
  - Sum sinusoids
* - Subtractive
  - Filter a harmonically rich source
```

The `{csv-table}` directive:

```{csv-table} Common sample rates
:header-rows: 1

Use, Rate (Hz)
Telephone, 8000
CD audio, 44100
Studio, 48000
```

## 9. Cross-references and citations

| Target | Role | Live example |
| ------ | ---- | ------------ |
| A labeled section | `` {ref}`label` `` | {ref}`why-markdown` |
| A numbered figure | `` {numref}`label` `` | {numref}`fig-waveform-md` |
| Another page | `` {doc}`path` `` | {doc}`About <about>` |
| An equation | `` {eq}`label` `` | {eq}`eq-euler-md` |
| A theorem | `` {prf:ref}`label` `` | {prf:ref}`thm-nyquist-md` |

**Citations** pull from `content/references.bib`. Cite with
`` {cite}`dannenberg1997machine` `` → {cite}`dannenberg1997machine`. Every
citation is collected automatically on the {doc}`References <references>` page.

## 10. Footnotes

Footnotes attach a small reference[^demo] that collects at the foot of the page.

[^demo]: This is the footnote text. Footnotes suit asides and source notes.

```{note}
MyST also offers `{margin}` and `{sidebar}` directives for asides that float
beside the text. This book **avoids them** — they overlap the right-hand
*Contents* panel. Keep asides in the body text, or use an admonition like this.
```

## 11. Exercises and solutions

The `sphinx-exercise` extension provides `{exercise}` and `{solution}`. Source:

````markdown
```{exercise}
:label: ex-demo-md
State the Nyquist frequency for a 48 kHz sample rate.
```

```{solution} ex-demo-md
:class: dropdown
24 kHz — half the sample rate.
```
````

renders as:

```{exercise}
:label: ex-demo-md
State the Nyquist frequency for a 48 kHz sample rate.
```

```{solution} ex-demo-md
:class: dropdown
24 kHz — half the sample rate.
```

A **gated** exercise (`{exercise-start}` … `{exercise-end}`) can wrap several
blocks:

```{exercise-start}
:label: ex-gated-md
```

Describe the spectrum of a 330 Hz sawtooth wave. Which harmonics are present,
and how do their amplitudes fall off?

```{exercise-end}
```

## 12. Theorems, proofs, and definitions

The `sphinx-proof` extension provides `{prf:theorem}`, `{prf:proof}`,
`{prf:definition}`, `{prf:lemma}`, `{prf:example}`, and `{prf:algorithm}`.

```{prf:definition} Sample rate
:label: def-sample-rate-md
The **sample rate** is the number of samples stored per second of audio.
```

```{prf:theorem} Nyquist–Shannon sampling theorem
:label: thm-nyquist-md
A signal containing no frequencies above $f_\text{max}$ is fully determined by
samples taken at a rate $f_s > 2\,f_\text{max}$.
```

```{prf:proof}
A full proof is omitted in this template; see any signal-processing text.
```

```{prf:example}
At $f_s = 44100$ Hz, frequencies up to $22050$ Hz can be represented.
```

## 13. Panels: tabs, cards, dropdowns, buttons

These come from the `sphinx-design` extension.

**Tab set:**

````{tab-set}
```{tab-item} macOS
`brew install ...`, then `pip install ...`
```
```{tab-item} Linux
`apt install ...`, then `pip install ...`
```
```{tab-item} Windows
Use Command Prompt with `py -m pip install ...`
```
````

**Card grid** (responsive: 1 column on phones, 2 on wide screens):

````{grid} 1 1 2 2
```{grid-item-card} Synthesis
Generate sound from scratch.
```
```{grid-item-card} Analysis
Measure and visualize sound.
```
````

**Dropdown:**

```{dropdown} Show the answer
The answer stays hidden until the reader clicks.
```

**Button and badges:**

```{button-link} https://pyquist.org
:color: primary
:expand:
Open the Pyquist documentation
```

Inline badges: {bdg-primary}`primary` {bdg-secondary}`secondary`
{bdg-success}`success` {bdg-danger}`danger`.

## 14. Substitutions

Substitutions are reusable snippets defined once in `_config.yml` and inserted
with `{{ name }}`. This book defines, among others, `{{ course }}`:

> The course is **{{ course }}**.

Edit `myst_substitutions` in `_config.yml` to add your own.

## 15. Using this template

To start a new prose-only chapter:

1. Copy `content/template.md`.
2. Rename it and move it into a `chNN-*/` folder.
3. Register it in `_toc.yml`.
4. Replace the content with your own.

```{admonition} Before publishing
:class: warning
Remove this **Markdown Template** page from `_toc.yml` — it is an author
reference, not course content.
```

```{seealso}
For pages that need to execute {{ pyquist }} code at build time, start from
the {doc}`notebook template <template>` instead.
```
