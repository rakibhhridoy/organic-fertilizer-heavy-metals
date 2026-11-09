# -*- coding: utf-8 -*-
"""Emit LaTeX table bodies for the revision analyses (HAZADV-D-26-02471).
Reads exploration/outputs/rev_*.csv written by exploration/scripts/07_revision_sensitivity.py.
Run:  python3 scripts/gen_tables_rev.py   (from manuscript/)
"""
import os, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUTP = os.path.join(ROOT, "exploration", "outputs"); TBL = os.path.join(ROOT, "tables")
rd = lambda f: pd.read_csv(os.path.join(OUTP, f))
ABBR = {"Cow dung": "Cow dung", "Bone meal": "Bone meal", "Trichocompost": "Trichocompost",
        "Generic Organic Fertilizer": "Generic OF", "Vermicompost": "Vermicompost",
        "Horn meal": "Horn meal", "Neem cake": "Neem cake", "OVERALL": "\\textbf{Overall}"}

def sci(v, d=2):
    if not np.isfinite(v): return "--"
    m, e = f"{v:.{d}e}".split("e")
    return f"${m}\\times10^{{{int(e)}}}$"
def yrs(v):
    return "never" if not np.isfinite(v) else f"{v:,.0f}".replace(",", "{,}")
def write(name, lines):
    with open(os.path.join(TBL, name), "w") as f: f.write("\n".join(lines) + "\n")
    print("  wrote tables/" + name)

# S16  Cr(VI) and inorganic-As scenarios
sc = rd("rev_scenarios.csv"); L = []
for kind, g in sc.groupby("kind", sort=False):
    if kind.startswith("As submitted"): continue
    # plain cells, not \\multicolumn: the body is pulled in by \\@input, after which
    # \\multicolumn cannot open a row
    L.append(f"\\textit{{{kind}}} & & & & & \\\\")
    for r in g.itertuples():
        L.append(f"\\quad {100*r.value:.0f}\\% & {r.cons_HQ:.4f} & {r.cons_HI:.3f} & "
                 f"{sci(r.cons_CR)} & {r.hand_HQ:.5f} & {sci(r.hand_CR)} \\\\")
write("si_rev_scenarios_body.tex", L)

# S17  fertilizer-attributable increment by type
inc = rd("rev_increment.csv"); L = []
for t, g in inc.groupby("Type", sort=False):
    a, b = g[g.years == 10].iloc[0], g[g.years == 100].iloc[0]
    L.append(f"{ABBR[t]} & {a.total_HI:.3f} & {a.incr_HI:.4f} & {100*a.incr_share:.1f} & "
             f"{sci(a.incr_CR_AsPb)} & {b.incr_HI:.3f} & {100*b.incr_share:.1f} & {sci(b.incr_CR_AsPb)} \\\\")
    if t == "Neem cake": L.append("\\midrule")
write("si_rev_increment_body.tex", L)

# S18  per-product
pp = rd("rev_per_product.csv"); L = []; prev = None
for r in pp.itertuples():
    lab = ABBR[r.Type] if r.Type != prev else ""; prev = r.Type
    over = r.over if isinstance(r.over, str) and r.over else "--"
    L.append(f"{lab} & {r.Sample} & {over} & {r.hand_HI:.4f} & {sci(r.hand_CR_AsPb)} & "
             f"{sci(r.hand_CR_Cr)} & {r.incr_HI_100:.3f} & {sci(r.incr_CR_AsPb_100)} & "
             f"{r.PLI:.2f} & {r.RI:.0f} & {r.PN:.2f} \\\\")
write("si_rev_perproduct_body.tex", L)

# S19  indices on three bases
bs = rd("rev_basis.csv"); L = []
for t, g in bs.groupby("Type", sort=False):
    v = {r.basis: r for r in g.itertuples()}
    cells = []
    for c in ("PLI", "RI", "PN"):
        cells += [f"{getattr(v[b], c):.2f}" if c != "RI" else f"{getattr(v[b], c):.1f}"
                  for b in ("mean", "median", "excl")]
    L.append(f"{ABBR[t]} & {int(v['excl'].n)} & " + " & ".join(cells) + " \\\\")
