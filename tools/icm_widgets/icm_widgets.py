"""icm_widgets — parameter sliders for the book's interactive widgets.

The sanctioned way to put sliders on a page widget with no kernel and no
HTML/JavaScript in the notebook cell. Build the figure as for the house
``FuncAnimation`` pattern — static axes plus dynamic artists moved by an
``update(**params)`` callback — and declare the parameters::

    from icm_widgets import ParamPlayer, slider, play

    fig, ax = plt.subplots(figsize=(8.2, 2.4))
    line, = ax.plot([], [], color="#C41230", lw=2.0)

    def update(amplitude, phase):
        line.set_data(t, amplitude * np.sin(2 * np.pi * t + phase))

    ParamPlayer(
        fig, update, dynamic=[line],
        amplitude=slider(0.25, 2.0, step=0.25, value=1.0),
        phase=play(0, 2 * np.pi, frames=12, period=1.0),
    )

Construction renders every grid combination up front: one full background
frame plus one transparent, marks-only overlay per combination. The widget
displays as self-contained HTML (frames + a small mount script), so it looks
the same on the book page, in VS Code, and in vanilla Jupyter; every pixel is
matplotlib's. Frames are SVG by default; pass ``frame_format="png"`` for
raster content (imshow, spectrograms). Keep the grid in the low hundreds —
``weight_mb`` reports the embedded size.
"""
from __future__ import annotations

import base64
import io
import itertools
import json
from dataclasses import dataclass

import numpy as np

__version__ = "0.3.0"
__all__ = [
    "ParamPlayer", "slider", "play",
    "house_style", "RED", "BLUE", "GOLD", "IRON", "TEAL", "STEEL",
]

# The book's plot palette (Carnegie Mellon's colors) — import the names
# instead of pasting hex codes.
RED, BLUE, GOLD, IRON, TEAL, STEEL = (
    "#C41230", "#007BC0", "#FDB515", "#6D6E71", "#008F91", "#E0E0E0",
)


def house_style():
    """Apply the book's house plotting style to matplotlib's rcParams.

    Call once in the widget's style cell. The ``animation.*`` keys only
    matter for ``to_jshtml()`` widgets and are harmless elsewhere, so one
    call covers both the FuncAnimation and ParamPlayer patterns.
    """
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.dpi": 64,                # sets the embedded player's size
        "figure.subplot.bottom": 0.18,   # room so x-axis labels aren't cropped
        "animation.html": "jshtml",
        "animation.frame_format": "svg",
        "animation.embed_limit": 40,     # MB; matplotlib's 20 MB default drops frames
        "text.usetex": False,            # mathtext: no LaTeX install needed
        "font.size": 12,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#6D6E71",
        "xtick.color": "#6D6E71", "ytick.color": "#6D6E71",
        "xtick.labelcolor": "#3b3b3b", "ytick.labelcolor": "#3b3b3b",
        "axes.labelcolor": "#3b3b3b",
    })


@dataclass(frozen=True)
class slider:
    """A snapping slider over ``lo .. hi`` (inclusive) in steps of ``step``.

    ``value`` is the starting position (nearest grid value wins). ``unit`` is
    appended to the readout ("2.00 Hz"); ``label`` defaults to the parameter
    name.
    """

    lo: float
    hi: float
    step: float
    value: float | None = None
    unit: str = ""
    label: str | None = None

    def grid(self) -> list[float]:
        n = int(round((self.hi - self.lo) / self.step)) + 1
        return [float(v) for v in np.linspace(self.lo, self.hi, n)]

    def decimals(self) -> int:
        s = f"{self.step:.10f}".rstrip("0")
        return max(0, len(s.split(".")[1])) if "." in s else 0


@dataclass(frozen=True)
class play:
    """The animated dimension: ``frames`` values over ``lo .. hi`` (endpoint
    excluded, so a cyclic quantity like a phase loops seamlessly).

    One full sweep takes ``period`` seconds; if ``rate`` names another
    parameter, the sweep speed is multiplied by that parameter's current
    value. At most one ``play`` dimension per widget.
    """

    lo: float
    hi: float
    frames: int
    period: float = 1.0
    rate: str | None = None
    label: str | None = None

    def grid(self) -> list[float]:
        return [float(v) for v in np.linspace(self.lo, self.hi, self.frames, endpoint=False)]


