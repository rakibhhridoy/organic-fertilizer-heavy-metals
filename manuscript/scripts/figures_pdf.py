# -*- coding: utf-8 -*-
"""Generate the four manuscript figures as vector PDF from the cleaned dataset.
Run:  python3 scripts/figures_pdf.py   (from the manuscript/ directory)
"""
import os, pandas as pd, numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "savefig.dpi": 300, "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT  = os.path.join(ROOT, "figures")
os.makedirs(OUT, exist_ok=True)
df = pd.read_pickle(os.path.join(ROOT, "data", "clean_data.pkl"))

metals = ["Cu","Cr","Pb","Cd","Zn","Ni"]
MAL = {"Cu":500,"Cr":50,"Pb":30,"Cd":5,"Zn":1000,"Ni":30}
types = ["Cow dung","Bone meal","Trichocompost","Generic Organic Fertilizer",
         "Vermicompost","Horn meal","Neem cake"]
short = {"Generic Organic Fertilizer":"Generic OF"}
labels = [short.get(t,t) for t in types]
palette = plt.cm.Set2(np.linspace(0,1,len(types)))

# Fig 1 boxplots
fig, axes = plt.subplots(2, 3, figsize=(11, 6.5))
for ax, m in zip(axes.flat, metals):
    data=[df[df["Type"]==t][m].values for t in types]
    bp=ax.boxplot(data, patch_artist=True, widths=0.6, medianprops=dict(color="black"))
    for patch,c in zip(bp["boxes"],palette): patch.set_facecolor(c); patch.set_alpha(0.85)
    lim=MAL[m]; ymax=max(df[m].max(),lim)*1.08
    if lim<=ymax:
        ax.axhline(lim, ls="--", lw=1.2, color="#c0392b")
        ax.text(0.98, lim, f" MAL {lim}", color="#c0392b", va="bottom", ha="right",
                transform=ax.get_yaxis_transform(), fontsize=7)
    ax.set_title(f"{m} (ppm)"); ax.set_xticks(range(1,len(types)+1))
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=7)
fig.suptitle("Heavy metal concentrations by organic fertilizer type (dashed = Bangladesh MAL)", y=1.0)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig1_boxplots.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 2 heatmap
mean_tbl=df.groupby("Type")[metals].mean().reindex(types)
pct=mean_tbl.copy()
for m in metals: pct[m]=mean_tbl[m]/MAL[m]*100
fig,ax=plt.subplots(figsize=(7,4.2))
im=ax.imshow(pct.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=100)
ax.set_xticks(range(len(metals))); ax.set_xticklabels(metals)
ax.set_yticks(range(len(types))); ax.set_yticklabels(labels)
for i in range(len(types)):
    for j in range(len(metals)):
        v=pct.values[i,j]
        ax.text(j,i,f"{mean_tbl.values[i,j]:.1f}", ha="center", va="center",
                fontsize=7, color="black" if v<60 else "white")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04).set_label("Mean as % of MAL")
ax.set_title("Mean concentration (ppm) and proximity to Bangladesh MAL")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig2_heatmap.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 3 correlation
corr=df[metals].corr(method="spearman")
fig,ax=plt.subplots(figsize=(5,4.2))
im=ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(metals))); ax.set_xticklabels(metals)
ax.set_yticks(range(len(metals))); ax.set_yticklabels(metals)
for i in range(len(metals)):
    for j in range(len(metals)):
        ax.text(j,i,f"{corr.values[i,j]:.2f}", ha="center", va="center", fontsize=8,
                color="white" if abs(corr.values[i,j])>0.6 else "black")
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Spearman rho")
ax.set_title("Inter-metal correlation (Spearman)")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig3_corr.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 4 PCA -- on LOG-transformed concentrations, to match the analysis in
# 04_stats_source.py. A raw-scale ordination is dominated by the single 306.7
# mg/kg Cr sample and produces a spurious Cr-only second axis.
X=np.log(df[metals].values); Xz=(X-X.mean(0))/X.std(0)
U,S,Vt=np.linalg.svd(Xz, full_matrices=False); scores=U*S
evr=S**2/(S**2).sum()
fig,ax=plt.subplots(figsize=(6.2,5))
for t,c in zip(types,palette):
    mask=(df["Type"]==t).values
    ax.scatter(scores[mask,0], scores[mask,1], color=c, s=45, edgecolor="k",
               linewidth=0.4, label=short.get(t,t))
for j,m in enumerate(metals):
    ax.arrow(0,0, Vt[0,j]*3, Vt[1,j]*3, color="grey", width=0.01, head_width=0.12, alpha=0.7)
    ax.text(Vt[0,j]*3.3, Vt[1,j]*3.3, m, fontsize=8, ha="center")
ax.set_xlabel(f"PC1 ({evr[0]*100:.0f}%)"); ax.set_ylabel(f"PC2 ({evr[1]*100:.0f}%)")
ax.legend(fontsize=7, loc="best", framealpha=0.9)
ax.set_title("PCA of fertilizer samples by heavy metal profile (log scale)")
ax.axhline(0,color="grey",lw=0.5); ax.axvline(0,color="grey",lw=0.5)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig4_pca.pdf"), bbox_inches="tight"); plt.close(fig)

print("Saved fig1-4 .pdf to", OUT)
