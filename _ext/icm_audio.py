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
_ROLE_RE = re.compile(r"^(?P<label>.*?)\s*<(?P<url>[^>\s]+)>\s*$")


class AudioDirective(Directive):
    """``:::{audio}`` — a captioned audio clip.

    Body: a Markdown link to the clip on the first non-blank line, then an
    optional caption. Renders a clean ``audio-block`` card — a large round
    play/pause button (the same control as the inline ``{audio}`` role) beside
    the caption — instead of the old "🔊 Listen" admonition.
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

        block = nodes.container()
        block["classes"] = ["audio-block"]
        # The big play/pause button — same chip control as the inline role, so
        # _static/audio-chip.js wires it and the styling stays consistent.
        block += nodes.raw("", _chip_button(src, label, "audio-chip-lg"), format="html")

        # The caption (everything after the link line) sits beside the button,
        # parsed as Markdown so math, emphasis, and links render normally.
        body = nodes.container()
        body["classes"] = ["audio-block-body"]
        caption = content[link_index + 1 :]
        if any(line.strip() for line in caption):
            self.state.nested_parse(
                caption, self.content_offset + link_index + 1, body
            )
        else:
            body += nodes.inline("", label)  # fall back to the link text
        block += body

        return [block]

    def _error(self, message: str):
        error = self.state_machine.reporter.error(
            message,
            nodes.literal_block(self.block_text, self.block_text),
            line=self.lineno,
        )
        return error


# A round play/pause button. The play triangle and pause bars are both present;
# CSS shows one based on the `is-playing` class that _static/audio-chip.js
# toggles. Shared by the inline {audio} role and the block {audio} directive
# (the block passes ``audio-chip-lg`` for a larger button).
def _chip_button(src: str, label: str, extra_class: str = "") -> str:
    cls = "audio-chip" + (f" {extra_class}" if extra_class else "")
    label = escape(label, quote=True)
    return (
        f'<button type="button" class="{cls}" '
        f'data-audio-src="{escape(src, quote=True)}" '
        f'aria-label="Play {label}" title="{label}">'
        # Progress ring (the button's circular outline). r=15.9155 → circumference
        # 100, so audio-chip.js sets `stroke-dashoffset = 100 − percent`.
        '<svg class="audio-chip-ring" viewBox="0 0 36 36" aria-hidden="true">'
        '<circle class="acr-track" cx="18" cy="18" r="15.9155"></circle>'
        '<circle class="acr-fill" cx="18" cy="18" r="15.9155"></circle>'
        "</svg>"
        '<svg class="audio-chip-icon" viewBox="0 0 24 24" aria-hidden="true">'
        '<path class="ac-play" d="M8 5v14l11-7z"></path>'
        '<g class="ac-pause"><rect x="7" y="5" width="3.5" height="14"></rect>'
        '<rect x="13.5" y="5" width="3.5" height="14"></rect></g>'
        "</svg></button>"
    )


def _label_nodes(label: str) -> list:
    """Render the visible label, turning ``$…$`` segments into inline math."""
    out: list = []
    for i, seg in enumerate(re.split(r"\$([^$]+)\$", label)):
        if i % 2:  # the bit between a pair of `$` → inline math
            out.append(nodes.math(text=seg))
        elif seg:
            out.append(nodes.Text(seg))
    return out


class AudioRole(SphinxRole):
    """``{audio}`label <url>``` — a compact *inline* play button + label.

    The block ``{audio}`` directive above is a full "🔊 Listen" callout; this
    inline counterpart drops a small round play/pause button mid-flow or inside
    an ``audio-figure``/``audio-list``/``audio-board`` group, followed by the
    **visible label** (``$…$`` in the label renders as math). So the button
    always comes first and the label is self-contained — no separate text is
    needed next to it. Behavior is wired by ``_static/audio-chip.js``, styling
    by ``_static/custom.css``.

    Upstream authors it as ``:audio[label](url)`` (+ a descriptive label line or
    trailing text); the split tool folds that into ``{audio}`label <url>```.
    """

    def run(self):
        match = _ROLE_RE.match(self.text.strip())
        if match:
            label, url = match.group("label").strip(), match.group("url").strip()
        else:
            label, url = "", self.text.strip()
        # The aria/tooltip name is the plain label (drop `$` math delimiters).
        aria = re.sub(r"\$([^$]+)\$", r"\1", label).strip() or "audio clip"
        button = nodes.raw("", _chip_button(url, aria), format="html")
        return [button, *_label_nodes(label)], []


def setup(app: Sphinx) -> dict:
    app.add_directive("audio", AudioDirective)
    app.add_role("audio", AudioRole())
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
