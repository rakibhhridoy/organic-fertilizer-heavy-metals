# -*- coding: utf-8 -*-
"""Advanced statistics & source apportionment.
Dunn's post-hoc (BH), epsilon-squared effect size, HCA dendrogram,
varimax-rotated factor loadings, APCS-MLR source apportionment (exploratory).
Run:  python3 scripts/04_stats_source.py   (from manuscript/exploration/)
"""
import os, numpy as np, pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, dendrogram
import scikit_posthocs as sp
import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
ROOT=os.path.dirname(EXP); OUT=os.path.join(EXP,"outputs")
df=pd.read_pickle(os.path.join(ROOT,"data","clean_data.pkl"))
metals=["Cu","Cr","Pb","Cd","Zn","Ni"]
types=["Cow dung","Bone meal","Trichocompost","Generic Organic Fertilizer",
       "Vermicompost","Horn meal","Neem cake"]

# ---- Kruskal-Wallis effect size (eta-squared) + Dunn's post-hoc ----
# eta^2[H] = (H - k + 1)/(n - k)  (Cohen; via rcompanion). NB: distinct from
# epsilon^2 = H/(n-1). We report eta-squared and label it as such.
N=len(df); k=len(types)
print("=== Kruskal-Wallis H, eta^2, BH-adjusted p, and Dunn pairs ===")
# The omnibus KW is run over a family of 8 response variables (6 metals + pH + EC).
# Raw p-values are therefore BH-adjusted ACROSS that family before significance is
# claimed; eta^2 is truncated at 0, since (H-k+1)/(N-k) can go negative when
# H < k-1 and a negative variance-explained is not interpretable.
fam=metals+["pH","EC"]
raw={}
for m in fam:
    H,p=stats.kruskal(*[g[m].values for _,g in df.groupby("Type")])
    raw[m]=(H,p)

def bh(pvals):
    """Benjamini-Hochberg step-up adjusted p-values."""
    items=sorted(pvals.items(), key=lambda x:x[1]); n=len(items); adj={}; prev=1.0
    for i in range(n-1,-1,-1):
        name,p=items[i]
        prev=min(prev, p*n/(i+1)); adj[name]=min(prev,1.0)
    return adj

padj=bh({m:raw[m][1] for m in fam})

eff=[]; dunn_rows=[]
for m in metals:
    H,p=raw[m]
    eta2=max(0.0,(H-k+1)/(N-k))   # truncated at 0
    eff.append((m,round(H,2),round(p,4),round(padj[m],4),round(eta2,3)))
    tag="sig(BH)" if padj[m]<0.05 else ("marginal(raw only)" if p<0.05 else "n.s.")
    if padj[m]<0.05:
        d=sp.posthoc_dunn(df, val_col=m, group_col="Type", p_adjust="fdr_bh")
        pairs=[(a,b,round(d.loc[a,b],3)) for i,a in enumerate(d.index) for b in d.columns[i+1:] if d.loc[a,b]<0.05]
        for a,b,pp in pairs: dunn_rows.append((m,a,b,pp))
        print(f"  {m}: H={H:.2f} p={p:.4f} p_BH={padj[m]:.4f} eta2={eta2:.3f} [{tag}] -> "+
              ("; ".join(f'{a}~{b}(p={pp})' for a,b,pp in pairs) if pairs else "no pair survives BH"))
    else:
        print(f"  {m}: H={H:.2f} p={p:.4f} p_BH={padj[m]:.4f} eta2={eta2:.3f} [{tag}]")
for m in ["pH","EC"]:
    H,p=raw[m]
    print(f"  {m}: H={H:.2f} p={p:.4f} p_BH={padj[m]:.4f} "
          f"[{'sig(BH)' if padj[m]<0.05 else 'n.s.'}]")
pd.DataFrame(eff,columns=["Metal","H","p","p_BH","eta2"]).to_csv(os.path.join(OUT,"kw_effectsize.csv"),index=False)
# Significant Dunn pairs, consumed by the SI table and the significance brackets
# in Fig. 1. Exported rather than hard-coded so the two cannot drift apart.
pd.DataFrame(dunn_rows,columns=["Metal","GroupA","GroupB","p_BH"]).to_csv(
    os.path.join(OUT,"dunn_pairs.csv"),index=False)
pd.Series(padj).to_csv(os.path.join(OUT,"kw_padj_family.csv"),header=["p_BH"])

