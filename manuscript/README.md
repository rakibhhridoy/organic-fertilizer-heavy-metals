# Heavy Metals in Commercial Organic Fertilizers (Bangladesh) — Manuscript

Reproducible analysis pipeline for the research article:
*Assessment of Heavy Metal Contamination in Commercial Organic Fertilizers in
Bangladesh and Its Compliance with National Regulatory Limits.*

## Layout

> **Note.** `manuscript.tex`, `supplementary.tex` and `references.bib` are kept
> outside version control; this repository holds the dataset and pipeline only.
> The layout below describes the full working directory, so the LaTeX targets in
> the Makefile will not run from a clean clone.

```
manuscript/
├── manuscript.tex      # Main article (untracked)
├── supplementary.tex   # Supplementary Material (untracked)
├── references.bib      # Bibliography (untracked)
├── Makefile            # Build targets
├── figures/            # Vector PDF figures (generated)
├── tables/             # LaTeX table bodies, \input by the .tex (generated)
├── data/               # Raw + cleaned data
│   ├── OF_HM_TGT.xlsx  #   THE dataset. Sheet1 concentrations (blank-corrected,
│   │                   #   supplier-labelled, BDL flags); Sheet2 calibration/LOD/LOQ;
│   │                   #   Sheet3 spike recovery. Nothing else is a data source.
│   ├── soil_reference_values.csv  # Cbv / Csv / toxic-response factors
│   ├── clean_data.csv/.pkl
│   └── risk_loading.csv
└── scripts/            # Reproducible analysis (Python 3: pandas, scipy, matplotlib)
    ├── 01_clean.py     #   raw -> clean_data (BDL rule, brand parsing, outlier flags)
    ├── 02_risk.py      #   soil-loading risk model (Su et al. 2025)
    ├── gen_tables.py   #   -> tables/*.tex
    ├── gen_tables_qaqc.py #   -> QA/QC table bodies
    ├── export_fig_data.py #   analysis outputs -> figures/data/*.json
    ├── figures_d3/     #   D3 figure sources (Node, ES modules)
    │   ├── theme.mjs   #     palette / type scale / axis helpers
    │   ├── build.mjs   #     driver: JSON -> figures/svg/*.svg
    │   └── fig_*.mjs   #     one module per figure
    ├── svg_to_pdf.sh   #   figures/svg/*.svg -> figures/*.pdf (Inkscape, text->path)
    └── figures_pdf.py  #   LEGACY matplotlib figures (superseded by figures_d3)
```

## Build

```
make            # manuscript.pdf + supplementary.pdf  (latexmk -> pdflatex + bibtex)
make tables     # regenerate table bodies AND figures from data/
make figures    # figures only: data -> JSON -> D3/SVG -> vector PDF
make clean      # remove LaTeX build artefacts (keeps PDFs)
```

Full reproduction from raw data:
```
python3 scripts/01_clean.py && python3 scripts/02_risk.py
python3 scripts/gen_tables.py && python3 scripts/figures_pdf.py
make
```

## Before submission — outstanding items

- **Author block** — DONE. Ahnaf Ibne Nasir (first), Md Rakib Hasan (second, corresponding);
  equal contribution footnote on both. CRediT confirmed.
- **Methods specifics** — DONE except one. Study area (greater Dhaka: Dhaka, Gazipur,
  Savar, Narayanganj), sampling March–May 2026, 2 mm sieve, digestion 2 g → 50 mL
  (factor 25), Varian AA240, pH in 1:2.5 and EC in 1:5 (w/v) suspension.
  Standards described generically (certified 1000 mg/L single-element stocks, no supplier named).
- **LOD units — largely resolved.** Sheet2 LOD/LOQ are solution-phase (mg/L). At the
  corrected factor of 25 (2 g → 50 mL) they rescale to 0.15 (Cd) – 6.10 (Zn) mg/kg:
  Cu and Zn are fully consistent with the reported data, Cr and Pb nearly so (1 and 3
  values below). **Ni remains the exception** — 14/35 values fall under its 2.33 mg/kg
  method limit — so §2.4 names Ni explicitly and flags its low end as indicative.
  Non-detects are still assigned operationally (blank subtraction), so one criterion
  applies to every element.
- **Calibration range** — Sheet2 gives slope/LOD/LOQ but not the working-standard
  concentrations, so the calibration range is no longer documented in Table 1. Add it if
  the journal asks.
- **Risk model** — RESOLVED. All soil reference values now live in
  `data/soil_reference_values.csv` (single source of truth, read by `02_risk.py`,
  `03_indices.py`, `params_hhra.py` and `06_montecarlo.py` via `scripts/soil_refs.py`).
  Cbv = Kabata-Pendias world-soil means; Csv = Dutch VROM (2000) intervention values;
  a Canadian CCME agricultural bound is reported as a strict sensitivity.
  Bangladesh has no national soil baseline or soil quality standard — stated explicitly
  in Methods.
