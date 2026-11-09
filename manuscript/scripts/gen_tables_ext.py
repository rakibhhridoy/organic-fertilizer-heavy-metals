# -*- coding: utf-8 -*-
"""Emit LaTeX table bodies for the extended analyses (indices, stats, source
apportionment, health risk, Monte Carlo). Reads exploration/outputs/*.csv.
Run:  python3 scripts/gen_tables_ext.py   (from manuscript/)
"""
import os, pandas as pd, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
OUTP=os.path.join(ROOT,"exploration","outputs")
TBL=os.path.join(ROOT,"tables")

def esc(s): return str(s).replace("&","\\&")

# --- Table: pollution & ecological indices by type ---
idx=pd.read_csv(os.path.join(OUTP,"indices_by_type.csv"))
with open(os.path.join(TBL,"table_indices_body.tex"),"w") as f:
    for _,r in idx.iterrows():
        f.write(f"{esc(r['Type'])} & {r['PLI']:.2f} & {r['mCd']:.2f} & {r['RI']:.1f} & "
                f"{esc(r['RI_class'])} & {r['PN(vs MAL)']:.2f} \\\\\n")

# --- Table: KW H, raw p, BH-adjusted p, eta2, Dunn pairs ---
# Significance is claimed on the BH-adjusted p across the 8-variable family.
kw=pd.read_csv(os.path.join(OUTP,"kw_effectsize.csv"))
# Dunn pairs are read from the analysis output rather than transcribed, so the
# table cannot drift from the test that produced it.
ABBR={"Cow dung":"CD","Bone meal":"BM","Trichocompost":"TC",
      "Generic Organic Fertilizer":"GOF","Vermicompost":"VC","Horn meal":"HM",
      "Neem cake":"NC"}
_dp=pd.read_csv(os.path.join(OUTP,"dunn_pairs.csv"))
dunn={}
for m,g in _dp.groupby("Metal"):
    dunn[m]="; ".join(f"{ABBR[a]}--{ABBR[b]}" for a,b in zip(g["GroupA"],g["GroupB"]))
with open(os.path.join(TBL,"table_kw_body.tex"),"w") as f:
    for _,r in kw.iterrows():
        m=r['Metal']; sig="Yes" if r['p_BH']<0.05 else "No"
        f.write(f"{m} & {r['H']:.2f} & {r['p']:.4f} & {r['p_BH']:.4f} & "
                f"{r['eta2']:.3f} & {sig} & {dunn.get(m,'--')} \\\\\n")

# PCA loadings are no longer tabulated: the single retained component is shown
# as an inset bar chart inside the PCA panel (see scripts/figures_d3/fig_pca.mjs,
# fed from varimax_loadings.csv via export_fig_data.py).
_stale_load=os.path.join(TBL,"table_loadings_body.tex")
if os.path.exists(_stale_load):
    os.remove(_stale_load); print("removed stale table_loadings_body.tex")

# --- SI Table: forced 2-component solution (transparency / robustness) ---
load2=pd.read_csv(os.path.join(OUTP,"varimax_loadings_2comp.csv"), index_col=0)
with open(os.path.join(TBL,"si_loadings2_body.tex"),"w") as f:
    for m,row in load2.iterrows():
        f.write(m+" & "+" & ".join(f"{v:.2f}" for v in row.values)+" \\\\\n")

# APCS-MLR table deliberately not generated (analysis dropped; see 04_stats_source.py).
_stale=os.path.join(TBL,"si_apcs_body.tex")
if os.path.exists(_stale): os.remove(_stale); print("removed stale si_apcs_body.tex")

# --- Table: health risk (HI, CR) ---
# Handler pathway is reported per fertilizer type: it is driven by the product
# itself and discriminates between categories. Consumer pathway is reported as an
# overall total (background + 10-year increment) and, separately, as the
# fertilizer-attributable increment alone, because the total is dominated by the
# assumed soil background (revision, R1.3). Cancer risk is As+Pb, with the Cr(VI)
# term in its own column because it rests on an assumed Cr(VI) fraction (R1.1).
def sci(v):
    m, e = f"{v:.2e}".split("e")
    return f"${m}\\times10^{{{int(e)}}}$"
hr=pd.read_csv(os.path.join(OUTP,"health_risk.csv"))
with open(os.path.join(TBL,"table_health_body.tex"),"w") as f:
    sub=hr[(hr["Scenario"]=="Handler")].reset_index(drop=True)
    for i,r in sub.iterrows():
        scen_lbl = "\\textit{Handler}" if i==0 else ""
        name = ("\\textbf{Overall}" if r['Type']=="OVERALL" else esc(r['Type']))
        f.write(f"{scen_lbl} & {name} & {r['HI']:.4f} & {sci(r['CR_AsPb'])} & {sci(r['CR_Cr'])} \\\\\n")
    f.write("\\midrule\n")
    c=hr[(hr["Scenario"]=="Consumer") & (hr["Type"]=="OVERALL")].iloc[0]
    f.write(f"\\textit{{Consumer}} & Total (background + increment) & {c['HI']:.3f} & "
            f"{sci(c['CR_AsPb'])} & {sci(c['CR_Cr'])} \\\\\n")
    f.write(f" & Fertilizer increment only & {c['HI_incr']:.4f} & "
            f"{sci(c['CR_AsPb_incr'])} & {sci(c['CR_Cr_incr'])} \\\\\n")

# --- Table: Monte Carlo soil accumulation ---
mc=pd.read_csv(os.path.join(OUTP,"mc_soil_accumulation.csv"))
with open(os.path.join(TBL,"table_mcsoil_body.tex"),"w") as f:
    for _,r in mc.iterrows():
        f.write(f"{r['Metal']} & {r['Tmax_median']:.0f} & {r['Tmax_P5']:.0f} & "
                f"{r['P_exceed_50y']:.4f} & {r['P_exceed_100y']:.4f} \\\\\n")

# --- SI Table: HHRA parameters ---
import importlib.util
spec=importlib.util.spec_from_file_location("P", os.path.join(ROOT,"exploration","scripts","params_hhra.py"))
P=importlib.util.module_from_spec(spec); spec.loader.exec_module(P)
with open(os.path.join(TBL,"si_hhra_params_body.tex"),"w") as f:
    for m in P.metals:
        sf = "--" if P.SF_o[m] is None else f"{P.SF_o[m]:g}"
        lab = "Cr(VI)" if m=="Cr" else m
        f.write(f"{lab} & {P.RfD_o[m]:g} & {P.GIABS[m]:g} & {P.ABS_d[m]:g} & {sf} & "
                f"{P.BG_SOIL[m]:g} & {P.TF[m]:g} \\\\\n")
        if m=="Cr":
            f.write(f"Cr(III) & {P.RfD_CR3:g} & {P.GIABS_CR3:g} & {P.ABS_d[m]:g} & -- & "
                    f"(total Cr) & (total Cr) \\\\\n")

print("Wrote extended table bodies to", TBL)
