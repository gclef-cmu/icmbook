#!/usr/bin/env python3
"""Split each icm-text/{n}-{slug}/index.md into per-section files under content/ch{nn}/.

Treats the `icm-text/` git submodule (the pinned ground-truth prose repo) as
the source of truth. For each chapter folder:
  - Parses the chapter number from the folder-name prefix (e.g. "2-foo" -> 2).
  - Strips YAML frontmatter and pulls the chapter title from the first `# ` heading.
  - Splits the body on `## ` headings, respecting fenced code blocks so that
    `#`-comments inside ```python``` blocks aren't mistaken for headings.
  - Writes content/ch{nn}/index.md containing `# {n}. {title}` plus the intro
    paragraphs that appeared before the first `## ` section.
  - Writes content/ch{nn}/{ii}.md for each section, demoting every heading one
    level (## -> #, ### -> ##, ...) and prefixing the leading heading with
    `{chapter}.{section_index}`.
  - Copies the chapter's assets/, code/, and figures/ subdirs across so relative
    `./assets/...` links in the source still resolve in the generated tree.
  - Regenerates the chapter parts block of _toc.yml in place.

Run via `make split`. WARNING: this wipes content/ch*/ and regenerates it from
icm-text/, dropping any local styling overrides — review `git diff content/`
afterward. Generated content/ch*/ directories are gitignored.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE = REPO / "icm-text"  # ground-truth prose, pinned git submodule
CONTENT = REPO / "content"
TOC = REPO / "_toc.yml"

CHAPTER_FOLDER_RE = re.compile(r"^(\d+)-(.+)$")
FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
# Upstream remark-style block directives `:::name` / `:::name[arg]` → MyST
# `:::{myst} arg`. Maps each upstream name to its MyST directive; the optional
# `[arg]` becomes the directive's argument (e.g. the definition/example title).
#   audio       — the book's {audio} directive (_ext/icm_audio.py)
#   definition  — {prf:definition} (sphinx-proof)
#   example     — {prf:example}    (sphinx-proof)
#   aside       — {note}           (a skippable aside)
#   tip         — {tip}
#   exercise    — {exercise}       (sphinx-exercise)
# `figure` is handled separately (SIMPLE_FIGURE_RE) since it carries an image.
_BLOCK_DIRECTIVE_MAP = {
    "audio": "audio",
    "definition": "prf:definition",
    "example": "prf:example",
    "aside": "note",
    "tip": "tip",
    "exercise": "exercise",
}
BLOCK_DIRECTIVE_RE = re.compile(
    r"^(\s*)(:{3,})(" + "|".join(_BLOCK_DIRECTIVE_MAP) + r")(?:\[([^\]]*)\])?\s*$"
)
# sphinx-proof auto-labels (definition-0, …) restart at 0 in each split section
# file and collide across them. Give these titled directives a stable, unique
# `:label:` (prefix + slugified title) so the build doesn't warn and they stay
# cross-referenceable.
_LABELED_DIRECTIVES = {"prf:definition": "def", "prf:example": "ex"}
# Simple figure: a `:::figure` block whose next line is a single image — either
# a plain Markdown image `![alt](path)` or the role form `:figure![alt](path)`.
# We only brace the opener (`:::figure` → `:::{figure}`) and leave the image and
# caption as-is; the custom {figure} directive (_ext/icm_figure.py) reads the
# image from its first body line. The image-line lookahead means grid / audio
# figures (whose next line is math or `:audio`, not an image) DON'T match and
# stay brace-less — they depend on the still-deferred inline `:audio` pattern.
SIMPLE_FIGURE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<colons>:{3,})figure[ \t]*\n"
    r"(?P=indent)(?::figure)?(?P<image>!\[[^\]]*\]\([^)\s]+\))[ \t]*\n",
    re.MULTILINE,
)
# Upstream remark-style inline roles `:name[content]` → MyST `` {name}`content` ``.
# Only the names listed here are translated (others are left untouched). Both
# roles are defined in _ext/icm_roles.py:
#   unit  — renders a unit fraction; works in prose only, not inside `$…$`/`$$…$$`
#           math (a markdown role can't be parsed there).
#   vocab — italicizes a term and links it to its Glossary entry; the term must
#           be defined in content/glossary.md or the build warns.
_INLINE_ROLE_NAMES = ("unit", "vocab")
INLINE_ROLE_RE = re.compile(r":(" + "|".join(_INLINE_ROLE_NAMES) + r")\[([^\]]+)\]")
# The {audio} role now renders its OWN label (after the button), so each clip's
# descriptive label — a formula line above an audio-figure item, or the trailing
# text on an audio-list/board item — is FOLDED into the role and the now-
# redundant bracket label is dropped. Run after CONTAINER_BLOCK_RE (which still
# needs the raw `:audio[`/`![` to classify) and before the inline pass.
# We keep the concise BRACKET label (`:audio[label]`) — the "label" — and drop
# the redundant descriptive text beside it (a formula line above, or trailing
# text), since the role now renders the bracket label itself.
#   audio-figure item: `<formula line>⏎:audio[label](url) :figure![alt](img)`
#       → `{audio}`label <url>` ![alt](img)`  (formula line dropped)
AUDIO_FIGURE_ITEM_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?![ \t]*(?::audio|:figure|!\[|:::|\{|>|#))"
    r"\S[^\n]*?[ \t]*\n"
    r"(?P=indent):audio\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+)\)[ \t]+"
    r":figure!\[(?P<alt>[^\]]*)\]\((?P<img>[^)\s]+)\)[ \t]*$",
    re.MULTILINE,
)
#   audio-list / audio-board item: `:audio[label](url) <trailing text>`
#       → `{audio}`label <url>``  (trailing text dropped)
AUDIO_TRAILING_RE = re.compile(
    r":audio\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+)\)[ \t]+(?!:figure\b)\S[^\n]*?[ \t]*$",
    re.MULTILINE,
)
# Any remaining bare `:audio[label](url)` (no descriptive label) → role with the
# bracket label. Distinct from the BLOCK `:::audio` opener (no `[`).
AUDIO_INLINE_RE = re.compile(r":audio\[(?P<label>[^\]]*)\]\((?P<url>[^)\s]+)\)")
# Inline figure image `:figure![alt](path)` → plain Markdown image `![alt](path)`
# (an inline `<img>`); used inside audio-figure grids to pair a clip with its
# waveform. Just strips the `:figure` role prefix.
FIGURE_INLINE_RE = re.compile(r":figure(?P<image>!\[[^\]]*\]\([^)\s]+\))")
# A whole `:::figure … :::` block left brace-less after SIMPLE_FIGURE_RE — i.e.
# one that GROUPS clips (inline `:audio`/images/labels) rather than holding a
# single image. We rename the wrapper so MyST's colon_fence renders it as a
# styled div, and pick the class by content so each gets its ideal layout
# (all defined in `_static/custom.css`):
#   • per-item images — every clip paired with its OWN waveform (each `:audio`
#     and image on the same line) → `audio-figure`: narrow columns, side-by-side
#     comparison.
#   • shared image — several clips above ONE combined plot (the image is on its
#     own line, no `:audio`) → `audio-board`: clip buttons in a centered row,
#     the plot full-width below.
#   • no image — clips + text labels → `audio-list`: wider columns, one-line
#     labels.
CONTAINER_BLOCK_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<colons>:{3,})figure[ \t]*\n"
    r"(?P<body>.*?)"
    r"^(?P=indent)(?P=colons)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)


def _container_sub(m: re.Match) -> str:
    body = m["body"]
    if "![" not in body:
        cls = "audio-list"
    elif any("![" in ln and ":audio[" not in ln for ln in body.splitlines()):
        cls = "audio-board"  # clips share one combined plot (a standalone image)
    else:
        cls = "audio-figure"  # each clip paired with its own waveform image
    return f"{m['indent']}{m['colons']}{cls}\n{body}{m['indent']}{m['colons']}"


def _audio_figure_item_sub(m: re.Match) -> str:
    # Fold the label line into the role (dropping the bracket label); keep the
    # image. The role renders the label after the button.
    return f"{m['indent']}{{audio}}`{m['label']} <{m['url']}>` ![{m['alt']}]({m['img']})"


def _audio_trailing_sub(m: re.Match) -> str:
    # Fold the trailing text into the role as its label (dropping the bracket).
    return f"{{audio}}`{m['label']} <{m['url']}>`"


def _simple_figure_sub(m: re.Match) -> str:
    # Brace the opener and normalize the image to a plain Markdown image (drop
    # any `:figure` role prefix, which MyST would otherwise misread as a
    # directive option since it starts with `:`). Keep the image line's trailing
    # newline so the blank line before the caption is preserved.
    return f"{m['indent']}{m['colons']}{{figure}}\n{m['indent']}{m['image']}\n"


def split_body(body: str):
    """Walk the body, splitting on `## ` headings outside fenced code blocks.

    Returns (intro_block_lines, [(section_title, section_content_lines), ...]).
    The intro block still contains the chapter `# ` heading; callers handle it.
    """
    lines = body.splitlines(keepends=True)
    intro_lines: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    cur_title: str | None = None
    cur_lines: list[str] = []
    fence: str | None = None

    def flush():
        nonlocal cur_title, cur_lines
        if cur_title is None:
            intro_lines.extend(cur_lines)
        else:
            sections.append((cur_title, cur_lines))
        cur_title = None
        cur_lines = []

    for line in lines:
        if fence is None:
            fm = FENCE_RE.match(line)
            if fm:
                fence = fm.group(1)
                cur_lines.append(line)
                continue
            hm = HEADING_RE.match(line)
            if hm and len(hm.group(1)) == 2:
                flush()
                cur_title = hm.group(2).strip()
                continue
            cur_lines.append(line)
        else:
            cur_lines.append(line)
            stripped = line.strip()
            # Close on a line that is only fence chars of the same kind, length >= opener.
            if (
                stripped
                and set(stripped) == {fence[0]}
                and len(stripped) >= len(fence)
            ):
                fence = None

    flush()
    return intro_lines, sections


def demote_headings(lines: list[str]) -> list[str]:
    """Demote markdown headings by one level (## -> #, ### -> ##, ...).

    Lines inside fenced code blocks are left untouched.
    """
    out: list[str] = []
    fence: str | None = None
    for line in lines:
        if fence is None:
            fm = FENCE_RE.match(line)
            if fm:
                fence = fm.group(1)
                out.append(line)
                continue
            hm = HEADING_RE.match(line)
            if hm and 2 <= len(hm.group(1)) <= 6:
                out.append(f"{hm.group(1)[1:]} {hm.group(2)}\n")
                continue
            out.append(line)
        else:
            out.append(line)
            stripped = line.strip()
            if (
                stripped
                and set(stripped) == {fence[0]}
                and len(stripped) >= len(fence)
            ):
                fence = None
    return out


def translate_directives(lines: list[str]) -> list[str]:
    """Translate upstream remark-style directives to their MyST equivalents.

    The icm-text source is authored in the professor's remark flavor; MyST
    (Jupyter Book) needs slightly different markers. This is the one seam
    between the two renderers, so the source stays authored upstream-style and
    renders correctly here. Currently handled:

    - Block: ``:::name`` / ``:::name[arg]`` → ``:::{myst} arg`` for the names in
      ``_BLOCK_DIRECTIVE_MAP`` (audio, definition, example, aside, tip,
      exercise). A brace-less ``:::name`` would otherwise fall through MyST's
      ``colon_fence`` to a generic ``<div class="name">``.
    - Inline: ``:unit[a,b]`` → ``{unit}`a,b` `` and ``:vocab[term]`` →
      ``{vocab}`term` `` (the roles in ``_ext/icm_roles.py``). See
      ``_INLINE_ROLE_NAMES`` for the full list.

    Simple ``:::figure`` blocks are handled before this pass by
    ``SIMPLE_FIGURE_RE``; ``figure`` is intentionally absent from the block map.

    Fence-aware: lines inside ``` ``` ``` / ``~~~`` code blocks are left
    untouched, so syntax examples that *show* the upstream form survive verbatim.
    """
    out: list[str] = []
    fence: str | None = None
    for line in lines:
        if fence is None:
            fm = FENCE_RE.match(line)
            if fm:
                fence = fm.group(1)
                out.append(line)
                continue
            bm = BLOCK_DIRECTIVE_RE.match(line.rstrip("\n"))
            if bm:
                eol = "\n" if line.endswith("\n") else ""
                indent, colons, myst = bm.group(1), bm.group(2), _BLOCK_DIRECTIVE_MAP[bm.group(3)]
                title = bm.group(4)
                arg = f" {title}" if title else ""
                out.append(f"{indent}{colons}{{{myst}}}{arg}{eol}")
                if title and myst in _LABELED_DIRECTIVES:
                    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                    out.append(f"{indent}:label: {_LABELED_DIRECTIVES[myst]}-{slug}{eol}")
                continue
            # Inline translations (order-independent; distinct prefixes).
            new = AUDIO_INLINE_RE.sub(r"{audio}`\g<label> <\g<url>>`", line)
            new = FIGURE_INLINE_RE.sub(r"\g<image>", new)
            new = INLINE_ROLE_RE.sub(r"{\1}`\2`", new)
            out.append(new)
        else:
            out.append(line)
            stripped = line.strip()
            if (
                stripped
                and set(stripped) == {fence[0]}
                and len(stripped) >= len(fence)
            ):
                fence = None
    return out


def split_chapter(folder: Path) -> dict | None:
    m = CHAPTER_FOLDER_RE.match(folder.name)
    if not m:
        return None
    chapter_num = int(m.group(1))
    src = folder / "index.md"
    if not src.exists():
        print(f"  skip {folder.name}: no index.md", file=sys.stderr)
        return None

    raw = src.read_text()
    body = FRONTMATTER_RE.sub("", raw, count=1)
    body = SIMPLE_FIGURE_RE.sub(_simple_figure_sub, body)
    body = CONTAINER_BLOCK_RE.sub(_container_sub, body)
    body = AUDIO_FIGURE_ITEM_RE.sub(_audio_figure_item_sub, body)
    body = AUDIO_TRAILING_RE.sub(_audio_trailing_sub, body)
    body = "".join(translate_directives(body.splitlines(keepends=True)))
    intro_lines, sections = split_body(body)

    # Pull the chapter title from the first `# ` in the intro block.
    chapter_title = ""
    intro_after_title: list[str] = []
    seen_title = False
    for line in intro_lines:
        if not seen_title:
            hm = HEADING_RE.match(line)
            if hm and len(hm.group(1)) == 1:
                chapter_title = hm.group(2).strip()
                seen_title = True
                continue
            if line.strip() == "":
                continue
            # Anything else before the title is unexpected; drop it.
            continue
        intro_after_title.append(line)
    intro_text = "".join(intro_after_title).strip("\n")

    out_dir = CONTENT / f"ch{chapter_num:02d}"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    index_md = f"# {chapter_num}. {chapter_title}\n"
    if intro_text:
        index_md += f"\n{intro_text}\n"
    (out_dir / "index.md").write_text(index_md)

    section_refs: list[str] = []
    for i, (title, content_lines) in enumerate(sections):
        body_text = "".join(demote_headings(content_lines)).strip("\n")
        section_md = f"# {chapter_num}.{i} {title}\n"
        if body_text:
            section_md += f"\n{body_text}\n"
        (out_dir / f"{i:02d}.md").write_text(section_md)
        section_refs.append(f"content/ch{chapter_num:02d}/{i:02d}")

    for sub in ("assets", "code", "figures"):
        src_sub = folder / sub
        if src_sub.exists():
            shutil.copytree(src_sub, out_dir / sub)

    return {
        "chapter_num": chapter_num,
        "index": f"content/ch{chapter_num:02d}/index",
        "sections": section_refs,
        "slug": folder.name,
        "title": chapter_title,
        "section_count": len(sections),
    }


def regenerate_toc(results: list[dict]) -> None:
    """Replace the chapter parts block in _toc.yml with one generated from results.

    The "chapter parts block" is the first top-level `  - chapters:` entry whose
    body references `content/ch`. Other parts (templates, course, reference) are
    left untouched.
    """
    text = TOC.read_text()
    lines = text.splitlines()
    parts_starts = [i for i, l in enumerate(lines) if l.rstrip() == "  - chapters:"]
    chapter_start = chapter_end = None
    for idx, start in enumerate(parts_starts):
        end = parts_starts[idx + 1] if idx + 1 < len(parts_starts) else len(lines)
        if any("content/ch" in lines[j] for j in range(start, end)):
            chapter_start, chapter_end = start, end
            break
    if chapter_start is None:
        sys.exit("could not locate chapter parts block in _toc.yml")

    new_block = ["  - chapters:"]
    for r in sorted(results, key=lambda r: r["chapter_num"]):
        new_block.append(f"      - file: {r['index']}")
        if r["sections"]:
            new_block.append("        sections:")
            for s in r["sections"]:
                new_block.append(f"          - file: {s}")
    # Preserve the blank line between this part and the next one.
    new_block.append("")

    new_lines = lines[:chapter_start] + new_block + lines[chapter_end:]
    # Drop accidental double blank lines and trailing blanks.
    cleaned: list[str] = []
    for line in new_lines:
        if line == "" and cleaned and cleaned[-1] == "":
            continue
        cleaned.append(line)
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    TOC.write_text("\n".join(cleaned) + "\n")


def main() -> int:
    if not SOURCE.exists() or not any(SOURCE.iterdir()):
        sys.exit(
            f"icm-text/ not found or empty at {SOURCE}\n"
            "  run: git submodule update --init icm-text"
        )
    folders = sorted(
        p for p in SOURCE.iterdir() if p.is_dir() and CHAPTER_FOLDER_RE.match(p.name)
    )
    results: list[dict] = []
    for folder in folders:
        r = split_chapter(folder)
        if r:
            print(
                f"  ch{r['chapter_num']:02d}  {r['section_count']} section(s)  "
                f"<- icm-text/{r['slug']}"
            )
            results.append(r)
    if not results:
        sys.exit("no chapters found in icm-text/")
    regenerate_toc(results)
    print(f"  updated {TOC.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
