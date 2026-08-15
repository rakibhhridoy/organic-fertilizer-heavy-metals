# -*- coding: utf-8 -*-
"""Pollution & ecological risk indices for organic fertilizers.
CF, Igeo, PLI, Nemerow P_N, Hakanson RI, modified degree of contamination (mCd).
Run from manuscript/exploration/ :  python3 scripts/03_indices.py
"""
import os, sys, pandas as pd, numpy as np
import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
ROOT=os.path.dirname(EXP); OUT=os.path.join(EXP,"outputs")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(ROOT,"scripts"))
from soil_refs import CBV as BG, TR as Tr, MAL, METALS as metals

df=pd.read_pickle(os.path.join(ROOT,"data","clean_data.pkl"))
types=["Cow dung","Bone meal","Trichocompost","Generic Organic Fertilizer",
       "Vermicompost","Horn meal","Neem cake"]


# ---- per-sample indices ----
S=df.copy()
for m in metals:
    S["CF_"+m]=df[m]/BG[m]                    # contamination factor (vs background)
    S["Er_"+m]=Tr[m]*S["CF_"+m]               # ecological risk factor
    S["Pi_"+m]=df[m]/MAL[m]                   # single-factor pollution index (vs MAL)
cf_cols=["CF_"+m for m in metals]
pi_cols=["Pi_"+m for m in metals]
S["PLI"]=np.power(S[cf_cols].prod(axis=1), 1.0/len(metals))    # pollution load index
S["mCd"]=S[cf_cols].mean(axis=1)                               # modified degree of contamination
S["RI"]=S[["Er_"+m for m in metals]].sum(axis=1)              # Hakanson RI
S["PN"]=np.sqrt((S[pi_cols].mean(axis=1)**2 + S[pi_cols].max(axis=1)**2)/2)  # Nemerow (vs MAL)

def cls_PLI(v): return "unpolluted" if v<1 else "moderate" if v<2 else "heavy" if v<3 else "extreme"
def cls_RI(v):  return "low" if v<150 else "moderate" if v<300 else "considerable" if v<600 else "very high"
def cls_PN(v):  return "clean" if v<=0.7 else "warning" if v<=1 else "slight" if v<=2 else "moderate" if v<=3 else "heavy"

# ---- per-type summary ----
agg=S.groupby("Type")
summ=pd.DataFrame({
    "PLI":agg["PLI"].mean(),"mCd":agg["mCd"].mean(),
    "RI":agg["RI"].mean(),"PN(vs MAL)":agg["PN"].mean(),
}).reindex(types).round(2)
summ["PLI_class"]=summ["PLI"].map(cls_PLI)
summ["RI_class"]=summ["RI"].map(cls_RI)
summ["PN_class"]=summ["PN(vs MAL)"].map(cls_PN)
print("=== Per-type mean indices ==="); print(summ.to_string())

# mean ecological risk factor per metal (which metal drives RI)
Er_mean=S[["Er_"+m for m in metals]].mean(); Er_mean.index=metals
print("\n=== Mean ecological risk factor Er per metal (overall) ===")
print(Er_mean.round(2).to_string())
print("Overall mean RI = %.1f (%s)" % (S["RI"].mean(), cls_RI(S["RI"].mean())))

summ.to_csv(os.path.join(OUT,"indices_by_type.csv"))
S[["Type","PLI","mCd","RI","PN"]].to_csv(os.path.join(OUT,"indices_by_sample.csv"), index=False)
# Er per metal per type (drives the stacked RI figure; consumed by the D3 build)
agg[["Er_"+m for m in metals]].mean().reindex(types).to_csv(
    os.path.join(OUT,"er_by_type.csv"))

# ---- figure: RI stacked by Er contribution, per type ----
short={"Generic Organic Fertilizer":"Generic OF"}
labels=[short.get(t,t) for t in types]
er_by_type=agg[["Er_"+m for m in metals]].mean().reindex(types)
fig,ax=plt.subplots(figsize=(8,4.6))
bottom=np.zeros(len(types))
colors=plt.cm.tab10(np.linspace(0,1,len(metals)))
for m,c in zip(metals,colors):
    vals=er_by_type["Er_"+m].values
    ax.bar(labels, vals, bottom=bottom, label=m, color=c); bottom+=vals
ax.axhline(150, ls="--", color="grey", lw=1); ax.text(6.4,155,"RI=150 (low|moderate)",fontsize=7,ha="right")
ax.set_ylabel("Potential ecological risk index (RI)")
ax.set_title("Håkanson RI by fertilizer type, stacked by metal contribution (E$_r$)")
ax.legend(ncol=6, fontsize=8, loc="upper center", bbox_to_anchor=(0.5,-0.18))
plt.xticks(rotation=30, ha="right")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_RI_stacked.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(OUT,"fig_RI_stacked.png"), dpi=150, bbox_inches="tight"); plt.close(fig)
print("\nSaved indices_by_type.csv, indices_by_sample.csv, fig_RI_stacked.[pdf|png]")
