"""Custom inline primitives: ``{vocab}`` and ``{unit}``.

``{vocab}`term``` italicizes a term and links it to its glossary entry.

``{unit}`num``` / ``{unit}`num,denom``` typesets a unit or a unit fraction
(comma or slash both separate). It is not a docutils role — it expands to raw
LaTeX as a ``source-read`` substitution, because MyST never processes roles
inside ``$…$``/``$$…$$`` math. Wrap it in ``$…$`` inline or drop it into a
math block; fenced code blocks are skipped so examples render literally.
"""
from __future__ import annotations

import json
import re

from docutils import nodes
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole


class VocabRole(SphinxRole):
    """``{vocab}`term``` — an italic link to the term's glossary entry.

    An unknown term warns at build time, keeping glossary and prose in sync.
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


# ``{unit}`…``` with an argument; a bare ``{unit}`` mention (as in docs about
# the feature) is left untouched.
UNIT_RE = re.compile(r"\{unit\}`([^`]+)`")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def _unit_latex(arg: str) -> str:
    """Render a ``{unit}`` argument as raw LaTeX (no surrounding math mode)."""
    parts = [p.strip() for p in re.split(r"[,/]", arg)]
    if len(parts) >= 2 and parts[1]:
        return r"\frac{\text{%s}}{\text{%s}}" % (parts[0], parts[1])
    return r"\text{%s}" % parts[0]


def _expand_text(text: str) -> str:
    """Expand every ``{unit}`…``` in Markdown text, outside code fences."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
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
    return "".join(out)


def substitute_units(app: Sphinx, docname: str, source: list[str]) -> None:
    """``source-read`` handler: expand ``{unit}`…``` to raw LaTeX.

    Markdown pages are rewritten directly. Notebooks arrive as raw .ipynb
    JSON that myst-nb decodes again after us — splicing LaTeX into the JSON
    text would let that second decode mangle the backslashes (``\\frac`` →
    form-feed + ``rac``). So decode, expand each Markdown cell, re-encode,
    and let ``json.dumps`` escape the LaTeX correctly.
    """
    text = source[0]
    if str(app.env.doc2path(docname)).endswith(".ipynb"):
        try:
            nb = json.loads(text)
        except ValueError:
            source[0] = _expand_text(text)
            return
        for cell in nb.get("cells", []):
            if cell.get("cell_type") != "markdown":
                continue
            cell_src = cell.get("source", "")
            joined = "".join(cell_src) if isinstance(cell_src, list) else cell_src
            cell["source"] = _expand_text(joined)
        source[0] = json.dumps(nb)
    else:
        source[0] = _expand_text(text)


def setup(app: Sphinx) -> dict:
    app.add_role("vocab", VocabRole())
    app.connect("source-read", substitute_units)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
