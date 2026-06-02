"""Custom ``audio`` directive for the textbook.

Registered via Jupyter Book's ``local_extensions`` in ``_config.yml``. Gives
authors a clean, semantic way to embed a short audio clip with a caption,
replacing the verbose ``{admonition} 🔊 Listen`` + ``:class: note listen`` +
raw ``<audio>`` pattern.

Authoring syntax mirrors the upstream ``icm-text`` source (the professor's
remark-flavored ``:::audio``) so the body is identical across both renderers —
only the fence marker differs (``:::audio`` there, ``:::{audio}`` here, which
the split/merge tooling bridges). The first line of the body is a Markdown
link whose target is the audio file and whose text describes the clip; any
remaining content is the caption::

    :::{audio}
    [A 440 Hz sine tone](./assets/audio-sine-440.wav)

    A 440 Hz sine tone, one second long.
    :::

This renders the same DOM as the old hand-written callout — an
``.admonition.note.listen`` with a "🔊 Listen" title, an ``<audio controls>``
player, and the caption — so the existing ``listen`` CSS in
``_static/custom.css`` styles it unchanged. The link text is preserved as the
player's ``aria-label`` and as a download fallback for browsers without
``<audio>`` support.
"""
from __future__ import annotations

import re
from html import escape

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxRole

# Matches a single Markdown inline link: [text](target). The target stops at
# the first whitespace so an optional "title" after the URL is ignored.
_LINK_RE = re.compile(r"^\s*\[(?P<text>.+?)\]\(\s*(?P<href>\S+?)\s*\)\s*$")
# Role content for the inline {audio}: ``label <url>`` (Sphinx link convention),
# or just ``url`` if no angle-bracketed target is given.
_ROLE_RE = re.compile(r"^(?P<label>.*?)\s*<(?P<url>[^>]+)>\s*$")


class AudioDirective(Directive):
    """``:::{audio}`` — a captioned audio player.

    Body: a Markdown link to the clip on the first non-blank line, then an
    optional caption. See the module docstring for the full contract.
    """

    has_content = True

    def run(self):
        content = self.content
        # Locate the link line (the first non-blank line of the body).
        link_index = next(
            (i for i, line in enumerate(content) if line.strip()), None
        )
        if link_index is None:
            return [self._error("`audio` directive requires a link to the clip.")]

        match = _LINK_RE.match(content[link_index])
        if match is None:
            return [
                self._error(
                    "`audio` directive's first line must be a Markdown link, "
                    "e.g. `[A 440 Hz sine tone](./assets/tone.wav)`."
                )
            ]
        label, src = match.group("text").strip(), match.group("href").strip()

        admonition = nodes.admonition()
        admonition["classes"] = ["note", "listen"]
        admonition += nodes.title("", "🔊 Listen")

        player = (
            f'<audio controls src="{escape(src, quote=True)}" '
            f'aria-label="{escape(label, quote=True)}">'
            f'<a href="{escape(src, quote=True)}">{escape(label)}</a>'
            f"</audio>"
        )
        admonition += nodes.raw("", player, format="html")

        # Everything after the link line is the caption; parse it as Markdown
        # so math, emphasis, and links inside it render normally.
        caption = content[link_index + 1 :]
        if any(line.strip() for line in caption):
            self.state.nested_parse(
                caption, self.content_offset + link_index + 1, admonition
            )

        return [admonition]

    def _error(self, message: str):
        error = self.state_machine.reporter.error(
            message,
            nodes.literal_block(self.block_text, self.block_text),
            line=self.lineno,
        )
        return error


# A small round play/pause button. The play triangle and pause bars are both
# present; CSS shows one or the other based on the `is-playing` class that
# _static/audio-chip.js toggles. Filled at render time with src + label.
_CHIP_HTML = (
    '<button type="button" class="audio-chip" data-audio-src="{src}"'
    ' aria-label="Play {label}" title="{label}">'
    '<svg class="audio-chip-icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path class="ac-play" d="M8 5v14l11-7z"></path>'
    '<g class="ac-pause"><rect x="7" y="5" width="3.5" height="14"></rect>'
    '<rect x="13.5" y="5" width="3.5" height="14"></rect></g>'
    "</svg></button>"
)


class AudioRole(SphinxRole):
    """``{audio}`label <url>``` — a compact *inline* play button.

    The block ``{audio}`` directive above is a full "🔊 Listen" callout; this
    inline counterpart drops a small round play/pause button mid-flow or inside
    an ``audio-figure`` grid (e.g. next to a waveform image). The descriptive
    label becomes the button's ``aria-label``/tooltip — the visible label comes
    from the surrounding text. Behavior is wired by ``_static/audio-chip.js``,
    styling by ``_static/custom.css``.

    Upstream authors it as ``:audio[label](url)``; the split tool rewrites that
    to the MyST role form ``{audio}`label <url>```.
    """

    def run(self):
        match = _ROLE_RE.match(self.text.strip())
        if match:
            label, url = match.group("label").strip(), match.group("url").strip()
        else:
            label, url = "", self.text.strip()
        html = _CHIP_HTML.format(
            src=escape(url, quote=True), label=escape(label, quote=True)
        )
        return [nodes.raw("", html, format="html")], []


def setup(app: Sphinx) -> dict:
    app.add_directive("audio", AudioDirective)
    app.add_role("audio", AudioRole())
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