write("si_rev_basis_body.tex", L)
bo = rd("rev_basis_overall.csv").set_index("basis"); L = []
for m in ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]:
    L.append(f"{m} & " + " & ".join(yrs(bo.loc[b, f'T_{m}']) for b in ("mean", "median", "excl")) +
             " & " + " & ".join(yrs(bo.loc[b, f'Tccme_{m}']) for b in ("mean", "median", "excl")) + " \\\\")
write("si_rev_basis_tmax_body.tex", L)

# S20  Grubbs outliers
ol = rd("rev_outliers.csv"); L = []
for r in ol.itertuples():
    L.append(f"{r.Element} & {ABBR[r.Type]} & {r.Sample} & {r.Value:.2f} & {r.type_mean:.2f} & "
             f"{r.type_mean_excl:.2f} & {'Yes' if r.over_MAL else 'No'} \\\\")
write("si_rev_outliers_body.tex", L)

# S21  PCA eigenvalues and parallel analysis
pc = rd("rev_pca.csv"); L = []
for r in pc.itertuples():
    L.append(f"{r.Component} & {r.eig_all:.3f} & {r.var_all:.1f} & {r.cum_all:.1f} & {r.pa95_all:.3f} & "
             f"{r.loo_min:.2f}--{r.loo_max:.2f} & {r.eig_excl:.3f} & {r.pa95_excl:.3f} \\\\")
write("si_rev_pca_body.tex", L)

# S22  non-detects
nd = rd("rev_nondetects.csv"); L = []
for r in nd.itertuples():
    L.append(f"{r.Element} & {r.n_ND} & {r.lowest_quantified:.4f} & {r.mean_zero:.4f} & {r.mean_half:.4f} & "
             f"{r.mean_full:.4f} & {r.mean_ROS:.4f} & {r.mean_KM:.4f} \\\\")
write("si_rev_nondetects_body.tex", L)

# S23  soil loading with losses
ls = rd("rev_losses.csv"); L = []
for sn, g in ls.groupby("scenario", sort=False):
    L.append(f"\\textit{{{sn.capitalize()} scenario}} & & & & & & & \\\\")
    for r in g.itertuples():
        L.append(f"\\quad {r.Element} & {r.logKd:.1f} & {1000*(r.k_off+r.k_leach):.2f} & {r.C_ss:.2f} & "
                 f"{yrs(r.T_dutch_noloss)} & {yrs(r.T_dutch_loss)} & {yrs(r.T_ccme_noloss)} & {yrs(r.T_ccme_loss)} \\\\")
write("si_rev_losses_body.tex", L)
# S24  world vs Bangladeshi soil background
bd = rd("rev_bdsoil.csv"); W = bd[bd.set == "World"].set_index("Element"); B = bd[bd.set == "Bangladesh"].set_index("Element")
ty = lambda v: "Exceeded" if v <= 0 else yrs(v)
L = []
for m in ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]:
    w, b = W.loc[m], B.loc[m]
    L.append(f"{m} & {w.Cbv:g} & {b.Cbv:g} & {w.CF:.2f} & {b.CF:.2f} & {w.Igeo:.2f} & {b.Igeo:.2f} & {w.Er:.2f} & {b.Er:.2f} & "
             f"{ty(w.T_dutch)} & {ty(b.T_dutch)} & {ty(w.T_ccme)} & {ty(b.T_ccme)} \\\\")
write("si_rev_bdsoil_body.tex", L)
w, b = W.loc["ALL"], B.loc["ALL"]
L = [f"Mean PLI & {w.PLI:.2f} & {b.PLI:.2f} \\\\", f"Mean RI & {w.RI:.0f} & {b.RI:.0f} \\\\",
     f"Cd share of mean RI (\\%) & {100*W.loc['Cd'].Er_share:.0f} & {100*B.loc['Cd'].Er_share:.0f} \\\\",
     f"Products with PLI $\\geq 1$ & {w.n_PLI_ge1:.0f} & {b.n_PLI_ge1:.0f} \\\\",
     f"Products with RI $\\geq 150$ & {w.n_RI_ge150:.0f} & {b.n_RI_ge150:.0f} \\\\",
     f"Consumer HI & {w.HI:.2f} & {b.HI:.2f} \\\\",
     f"Fertilizer share of consumer HI (\\%) & {100*w.incr_share:.1f} & {100*b.incr_share:.1f} \\\\",
     f"Consumer CR, As+Pb & {sci(w.CR_AsPb)} & {sci(b.CR_AsPb)} \\\\",
     f"Consumer CR, Cr(VI) & {sci(w.CR_Cr)} & {sci(b.CR_Cr)} \\\\"]
