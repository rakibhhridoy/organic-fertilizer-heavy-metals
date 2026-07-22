# -*- coding: utf-8 -*-
"""Export every figure's data as JSON for the D3 build (scripts/figures_d3/).
Single writer to figures/data/*.json. Run after the analysis pipeline:
    python3 scripts/export_fig_data.py   (from manuscript/)

Reads: data/clean_data.pkl, data/soil_reference_values.csv,
       exploration/outputs/{er_by_type,mc_soil_accumulation,mc_figures}.* .
"""
import os, sys, json, numpy as np, pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, to_tree

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from soil_refs import CBV, CSV, TR, METALS as metals

DATA = os.path.join(ROOT, "data")
EXP  = os.path.join(ROOT, "exploration", "outputs")
OUT  = os.path.join(ROOT, "figures", "data")
os.makedirs(OUT, exist_ok=True)

df = pd.read_pickle(os.path.join(DATA, "clean_data.pkl"))
types = ["Cow dung", "Bone meal", "Trichocompost", "Generic Organic Fertilizer",
         "Vermicompost", "Horn meal", "Neem cake"]
SHORT = {"Generic Organic Fertilizer": "Generic OF"}
MAL = {"Cu": 500, "Cr": 50, "Pb": 30, "Cd": 5, "Zn": 1000, "Ni": 30}


def dump(name, obj):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f, separators=(",", ":"))
    print("  wrote figures/data/" + name)


def q(v, p):
    return float(np.percentile(v, p))


# ---- Fig 1: boxplots (log y), per metal per type ----
box = {"metals": metals, "MAL": MAL,
       "types": [SHORT.get(t, t) for t in types], "panels": {}}
for m in metals:
    panel = []
    for t in types:
        v = df.loc[df.Type == t, m].values
        panel.append({
            "type": SHORT.get(t, t),
            "min": float(v.min()), "q1": q(v, 25), "med": q(v, 50),
            "q3": q(v, 75), "max": float(v.max()),
            "points": [round(float(x), 4) for x in v],
        })
    box["panels"][m] = panel

# Kruskal-Wallis effect sizes + significant Dunn pairs, so Fig. 1 can carry the
# test result alongside the distributions it describes. Read from the analysis
# outputs, never re-derived here.
_kw = pd.read_csv(os.path.join(EXP, "kw_effectsize.csv")).set_index("Metal")
box["kw"] = [{"metal": m, "H": float(_kw.loc[m, "H"]),
              "p": float(_kw.loc[m, "p"]), "pBH": float(_kw.loc[m, "p_BH"]),
              "eta2": float(_kw.loc[m, "eta2"]),
              "sig": bool(_kw.loc[m, "p_BH"] < 0.05)} for m in metals]
_dp = pd.read_csv(os.path.join(EXP, "dunn_pairs.csv"))
box["dunn"] = [{"metal": r.Metal, "a": SHORT.get(r.GroupA, r.GroupA),
                "b": SHORT.get(r.GroupB, r.GroupB), "pBH": float(r.p_BH)}
               for r in _dp.itertuples()]
dump("fig1_box.json", box)

# ---- Fig 2: mean-concentration heatmap, coloured by % of MAL ----
gmean = df.groupby("Type")[metals].mean().reindex(types)
heat = {"metals": metals, "types": [SHORT.get(t, t) for t in types], "cells": []}
for t in types:
    for m in metals:
        val = float(gmean.loc[t, m])
        heat["cells"].append({"type": SHORT.get(t, t), "metal": m,
                              "value": round(val, 3),
                              "pctMAL": round(100 * val / MAL[m], 2)})
dump("fig2_heatmap.json", heat)

# ---- Fig 3: Spearman correlation matrix ----
corr = df[metals].corr("spearman")
pmat = pd.DataFrame(index=metals, columns=metals, dtype=float)
for a in metals:
    for b in metals:
        pmat.loc[a, b] = stats.spearmanr(df[a], df[b])[1]
cor = {"metals": metals, "cells": []}
for a in metals:
    for b in metals:
        cor["cells"].append({"x": b, "y": a,
                            "r": round(float(corr.loc[a, b]), 3),
                            "p": round(float(pmat.loc[a, b]), 4)})
dump("fig3_corr.json", cor)

# ---- Fig 4: PCA (log scale) sample scores + loadings ----
X = np.log(df[metals].values); Xz = (X - X.mean(0)) / X.std(0)
U, S, Vt = np.linalg.svd(Xz, full_matrices=False)
evr = (S ** 2 / (S ** 2).sum())
scores = U * S
pca = {"varPC1": round(float(evr[0]) * 100, 1),
       "varPC2": round(float(evr[1]) * 100, 1),
       "types": [SHORT.get(t, t) for t in types], "points": [], "loadings": []}
