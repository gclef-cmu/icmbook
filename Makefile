.PHONY: book clean spotless all serve check pdf sync-pyquist-readme split merge wheels check-thebe-fork template-interactive template-animation

PYQUIST_SUBMODULE  := pyquist
PYQUIST_README_SRC := $(PYQUIST_SUBMODULE)/README.md
PYQUIST_README     := content/pyquist/_pyquist_readme.md

all: book

# Pull the latest prose from the icm-text submodule into per-section files
# under content/ch{nn}/ (bump the submodule first to advance the pin). Also
# mirrors icm-f26/ into content/course/ and refs.bib into content/references.bib.
# WARNING: wipes content/ch*/ and content/course/ entirely, dropping any local
# styling overrides — review with `git diff content/` afterwards.
split:
	python3 tools/split_chapters.py

# Inverse of split: reassembles content/ch{nn}/ into icm-text-merged/ for a
# PR up to icm-text. Self-checks that the round-trip is byte-identical.
merge:
	python3 tools/merge_chapters.py

# Regenerate the "Template - Interactive" page: index.ipynb is GENERATED from
# main.md + the notebooks/ folder next to it, the same expansion `make split`
# performs for chapters. Edit the sources, then re-run this. Untouched by
# `make split`.
template-interactive:
	@python3 -c "import sys; sys.path.insert(0, 'tools'); \
	from pathlib import Path; \
	import nbformat; \
	from split_chapters import build_section_notebook; \
	folder = Path('content/template-interactive'); \
	nb = build_section_notebook((folder / 'main.md').read_text(), folder, 99, 0); \
	nbformat.write(nb, str(folder / 'index.ipynb')); \
	print('wrote', folder / 'index.ipynb')"

# Regenerate the "Template - Animation" page — same model as above, with
# manim companions in notebooks/. sec_index=1 keeps its cell ids (ch99s01…)
# clear of template-interactive's (ch99s00…). Untouched by `make split`.
template-animation:
	@python3 -c "import sys; sys.path.insert(0, 'tools'); \
	from pathlib import Path; \
	import nbformat; \
	from split_chapters import build_section_notebook; \
	folder = Path('content/template-animation'); \
	nb = build_section_notebook((folder / 'main.md').read_text(), folder, 99, 1); \
	nbformat.write(nb, str(folder / 'index.ipynb')); \
	print('wrote', folder / 'index.ipynb')"

# Mirror the Pyquist README from the pinned submodule; runs on every
# `make book`. The sed step rewrites `examples/…` relative links to absolute
# GitHub URLs so they resolve from the book site.
sync-pyquist-readme:
	@test -f $(PYQUIST_README_SRC) || { \
		echo "ERROR: $(PYQUIST_README_SRC) not found — is the submodule initialized?"; \
		echo "  run: git submodule update --init $(PYQUIST_SUBMODULE)"; \
		exit 1; \
	}
	@cp $(PYQUIST_README_SRC) $(PYQUIST_README)
	@sed -i.bak 's|](examples/|](https://github.com/gclef-cmu/pyquist/blob/main/examples/|g' $(PYQUIST_README)
	@rm -f $(PYQUIST_README).bak

# Fetch the pinned thebe runtime bundles for the live-code layer. Self-hosted
# because the kernel web worker must be same-origin. This stack embeds
# pyodide_kernel 0.4.7, which caps the runtime at Pyodide 0.27.x (the pin
# lives in _static/live-cells.js; tools/soundfile_stub fills the gap).
# Cached and gitignored; `rm -rf vendor/thebe-dist` to force a re-fetch.
# IMPORTANT: lives under vendor/ (html_extra_path), NOT _static/ — Jupyter
# Book registers every _static .js as a page script, which would eagerly
# execute the bundle's worker-only chunks and ship ~4 MB on every page. The
# service worker must sit at the site root to get root scope.
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

# Build the wheels the in-browser kernel installs: pyquist from the pinned
# submodule, icm-widgets, and the browser stubs. Output is gitignored and
# rebuilt on every `make book` so it always matches the submodule pin.
wheels:
	rm -rf _static/wheels
	python3 -m pip wheel --no-deps -q -w _static/wheels ./tools/sounddevice_stub
	python3 -m pip wheel --no-deps -q -w _static/wheels ./tools/soundfile_stub
	python3 -m pip wheel --no-deps -q -w _static/wheels ./tools/icm_widgets
	python3 -m pip wheel --no-deps -q -w _static/wheels ./pyquist
	@# Install-order manifest for live-cells.js: the stubs must install
	@# before pyquist so micropip treats those dependencies as satisfied and
	@# never fetches the real packages.
	python3 -c "import glob, json, os; \
		ws = sorted(os.path.basename(p) for p in glob.glob('_static/wheels/*.whl')); \
		ws.sort(key=lambda w: 0 if w.startswith(('sounddevice', 'soundfile')) else 1); \
		open('_static/wheels/manifest.json', 'w').write(json.dumps(ws))"

# The live-code page glue needs the TeachBooks sphinx-thebe FORK, but
# upstream ships the same dist name AND version, so a fresh env silently
# keeps upstream — the build succeeds and the deployed pages break in the
# browser. Detect the fork by a file only it ships and fail loudly with the
# fix. (CI force-installs the fork for the same reason.)
check-thebe-fork:
	@python3 -c "import pathlib, sphinx_thebe; \
		raise SystemExit(0 if (pathlib.Path(sphinx_thebe.__file__).parent \
		/ '_static' / 'sphinx-thebe-lite.js').exists() else 1)" || { \
		echo "ERROR: upstream sphinx-thebe is installed; the book needs the TeachBooks fork:"; \
		echo "  pip install --force-reinstall --no-deps 'sphinx-thebe @ git+https://github.com/TeachBooks/Sphinx-Thebe@1f3a80969622b7d63f48f05d8769f5cb933202a0'"; \
		exit 1; }

book: check-thebe-fork sync-pyquist-readme wheels vendor-thebe
	@# PIP_DISABLE_PIP_VERSION_CHECK: keeps pip's "new release" notice out of
	@# baked %pip cell output. ICM_BOOK_BUILD: kernel-only preview cells
	@# guard on this and build nothing.
	PIP_DISABLE_PIP_VERSION_CHECK=1 ICM_BOOK_BUILD=1 jupyter-book build ./
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
