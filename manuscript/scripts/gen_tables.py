# -*- coding: utf-8 -*-
"""Emit LaTeX table bodies (booktabs) from the cleaned dataset. Reproducible.
Run:  python3 scripts/gen_tables.py   (from the manuscript/ directory)
"""
import os, sys, pandas as pd, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
TBL  = os.path.join(ROOT, "tables")
os.makedirs(TBL, exist_ok=True)

df = pd.read_pickle(os.path.join(DATA, "clean_data.pkl"))
types = ["Cow dung","Bone meal","Trichocompost","Generic Organic Fertilizer",
         "Vermicompost","Horn meal","Neem cake"]
sys.path.insert(0, HERE)
from soil_refs import MAL, METALS as metals

def esc(t): return t.replace("&","\\&")

with open(os.path.join(TBL,"table1_body.tex"),"w") as f:
    for t in types:
        g = df[df["Type"]==t]
        cells = [f"{g['pH'].mean():.2f}", f"{g['EC'].mean():.2f}"] + \
                [f"{g[m].mean():.2f} $\\pm$ {g[m].std():.2f}" for m in metals]
        f.write(f"{esc(t)} & " + " & ".join(cells) + " \\\\\n")
    f.write("\\midrule\n")
    g = df
    cells = [f"{g['pH'].mean():.2f}", f"{g['EC'].mean():.2f}"] + \
            [f"{g[m].mean():.2f} $\\pm$ {g[m].std():.2f}" for m in metals]
    f.write("\\textbf{Overall} & " + " & ".join(cells) + " \\\\\n")

def thou(x): return f"{x:,.0f}".replace(",", "{,}")

rl = pd.read_csv(os.path.join(DATA,"risk_loading.csv"))
with open(os.path.join(TBL,"table2_body.tex"),"w") as f:
    for _,r in rl.iterrows():
        f.write(f"{r['Metal']} & {r['Conc_mgkg']:.2f} & {r['Load_g_ha_yr']:.1f} & "
                f"{r['dSoil_mgkg_yr']:.4f} & {thou(r['Yrs_to_limit'])} & "
                f"{thou(r['Yrs_to_limit_strict'])} \\\\\n")

with open(os.path.join(TBL,"table3_body.tex"),"w") as f:
    for m in ["Cd","Pb","Cr","Ni","Zn","Cu","As"]:
        ex = df[df[m] > MAL[m]]
        osr = 100*len(ex)/len(df)
        rng = f"{df[m].min():.2f}--{df[m].max():.2f}"
        which = ", ".join(sorted({esc(t) for t in ex['Type']})) if len(ex) else "--"
        f.write(f"{m} & {MAL[m]:g} & {rng} & {df[m].mean():.2f} & {len(ex)} & {osr:.1f} & {which} \\\\\n")

# SI Kruskal-Wallis table: raw and BH-adjusted p across the 9-variable family.
fam = metals+["pH","EC"]
_raw = {m: stats.kruskal(*[g[m].values for _,g in df.groupby("Type")]) for m in fam}
_items = sorted(((m, _raw[m][1]) for m in fam), key=lambda x: x[1])
_padj, _prev = {}, 1.0
for _i in range(len(_items)-1, -1, -1):
    _n, _p = _items[_i]
    _prev = min(_prev, _p*len(_items)/(_i+1)); _padj[_n] = min(_prev, 1.0)
# eta-squared and the significant Dunn pairs come from the analysis outputs, so
# the SI table and the Fig. 1 effect-size panel cannot disagree.
_eff = pd.read_csv(os.path.join(ROOT,"exploration","outputs","kw_effectsize.csv")
                   ).set_index("Metal")
_dunn = pd.read_csv(os.path.join(ROOT,"exploration","outputs","dunn_pairs.csv"))
_ABBR = {"Cow dung":"CD","Bone meal":"BM","Trichocompost":"TC",
         "Generic Organic Fertilizer":"GOF","Vermicompost":"VC",
         "Horn meal":"HM","Neem cake":"NC"}
_pairs = {}
for r in _dunn.itertuples():
    _pairs.setdefault(r.Metal, []).append(
        f"{_ABBR.get(r.GroupA,r.GroupA)}--{_ABBR.get(r.GroupB,r.GroupB)}")
with open(os.path.join(TBL,"si_kw_body.tex"),"w") as f:
    for m in fam:
        H,p = _raw[m]
        e = f"{_eff.loc[m,'eta2']:.3f}" if m in _eff.index else "--"
        dn = "; ".join(_pairs.get(m, [])) or "--"
        f.write(f"{m} & {H:.2f} & {p:.4f} & {_padj[m]:.4f} & {e} & "
                f"{'Yes' if _padj[m]<0.05 else 'No'} & {dn} \\\\\n")

corr = df[metals].corr(method="spearman")
with open(os.path.join(TBL,"si_corr_body.tex"),"w") as f:
    for i,mi in enumerate(metals):
        row=[mi]+[f"{corr.values[i,j]:.2f}" if j<=i else "" for j in range(len(metals))]
        f.write(" & ".join(row)+" \\\\\n")

with open(os.path.join(TBL,"si_fulldata_body.tex"),"w") as f:
    prev=None
    for _,r in df.iterrows():
        t=r["Type"]; label=esc(t) if t!=prev else ""; prev=t
        supplier=esc(r["Brand"]) + (f" ({r['Pack']})" if r["Pack"] else "")
        vals=["$<$LOD" if r[m+"_bdl"] else f"{r[m]:.2f}" for m in metals]
        f.write(f"{label} & {r['Sample']} & {supplier} & "
                f"{r['pH']:.2f} & {r['EC']:.2f} & " + " & ".join(vals) + " \\\\\n")

with open(os.path.join(TBL,"si_desc_body.tex"),"w") as f:
    for m in metals:
        s=df[m]
        f.write(f"{m} & {s.mean():.2f} & {s.std():.2f} & {s.median():.2f} & "
                f"{s.min():.2f} & {s.max():.2f} & {100*s.std()/s.mean():.1f} \\\\\n")

print("Wrote LaTeX table bodies to", TBL)
