# Template - Animation

This page is the author reference for **narrative animations** — short, scripted
clips rendered at build time by [Manim Community Edition](https://www.manim.community)
(the maintained fork of 3Blue1Brown's animation engine) and baked into the page as
plain looping video. It is the book's second rendering engine, deliberately separate
from the interactive-widget pipeline, because it does a different job:

|                        | Interactive widget                                  | Narrative animation                          |
|------------------------|-----------------------------------------------------|----------------------------------------------|
| Template               | [Template - Interactive](../template-interactive/index) | this page                                |
| Engine                 | plotly + ipywidgets (`icm_plotly`)                  | manim + `icm_anim`                           |
| The reader can         | drag sliders, edit the code, re-run live            | watch — it plays like a figure               |
| What ships in the page | a live plotly figure (the in-browser kernel starts on page load) | one bare `<video>` tag, mp4 inlined — autoplays muted, loops, no controls |
| The code on the page   | visible or collapsible, always runnable             | never shown, never runnable                  |
| Best for               | exploring a parameter                               | telling one story well — morphing shapes, math that moves, choreography |

Why a second engine: a widget is live — it needs the in-browser kernel and its
libraries, and everything it renders has to coexist with the theme and the
live-code layer. An animation bakes to **inert media** — no script, no styles,
no kernel, nothing to fight. The cost is symmetry: a clip cannot be edited or
re-run in the browser, so it narrates; it never explores.

This page in the sidebar is the *generated* `index.ipynb`. Edit `main.md` or a
companion notebook, then run `make template-animation` to regenerate it.

:::{admonition} Status: proposal
:class: warning
`manim` is **not yet on the approved-library list** in Template - Interactive §4 —
this page and the `{animation}` machinery are the working proposal. No chapter
content uses it yet; once it has sign-off, adopting it in a chapter is one
directive away.
:::

## 1. How an animation section works

An animation section is two pieces, exactly like an interactive one:

1. **The section Markdown** in `icm-text/{n}-{slug}/index.md`, with a directive
   where the clip belongs:

   ```markdown
   The claim is easier to watch than to read:

   :::{animation}[notebooks/phasor-unrolled.ipynb]
   :::
   ```

2. **A companion notebook** in that chapter's `notebooks/` folder, holding the
   manim scene (next section).

`make split` expands the directive into the generated section notebook: the prose
becomes Markdown cells, and every companion cell is spliced in **hidden** — tagged
`icm-hide-input` (the source never shows) and `disable-execution-cell` (the
live-code layer mounts no editor and no ▶ Run chip; manim is compiled machinery
with no browser build). At build time the cells execute like any others, and
`anim.show(...)` bakes the finished clip into the page as bare `<video>`
elements — a light and a dark render side by side, the page displaying the one
that matches the reader's theme toggle — autoplaying muted and looping: the
embedded-figure feel of the chapter 4 GIF, at a fraction of a GIF's weight.

## 2. The companion notebook

Two cells, both pure Python. The widget guideline is binding for animation cells
too — never write HTML or JavaScript in a cell; `icm_anim.show()` is the one
place the video element is made.

The first cell is the imports:

```python
import numpy as np
from manim import *

import icm_anim as anim
```

The second defines one scene and ends by showing it:

```python
class MyScene(Scene):
    def construct(self):
        dot = Dot(color=anim.RED)
        self.play(FadeIn(dot))
        ...

anim.show(MyScene)
```

The rules of the shape:

- **`anim.show(SceneCls)` is the cell's last expression** — what it returns is
  the video that lands on the page.
- **Palette: `anim.RED`, `anim.BLUE`, `anim.GOLD`, `anim.IRON`, `anim.TEAL`,
  `anim.STEEL`, plus `anim.INK` for one-off label greys — never manim's bare
  names.** `from manim import *` rebinds `RED`/`BLUE`/`GOLD`/`TEAL` to manim's
  neon palette, so a bare `RED` silently draws the wrong red. The `anim.*` names
  are the book's palette (single-sourced in `icm_widgets`, the same names
  `icm_plotly` re-exports) — shared with every figure and widget in the book.
- **Clips follow the reader's theme by default** (`theme="auto"`): the scene is
  rendered twice — house palette on the light page, and on the theme's dark
  background — and the page displays whichever matches the light/dark toggle.
  `anim.show(MyScene, theme="dark")` instead pins the borrowed 3Blue1Brown look
  in both modes (`theme="light"` pins the light render). Text ink and background
  are themed per render and reset afterward — nothing leaks between cells;
  geometry takes explicit `anim.*` colors.
- Three quality words: `quality="low"` (480p15) to iterate in VS Code — several
  times faster — `"medium"` (720p30, the default) to publish, and `"high"`
  (1080p60) only with a reason.
- `show()` enforces a weight budget (`max_mb=8` of page payload, both renders of
  an auto clip included) and raises rather than quietly shipping a heavy page.
- No visibility markers: animation cells are always hidden, and `# hide` /
  `# collapse` / `# no-output` markers are ignored.

## 3. Demo: the phasor, unrolled

The claim chapter 5 spends its first pages on — *a sinusoid is a rotating phasor
read off one axis* — as ten seconds of film. Everything here is an
`always_redraw` updater hanging off one `ValueTracker`, manim's version of the
update-function idea from the interactive template; the geometry, the trace, and
the dashed thread stay synchronized because they are all functions of the same
clock.

:::{animation}[notebooks/phasor-unrolled.ipynb]
:::

## 4. Demo: math that morphs

The other thing film does that a widget cannot: **the formula is a character**.
Here the partial Fourier sums of a square wave sharpen step by step, and the
`MathTex` label morphs in lockstep with the curve — `Transform` interpolates
both. Try writing that with a matplotlib artist.

:::{animation}[notebooks/harmonics-square.ipynb]
:::

## 5. Demo: the borrowed look

Section 5.5's margin cites the 3Blue1Brown video this whole aesthetic comes
from, and its winding machine is one argument away: `anim.show(WindingMachine,
theme="dark")` pins the borrowed look — dark in both reader modes. The signal
$g(t) = 1 + \cos(2\pi \cdot 3t)$ is wound around the origin while the winding
frequency sweeps up to 3 cycles per second — watch the curve snap into alignment
when the winding rate matches the signal's own frequency. This clip *narrates*
the idea; the interactive widget in 5.5 is where the reader gets to drive it.

:::{animation}[notebooks/winding-machine.ipynb]
:::

## 6. Cost and budget

Measured on this page's three clips (Apple silicon, `"medium"` = 720p30; an
auto clip's payload covers *both* of its renders):

| clip | film | page payload | render time |
|------|------|--------------|-------------|
| `PhasorUnrolled` (auto: light + dark) | 9.6 s | 0.66 MB | ~6 s |
| `HarmonicsBecomeSquare` (auto: light + dark) | 9.4 s | 1.3 MB | ~13 s |
| `WindingMachine` (pinned dark; every frame changes) | 9.8 s | 1.6 MB | ~12 s |

The whole page executes in ~36 s and carries ~3.6 MB of embedded video (base64
adds a third on top of each mp4). For scale, the two interactive pages in
chapter 5 weigh 16–19 MB each — a narrative page is still the *light* kind of
animated page. Note how the codec charges for **change, not seconds**: the
quiet phasor pair costs well under half the single busy winding clip at the
same length. House budget: keep a clip under **~20 seconds**, a page under
**~4 MB** of embedded video — a video earns its seconds or it should be a
figure.

## 7. When something looks wrong

| symptom | cause and fix |
|---------|---------------|
| `LaTeX error converting to dvi` | `MathTex`/`Tex` need a TeX distribution (`latex` + `dvisvgm` on PATH — MacTeX locally; CI installs texlive). Use Pango `Text(...)` for plain words if TeX is unavailable. |
| colors look neon, the red is wrong | the scene used manim's bare `RED`/`BLUE`/`GOLD`/`TEAL` — the star import shadows the book palette; use `anim.RED` and friends. |
| nothing visible on the white frame | geometry with no explicit color defaults to manim's white-on-dark; pass `color=anim.INK` (or a palette name) — only the text classes are themed automatically. |
| the clip does not respond to ▶ Run | correct — animations are watch-only; the live layer skips them on purpose. |
| `show()` raises "weighs X MB" | shorten the clip or calm the motion — codecs charge for change, not seconds (the dark winding clip costs five times the quiet phasor at equal length) — and remember an auto clip ships both renders. |
| `TypeError: show() wants the Scene subclass` | pass the class itself — `anim.show(MyScene)`, not `anim.show(MyScene())`. |
| the clip ignores the theme toggle | it was pinned with `theme="dark"` or `theme="light"` — by design for the borrowed look; the default `theme="auto"` follows the reader. |
| the render is slow while authoring | `quality="low"` to iterate, `"medium"` to publish. |

:::{admonition} Before publishing
:class: warning
Remove this **Template - Animation** page from `_toc.yml` — it is an author
reference, not course content.
:::
