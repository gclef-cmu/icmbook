.PHONY: book clean spotless all serve check pdf sync-pyquist-readme

all: book

# Refresh the Pyquist README snapshot used by content/pyquist/Overview.md.
# Runs on every `make book` so the Overview reflects the upstream README; the
# script is offline-tolerant (it keeps the previous copy if the fetch fails).
sync-pyquist-readme:
	python3 tools/fetch_pyquist_readme.py

book: sync-pyquist-readme
	jupyter-book build ./

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
