.PHONY: book clean spotless all serve check pdf sync-pyquist-readme split merge wheels

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

# Fetch the pinned thebe runtime bundles the live-code layer loads (see
# _static/live-cells.js). Self-hosted because the kernel web worker must be
# same-origin — a CDN copy is blocked by the browser. pyodide_kernel 0.4.7
# inside thebe-lite 0.5.0 is required: the TeachBooks extension's vendored
# bundle ships kernel 0.2.0, which hangs on `await` under Pyodide 0.28
# (and pyquist needs 0.28 for numpy>=2 + soundfile). Downloaded once and
# cached (gitignored); `rm -rf _static/thebe-dist` to force a re-fetch.
# IMPORTANT: lives under vendor/ (html_extra_path), NOT _static/ — Jupyter
# Book auto-registers every .js under _static as a page script, which would
# eagerly execute the bundle's worker-only webpack chunks on page load
# (breaking them AND shipping ~4 MB on every page). html_extra_path copies
# files verbatim with no registration. The service worker must be served
# from the site root to get root scope.
THEBE_DIST := vendor/thebe-dist
vendor-thebe:
	@if [ ! -f $(THEBE_DIST)/.ok ]; then \
		echo "Fetching thebe-lite 0.5.0 + thebe 0.9.3 bundles..."; \
		rm -rf $(THEBE_DIST); mkdir -p $(THEBE_DIST)/tmp1 $(THEBE_DIST)/tmp2; \
		curl -sL https://registry.npmjs.org/thebe-lite/-/thebe-lite-0.5.0.tgz | tar xz -C $(THEBE_DIST)/tmp1; \
		curl -sL https://registry.npmjs.org/thebe/-/thebe-0.9.3.tgz | tar xz -C $(THEBE_DIST)/tmp2; \
		mv $(THEBE_DIST)/tmp1/package/dist/lib $(THEBE_DIST)/lite; \
		mv $(THEBE_DIST)/tmp2/package/lib $(THEBE_DIST)/core; \
		rm -rf $(THEBE_DIST)/tmp1 $(THEBE_DIST)/tmp2 $(THEBE_DIST)/lite/*.map $(THEBE_DIST)/core/*.map; \
		cp $(THEBE_DIST)/lite/service-worker.js vendor/service-worker.js; \
		touch $(THEBE_DIST)/.ok; \
	fi

# Build the wheels that the in-browser (thebe-lite/Pyodide) kernel installs:
# the real pyquist wheel from the pinned submodule, plus a stub `sounddevice`
# (see tools/sounddevice_stub/) that stands in for the PortAudio package,
# which cannot exist in WebAssembly. Both are pure Python — any python3 with
# pip builds them. Output is gitignored; rebuilt on every `make book` so the
# wheel always matches the submodule pin.
wheels:
	rm -rf _static/wheels
	python3 -m pip wheel --no-deps -q -w _static/wheels ./tools/sounddevice_stub
	python3 -m pip wheel --no-deps -q -w _static/wheels ./tools/soundfile_stub
	python3 -m pip wheel --no-deps -q -w _static/wheels ./pyquist
	@# Install-order manifest consumed by _static/live-cells.js: the stubs
	@# (sounddevice always; soundfile until the kernel stack reaches
	@# Pyodide 0.28) must install before pyquist so micropip treats those
	@# dependencies as satisfied and never fetches the real packages.
	python3 -c "import glob, json, os; \
		ws = sorted(os.path.basename(p) for p in glob.glob('_static/wheels/*.whl')); \
		ws.sort(key=lambda w: 0 if w.startswith(('sounddevice', 'soundfile')) else 1); \
		open('_static/wheels/manifest.json', 'w').write(json.dumps(ws))"

book: sync-pyquist-readme wheels vendor-thebe
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
