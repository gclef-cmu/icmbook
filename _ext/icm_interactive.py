"""The ``{interactive}`` directive — embed a runnable notebook in a section.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Authors
drop a companion notebook into a section with::

    :::{interactive}[notebooks/fourier-winding.ipynb]
    :::

and its cells are embedded inline. Each code cell's source visibility is set by a
whole-line ``# hide`` / ``# collapse`` / ``# show`` marker (case-insensitive,
first wins; the marker is an ordinary comment and stays in the source):
``# hide`` removes the source from view entirely (only the output shows),
``# collapse`` tucks it behind a collapsed "Show setup" bar, ``# show`` or no
marker leaves it visible. Hide every code cell and only the outputs remain.

Two layers consume the directive, and they are deliberately complementary:

* ``tools/split_chapters.py`` (``make split``) is the *primary* path. A section
  whose body contains an ``{interactive}`` directive is emitted as a Jupyter
  **notebook** (``.ipynb``): the surrounding prose becomes Markdown cells and the
  referenced notebook's cells are spliced in (markdown -> prose, code -> live
  cells, ``# hide`` ones tagged ``icm-hide-input``, ``# collapse`` ones
  ``hide-input``). The cells build-execute
  (``execute_notebooks: auto``) so their output is baked into the page, and the
  live-code layer (``_static/live-cells.js`` + thebe-lite) keeps them runnable.
  The directive itself never reaches Sphinx there — the splitter has already
  turned it into real notebook cells.

* this Sphinx directive is the *fallback*. On a plain Markdown page (any section
  not split into a notebook) it renders the notebook statically: each markdown
  cell as prose and each visible code cell as a code block, with no outputs. The
  point is that the directive is always valid and never raises an "unknown
  directive" error.

The single argument is the path to the ``.ipynb``. It is written in ``[brackets]``
(mirroring the upstream remark-flavored ``:figure![alt](path)`` style) but a bare
path is accepted too. It is resolved relative to the page's source file.
"""
from __future__ import annotations

import re
from pathlib import Path

import nbformat
from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import StringList
from sphinx.application import Sphinx


def parse_interactive_arg(arg: str) -> str:
    """Pull the notebook path out of an ``{interactive}`` argument.

    Accepts ``[notebooks/foo.ipynb]`` (the authored bracket form) or a bare
    ``notebooks/foo.ipynb``. Shared with ``tools/split_chapters.py`` so the
    splitter and this directive agree on what a path looks like.
    """
    arg = arg.strip()
    if arg.startswith("[") and arg.endswith("]"):
        arg = arg[1:-1].strip()
    return arg


# Kept in lockstep with ``tools/split_chapters.py``: a notebook code cell's
# visibility is set by a whole-line `# hide` / `# collapse` / `# show` marker
# (case-insensitive, first wins; the marker stays in the source — it is just
# a comment).
VISIBILITY_MARKER_RE = re.compile(r"^#\s*(hide|collapse|show)\s*$", re.IGNORECASE)


def cell_visibility(source: str) -> str:
    """Return ``"hide"``, ``"collapse"`` or ``"show"`` for a notebook code cell."""
    for line in source.splitlines():
        m = VISIBILITY_MARKER_RE.match(line.strip())
        if m:
            return m.group(1).lower()
    return "show"


class InteractiveDirective(Directive):
    """``:::{interactive}[notebooks/foo.ipynb]`` — embed a runnable notebook in the page."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        rel = parse_interactive_arg(self.arguments[0])
        source = self.state.document.get("source")
        if not source:
            return [self._error("`interactive` could not locate the page source.")]
        target = (Path(source).parent / rel).resolve()
        if target.suffix != ".ipynb":
            return [self._error(f"`interactive` expects a .ipynb notebook, got `{rel}`.")]
        return self._render_notebook(target, rel)

    def _render_notebook(self, path: Path, rel: str):
        """``.ipynb`` target — *fallback only*.

        The real book never reaches this branch: ``tools/split_chapters.py``
        expands a notebook directive into actual notebook cells before Sphinx
        sees the page. This just keeps a plain-Markdown build of the unsplit
        source from erroring — it renders each markdown cell as prose and each
        visible (`# show` / unmarked) code cell as a static block; `# hide`
        and `# collapse` cells are skipped (no collapsing UI exists here). No outputs
        exist here; the executed animation only appears via the split notebook.
        """
        try:
            nb = nbformat.read(str(path), as_version=4)
        except OSError as exc:
            return [self._error(f"`interactive` cannot read `{rel}`: {exc}")]

        out: list[nodes.Node] = []
        for c in nb.cells:
            if c.cell_type == "markdown":
                container = nodes.container()
                self.state.nested_parse(StringList(c.source.splitlines()), 0, container)
                out += container.children
            elif c.cell_type == "code":
                code = c.source
                if cell_visibility(code) != "show" or not code.strip():
                    continue
                block = nodes.literal_block(code, code)
                block["language"] = "python"
                block["classes"].append("interactive-code-block")
                out.append(block)
        return out

    def _error(self, message: str):
        return self.state_machine.reporter.error(
            message,
            nodes.literal_block(self.block_text, self.block_text),
            line=self.lineno,
        )


def setup(app: Sphinx) -> dict:
    app.add_directive("interactive", InteractiveDirective)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
