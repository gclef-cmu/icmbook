"""Group the glossary into A–Z sections with a clickable alphabet bar.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Sphinx's
``{glossary}`` directive renders a single flat definition list; this extension
post-processes that list (at ``doctree-resolved``) so the Glossary page reads
like Sphinx's own back-of-book index (``genindex``):

- entries are split into per-initial-letter groups, each under a big letter
  heading with a stable anchor (``#glossary-letter-a``), and
- a jump bar of A–Z links is prepended, with letters that have no entries
  shown greyed-out and non-clickable.

The transform only *regroups* existing definition-list items — it never edits
their content — so every term keeps its ``term-*`` id and all ``{vocab}``
cross-references continue to resolve. Styling lives in ``_static/custom.css``
(see the GLOSSARY section).
"""
from __future__ import annotations

import string

from docutils import nodes
from sphinx.application import Sphinx

ALPHABET = string.ascii_uppercase
_SYMBOL = "#"  # bucket for terms that don't start with a Latin letter


def _anchor(letter: str) -> str:
    """Stable HTML id for a letter group ('A' -> 'glossary-letter-a')."""
    return "glossary-letter-" + ("symbol" if letter == _SYMBOL else letter.lower())


def _initial(item: nodes.definition_list_item) -> str:
    """Uppercase first letter of an entry's term, or '#' if non-alphabetic."""
    term = item.next_node(nodes.term)
    text = term.astext().strip() if term is not None else ""
    ch = text[0].upper() if text else _SYMBOL
    return ch if ch in ALPHABET else _SYMBOL


def _group_one(dl: nodes.definition_list) -> None:
    """Replace one flat glossary ``<dl>`` with letter-grouped sections + nav."""
    items = [c for c in dl.children if isinstance(c, nodes.definition_list_item)]
    if not items:
        return

    # Bucket items by initial letter, preserving the (already sorted) order.
    groups: dict[str, list[nodes.definition_list_item]] = {}
    for item in items:
        groups.setdefault(_initial(item), []).append(item)

    # Alphabetical letters first, the '#' (symbol) bucket last if present.
    present = [c for c in ALPHABET if c in groups]
    if _SYMBOL in groups:
        present.append(_SYMBOL)
    present_set = set(present)

    new_nodes: list[nodes.Node] = []

    # --- A–Z jump bar -----------------------------------------------------
    # Must be a paragraph (an inline/TextElement context): the HTML writer
    # asserts that a reference in a *block* parent wraps a single image.
    nav = nodes.paragraph(classes=["glossary-nav"])
    for letter in list(ALPHABET) + ([_SYMBOL] if _SYMBOL in groups else []):
        if letter in present_set:
            nav += nodes.reference(
                "", letter, refid=_anchor(letter),
                classes=["glossary-nav-letter"],
            )
        else:
            nav += nodes.inline(
                "", letter, classes=["glossary-nav-letter", "is-empty"],
            )
    new_nodes.append(nav)

    # --- One heading + sub-list per present letter ------------------------
    for letter in present:
        heading = nodes.rubric(
            "", letter, ids=[_anchor(letter)],
            classes=["glossary-letter-heading"],
        )
        new_nodes.append(heading)

        sub = nodes.definition_list(
            classes=["simple", "glossary", "glossary-letter-group"]
        )
        for item in groups[letter]:
            sub += item  # reparents; the old dl is discarded below
        new_nodes.append(sub)

    dl.replace_self(new_nodes)


def group_glossary(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    for dl in list(doctree.findall(nodes.definition_list)):
        if "glossary" in dl.get("classes", []):
            _group_one(dl)


def setup(app: Sphinx) -> dict:
    app.connect("doctree-resolved", group_glossary)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
