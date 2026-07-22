# Makefile -- build the manuscript and supplementary PDFs
# Usage:
#   make            # build both PDFs
#   make manuscript # build manuscript.pdf only
#   make supp       # build supplementary.pdf only
#   make tables     # regenerate LaTeX table bodies + vector figures from data
#   make clean      # remove LaTeX build artefacts (keeps PDFs)
#   make distclean  # also remove the output PDFs

LATEXMK = latexmk -pdf -interaction=nonstopmode -halt-on-error

.PHONY: all manuscript supp tables figures analysis docx clean distclean

all: manuscript supp

manuscript: manuscript.tex references.bib
	$(LATEXMK) manuscript.tex

supp: supplementary.tex references.bib
	$(LATEXMK) supplementary.tex

# Regenerate table bodies and figures from the analysis scripts.
# Requires Python 3 (pandas, scipy, scikit-learn, scikit-posthocs, matplotlib)
# and, for the figures, Node + Inkscape (see the `figures` target).
tables: analysis
	python3 scripts/gen_tables.py
	python3 scripts/gen_tables_ext.py
	python3 scripts/gen_tables_qaqc.py
	$(MAKE) figures

# Publication figures: data -> JSON -> D3/SVG -> vector PDF.
# Node deps install once into scripts/figures_d3/node_modules.
figures:
	python3 scripts/export_fig_data.py
	cd scripts/figures_d3 && [ -d node_modules ] || npm install --silent --no-audit --no-fund
	node scripts/figures_d3/build.mjs
	sh scripts/svg_to_pdf.sh

# Full analysis pipeline: raw -> clean -> risk -> extended analyses
analysis:
	python3 scripts/01_clean.py
	python3 scripts/02_risk.py
	python3 exploration/scripts/03_indices.py
	cd exploration && python3 scripts/04_stats_source.py
	cd exploration && python3 scripts/05_health_risk.py
	cd exploration && python3 scripts/06_montecarlo.py

# Word version for co-author review / submission. Needs pandoc; figures are
# rasterised to 600 dpi PNG because Word cannot display vector PDF reliably.
docx: figures
	mkdir -p docx/figures
	for f in figures/*.pdf; do \
	  pdftoppm -png -r 600 -singlefile "$$f" "docx/figures/$$(basename $$f .pdf)"; \
	done
	python3 scripts/make_docx.py

clean:
	latexmk -c manuscript.tex supplementary.tex
	rm -f *.bbl *.spl

distclean: clean
	rm -f manuscript.pdf supplementary.pdf
