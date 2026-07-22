# Exploratory analysis — findings & integration plan

> **SUPERSEDED (2026-07-21).** The numbers below were computed with the original
> raw dataset and the earlier ad-hoc soil reference values. Both have since changed:
> the dataset is now the blank-corrected `OF_HM_TG.xlsx`, and soil background/safe
> values come from `data/soil_reference_values.csv` (Kabata-Pendias world-soil means
> + Dutch VROM 2000 intervention values). Indices, T_max and health-risk figures in
> this file are therefore out of date. The manuscript and `README.md` carry the
> current values; regenerate with `make analysis && make tables`.

Prototype extension of the heavy-metals manuscript. All results derive from the
same 35-sample dataset (7 fertilizer types × 5 replicates; Cu, Cr, Pb, Cd, Zn, Ni).
Reference/parameter values (soil background, soil safe limits, USEPA RfD/SF,
transfer factors) are representative literature values flagged for localisation
before submission. Scripts in `scripts/`, outputs in `outputs/`.

---

## 1. Pollution & ecological risk indices  (`03_indices.py`)

| Type | PLI | mCd | RI | RI class | Nemerow P_N (vs MAL) |
|---|---|---|---|---|---|
| Cow dung | 0.41 | 0.68 | 51.6 | low | 0.17 clean |
| Bone meal | 0.38 | 0.68 | 42.3 | low | 0.22 clean |
| Trichocompost | 0.58 | 0.80 | 46.5 | low | 0.20 clean |
| **Generic OF** | **1.12** | **2.20** | **204.2** | **moderate** | 0.62 clean |
| Vermicompost | 0.63 | 1.12 | 73.1 | low | **1.08 slight** |
| Horn meal | 0.34 | 0.60 | 34.2 | low | 0.26 clean |
| Neem cake | 0.45 | 1.16 | 124.1 | low | 0.38 clean |

**Key insight — compliance ≠ ecological safety.** Cadmium dominates the Håkanson
ecological risk index (mean E_r = 70, ≈ 86 % of total RI) *despite* complying with
the Bangladesh MAL, because of its high toxic-response weight. **Generic organic
fertilizer** is flagged as *moderate* ecological risk (RI = 204) by every index;
vermicompost trips the Nemerow warning (P_N > 1) via its Cr hotspot.

→ Figure: `fig_RI_stacked.pdf` (RI by type, stacked by metal contribution).

---

## 2. Statistics & source apportionment  (`04_stats_source.py`)

**Effect sizes (eta-squared) + Dunn's post-hoc (BH-corrected):**

| Metal | H | p | η² | Significant pairs (BH) |
|---|---|---|---|---|
| Cu | 15.7 | 0.016 | 0.35 (large) | Bone meal–Generic OF; Generic OF–Horn meal |
| Ni | 16.0 | 0.014 | 0.36 (large) | Generic OF–Horn meal |
| Cd | 12.6 | 0.049 | 0.24 (med) | none survive correction |
| Cr, Pb, Zn | n.s. | — | small | — |

**Source apportionment (PCA-varimax, Kaiser criterion → 2 factors, 66 % variance; APCS-MLR):**
- **Factor 1** (49.5 %; Cu 0.90, Zn 0.77, Pb 0.75, Ni 0.72, Cd 0.70): general
  waste / mixed-anthropogenic source; APCS-MLR attributes 94–99 % of these five
  metals to it.
- **Factor 2** (16.9 %; Cr −0.99): a **Cr-specific source** (97.5 % of Cr by
  APCS-MLR) consistent with tannery / leather-waste inputs — highly relevant to
  Bangladesh. Cr separates cleanly from all other metals.

→ Figure: `fig_dendrogram.pdf` (Ward clustering of types). *Caveat: APCS-MLR is
exploratory at n = 35 — report as supportive, not definitive.*

---

## 3. Human health risk — USEPA framework  (`05_health_risk.py`)

| Scenario | HI (overall) | Cancer risk (overall) | Dominant metal |
|---|---|---|---|
| **Handlers** (occupational) | 0.011 | 4.5×10⁻⁷ | Cr |
| **Consumers** (via crops) | 0.390 | 2.1×10⁻⁵ | Cr (HQ 0.23) |

Both HI < 1 (no non-carcinogenic concern at central estimates). Cancer risk is
within the 10⁻⁶–10⁻⁴ "tolerable" band for both, but the **crop-consumer pathway is
~200× the handler pathway** and is Cr-dominated. Handler cancer risk peaks for
vermicompost (1.7×10⁻⁶) via its Cr hotspot.

---

## 4. Monte Carlo simulation + sensitivity  (`06_montecarlo.py`, N = 30 000)

**Probabilistic soil accumulation** — even under full parameter uncertainty
(concentration lognormal fits; application 3–10 t/ha; depth 0.15–0.25 m):

| Metal | Median T_max (yr) | P(exceed ≤ 100 yr) |
|---|---|---|
| Zn | 1,415 | 0.000 |
| Cu | 2,567 | 0.001 |
| Cd | 4,041 | 0.000 |
| Cr | 4,286 | 0.001 |
| Ni | 5,234 | **0.008** |
| Pb | 5,607 | 0.000 |

→ Soil accumulation risk is negligible on policy-relevant horizons (Ni highest, still < 1 %).

**Probabilistic health risk (consumer):** HI mean 0.46, **P95 0.75**, P(HI>1)=0.7 %.
Cancer risk mean 3.4×10⁻⁵, **P95 7.6×10⁻⁵**, **P(CR>10⁻⁴)=1.5 %**, P(CR>10⁻⁶)=100 %.

**Global sensitivity (standardised rank regression):**
- HI ← intake rate (+0.55) and body weight (−0.57); fertilizer concentration
  contributes little (soil background dominates the dietary pathway).
- Cancer risk ← **Cr(VI) fraction (+0.71)**, the single most influential input —
  and it is an *unmeasured assumption*. Strong case for Cr speciation in future work.

→ Figures: `fig_mc_exceedance.pdf`, `fig_mc_risk_dist.pdf`.

---

## Recommended integration into the manuscript

**Strong — add to main text:**
1. Pollution/ecological indices (PLI, RI, Nemerow) as a Results subsection + the
   "compliance ≠ ecological safety / Cd drives RI" narrative. New Table + `fig_RI_stacked`.
2. Dunn's post-hoc + effect sizes — upgrade the existing Kruskal–Wallis paragraph.
3. Monte Carlo soil-accumulation and probabilistic risk — replaces the single-point
   T_max with distributions; `fig_mc_exceedance`. Headline: robust low soil risk.
4. Sensitivity result on Cr(VI) fraction → sharpen the "future Cr speciation" recommendation.

**Include but frame carefully (main text brief + SI detail):**
5. Health risk (both scenarios) — report central + P95; foreground the Cr-driven
   consumer pathway. Put the full parameter table and per-type breakdown in SI.
6. Source apportionment — present PCA-varimax + the tannery-Cr interpretation;
   keep APCS-MLR in SI as exploratory.

**Before submission (all flagged in code):** localise soil background/safe values,
verify RfD/SF and transfer factors, measure or bound the Cr(VI) fraction, and add
As/Hg. These do not change the qualitative conclusions but are needed for defensible
absolute numbers.
