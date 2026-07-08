# Template - Interactive

This page is a **living template** for **interactive widget** sections — pages
whose code runs at build time (so its output is baked into the page) *and* in
the reader's browser (so every cell is editable and re-runnable). It is also a
**tutorial**: by the end you should be able to write a fun widget from scratch
that looks native to the book.

Use it three ways:

1. **As a tutorial** — Section 2 is the quick start: the anatomy of a widget
   notebook and the eight steps from blank file to built page.
2. **As a starting point** — copy `notebooks/starter.ipynb` (Section 3) and
   grow it.
3. **As a worked example** — every cell on this page runs: Section 6 shows the
   same cell under all three visibility modes and Section 7 is a finished
   widget. Compare the page against its sources in
   `content/template-interactive/` (`main.md` plus the `notebooks/` folder).

:::{seealso}
For prose-only pages see the {doc}`Markdown template <../template-md>`; for
ordinary executable pages (code discussed *as code*, no widget) see the
{doc}`notebook template <../template-notebook>`.
:::

## 1. How an interactive section works

A chapter's interactive section is authored as **two pieces, side by side**:

- the chapter's Markdown — the prose, with a one-line directive where the
  widget belongs:

  ````markdown
  :::{interactive}[notebooks/my-widget.ipynb]
  :::
  ````

- the companion notebook in the chapter's `notebooks/` folder — Markdown
  cells and code cells, written and tested like any notebook (VS Code's
  "Run All" is the fastest loop).

The split pipeline (`tools/split_chapters.py`) then emits the section as a
Jupyter notebook page: the surrounding prose becomes Markdown cells and the
companion notebook's cells are spliced in where the directive was. From there,
two runs of the same code produce what the reader experiences:

1. **At build time** the cells execute (`execute_notebooks: auto`) and their
   output — an animation player, a plot, an audio card — is baked into the
   HTML. A reader who never clicks anything still sees a finished page.
2. **In the browser** the live-code layer (`_static/live-cells.js`) mounts an
   editor on every visible cell at page load, then quietly boots the Python
   kernel (Pyodide, ~25 MB on first visit) and installs the book's wheels in
   the background — **installation always completes, but nothing executes**.
   A **▶ Run** therefore pays only for execution: the clicked cell's
   not-yet-run setup — the cells above it **from the same companion notebook
   only** (each is self-contained, so the rest of the page never runs on its
   behalf) — then the cell itself, whose baked output is replaced by the
   live one. Reloading the page restores the built page — that is the reset
   button.

Because the same cells run in both places, **write every cell against the
browser kernel** (Section 4); the build environment is a superset of it.

:::{note}
This page itself is built by that pipeline. Its sources live in
`content/template-interactive/`: `main.md` (the prose you are reading, plus
its `{interactive}` directives) and the `notebooks/` folder beside it.
`make template-interactive` expands them into the `index.ipynb` that
`_toc.yml` points at — the same expansion `make split` performs for chapter
sections. Edit the sources, regenerate, rebuild.
:::

## 2. Quick start: your first animation

Every widget notebook is the same **three cells** — learn this shape once and
every example on this page reads instantly:

1. **Dependencies** (`# hide`) — the `%pip install` line (inside a
   `with capture_output():` block) and every import. Copy it verbatim from
   Section 4.
2. **Style and precompute** (`# collapse`) — the house rcParams block and
   palette (Section 5), plus the arrays the animation will need.
3. **The widget** (visible, or `# hide` if the code is beside the point) — a
   figure, an `animate(n)` callback that only *moves* artists, a
   `FuncAnimation`, and the player registered and displayed:

   ```python
   anim = FuncAnimation(fig, animate, frames=n_frames, interval=1000 / fps)
   player = HTML(anim.to_jshtml())
   plt.close(fig)                        # only the player reaches the page
   glue("my-widget", player, display=False)
   player
   ```

From blank file to built page:

1. **Copy the starter** — `notebooks/starter.ipynb` (rendered in Section 3) —
   into your chapter's `notebooks/` folder and rename it
   (`notebooks/my-widget.ipynb`).
2. **Sketch the idea as a still figure first** — get the layout, colors, and
   labels right on frame one before animating anything.