class ParamPlayer:
    """Pre-render ``fig`` across a parameter grid and display it as a widget.

    ``update(**params)`` must only move the ``dynamic`` artists (set_data,
    set_text, set_color — the FuncAnimation discipline). The figure is closed
    after rendering; display the ParamPlayer itself (make it the cell's
    trailing expression, or ``glue`` it for a Markdown page).
    """

    def __init__(self, fig, update, *, dynamic, depends=None, frame_format="svg", **params):
        import matplotlib.pyplot as plt

        if not params:
            raise ValueError("ParamPlayer needs at least one slider() or play() parameter")
        plays = [n for n, p in params.items() if isinstance(p, play)]
        if len(plays) > 1:
            raise ValueError(f"at most one play() dimension, got {plays}")
        for n, p in params.items():
            if not isinstance(p, (slider, play)):
                raise TypeError(f"parameter {n!r} must be slider(...) or play(...)")
        dynamic = list(dynamic)
        names = list(params)

        # ``depends`` maps an artist to the parameters it responds to.
        # Artists sharing a subset render together as one layer whose frame
        # grid covers only those parameters, so a low-ink artist can afford
        # many more frames than the full product grid. Unlisted artists
        # depend on every parameter.
        depends = depends or {}
        for a, dep in depends.items():
            unknown = set(dep) - set(names)
            if unknown:
                raise ValueError(f"depends[{a!r}] names unknown parameters {sorted(unknown)}")

        def dep_of(artist):
            for a, dep in depends.items():
                if a is artist:
                    return tuple(n for n in names if n in set(dep))
            return tuple(names)

        layer_order: list[tuple] = []
        layer_artists: dict[tuple, list] = {}
        for a in dynamic:
            d = dep_of(a)
            if d not in layer_artists:
                layer_artists[d] = []
                layer_order.append(d)
            layer_artists[d].append(a)

        fig.canvas.draw()  # finalize layout before measuring/rendering

        # SVG frames stay crisp at any zoom and gzip well; raster content
        # (imshow, spectrograms) should use PNG instead — SVG would embed the
        # raster into every frame.
        if frame_format not in ("svg", "png"):
            raise ValueError(f'frame_format must be "svg" or "png", got {frame_format!r}')
        mime = "svg+xml" if frame_format == "svg" else "png"

        # Crop every frame to one FIXED box that includes the axis labels
        # (the raw figure bbox can clip labels on short figures). Reusing the
        # same box for the background and every overlay keeps them aligned.
        save_bbox = fig.get_tightbbox()

        def frame(transparent):
            buf = io.BytesIO()
            fig.savefig(buf, format=frame_format, dpi=fig.dpi, transparent=transparent,
                        bbox_inches=save_bbox)
            return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode("ascii")

        # Background: the figure's static chrome, dynamic artists hidden.
        for a in dynamic:
            a.set_visible(False)
        background = frame(False)

        # Overlays: one layer's artists at a time, on transparency, with axis
        # chrome and everything else hidden so nothing double-draws.
        hidden = []
        for ax in fig.axes:
            ax.set_axis_off()
            for child in ax.get_children():
                if any(child is a for a in dynamic):
                    continue
                if hasattr(child, "get_visible") and child.get_visible():
                    child.set_visible(False)
                    hidden.append(child)

        def start_value(p):
            grid = p.grid()
            if isinstance(p, slider) and p.value is not None:
                return grid[min(range(len(grid)), key=lambda i: abs(grid[i] - p.value))]
            return grid[0]

        base_values = {n: start_value(params[n]) for n in names}

        layers = []
        for dep in layer_order:
            arts = layer_artists[dep]
            for a in dynamic:
                a.set_visible(any(a is x for x in arts))
            frames = []
            for combo in itertools.product(*(params[n].grid() for n in dep)):
                values = dict(base_values)
                values.update(zip(dep, combo))
                update(**values)
                frames.append(frame(True))
            layers.append({"params": list(dep), "frames": frames})

        for a in dynamic:
            a.set_visible(True)
        for child in hidden:
            child.set_visible(True)
        for ax in fig.axes:
            ax.set_axis_on()

        w, h = fig.get_size_inches()
        spec_params = []
        for n in names:
            p = params[n]
            if isinstance(p, slider):
                grid = p.grid()
                start = min(range(len(grid)), key=lambda i: abs(grid[i] - (p.value if p.value is not None else grid[0])))
                spec_params.append({
                    "kind": "slider", "name": n, "label": p.label or n,
                    "values": grid, "start": start,
                    "unit": p.unit, "decimals": p.decimals(),
                })
            else:
                spec_params.append({
                    "kind": "play", "name": n, "n": p.frames,
                    "period": p.period, "rate": p.rate,
                })

        self.spec = {
            "width": round(w * fig.dpi, 1),
            "height": round(h * fig.dpi, 1),
            "background": background,
            "params": spec_params,
            "layers": layers,
        }
        plt.close(fig)

    @property
    def weight_mb(self) -> float:
        """Embedded size of the widget's HTML, in MB (frames dominate)."""
        return len(self._json()) / 1e6

    def _json(self) -> str:
        # "</" would end the enclosing <script> tag early; JSON allows the escape.
        return json.dumps(self.spec).replace("</", "<\\/")

    def _repr_html_(self) -> str:
        import uuid

        uid = "icmw" + uuid.uuid4().hex[:10]
        return (
            f'<div class="icm-widget" id="{uid}">'
            f'<script type="application/vnd.icm-widget+json">{self._json()}</script>'
            f"</div>\n<style>{_WIDGET_CSS % {'uid': uid}}</style>"
            f"\n<script>{_WIDGET_JS % {'uid': uid}}</script>"
        )

    def __repr__(self) -> str:
        n = sum(len(L["frames"]) for L in self.spec["layers"])
        return (f"<icm_widgets.ParamPlayer: {n} frames in "
                f"{len(self.spec['layers'])} layer(s), {self.weight_mb:.1f} MB embedded>")