write("si_rev_bdsoil_all_body.tex", L)
# S25  calibration standards vs measured range (R1.6); data/calibration_standards.csv
import sys; sys.path.insert(0, HERE)
from qaqc import DIGEST_FACTOR
cs = pd.read_csv(os.path.join(ROOT, "data", "calibration_standards.csv"), comment="#")
cd = pd.read_csv(os.path.join(ROOT, "data", "clean_data.csv"))
mal = pd.read_csv(os.path.join(ROOT, "data", "fertilizer_limits.csv"), comment="#").set_index("Element")["MAL_mgkg"]
fmt = lambda v: f"{v:g}"
L = []
for m in ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]:
    g = cs[cs.Element == m].sort_values("Level")
    k = DIGEST_FACTOR[m] / (1000.0 if g.Unit.iloc[0] == "ug/L" else 1.0)
    lo, hi = g.Level.min() * k, g.Level.max() * k
    x = cd[m]; nb, na = int((x < lo).sum()), int((x > hi).sum())
    unit = "\\si{\\micro g.L^{-1}}" if g.Unit.iloc[0] == "ug/L" else "\\si{mg.L^{-1}}"
    L.append(f"{m} & {', '.join(fmt(v) for v in g.Level)} {unit} & {', '.join(fmt(v) for v in g.RSD_pct)} & "
             f"{lo:g}--{hi:g} & {mal[m]:g} & {x.min():.3g}--{x.max():.3g} & {nb} / {len(x)-nb-na} / {na} \\\\")
write("si_rev_calrange_body.tex", L)
# S1 (revised): per-result data-quality flags (R1.6); exploration/outputs/rev_qflags.csv
qf = rd("rev_qflags.csv").set_index(["Sample", "Element"])
MK = {"<LOQ": "$^{q}$", "below lowest standard": "$^{l}$", "within standards": "",
      "above highest standard": "$^{h}$", "above highest standard, absorbance > 1": "$^{a}$"}
L, prev = [], None
for _, r in cd.iterrows():
    t = r["Type"]; label = t.replace("&", "\\&") if t != prev else ""; prev = t
    vals = []
    for m in ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]:
        if r[m + "_bdl"]: vals.append("$<$LOD"); continue
        vals.append(f"{r[m]:.2f}" + MK[qf.loc[(r.Sample, m), "flag"]])
    L.append(f"{label} & {r['Sample']} & {r['pH']:.2f} & {r['EC']:.2f} & " + " & ".join(vals) + " \\\\")
write("si_fulldata_flagged_body.tex", L)

# S26  Zn sensitivity to under-reading above absorbance 1 (R1.6); rev_zn_sensitivity.csv
zs = rd("rev_zn_sensitivity.csv")
L = []
for _, z in zs.iterrows():
    L.append(f"{z.factor:.2f} & {z.Zn_mean:.1f} & {z.Zn_max:.0f} & {z.Zn_over_MAL:.0f} & {z.Zn_CF:.2f} & {z.Zn_Igeo:.2f} & "
             f"{z.PLI:.2f} & {z.n_PLI_ge1:.0f} & {z.RI:.1f} & {z.n_RI_ge150:.0f} & {z.n_PN_gt1:.0f} & "
             f"{yrs(z.T_Zn_dutch)} & {yrs(z.T_Zn_ccme)} & {z.HI:.2f} & {100*z.incr_share:.1f} \\\\")
write("si_rev_znsens_body.tex", L)
print("Wrote revision table bodies to", TBL)
