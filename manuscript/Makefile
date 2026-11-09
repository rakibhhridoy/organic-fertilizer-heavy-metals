# Makefile -- build the manuscript and supplementary PDFs
# Usage:
#   make            # build both PDFs
#   make manuscript # build manuscript.pdf only
#   make supp       # build supplementary.pdf only
#   make tables     # regenerate LaTeX table bodies + vector figures from data
#   make submissions # refresh submissions/EnvironmentalAdvances/ and submissions/EGAH/
#   make upload     # refresh just the flat standalone source set
#   make clean      # remove LaTeX build artefacts (keeps PDFs)
#   make distclean  # also remove the output PDFs

LATEXMK = latexmk -pdf -interaction=nonstopmode -halt-on-error

# Figure resolution for the Word build. 300 dpi keeps the file emailable
# (~1 MB); raise to 600 for a production-quality Word deliverable.
DOCX_DPI = 300

.PHONY: all manuscript egah supp tables figures analysis docx upload upload-egah submissions clean distclean

all: manuscript supp

# manuscript.pdf is the ELSEVIER form, for Environmental Advances (primary target).
manuscript: manuscript.tex references.bib
	$(LATEXMK) manuscript.tex

# manuscript_egah.pdf is the SPRINGER form of the same source, for Environmental
# Geochemistry and Health (secondary target). The form is selected by \SPRINGERFORM,
# so there is only ever one manuscript source to edit.
egah: manuscript.tex references.bib
	pdflatex -interaction=nonstopmode -jobname=manuscript_egah "\def\SPRINGERFORM{}\input{manuscript}"
	bibtex manuscript_egah
	pdflatex -interaction=nonstopmode -jobname=manuscript_egah "\def\SPRINGERFORM{}\input{manuscript}"
	pdflatex -interaction=nonstopmode -jobname=manuscript_egah "\def\SPRINGERFORM{}\input{manuscript}"

supp: supplementary.tex references.bib
	$(LATEXMK) supplementary.tex

# Regenerate table bodies and figures from the analysis scripts.
# Requires Python 3 (pandas, scipy, scikit-learn, scikit-posthocs, matplotlib)
# and, for the figures, Node + Inkscape (see the `figures` target).
tables: analysis
	python3 scripts/gen_tables.py
	python3 scripts/gen_tables_ext.py
	python3 scripts/gen_tables_qaqc.py
	python3 scripts/gen_tables_rev.py
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
	cd exploration && python3 scripts/07_revision_sensitivity.py

# Word version for co-author review / submission. Needs pandoc; figures are
# rasterised to 600 dpi PNG because Word cannot display vector PDF reliably.
docx: figures
	mkdir -p docx/figures
	for f in figures/*.pdf; do \
	  pdftoppm -png -r $(DOCX_DPI) -singlefile "$$f" "docx/figures/$$(basename $$f .pdf)"; \
	done
	python3 scripts/make_docx.py
	python3 scripts/make_docx.py supplementary

# Journal upload set: a flat, standalone copy of the source with the figures
# renamed Fig1..Fig6 and the table bodies inlined. Overwrites upload/ .
upload: manuscript
	python3 scripts/build_upload.py

# The EGAH flat set, built from the same source in Springer form.
upload-egah: egah
	python3 scripts/build_upload.py egah

# Assemble both complete, uploadable journal folders under submissions/.
# Builds both manuscript forms and the supplementary first, so one command
# refreshes everything a submission needs.
submissions: manuscript egah supp docx
	python3 scripts/build_submissions.py

clean:
	latexmk -c manuscript.tex supplementary.tex
	rm -f *.bbl *.spl

distclean: clean
	rm -f manuscript.pdf supplementary.pdf manuscript_egah.pdf