# Layout-only fallback styling, scoped to this widget instance. The book's
# custom.css layers the house branding on top; elsewhere the native controls
# show with the same layout.
_WIDGET_CSS = """\
#%(uid)s { max-width: 100%%; margin: 0.4rem auto; }
#%(uid)s .icm-widget-stage { position: relative; }
#%(uid)s .icm-widget-stage img { display: block; width: 100%%; margin: 0; }
#%(uid)s .icm-widget-stage canvas { position: absolute; left: 0; top: 0;
  width: 100%%; height: 100%%; }
#%(uid)s .icm-widget-row { display: flex; align-items: center; justify-content: center;
  gap: 0.6em; margin: 0.3rem 0; font-family: sans-serif; font-size: 0.78rem; color: #6d6e71; }
#%(uid)s .icm-widget-row > span { flex-shrink: 0; }
#%(uid)s .icm-widget-row > span:first-child { width: 6.5em; text-align: right; }
#%(uid)s .icm-widget-row input { flex: 0 0 auto; width: 200px; }
#%(uid)s .icm-widget-row input[type="range"] {
  -webkit-appearance: none; appearance: none;
  height: 4px; border-radius: 999px; background: #e3e3e3; outline: none;
}
#%(uid)s .icm-widget-row input[type="range"]::-webkit-slider-runnable-track {
  height: 4px; border-radius: 999px;
}
#%(uid)s .icm-widget-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none; width: 14px; height: 14px; margin-top: -5px;
  border: none; border-radius: 50%%; background: var(--cmu-red, #c41230);
  cursor: pointer; transition: transform 0.15s ease, background 0.15s ease;
}
#%(uid)s .icm-widget-row input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.2); background: var(--cmu-red-dark, #9b0e26);
}
#%(uid)s .icm-widget-row input[type="range"]::-moz-range-track {
  height: 4px; border-radius: 999px; background: #e3e3e3;
}
#%(uid)s .icm-widget-row input[type="range"]::-moz-range-thumb {
  width: 14px; height: 14px; border: none; border-radius: 50%%;
  background: var(--cmu-red, #c41230); cursor: pointer;
}
#%(uid)s .icm-widget-val { min-width: 3.6em; text-align: left;
  font-variant-numeric: tabular-nums; }
#%(uid)s .anim-buttons { display: flex; justify-content: center; margin: 0.5rem 0 0.2rem; }
#%(uid)s .anim-buttons button {
  display: flex; align-items: center; justify-content: center;
  width: 2rem; height: 2rem; padding: 0;
  border: 1px solid #d0d0d0; border-radius: 999px;
  background: #ffffff; color: #5a5a5a; cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease, background 0.15s ease;
}
#%(uid)s .anim-buttons button:hover {
  color: var(--cmu-red, #c41230); border-color: var(--cmu-red, #c41230);
}
#%(uid)s .anim-buttons button[title="Play"] {
  background: var(--cmu-red, #c41230); border-color: var(--cmu-red, #c41230);
  color: #ffffff;
}
#%(uid)s .anim-buttons button[title="Play"]:hover {
  background: var(--cmu-red-dark, #9b0e26); border-color: var(--cmu-red-dark, #9b0e26);
}
#%(uid)s .anim-buttons button svg {
  width: 0.85rem; height: 0.85rem; display: block; fill: currentColor;
}
"""