# ---- Hierarchical cluster analysis of fertilizer types (mean z-profiles) ----
means=df.groupby("Type")[metals].mean().reindex(types)
Z=(means-means.mean())/means.std()
link=linkage(Z.values, method="ward")
short={"Generic Organic Fertilizer":"Generic OF"}
fig,ax=plt.subplots(figsize=(7,4))
dendrogram(link, labels=[short.get(t,t) for t in types], ax=ax, leaf_rotation=30)
ax.set_ylabel("Ward distance"); ax.set_title("Hierarchical clustering of fertilizer types (heavy-metal profile)")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_dendrogram.pdf"),bbox_inches="tight")
fig.savefig(os.path.join(OUT,"fig_dendrogram.png"),dpi=150,bbox_inches="tight"); plt.close(fig)

# ---- PCA + varimax rotation of loadings ----
# PCA/APCS-MLR are Pearson-based and are therefore run on LOG-TRANSFORMED
# concentrations. Running them on the raw values is inconsistent with the
# non-parametric treatment used above (chosen because the metals are skewed with
# extreme values), and it is not robust: on raw data the second factor is defined
# almost solely by Cr (loading -0.99), an artefact driven by the single
# 306.7 mg/kg vermicompost sample. Under log (and equally under rank)
# transformation that factor resolves as a joint Cr-Zn-Pb component. The log
# solution is reported as primary; see audit note in the manuscript SI.
X=np.log(df[metals].values); Xz=(X-X.mean(0))/X.std(0)
U,S,Vt=np.linalg.svd(Xz,full_matrices=False)
eig=S**2/len(X)                            # correlation-matrix eigenvalues
evr=eig/eig.sum()
ncomp=int((eig>1).sum())                    # Kaiser criterion (eigenvalue > 1)
scores_all=U*S
# structure loadings = correlation between each variable and each PC score
# (guaranteed |loading| <= 1, unlike the eigvec*sqrt(eig) shortcut)
load=np.array([[np.corrcoef(Xz[:,i], scores_all[:,j])[0,1] for j in range(ncomp)]
               for i in range(len(metals))])

def varimax(Phi,q=50,tol=1e-6):
    p,k=Phi.shape; R=np.eye(k); d=0
    for _ in range(q):
        L=Phi@R
        u,s,vt=np.linalg.svd(Phi.T@(L**3-(L@np.diag(np.diag(L.T@L)/p))))
        R=u@vt; d_old=d; d=s.sum()
        if d_old!=0 and d/d_old<1+tol: break
    return Phi@R
Lrot=varimax(load) if ncomp>1 else load
print(f"\n=== PCA (log scale): eigenvalues {np.round(eig,3)} ===")
print(f"    Kaiser retains {ncomp} component(s); cum. variance {evr[:ncomp].sum()*100:.1f}%")
loaddf=pd.DataFrame(np.round(Lrot,2), index=metals, columns=[f"PC{i+1}" for i in range(ncomp)])
print("Loadings (primary solution):"); print(loaddf.to_string())
loaddf.to_csv(os.path.join(OUT,"varimax_loadings.csv"))

# Two-component solution reported for transparency: PC2 sits just below the
# Kaiser threshold (eigenvalue ~0.97), and on the RAW scale a two-factor solution
# is what produced the apparent "Cr-specific source". Forcing two components on
# the log scale shows that second axis is a joint Cr-Zn-Pb contrast, not Cr alone.
load2=np.array([[np.corrcoef(Xz[:,i],scores_all[:,j])[0,1] for j in range(2)]
                for i in range(len(metals))])
L2=varimax(load2)
load2df=pd.DataFrame(np.round(L2,2), index=metals, columns=["PC1","PC2"])
print(f"\n=== Forced 2-component solution (cum. variance {evr[:2].sum()*100:.1f}%) ===")
print(load2df.to_string())
load2df.to_csv(os.path.join(OUT,"varimax_loadings_2comp.csv"))

# ---- APCS-MLR: NOT REPORTED ----
# Deliberately dropped. Classical APCS defines absolute scores against a
# hypothetical zero-concentration sample, which is undefined on the log scale
# (log 0 -> -inf). More decisively, the log-scale PCA retains a SINGLE component,
# under which apportionment is degenerate: every metal is assigned 100% to the
# one factor, which carries no information. The apparent "97.5% of Cr from a
# Cr-specific source" reported in earlier drafts was an artefact of running a
# Pearson-based decomposition on raw, extreme-value-dominated concentrations.
# Retained here as a comment so the omission is deliberate and traceable.
_apcs_dropped = ("APCS-MLR omitted: degenerate under the 1-component log-scale "
                 "solution; prior raw-scale result was outlier-driven.")
print("\n=== APCS-MLR: omitted ===")
print("  " + _apcs_dropped)
for f in ("apcs_contributions.csv",):
    p=os.path.join(OUT,f)
    if os.path.exists(p): os.remove(p); print(f"  removed stale {f}")

print("\nSaved kw_effectsize.csv, kw_padj_family.csv, fig_dendrogram, "
      "varimax_loadings.csv, varimax_loadings_2comp.csv")