- **References** — `references.bib` contains 29 verified real sources
  (regulatory, methodological, toxicological, contextual and regional), each
  checked against the primary record with DOIs where available; all are cited
  in-text (no orphans, no placeholders). A further ~15 benchmark-comparison
  references are queued to reach full journal density (~45) once the web-search
  quota resets. Only the soil background/safe values these support still need
  local substitution.
- **Funding / acknowledgements** — DONE. Funded by the University Grants Commission of
  Bangladesh (no grant number cited, at the authors' instruction); lab facilities
  acknowledged to the Dept. of Soil, Water and Environment, DU.
- **As & Hg** — not measured; noted as a limitation. Add if data become available.

## Figures

Figures are authored in **D3** and rendered headless to SVG, then converted to
vector PDF with Inkscape (`--export-text-to-path`, so no font dependency ships
with the artwork). Requires Node 18+ and Inkscape; `make figures` installs the
Node deps on first run.

```
analysis outputs ──► scripts/export_fig_data.py ──► figures/data/*.json
                                                          │
                     scripts/figures_d3/build.mjs ◄────────┘
                                │
                                ▼
                     figures/svg/*.svg ──► scripts/svg_to_pdf.sh ──► figures/*.pdf
```

Design conventions (see `scripts/figures_d3/theme.mjs`):

- **One canvas width (540 units → 405 pt) for every figure**, so all are scaled
  identically by `width=\linewidth` and on-page type size is uniform. If you add
  a figure, keep `W = 540`.
- Categorical hues use a CVD-validated 8-slot order, assigned to a fixed entity
  (fertilizer type / metal) so colour never follows rank. Sequential = one blue
  hue; diverging (correlation) = blue↔red with a neutral midpoint.
- Where a scatter carries more than three categories, identity is encoded by
  **hue *and* marker shape**, never colour alone.
- Concentrations are plotted on a **log axis**: they span three orders of
  magnitude, and a linear axis with the MAL reference line crushes the data.

## Extended analyses (integrated)

The manuscript now includes pollution/ecological indices (PLI, mCd, Håkanson RI,
Nemerow), Dunn's post-hoc + effect sizes, PCA-varimax + APCS-MLR source
apportionment, a two-scenario USEPA health risk assessment, and a Monte Carlo
simulation with global sensitivity analysis. Prototype scripts, per-analysis
outputs and a findings report live in `exploration/`; `make analysis` runs the
full raw→clean→risk→indices→stats→health→Monte-Carlo pipeline, and `make tables`
regenerates every table body and figure from it.

## Key result

Of 35 samples across 7 fertilizer categories, all comply with the Bangladesh
maximum allowable limits for Cu, Cd, Zn and Ni; only Cr and Pb exceed (each
5.7 %, 2/35). Generic organic fertilizer and certain oil-cake / vermicompost
products carry the highest metal burdens. Soil-accumulation risk is low at mean
concentrations (Tmax ≈ 3,300–26,500 yr against the Dutch intervention values)
but localised hotspots warrant batch-level monitoring.

Figures are current as of `data/OF_HM_TGT.xlsx` and the reference values in
`data/soil_reference_values.csv`.
Mean concentrations: Zn 75.2 > Cu 23.5 > Cr 16.8 > Pb 9.9 > Ni 4.2 > Cd 0.44 mg/kg.

Note the reference-value change (2026-07-21) moved several secondary findings:
PLI and RI now classify **every** category as unpolluted / low risk (Generic OF
PLI 0.72, RI 100), where the earlier ad-hoc background put Generic OF in the
polluted / moderate bands. Conversely the probabilistic consumer health risk got
worse (P95 HI 1.11, P(CR>1e-4) 7.7 %) because the higher soil background feeds
that pathway. The primary compliance conclusion is unaffected.

## Data provenance

`OF_HM_TGT.xlsx` is the single, final laboratory file and the only data source in
the pipeline. It superseded an earlier chain of files (`OF HM.xlsx`, `TG.xlsx`,
`QAQC.docx`, `Names of Companies.docx` and their copies under `data/`), all of
which were deleted on 2026-07-21 at the author's instruction to remove ambiguity.
Supplier identities now live only in Sheet1's first column, from which
`01_clean.py` derives the Brand and Pack fields. Two consequences of that switch
are worth recording, because the deleted files no longer evidence them:

- The QA/QC tables now come from `OF_HM_TGT.xlsx` Sheet2/Sheet3. These differ
  from the earlier `QAQC.docx` record: the Cu and Cd calibration equations are
  transposed between the two sources, Pb differs entirely, and all recovery
  figures were revised (range 82.4–101.9 % vs 83.3–105.2 %). TGT is authoritative.
- Horn-meal Ni in samples HO2 and HO3 is reported as below detection. An earlier
  working version reinstated these as quantified values (0.47 and 0.55 mg/kg);
  that exception was withdrawn, and both are now `<LOD` with LOD/2 substitution,
  giving four non-detects in total.
