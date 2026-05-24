.PHONY: book clean spotless all serve check pdf sync-pyquist-readme

PYQUIST_README_URL := https://raw.githubusercontent.com/gclef-cmu/pyquist/main/README.md
PYQUIST_README    := content/pyquist/_pyquist_readme.md

all: book

# Mirror the upstream Pyquist README into content/pyquist/Overview.md.
# Runs on every `make book` so the Overview reflects whatever's on
# Pyquist's main branch. The sed step rewrites `examples/…` relative
# links to absolute GitHub URLs so they resolve from the book site.
sync-pyquist-readme:
	@curl -fsSL $(PYQUIST_README_URL) -o $(PYQUIST_README)
	@sed -i.bak 's|](examples/|](https://github.com/gclef-cmu/pyquist/blob/main/examples/|g' $(PYQUIST_README)
	@rm -f $(PYQUIST_README).bak

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
