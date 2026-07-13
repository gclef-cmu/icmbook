"""House plotly styling and page plumbing for interactive widget cells.

Importing this module registers the book's "icm" plotly template and makes it
the default, so widget cells never carry styling blocks. `show(build)` is the
one display path: it runs the cell's widget-building function everywhere
except the book build, where instantiating any ipywidgets model would bake
inert multi-MB widget-state JSON into the page.

Ships with the book: installed in the build environment (environment.yml) and
in the browser kernel (_static/wheels via `make wheels`), so notebook cells
never pip-install it.
"""

import os

import plotly.graph_objects as go
import plotly.io as pio

# The palette's single source of truth is icm_widgets (icm_anim shares it);
# re-exported here so widget cells import one module. icm_widgets ships
# everywhere this module does (wheels manifest + environment.yml).
from icm_widgets import BLUE, GOLD, IRON, RED, STEEL, TEAL  # noqa: F401

__all__ = ["show", "RED", "BLUE", "GOLD", "IRON", "TEAL", "STEEL"]

# House axis look: single grey spine, outside ticks, no grid — the plotly
# counterpart of the matplotlib house style.
_AXIS = dict(
    showline=True,
    linecolor="#6D6E71",
    linewidth=1,
    ticks="outside",
    tickcolor="#6D6E71",
    tickfont=dict(color="#3b3b3b"),
    title_font_color="#3b3b3b",
    title_font_size=12,
    title_standoff=12,
    zeroline=False,
    mirror=False,
    showgrid=False,
)

pio.templates["icm"] = go.layout.Template(
    layout=go.Layout(
        font=dict(size=12, color="#3b3b3b"),
        margin=dict(l=50, r=50, t=50, b=50),
        # Off by default: the widgets' traces are color-coded and hover
        # shows names; plotly's legends clip or overlap in narrow columns.
        # A figure that opts back in (showlegend=True) gets a horizontal
        # legend above the plot, clear of the right margin.
        showlegend=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
        xaxis=_AXIS,
        yaxis=_AXIS,
        xaxis2=_AXIS,
        yaxis2=_AXIS,
        plot_bgcolor="white",
        paper_bgcolor="white",
        # Zoom/select tools are pointless on fixedrange widget axes; the book
        # pages hide the whole modebar via CSS, this trims it elsewhere.
        modebar=dict(remove=["zoom", "select2d", "lasso2d", "autoScale2d"]),
        colorway=[
            "#C41230",  # carnegie red
            "#C41230",  # carnegie red (2x)
            "#007BC0",  # highland blue
            "#FDB515",  # gold thread
        ],
    )
)
pio.templates.default = "icm"


def show(figure, controls=None):
    """Render a widget everywhere it can exist — including the static page.

    ``figure()`` builds the visual: a plain ``go.Figure`` (never a
    FigureWidget, never ipywidgets — anything ipywidgets touches at build
    time bakes inert multi-MB widget-state JSON into the page).
    ``controls(fig)`` receives the live ``go.FigureWidget``, wires sliders
    to it, and returns the control widget to display above it.

    At book build only ``figure()`` runs, and the figure is baked into the
    page as inert JSON that live-cells.js renders with the book's vendored
    plotly.js the moment the page opens — no kernel, no wait. On the live
    page (the ``# autorun`` marker boots the kernel) and in VS Code, the
    same figure becomes a FigureWidget with the controls wired, replacing
    the baked one.
    """
    if os.environ.get("ICM_BOOK_BUILD"):
        from IPython.display import HTML, display

        # `</` escaped so the JSON can't close its own script tag.
        payload = figure().to_json().replace("</", "<\\/")
        display(HTML(
            '<div class="icm-plotly-fig">'
            '<script type="application/vnd.icm-plotly+json">'
            + payload + "</script></div>"
        ))
        return
    from IPython.display import display

    fig = go.FigureWidget(figure())
    # _config is private but synced to the frontend by design; responsive
    # turns on plotly.js's ResizeObserver so the figure reflows with its
    # container instead of clipping when the window narrows.
    fig._config = dict(fig._config or {}, responsive=True)
    ui = controls(fig) if controls is not None else None
    if ui is None:
        display(fig)
    else:
        display(ui, fig)
