"""Custom inline roles for the textbook.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Provides
the two book-specific primitives that have no native MyST equivalent:

- ``{vocab}`term``` — italicize a vocabulary term (CSS class ``vocab``) and add
  it to the book's global index (genindex).
- ``{unit}`num``` / ``{unit}`num,denom``` — typeset units in a common form as
  inline math. One argument renders a single unit; two render a fraction. The
  numerator and denominator may be separated by a comma or a slash, so
  ``{unit}`cycles,second``` and ``{unit}`cycles/second``` are equivalent.

Authoring note: MyST does not support the ``:role[text]`` syntax from the
CommonMark generic-directives proposal, so these are authored as MyST roles:
``{vocab}`periodic``` and ``{unit}`cycles,second```.
"""
from __future__ import annotations

import re

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole


class VocabRole(SphinxRole):
    """``{vocab}`term``` — italicize a term and link it to its glossary entry.

    Emits a cross-reference to a ``{glossary}`` term (Sphinx's ``std:term``).
    The glossary supplies the definition *and* the global-index entry, so the
    term renders as an italic link to its definition. An unknown term warns at
    build time, which keeps the glossary and prose in sync.
    """

    def run(self):
        term = self.text.strip()
        inner = nodes.emphasis(self.rawtext, term, classes=["vocab"])
        refnode = addnodes.pending_xref(
            self.rawtext,
            inner,
            refdomain="std",
            reftype="term",
            reftarget=term,
            refexplicit=False,
            refwarn=True,
        )
        self.set_source_info(refnode)
        return [refnode], []


class UnitRole(SphinxRole):
    """``{unit}`num``` or ``{unit}`num,denom``` — typeset units as inline math.

    The numerator and denominator may be separated by a comma or a slash, so
    ``{unit}`cycles,second``` and ``{unit}`cycles/second``` both render as the
    fraction ``\\frac{cycles}{second}``.
    """

    def run(self):
        parts = [p.strip() for p in re.split(r"[,/]", self.text)]
        if len(parts) >= 2 and parts[1]:
            latex = r"\frac{\text{%s}}{\text{%s}}" % (parts[0], parts[1])
        else:
            latex = r"\text{%s}" % parts[0]
        return [nodes.math(self.rawtext, latex)], []


def setup(app: Sphinx) -> dict:
    app.add_role("vocab", VocabRole())
    app.add_role("unit", UnitRole())
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
