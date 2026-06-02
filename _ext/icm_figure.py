"""Custom ``figure`` directive accepting the upstream simple form.

Overrides the stock docutils/MyST ``figure`` so a figure can be authored as
just an image and a caption — matching the icm-text source — while staying
fully backward-compatible with the standard ``:::{figure} path`` + options
form already used in chapters 0–2 and the templates.

Simple form (no argument; the first body line is the image, either a plain
Markdown image or the upstream ``:figure`` role prefix)::

    :::{figure}
    ![alt text](./assets/x.png)

    The caption.
    :::

Standard form (path argument + options) is untouched and keeps working::

    :::{figure} ./assets/x.png
    :width: 80%
    :name: fig-x

    The caption.
    :::

Registered via ``local_extensions`` in ``_config.yml`` (``override=True``). The
split tool braces a simple upstream ``:::figure`` to ``:::{figure}`` only when
its next line is an image, so grid/audio figures stay untouched.
"""
from __future__ import annotations

import re

from sphinx.application import Sphinx
from sphinx.directives.patches import Figure  # Sphinx's Figure: adds :name:/numfig

# First body line of the simple form: a Markdown image, optionally carrying the
# upstream ``:figure`` role prefix — ``![alt](path)`` or ``:figure![alt](path)``.
_IMAGE_RE = re.compile(
    r"^\s*(?::figure)?!\[(?P<alt>[^\]]*)\]\(\s*(?P<path>\S+?)\s*\)\s*$"
)


class SimpleFigure(Figure):
    """``figure`` that also accepts an image as its first body line."""

    required_arguments = 0
    optional_arguments = 1

    def run(self):
        if not self.arguments:
            # No path argument → expect the image as the first body line.
            index = next(
                (i for i, line in enumerate(self.content) if line.strip()), None
            )
            match = _IMAGE_RE.match(self.content[index]) if index is not None else None
            if match is None:
                return [
                    self.state_machine.reporter.error(
                        "`figure` directive needs a path argument or a Markdown "
                        "image as its first line, e.g. `![alt](./assets/x.png)`.",
                        line=self.lineno,
                    )
                ]
            self.arguments = [match.group("path")]
            if match.group("alt"):
                self.options.setdefault("alt", match.group("alt"))
            # Drop the image line (and the blank line after it) so the rest of
            # the content becomes the caption.
            del self.content[index]
            while index < len(self.content) and not self.content[index].strip():
                del self.content[index]
        return super().run()


def setup(app: Sphinx) -> dict:
    app.add_directive("figure", SimpleFigure, override=True)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
