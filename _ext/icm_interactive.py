"""The ``{interactive}`` directive — inline a runnable script, collapsibly.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Authors
mark the full, downloadable script at the end of a section with::

    :::{interactive}[./code/wavetable.py]
    :::

so the verbose script is *inlined* into the page instead of hidden behind a bare
``[code/wavetable.py](./code/wavetable.py)`` download link.

Two layers consume the directive, and they are deliberately complementary:

* ``tools/split_chapters.py`` (``make split``) is the *primary* path. A section
  whose body contains an ``{interactive}`` directive is emitted as a Jupyter
  **notebook** (``.ipynb``) rather than Markdown: the prose becomes Markdown
  cells and the referenced script becomes a single ``code`` cell tagged
  ``hide-input`` (collapsed behind a toggle) and ``skip-execution``. On those
  pages the live-code layer (``_static/live-cells.js`` + thebe-lite) makes the
  cell editable and runnable in the browser. The directive itself never reaches
  Sphinx there — the splitter has already turned it into a real notebook cell.

* this Sphinx directive is the *fallback*. On a plain Markdown page (the
  directives template, or any section that was not split into a notebook) it
  renders the same intent statically: a collapsible ``dropdown`` admonition
  holding the script as a syntax-highlighted code block. Markdown pages are not
  notebooks, so the code is shown but not executable — the point is that the
  directive is always valid and never raises an "unknown directive" error.

The single argument is the path to the script. It is written in ``[brackets]``
(mirroring the upstream remark-flavored ``:figure![alt](path)`` style) but a
bare path is accepted too. It is resolved relative to the page's source file.
"""
from __future__ import annotations

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


def parse_interactive_arg(arg: str) -> str:
    """Pull the script path out of an ``{interactive}`` argument.

    Accepts ``[./code/foo.py]`` (the authored bracket form) or a bare
    ``./code/foo.py``. Shared with ``tools/split_chapters.py`` so the splitter
    and this directive agree on what a path looks like.
    """
    arg = arg.strip()
    if arg.startswith("[") and arg.endswith("]"):
        arg = arg[1:-1].strip()
    return arg


class InteractiveDirective(Directive):
    """``:::{interactive}[./code/foo.py]`` — inline a script in a collapsible card."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    has_content = False

    def run(self):
        rel = parse_interactive_arg(self.arguments[0])
        source = self.state.document.get("source")
        if not source:
            return [self._error("`interactive` could not locate the page source.")]
        script = (Path(source).parent / rel).resolve()
        try:
            code = script.read_text()
        except OSError as exc:
            return [self._error(f"`interactive` cannot read `{rel}`: {exc}")]

        name = Path(rel).name
        # A collapsible card built from the theme's `dropdown` admonition (the
        # same `<details>` mechanism authors get from `:class: dropdown`), so the
        # existing admonition/toggle CSS styles it with no new rules. Collapsed
        # by default — it is a reference appendix, not part of the reading flow.
        card = nodes.admonition("", classes=["dropdown", "interactive-code"])
        card += nodes.title("", f"Full script: {name}")
        block = nodes.literal_block(code, code)
        block["language"] = "python"
        block["classes"].append("interactive-code-block")
        card += block
        return [card]

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
