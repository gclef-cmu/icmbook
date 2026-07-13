"""icm_widgets — the book's plot palette (Carnegie Mellon's colors).

One source of truth for color meaning across every drawing tool the book
uses — plotly widgets (via ``icm_plotly``), manim scenes (via ``icm_anim``),
and any static matplotlib figure::

    from icm_widgets import RED, BLUE, GOLD, IRON, TEAL, STEEL

The matplotlib widget machinery that used to live here (``ParamPlayer``,
``house_style``) was retired when interactive widgets moved to plotly — see
the Interactive template and ``tools/icm_plotly``.
"""
from __future__ import annotations

__version__ = "0.5.0"
__all__ = ["RED", "BLUE", "GOLD", "IRON", "TEAL", "STEEL"]

# Import the names instead of pasting hex codes.
RED, BLUE, GOLD, IRON, TEAL, STEEL = (
    "#C41230", "#007BC0", "#FDB515", "#6D6E71", "#008F91", "#E0E0E0",
)