3. **Animate with `FuncAnimation`** — precompute arrays up front; the
   `animate(n)` callback should only move artists (`set_ydata`, `set_text`,
   `set_color`).
4. **Add sound where it earns its place** — `pq.play(...)` renders the book's
   audio card in both environments.
5. **Mark every cell** (Section 6) — `# hide` the plumbing, `# collapse` the
   styling, leave the teaching code visible.
6. **Test the notebook on its own** — "Run All" in VS Code; the whole thing
   should finish well under 30 s.
7. **Drop the directive into the prose** where the widget belongs, with a
   lead-in paragraph above and a "try changing…" prompt below:

   ````markdown
   :::{interactive}[notebooks/my-widget.ipynb]
   :::
   ````

8. **Regenerate and build** — `make split` emits the section notebook (for
   this template page it is `make template-interactive`), then `make book`;
   click **▶ Run** on the built page to check the live path.

If something looks wrong on the page, check Section 9 — the common mistakes
all have one-line fixes.

## 3. A minimal starter

The whole mechanism at its smallest — one collapsed setup cell, one visible
cell that makes a figure and a sound. This is the file the quick start copies:

:::{interactive}[notebooks/starter.ipynb]
:::

## 4. The libraries a widget may use

| Library | What it powers | At build | In the browser |
| ------- | -------------- | -------- | -------------- |
| `numpy` | arrays, signal math | ✓ | ✓ preloaded (Pyodide build) |
| `matplotlib` | figures; `FuncAnimation` → the house animation player | ✓ | ✓ preloaded |
| `pyquist` (`pq`) | `pq.Audio`, `pq.play(...)` → the book's audio card | ✓ | ✓ self-hosted wheel, installed at kernel start |
| `myst_nb` (`glue`) | registers a build-time output for the page | ✓ | ✓ stubbed to a no-op — safe to call |
| `icm_widgets` | `ParamPlayer` — parameter **sliders** on a widget (Section 8) | ✓ | ✓ self-hosted wheel, installed at kernel start |
| `soxr`, `requests`, `tqdm` | pyquist's dependencies | ✓ | ✓ preloaded |
| `browseraudio` | `pq.record(...)` microphone capture | – | ✓ auto-installed when the page's code uses it |
| `soundfile` / `sounddevice` | WAV I/O, playback plumbing | real | stub wheels (WAV only; playback renders as an audio card) |

Two conventions keep the same cell runnable in both environments:

