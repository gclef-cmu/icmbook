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
# Simple figure: a `:::figure` block whose first line is a single `:figure!`
# image, e.g.
#     :::figure
#     :figure![alt text](./assets/x.png)
#
#     caption…
#     :::
# → MyST `:::{figure} ./assets/x.png` + `:alt: alt text`, keeping the caption.
# Multi-line (matches the opener + image lines); the caption and closing `:::`
# are left as-is. Grid figures (whose first line is math/`:audio`, not an image)
# don't match and are left untouched — they depend on the still-deferred inline
# `:audio`/`:figure!` pattern.
SIMPLE_FIGURE_RE = re.compile(
    r"^(?P<indent>[ \t]*)(?P<colons>:{3,})figure[ \t]*\n"
    r"(?P=indent):figure!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)\)[ \t]*\n",
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


def _simple_figure_sub(m: re.Match) -> str:
    return (
        f"{m['indent']}{m['colons']}{{figure}} {m['path']}\n"
        f"{m['indent']}:alt: {m['alt']}\n"
    )


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
                myst = _BLOCK_DIRECTIVE_MAP[bm.group(3)]
                arg = f" {bm.group(4)}" if bm.group(4) else ""
                out.append(f"{bm.group(1)}{bm.group(2)}{{{myst}}}{arg}{eol}")
                continue
            out.append(INLINE_ROLE_RE.sub(r"{\1}`\2`", line))
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
