.PHONY: book clean spotless all serve check pdf sync-pyquist-readme split merge

PYQUIST_SUBMODULE  := pyquist
PYQUIST_README_SRC := $(PYQUIST_SUBMODULE)/README.md
PYQUIST_README     := content/pyquist/_pyquist_readme.md

all: book

# Split each icm-text/{n}-{slug}/index.md into per-section files under
# content/ch{nn}/ so Jupyter Book's sidebar lists one entry per `## ` section.
# icm-text/ is the pinned ground-truth prose submodule. Run this MANUALLY when
# you want to pull the latest prose into content/ (bump the submodule first
# with `git submodule update --remote icm-text` to advance the pin).
# It also mirrors icm-text/refs.bib (the professor's ground-truth bibliography)
# into content/references.bib, so citations resolve against the upstream entries.
# WARNING: it wipes content/ch*/ entirely, dropping any local styling
# overrides (figure refactors, admonition wrappers, margin notes), and
# overwrites content/references.bib. Use `git diff content/` afterwards to
# review and re-apply your styling.
split:
	python3 tools/split_chapters.py

# Inverse of split: combines content/ch{nn}/ section files back into chapter-
# level icm-text-merged/{n}-{slug}/index.md files matching the icm-text layout,
# for preparing a PR up to icm-text. Includes a round-trip self-check that
# fails if the rendered site would change.
merge:
	python3 tools/merge_chapters.py

# Mirror the Pyquist README into content/pyquist/Overview.md from the
# pinned `pyquist/` git submodule. Runs on every `make book` so the
# Overview reflects whatever commit the submodule is checked out at
# (bump it with `git submodule update --remote pyquist`). The sed step
# rewrites `examples/…` relative links to absolute GitHub URLs so they
# resolve from the book site.
sync-pyquist-readme:
	@test -f $(PYQUIST_README_SRC) || { \
		echo "ERROR: $(PYQUIST_README_SRC) not found — is the submodule initialized?"; \
		echo "  run: git submodule update --init $(PYQUIST_SUBMODULE)"; \
		exit 1; \
	}
	@cp $(PYQUIST_README_SRC) $(PYQUIST_README)
	@sed -i.bak 's|](examples/|](https://github.com/gclef-cmu/pyquist/blob/main/examples/|g' $(PYQUIST_README)
	@rm -f $(PYQUIST_README).bak

book: sync-pyquist-readme
	jupyter-book build ./
	@# Sphinx doesn't track files referenced by raw <img>/<audio> HTML tags,
	@# so copy each chapter's assets folder into the build output ourselves.
	@for d in content/ch*/assets; do \
		dest="_build/html/$$(dirname $$d)"; \
		mkdir -p "$$dest"; \
		cp -R "$$d" "$$dest/"; \
	done

clean:
	jupyter-book clean ./

spotless:
	jupyter-book clean ./ --all

serve: book
	python -m http.server --directory _build/html/

check:
	jupyter-book build ./ --builder linkcheck

pdf:
	jupyter-book build ./ --builder pdflatex
