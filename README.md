# Heavy Metals in Commercial Organic Fertilizers (Bangladesh)

Data, analysis pipeline and manuscript source for:

> *Assessment of Heavy Metal and Arsenic Contamination in Commercial Organic Fertilizers in
> Bangladesh and Its Compliance with National Regulatory Limits.*
> Ahnaf Ibne Nasir, Md Rakib Hasan\*, Md Harun Mia, Md Raisuddin Sikder.
> Target journal: Environmental Geochemistry and Health.
> \*Corresponding author: rakibhhridoy@fermium.systems

Thirty-five commercial organic fertilizer products across seven categories,
sampled from the greater Dhaka region (March–May 2026) and analysed for Cu, Cr,
Pb, Cd, Zn and Ni plus pH and EC, benchmarked against the Bangladesh maximum
allowable limits.

## Layout

```
TGT.xlsx              the laboratory file (concentrations, calibration, recovery)
manuscript/           analysis pipeline and figure code
  data/               canonical dataset + soil reference values
  scripts/            analysis, table generation, D3 figures, DOCX build
  exploration/        indices, statistics, health risk, Monte Carlo
```

**The manuscript source is not in this repository.** `manuscript.tex`,
`supplementary.tex` and `references.bib` are kept outside version control, so
this repository holds the dataset and the analysis pipeline only. The
`make`, `make manuscript`, `make supp` and `make docx` targets therefore will
not run from a clean clone; `make analysis`, `make tables` and `make figures`
will.

`manuscript/README.md` documents the pipeline in detail, including the design
conventions for the figures and the outstanding items before submission.

## Reproducing

Requires Python 3 (pandas, scipy, scikit-learn, scikit-posthocs, matplotlib),
a LaTeX distribution, and — for the figures and Word build — Node 18+,
Inkscape and pandoc.

```bash
cd manuscript
make analysis   # raw data -> cleaned data -> indices, stats, risk, Monte Carlo
make tables     # table bodies + figures (data -> JSON -> D3/SVG -> vector PDF)
```

`make`, `make supp` and `make docx` additionally require the manuscript source,
which is not tracked here (see above).

Everything downstream derives from `TGT.xlsx` and
`manuscript/data/soil_reference_values.csv`; no result is entered by hand.

## Notes

- Generated outputs (PDFs, figures, table bodies, cleaned data) are not tracked;
  run `make tables` to produce them.
- The literature PDF under `draft/` is excluded from version control, as
  publisher files are not ours to redistribute. All sources are cited with DOIs
  in `manuscript/references.bib`.
- `TGT.xlsx` identifies each product by supplier and brand. **Review this before
  making the repository public or archiving it**, and check that naming
  commercial products is consistent with how the paper presents them.