tcode = df["Type"].values
for i in range(len(df)):
    pca["points"].append({"type": SHORT.get(tcode[i], tcode[i]),
                          "pc1": round(float(scores[i, 0]), 4),
                          "pc2": round(float(scores[i, 1]), 4)})
for j, m in enumerate(metals):
    pca["loadings"].append({"metal": m,
                            "pc1": round(float(Vt[0, j]), 4),
                            "pc2": round(float(Vt[1, j]), 4)})
# Structure loadings (variable-to-PC1 correlations) for the inset bar chart.
# Read from the analysis output rather than recomputed here, so the figure and
# the reported values cannot drift apart.
_sl = pd.read_csv(os.path.join(EXP, "varimax_loadings.csv"), index_col=0)
pca["structureLoadings"] = [{"metal": m, "pc1": round(float(_sl.loc[m, "PC1"]), 3)}
                            for m in metals]
dump("fig4_pca.json", pca)

# ---- Fig RI: Håkanson RI stacked by metal Er, per type ----
er = pd.read_csv(os.path.join(EXP, "er_by_type.csv"), index_col=0)
er.columns = [c.replace("Er_", "") for c in er.columns]
ri = {"metals": metals, "threshold": 150, "types": [], "stacks": []}
for t in types:
    row = {"type": SHORT.get(t, t), "total": round(float(er.loc[t].sum()), 2)}
    for m in metals:
        row[m] = round(float(er.loc[t, m]), 3)
    ri["stacks"].append(row)
ri["types"] = [SHORT.get(t, t) for t in types]
dump("fig_ri.json", ri)

# ---- Fig dendrogram: Ward linkage of type mean z-profiles ----
means = df.groupby("Type")[metals].mean().reindex(types)
Z = (means - means.mean()) / means.std()
link = linkage(Z.values, method="ward")
root = to_tree(link)


def node_json(n):
    if n.is_leaf():
        return {"name": SHORT.get(types[n.id], types[n.id]), "height": 0.0}
    return {"height": round(float(n.dist), 4),
            "children": [node_json(n.left), node_json(n.right)]}


dump("fig_dendro.json", {"tree": node_json(root),
                        "maxHeight": round(float(root.dist), 4)})

# ---- Soil loading / time-to-limit (deterministic, from 02_risk.py) ----
rl = pd.read_csv(os.path.join(DATA, "risk_loading.csv")).set_index("Metal")
dump("fig_tmax.json", {
    "metals": metals,
    "bounds": [
        {"key": "dutch",  "label": "Dutch intervention"},
        {"key": "strict", "label": "CCME agricultural"},
    ],
    "rows": [{"metal": m,
              "load": round(float(rl.loc[m, "Load_g_ha_yr"]), 1),
              "dutch": float(rl.loc[m, "Yrs_to_limit"]),
              "strict": float(rl.loc[m, "Yrs_to_limit_strict"])}
             for m in metals],
})

# ---- Pollution indices by type (PLI, mCd, Nemerow) ----
idx = pd.read_csv(os.path.join(EXP, "indices_by_type.csv")).set_index("Type")
dump("fig_indices.json", {
    "types": [SHORT.get(t, t) for t in types],
    "series": [
        {"key": "PLI", "label": "PLI", "threshold": 1},
        {"key": "mCd", "label": "mCd", "threshold": 1.5},
        {"key": "PN",  "label": "P$_N$ (vs MAL)", "threshold": 1},
    ],
    "rows": [{"type": SHORT.get(t, t),
              "PLI": round(float(idx.loc[t, "PLI"]), 3),
              "mCd": round(float(idx.loc[t, "mCd"]), 3),
              "PN":  round(float(idx.loc[t, "PN(vs MAL)"]), 3)}
             for t in types],
})

# ---- Health risk point estimates by scenario/type ----
hr = pd.read_csv(os.path.join(EXP, "health_risk.csv"))
hand = hr[(hr.Scenario == "Handler") & (hr.Type != "OVERALL")]
overall = {r.Scenario: {"HI": float(r.HI), "CR": float(r.CancerRisk)}
           for r in hr[hr.Type == "OVERALL"].itertuples()}
dump("fig_health.json", {
    "types": [SHORT.get(t, t) for t in types],
    "handler": [{"type": SHORT.get(r.Type, r.Type), "HI": float(r.HI),
                 "CR": float(r.CancerRisk)} for r in hand.itertuples()],
    "overall": overall,
})

# ---- Fig MC exceedance + risk histograms (computed in 06_montecarlo) ----
with open(os.path.join(EXP, "mc_figures.json")) as f:
    mc = json.load(f)
mc["metals"] = metals
dump("fig_mc.json", mc)

print("Done. figures/data/ JSON refreshed.")