- Install with `%pip install -q numpy matplotlib` **inside a
  `with capture_output():` block**, so pip's chatter stays off the page while a
  genuine install failure still raises loudly. Do **not** wrap the whole cell in
  a bare `%%capture` — it swallows the traceback too, and a silently-failed
  setup resurfaces cells later as a baffling `NameError`. The install is a no-op
  wherever the packages already exist (both environments) and documents what the
  notebook needs. Two packages are deliberately **not** in the install line:
  `pyquist` (the build uses the repo's editable install and the browser
  pre-installs the book's own wheel, so a PyPI fetch would fight both) and
  `myst-nb` (build-time only — it pulls `pyzmq`, which has no browser wheel, so
  the browser kernel stubs `glue` to a no-op instead).
- Import everything in that one cell, `# hide` it (Section 6), and let the
  teaching cells stay free of plumbing.

The standard first cell, in full:

```python
# hide
# --- Dependencies -----------------------------------------------------------
# Everything this notebook imports, installed up front. The installs are
# no-ops when the packages are already present (they ship with the book's
# build environment and with the browser kernel). The capture_output() block
# hides pip's chatter but still lets a genuine install failure raise. myst-nb
# isn't installed here — it's build-time only, and the browser kernel stubs
# its glue() to a no-op.
from IPython.utils.capture import capture_output
with capture_output():                 # swallow pip + import chatter (e.g. matplotlib's font cache); real failures still raise
    # numpy + matplotlib are Pyodide built-ins; the install is a no-op at build time
    %pip install -q numpy matplotlib
    import numpy as np
    import matplotlib.pyplot as plt
    import pyquist as pq
    from matplotlib.animation import FuncAnimation
    from myst_nb import glue
    from IPython.display import HTML
```

Every companion notebook on this page opens with a cell like it — that is
what keeps each one runnable on its own ("Run All" in VS Code) *and* lets the
notebooks run in any order on the page.

## 5. The house style

Widgets should look like the book drew them. Start every widget notebook with
this rcParams block, right after the dependencies:

```python
plt.rcParams.update({
    "figure.dpi": 64,                # sets the player's intrinsic size only —
    "figure.subplot.bottom": 0.18,   # reserve room for x-axis labels (jshtml crops at the figure bbox)
    "animation.html": "jshtml",      # SVG frames are vector, sharp at any zoom
    "animation.frame_format": "svg", # ~3x smaller gzipped than PNG, and crisp
    "animation.embed_limit": 40,     # MB; matplotlib's 20 MB default drops frames
    "text.usetex": False,            # mathtext: no LaTeX install needed locally
    "font.size": 12,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#6D6E71",
    "xtick.color": "#6D6E71", "ytick.color": "#6D6E71",
    "xtick.labelcolor": "#3b3b3b", "ytick.labelcolor": "#3b3b3b",
    "axes.labelcolor": "#3b3b3b",
})
```

The one line that decides how the animation *ages* is
`"animation.frame_format": "svg"`: frames ship as vectors, so the player is
retina-crisp at any size — and base64 SVG text gzips about 3× on the wire,
where PNG barely compresses. The exception is a figure with **raster content**
(`imshow`, a spectrogram): SVG would embed the raster into every frame — set
`"animation.frame_format": "png"` in that notebook instead.

Color is meaning. Widgets draw from CMU's palette — Carnegie red is both the
university's color and the book's accent (chips, links, the cell spine), so a
widget colored this way reads as part of the course:

| Swatch | Hex | Role |
| ------ | --- | ---- |
| <span style="color:#C41230">■</span> Carnegie red | `#C41230` | the primary object — the thing being built or measured |
| <span style="color:#007BC0">■</span> Highlands blue | `#007BC0` | a contrasting second series |
| <span style="color:#FDB515">■</span> gold thread | `#FDB515` | the moving part — a probe, the newest addition |
| <span style="color:#6D6E71">■</span> iron gray | `#6D6E71` | a composite or total signal |
| <span style="color:#008F91">■</span> teal thread | `#008F91` | a second component when red and blue are taken |
| <span style="color:#E0E0E0">■</span> steel gray | `#E0E0E0` | static guides: reference curves, unit circles |

Layout and animation conventions, all visible in the demo widget below:

- **Figure size** — wide and short fits the text column: `figsize=(8.2, …)`
  with heights around 2.4–3.8; use `width_ratios` for uneven panels.
- **Label everything** — axes carry units (`"time (ms)"`, `"amplitude"`); a
  moving quantity gets a live title or legend entry. Legends use a
  transparent frame (`.get_frame().set_alpha(0.0)`).
- **Animation budget** — `to_jshtml()` embeds every frame into the page, so
  keep ≤ ~120 frames and check `len(anim.to_jshtml()) / 1e6` (MB) while
  developing — past `animation.embed_limit` matplotlib silently drops frames.
- **Motion runs at ~24 fps** — the house rate: `interval=1000 / 24`. Going
  slower makes continuous motion visibly step. The exception is a discrete
  step-reveal (the demo widget adds one harmonic every half second) — those
  may go as slow as they like.
- **End the cell cleanly** — build the player, close the figure, register it,
  and make the player the cell's value:

  ```python
  player = HTML(anim.to_jshtml())
  plt.close(fig)                       # only the player reaches the page
  glue("my-widget", player, display=False)
  player
  ```

  `plt.close(fig)` stops the bare figure appearing next to the player, and
  `glue` lets any Markdown page re-embed the same player with
  `` {glue}`my-widget` ``.

You can see this style cell in the wild on this page: expand the
**Show setup** bars in Sections 3 and 7.

A widget that wants live **parameters** — sliders the reader drags — uses the
`icm_widgets` library instead of `FuncAnimation`; it follows the same
discipline and has its own tutorial and reference in Section 8.

## 6. Hide, collapse, show

Every code cell in a companion notebook chooses how much of itself the page
shows, with a whole-line marker:

| Marker | On the page | Use it for |
| ------ | ----------- | ---------- |
| `# hide` | source removed entirely; the output stands alone as native page content (no `output` tag) | boilerplate — or a widget whose code is beside the point |
| `# collapse` | source behind a collapsed **Show setup** bar | setup a curious reader might expand: styling, constants, helpers |
| `# show` (or no marker) | source visible and editable | the code you are teaching |
| `# no-output` (additional) | the cell's **baked output** is dropped from the page (it still runs, at build and in the browser) | a kernel-only cell whose output is dead page weight — e.g. a VS Code preview widget that bakes megabytes of inert state |

The marker must be a line of its own (conventionally the first line of the
cell), it is case-insensitive, and the first one wins. It is an ordinary comment: the split pipeline reads it to tag
the cell (`# hide` → `icm-hide-input`, `# collapse` → `hide-input`) and
leaves the line in place — expand any **Show setup** bar on this page and
the `# collapse` that put it there is the first thing you read, and a cell
copied off the page keeps its behavior in your own notebook. By convention
visible cells carry no marker: `# show` exists, but visible is the default.
Hidden and collapsed cells still **run**, both at build time and in the
browser — when a student runs a visible cell, the setup cells above it
execute first, in order.

To see the modes side by side, the rest of this section embeds
`notebooks/three-modes.ipynb`: the **same cell three times** — it draws two
cycles of a 220 Hz sawtooth, the wave the widget in Section 7 builds — and
nothing differs between the copies but the marker line. (The notebook also
opens with a hidden setup cell, which draws nothing.) The mode labels below
are Markdown cells inside that notebook, rendered as prose.

:::{interactive}[notebooks/three-modes.ipynb]
:::

## 7. The demo widget

Now the payoff: a full widget in the house style, from
`notebooks/harmonics-builder.ipynb`. Its dependencies cell is hidden, its
style cell sits behind the **Show setup** bar, and the two teaching cells
carry no marker at all — visible is the default. Press **▶ Run** anywhere
and the setup cells run first, automatically.

:::{interactive}[notebooks/harmonics-builder.ipynb]
:::

Try it live: change `n_harmonics` to 40 in the widget cell and press
**▶ Run**, or flip the recipe to odd harmonics only (a square wave) with
`k = np.arange(1, n_harmonics + 1, 2)` — then re-run the sound cell to hear
the difference.

## 8. Sliders: the `icm_widgets` library

An animation plays; a slider lets the reader ask *what if*. When a parameter
deserves exploring — an amplitude, a frequency, a filter cutoff —
`icm_widgets` puts sliders on the widget while the cell stays pure
matplotlib (never write HTML or JavaScript in a cell).

**The mental model.** `ParamPlayer` is `FuncAnimation` with named parameters
instead of a frame number: you build a figure with static chrome and dynamic
artists, and write an `update(**params)` that only *moves* the dynamic
artists. At construction it renders **every parameter combination** with
matplotlib — one background image plus small transparent overlays — and
displays a self-contained player whose script just swaps pre-rendered
frames. The browser does no math, every pixel is matplotlib's, and the
widget works on the book page, in VS Code, and in vanilla Jupyter alike —
kernel or no kernel.

Each feature below has its own live demo — the code is the cell, the widget
is its output, and every one of them can be edited and **▶ Run** right here.

### `slider` — a snapping parameter

```python
slider(lo, hi, step, value=None, unit="", label=None)
```

A slider over the inclusive grid `lo, lo+step, …, hi`. `value` is the
starting position (it snaps to the nearest grid value); `unit` is appended
to the live readout (`"0 dB"`); `label` defaults to the parameter name.
Every grid value is one rendered frame — step size is a page-weight
decision, not just a UX one. One parameter is a complete widget:

:::{interactive}[notebooks/feature-slider.ipynb]
:::

### `play` — the animated dimension

```python
play(lo, hi, frames, period=1.0, rate=None, label=None)
```

At most **one** per widget, with a play/pause button. Its grid is `frames`
values with the **endpoint excluded**, so a cyclic quantity loops
seamlessly — watch the phasor below cross 2π back into 0 without a stutter.
One full sweep takes `period` seconds; if `rate` names another parameter,
the sweep speed is multiplied by that parameter's current value
(`rate="frequency"` in the next subsection's widget — its wave travels at
whatever the frequency slider says).

**Frames are smoothness.** The runtime advances by wall clock, so more
frames never change the speed — they only smooth the motion. Default to
about **24 × `period`** frames (the house ~24 fps), and spend extra frames
here first: a played dimension costs frames *linearly*, while a finer
slider step multiplies the whole grid.

:::{interactive}[notebooks/feature-play.ipynb]
:::

### `ParamPlayer` — render and display the widget

```python
ParamPlayer(fig, update, dynamic=[...], depends={...}, **params)
```

`dynamic` lists the artists `update` moves; every other keyword argument is
a parameter and must match a name in `update`'s signature. Two contracts
differ from the animation pattern:

- **Do not call `plt.close(fig)`** — `ParamPlayer` closes the figure itself
  after rendering.
- **The `ParamPlayer` object is the thing to display** — make it the cell's
  trailing expression, and `glue("my-widget", widget, display=False)` only if
  a Markdown page should re-embed it.

It raises immediately on author mistakes: no parameters, more than one
`play`, a parameter that is neither `slider(…)` nor `play(…)`, or `depends`
naming an unknown parameter.

The complete widget below combines both parameter kinds — two sliders and a
rate-coupled play. Drag the sliders, or edit the cell and **▶ Run** it:

:::{interactive}[notebooks/param-player.ipynb]
:::

### Layers with `depends=`

By default every dynamic artist re-renders for the **full product grid**.
When artists respond to different parameter subsets, declare it —
`depends={artist: (parameter names…)}` — and artists with the same subset
render together as one **layer** whose frames cover only those parameters.
That is what makes a smooth played dimension affordable. Below, the wave
re-renders only per amplitude and the dot only per phase — the printed
`repr` says 52 frames in 2 layers, where one layer would need 4 × 48 = 192:

:::{interactive}[notebooks/feature-depends.ipynb]
:::

Section 5.2 of the book ("The phasor") is the layered example in the wild —
amplitude × frequency × a played phase.

### The page-weight budget

The page pays for every frame (the product of each layer's value counts —
a few KB of SVG each). Keep the total in the low hundreds, and check the
widget's `repr` and `weight_mb` while developing. The cell below rebuilds
the layered demo **without** `depends=`: the same widget now costs 192
frames instead of 52 — compare the two printed sizes —

:::{interactive}[notebooks/feature-budget.ipynb]
:::

### Where it runs

The build environment installs it editable (`environment.yml`) and the
browser kernel installs the book's own wheel automatically — so it works at
build time and under **▶ Run** with no install line in the cell (like
`pyquist`, do **not** add it to the `%pip install` line). On your own
machine, working in this repo is enough; outside it,
`pip install -e tools/icm_widgets`. The library is not on PyPI.

## 9. When something looks wrong

| Symptom | Cause and fix |
| ------- | ------------- |
| The figure appears twice — a static copy under the player | Missing `plt.close(fig)` before the cell ends |
| pip chatter printed on the page | The `%pip install` line isn't inside the `with capture_output():` block |
| The animation stops early or frames are missing | Over `animation.embed_limit` — matplotlib drops frames silently; raise the limit or use fewer frames |
| The animation is blurry | Raster frames — the house rcParams (`"animation.frame_format": "svg"`) is missing |
| An `imshow`/spectrogram animation is enormous | SVG embeds the raster into every frame — set `"animation.frame_format": "png"` in that notebook |
| Code shows on the page that shouldn't | The marker isn't on a whole line of its own, or isn't the cell's first line |
| The widget is missing from the built page | The directive path doesn't match the notebook, or you edited the generated `.ipynb` instead of the source and re-split |
| A slider widget takes ages to render or is huge | The frame grid multiplied out — check `repr(widget)` / `weight_mb`, coarsen slider steps, or split artists into layers with `depends=` (Section 8) |
| A bare figure shows instead of the slider widget | The `ParamPlayer` isn't the cell's trailing expression (and don't `plt.close(fig)` — it closes the figure itself) |
| `ModuleNotFoundError: icm_widgets` on your own machine | Outside this repo it isn't installed — `pip install -e tools/icm_widgets`; never add it to the `%pip` line (Section 8) |

:::{admonition} Before publishing
:class: warning
Remove this **Interactive Template** page from `_toc.yml` — it is an author
reference, not course content.
:::