# The mount runtime, embedded with every widget so it renders anywhere.
# Frames are composited layer by layer onto a canvas — one drawImage per
# layer per repaint. No math beyond frame indexing runs client-side.
_WIDGET_JS = """\
(function () {
  "use strict";
  var root = document.getElementById("%(uid)s");
  if (!root || root.dataset.icmMounted) return;
  root.dataset.icmMounted = "1";
  var spec = JSON.parse(root.querySelector(
    'script[type="application/vnd.icm-widget+json"]').textContent);

  root.style.width = spec.width + "px";
  var stage = document.createElement("div");
  stage.className = "icm-widget-stage";
  var bg = document.createElement("img");
  bg.src = spec.background;
  bg.alt = "";
  var canvas = document.createElement("canvas");
  var ctx = canvas.getContext("2d");
  // Back the canvas at devicePixelRatio so the SVG frames rasterize at the
  // display's native density; re-size on ratio changes (zoom, monitor move).
  function pixelRatio() {
    return Math.max(1, Math.min(window.devicePixelRatio || 1, 3));
  }
  var ratio = pixelRatio();
  function sizeCanvas() {
    canvas.width = Math.round(spec.width * ratio);
    canvas.height = Math.round(spec.height * ratio);
    needsDraw = true;
  }
  window.addEventListener("resize", function () {
    var r = pixelRatio();
    if (r !== ratio) {
      ratio = r;
      sizeCanvas();
    }
  });
  sizeCanvas();
  stage.appendChild(bg);
  stage.appendChild(canvas);
  root.appendChild(stage);

  var controls = document.createElement("div");
  controls.className = "anim-controls icm-widget-controls";
  controls.style.width = "100%%";
  root.appendChild(controls);

  var dims = spec.params.map(function (p) {
    return { p: p, n: p.kind === "play" ? p.n : p.values.length,
             idx: p.kind === "play" ? 0 : p.start };
  });
  var dimByName = {};
  dims.forEach(function (d) { dimByName[d.p.name] = d; });

  var needsDraw = true;
  // A small widget decodes every frame up front. Past EAGER_LIMIT total
  // frames that wedges the page (thousands of live SVG documents), so a
  // large widget decodes frames on demand around the playhead, keeps the
  // last-good frame per layer so playback never flickers, and evicts FIFO.
  var EAGER_LIMIT = 256;
  var LRU_MAX = 192;
  var totalFrames = spec.layers.reduce(function (s, L) {
    return s + L.frames.length;
  }, 0);
  var eager = totalFrames <= EAGER_LIMIT;

  function makeImg(uri) {
    var im = new Image();
    im.onload = function () { needsDraw = true; };
    im.src = uri;
    if (im.decode) im.decode().catch(function () {});
    return im;
  }

  var layers = spec.layers.map(function (L) {
    var lay = { params: L.params, uris: L.frames, cache: {}, order: [], last: null };
    if (eager) {
      for (var i = 0; i < L.frames.length; i++) lay.cache[i] = makeImg(L.frames[i]);
    }
    return lay;
  });

  function imageAt(lay, i) {
    var im = lay.cache[i];
    if (!im) {
      im = makeImg(lay.uris[i]);
      lay.cache[i] = im;
      lay.order.push(i);
      if (lay.order.length > LRU_MAX) delete lay.cache[lay.order.shift()];
    }
    return im;
  }

  function layerIndex(L) {
    var i = 0;
    for (var d = 0; d < L.params.length; d++) {
      var dim = dimByName[L.params[d]];
      i = i * dim.n + dim.idx %% dim.n;
    }
    return i;
  }

  function prefetch(lay) {
    if (eager || !playDim) return;
    if (lay.params.indexOf(playDim.p.name) === -1) return;
    var save = playDim.idx;
    for (var k = 1; k <= 4; k++) {
      playDim.idx = (save + k) %% playDim.n;
      imageAt(lay, layerIndex(lay));
    }
    playDim.idx = save;
  }

  function composite() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var l = 0; l < layers.length; l++) {
      var lay = layers[l];
      var im = imageAt(lay, layerIndex(lay));
      if (im.complete && im.naturalWidth) lay.last = im;
      // A cold frame draws the previous one for a tick instead of
      // flickering; its onload flags needsDraw. Destination size is
      // explicit: SVG intrinsic size is in pt and the backing store is
      // devicePixelRatio-scaled.
      var draw = im.complete && im.naturalWidth ? im : lay.last;
      if (draw) ctx.drawImage(draw, 0, 0, canvas.width, canvas.height);
      prefetch(lay);
    }
  }
  function valueOf(name) {
    var d = dimByName[name];
    return d && d.p.values ? d.p.values[d.idx] : 1;
  }

  var playDim = null;
  dims.forEach(function (dim) {
    var p = dim.p;
    if (p.kind === "play") { playDim = dim; return; }
    var row = document.createElement("label");
    row.className = "icm-widget-row";
    var name = document.createElement("span");
    name.textContent = p.label;
    var input = document.createElement("input");
    input.type = "range";
    input.className = "anim-slider";
    input.min = 0; input.max = p.values.length - 1; input.step = 1; input.value = p.start;
    input.setAttribute("aria-label", p.label);
    var val = document.createElement("span");
    val.className = "icm-widget-val";
    function fmt() {
      val.textContent = p.values[dim.idx].toFixed(p.decimals) + (p.unit ? " " + p.unit : "");
    }
    input.addEventListener("input", function () {
      dim.idx = parseInt(input.value, 10);
      fmt();
      needsDraw = true;
    });
    row.appendChild(name); row.appendChild(input); row.appendChild(val);
    controls.appendChild(row);
    fmt();
  });

  var playing = false;
  if (playDim) {
    var buttons = document.createElement("div");
    buttons.className = "anim-buttons";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("aria-label", "Play or pause");
    // The book's audio-chip icon geometry (see _ext/icm_audio.py).
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true" class="icm-ic-play">' +
      '<path d="M8 5v14l11-7z"></path></svg>' +
      '<svg viewBox="0 0 24 24" aria-hidden="true" class="icm-ic-pause">' +
      '<rect x="7" y="5" width="3.5" height="14"></rect>' +
      '<rect x="13.5" y="5" width="3.5" height="14"></rect></svg>';
    var icPlay = btn.querySelector(".icm-ic-play");
    var icPause = btn.querySelector(".icm-ic-pause");
    buttons.appendChild(btn);
    controls.appendChild(buttons);
    function setPlaying(v) {
      playing = v;
      btn.title = v ? "Pause" : "Play";  // the Play state fills red (CSS)
      icPlay.style.display = v ? "none" : "block";
      icPause.style.display = v ? "block" : "none";
    }
    btn.addEventListener("click", function () { setPlaying(!playing); });
    setPlaying(!window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  var head = 0, last = null;
  function loop(ts) {
    if (last !== null && playing && playDim) {
      // One sweep takes `period` seconds, scaled by the rate parameter's
      // current value.
      var period = playDim.p.period / (playDim.p.rate ? valueOf(playDim.p.rate) : 1);
      head = (head + (ts - last) / 1000 / period * playDim.n) %% playDim.n;
      var idx = Math.floor(head);
      if (idx !== playDim.idx) { playDim.idx = idx; needsDraw = true; }
    }
    last = ts;
    if (needsDraw) { needsDraw = false; composite(); }
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
"""
