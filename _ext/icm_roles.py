"""Custom inline primitives for the textbook.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Provides
the two book-specific primitives that have no native MyST equivalent:

- ``{vocab}`term``` — italicize a vocabulary term (CSS class ``vocab``) and add
  it to the book's global index (genindex). Implemented as a docutils role.
- ``{unit}`num``` / ``{unit}`num,denom``` — typeset units in a common form. One
  argument renders a single unit (``\\text{num}``); two render a fraction
  (``\\frac{\\text{num}}{\\text{denom}}``). The numerator and denominator may be
  separated by a comma or a slash, so ``{unit}`cycles,second``` and
  ``{unit}`cycles/second``` are equivalent.

``{unit}`` is **not** a docutils role: it expands to *raw LaTeX* and does not
inject math mode, so it composes with the surrounding math. Wrap it in ``$…$``
to use it inline (``${unit}`cycles,second`$``) or drop it unwrapped into a
``$$…$$`` block. The expansion runs as a ``source-read`` text substitution
before MyST parses the page, skipping fenced code blocks so that ``{unit}``
*examples* in the templates render literally. (A docutils role could not do
this: MyST never processes roles inside ``$…$``/``$$…$$`` math, so a role could
never be used in block latex.)

Authoring note: MyST does not support the ``:role[text]`` syntax from the
CommonMark generic-directives proposal, so ``{vocab}`` is authored as a MyST
role: ``{vocab}`periodic```.
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


# ``{unit}`num``` or ``{unit}`num,denom```. Matches a single-backtick argument;
# the lone ``{unit}`` mention (no argument) used when *documenting* the feature
# carries no trailing argument and so is intentionally left untouched.
UNIT_RE = re.compile(r"\{unit\}`([^`]+)`")
# A line that opens or closes a fenced code block (``` or ~~~, length >= 3).
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def _unit_latex(arg: str) -> str:
    """Render a ``{unit}`` argument as raw LaTeX (no surrounding math mode)."""
    parts = [p.strip() for p in re.split(r"[,/]", arg)]
    if len(parts) >= 2 and parts[1]:
        return r"\frac{\text{%s}}{\text{%s}}" % (parts[0], parts[1])
    return r"\text{%s}" % parts[0]


def substitute_units(app: Sphinx, docname: str, source: list[str]) -> None:
    """Expand ``{unit}`…``` to raw LaTeX in page source, outside code fences.

    Sphinx ``source-read`` handler. Walks the source line by line, tracking
    fenced code blocks (the same way ``tools/split_chapters.py`` does) so that
    ``{unit}`` examples shown inside ```` ```markdown ```` fences are left
    verbatim, and rewrites every other occurrence in place.
    """
    out: list[str] = []
    fence: str | None = None
    for line in source[0].splitlines(keepends=True):
        if fence is None:
            fm = FENCE_RE.match(line)
            if fm:
                fence = fm.group(1)
                out.append(line)
                continue
            out.append(UNIT_RE.sub(lambda m: _unit_latex(m.group(1)), line))
        else:
            out.append(line)
            stripped = line.strip()
            if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                fence = None
    source[0] = "".join(out)


def setup(app: Sphinx) -> dict:
    app.add_role("vocab", VocabRole())
    app.connect("source-read", substitute_units)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
