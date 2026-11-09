# -*- coding: utf-8 -*-
"""Sensitivity and robustness analyses added in the HAZADV-D-26-02471 revision.
Run:  python3 scripts/07_revision_sensitivity.py   (from manuscript/exploration/)
Reuses the risk models of 05_health_risk.py. Writes exploration/outputs/rev_*.csv,
which scripts/gen_tables_rev.py turns into the Supplementary tables.

  rev_scenarios.csv     Cr(VI) fraction and inorganic-As fraction scenarios  (R1.1, R1.2)
  rev_increment.csv     fertilizer-attributable consumer risk by type, 10/50/100 yr (R1.3)
  rev_per_product.csv   batch-level risk and indices for all 35 products     (R1.12)
  rev_basis.csv         indices by type on mean / median / outlier-excluded  (R6.4)
  rev_basis_overall.csv Tmax and risk on the same three bases                (R6.4, R1.14)
  rev_outliers.csv      Grubbs-flagged values                                (R1.14)
  rev_pca.csv           eigenvalues, parallel analysis, outlier influence    (R3.1, R1.7, R1.14)
  rev_nondetects.csv    substitution vs ROS vs Kaplan-Meier                  (R1.13)
  rev_losses.csv        soil loading with crop offtake and leaching          (R1.4)
  rev_bdsoil.csv        world-soil vs Bangladeshi soil background            (R1.9)
"""
import os, sys, importlib.util
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); EXP = os.path.dirname(HERE)
ROOT = os.path.dirname(EXP); OUT = os.path.join(EXP, "outputs")
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import params_hhra as P
from soil_refs import CBV, CBV_BD, CSV, CSV_STRICT, TR, MAL, METALS as metals
_spec = importlib.util.spec_from_file_location("hr", os.path.join(HERE, "05_health_risk.py"))
hr = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(hr)

df = pd.read_pickle(os.path.join(ROOT, "data", "clean_data.pkl"))
types = hr.types
Cmean = df[metals].mean()
S = lambda d: sum(d.values())
W0 = 2.6e6; M0 = 5000.0

# ---- Cr(VI) and inorganic-As scenarios (deterministic, overall mean) ----
rows = []
for f6 in (0.01, 0.05, P.CR6_FRACTION, 0.30, 1.0):
    hq, cr = hr.consumer_HQ_CR(Cmean, f6=f6); hh, hc = hr.handler_HQ_CR(Cmean, f6=f6)
    rows.append(dict(kind="Cr(VI) fraction", value=f6, cons_HQ=hq["Cr"], cons_HI=S(hq),
                     cons_CR=cr["Cr"], hand_HQ=hh["Cr"], hand_CR=hc["Cr"]))
for fi in (1.0, 0.75, 0.50, 0.25):
    hq, cr = hr.consumer_HQ_CR(Cmean, f_ias=fi); hh, hc = hr.handler_HQ_CR(Cmean, f_ias=fi)
    rows.append(dict(kind="Inorganic As fraction", value=fi, cons_HQ=hq["As"], cons_HI=S(hq),
                     cons_CR=cr["As"], hand_HQ=hh["As"], hand_CR=hc["As"]))
# the submitted model, for the record: Cr(VI) RfD applied to total Cr in the HQ
sub = {m: v for m, v in hr.consumer_HQ_CR(Cmean)[0].items()}
sub["Cr"] = sub["Cr"] / P.cr_inv_rfd() / P.RfD_o["Cr"]
rows.append(dict(kind="As submitted (Cr(VI) RfD on total Cr)", value=np.nan, cons_HQ=sub["Cr"],
                 cons_HI=S(sub), cons_CR=np.nan, hand_HQ=np.nan, hand_CR=np.nan))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "rev_scenarios.csv"), index=False)
print(pd.DataFrame(rows).to_string(index=False, float_format="{:.3g}".format))

# ---- fertilizer-attributable increment ----
rows = []
for t in types + ["OVERALL"]:
    C = Cmean if t == "OVERALL" else df[df.Type == t][metals].mean()
    for yrs in (10, 50, 100):
        th, tc = hr.consumer_HQ_CR(C, years=yrs)
        ih, ic = hr.consumer_HQ_CR(C, background=False, years=yrs)
        rows.append(dict(Type=t, years=yrs, total_HI=S(th), incr_HI=S(ih), incr_share=S(ih) / S(th),
                         total_CR_AsPb=tc["As"] + tc["Pb"], incr_CR_AsPb=ic["As"] + ic["Pb"],
                         incr_CR_Cr=ic["Cr"]))
inc = pd.DataFrame(rows); inc.to_csv(os.path.join(OUT, "rev_increment.csv"), index=False)
print("\n", inc[inc.Type == "OVERALL"].to_string(index=False, float_format="{:.3g}".format))

# ---- per product ----
ind = pd.read_csv(os.path.join(OUT, "indices_by_sample.csv"))
rows = []
for i, r in df.iterrows():
    C = r[metals]; hh, hc = hr.handler_HQ_CR(C)
    ih, ic = hr.consumer_HQ_CR(C, background=False, years=10)
    ih100, ic100 = hr.consumer_HQ_CR(C, background=False, years=100)
    rows.append(dict(Sample=r.Sample, Type=r.Type,
                     n_over_MAL=int(sum(r[m] > MAL[m] for m in metals)),
                     over=",".join(m for m in metals if r[m] > MAL[m]),
                     hand_HI=S(hh), hand_CR_AsPb=hc["As"] + hc["Pb"], hand_CR_Cr=hc["Cr"],
                     incr_HI_10=S(ih), incr_HI_100=S(ih100),
                     incr_CR_AsPb_100=ic100["As"] + ic100["Pb"], incr_CR_Cr_100=ic100["Cr"],
                     PLI=ind.PLI[i], RI=ind.RI[i], PN=ind.PN[i]))
pp = pd.DataFrame(rows); pp.to_csv(os.path.join(OUT, "rev_per_product.csv"), index=False)
for c in ["hand_HI", "hand_CR_AsPb", "hand_CR_Cr", "incr_HI_100", "incr_CR_AsPb_100", "RI", "PLI", "PN"]:
    j = pp[c].idxmax(); print(f"  max {c:18s} {pp[c].max():.3g} ({pp.Sample[j]})")
print(f"  handler CR(As+Pb)>1e-6: {(pp.hand_CR_AsPb>1e-6).sum()}, Cr>1e-6: {(pp.hand_CR_Cr>1e-6).sum()};"
      f" RI>=150: {(pp.RI>=150).sum()}; PLI>=1: {(pp.PLI>=1).sum()}; PN>1: {(pp.PN>1).sum()}")

# ---- Grubbs flags (same rule as scripts/01_clean.py) ----
def grubbs(x):
    x = np.asarray(x, float); n = len(x)
    z = np.abs(x - x.mean()) / (x.std(ddof=1) + 1e-12)
    t2 = stats.t.ppf(1 - 0.05 / (2 * n), n - 2) ** 2
    Gc = (n - 1) / np.sqrt(n) * np.sqrt(t2 / (n - 2 + t2))
    return int(z.argmax()) if z.max() > Gc else None
fl = []
for m in metals:
    for t in types:
        g = df[df.Type == t]; k = grubbs(g[m].values)
        if k is not None:
            fl.append(dict(Element=m, Type=t, Sample=g.Sample.iloc[k], Value=g[m].iloc[k],
                           type_mean=g[m].mean(), type_mean_excl=g[m].drop(g.index[k]).mean(),
                           over_MAL=bool(g[m].iloc[k] > MAL[m])))
fl = pd.DataFrame(fl); fl.to_csv(os.path.join(OUT, "rev_outliers.csv"), index=False)
flagged = sorted(set(fl.Sample)); keep = ~df.Sample.isin(flagged)
print(f"\n  Grubbs: {len(fl)} values in {len(flagged)} products: {flagged}")

# ---- indices and Tmax/risk on mean / median / outlier-excluded ----
ind["Sample"] = df.Sample.values
rows = []
for t in types:
    g = ind[ind.Type == t]; gk = g[~g.Sample.isin(flagged)]
    for basis, G, f in (("mean", g, "mean"), ("median", g, "median"), ("excl", gk, "mean")):
        rows.append(dict(Type=t, basis=basis, n=len(G), **{c: getattr(G[c], f)() for c in ("PLI", "mCd", "RI", "PN")}))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "rev_basis.csv"), index=False)
rows = []
for basis, C in (("mean", Cmean), ("median", df[metals].median()), ("excl", df[keep][metals].mean())):
    R = C * M0 / W0; th, tc = hr.consumer_HQ_CR(C); hh, hc = hr.handler_HQ_CR(C)
    rows.append(dict(basis=basis, n=35 if basis != "excl" else int(keep.sum()),
                     **{f"T_{m}": (CSV[m] - CBV[m]) / R[m] for m in metals},
                     **{f"Tccme_{m}": (CSV_STRICT[m] - CBV[m]) / R[m] for m in metals},
                     cons_HI=S(th), cons_CR_AsPb=tc["As"] + tc["Pb"], hand_HI=S(hh),
                     hand_CR_AsPb=hc["As"] + hc["Pb"]))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "rev_basis_overall.csv"), index=False)

# ---- PCA: eigenvalues, Horn's parallel analysis, influence of flagged products ----
def eig_of(X):
    Z = (X - X.mean(0)) / X.std(0)
    return np.sort(np.linalg.eigvalsh(np.corrcoef(Z, rowvar=False)))[::-1]
def pc1_loadings(X):
    Z = (X - X.mean(0)) / X.std(0); U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    sc = U[:, 0] * s[0]; return np.array([abs(np.corrcoef(Z[:, i], sc)[0, 1]) for i in range(Z.shape[1])])
Xall = np.log(df[metals].values); Xk = np.log(df[keep][metals].values)
rng = np.random.default_rng(7)
pa_all = np.percentile([eig_of(rng.normal(size=Xall.shape)) for _ in range(5000)], 95, axis=0)
pa_k = np.percentile([eig_of(rng.normal(size=Xk.shape)) for _ in range(5000)], 95, axis=0)
ea, ek = eig_of(Xall), eig_of(Xk)
loo = np.array([eig_of(np.delete(Xall, i, axis=0)) for i in range(len(Xall))])
rows = [dict(Component=f"PC{j+1}", eig_all=ea[j], var_all=100 * ea[j] / 7, cum_all=100 * ea[:j+1].sum() / 7,
             pa95_all=pa_all[j], eig_excl=ek[j], pa95_excl=pa_k[j],
             loo_min=loo[:, j].min(), loo_max=loo[:, j].max()) for j in range(7)]
pca = pd.DataFrame(rows); pca.to_csv(os.path.join(OUT, "rev_pca.csv"), index=False)
pd.DataFrame({"all": pc1_loadings(Xall), "excl": pc1_loadings(Xk)}, index=metals).to_csv(
    os.path.join(OUT, "rev_pca_pc1_loadings.csv"))
rs = stats.spearmanr(df[keep][metals]).statistic
pd.DataFrame(rs, index=metals, columns=metals).to_csv(os.path.join(OUT, "rev_spearman_excl.csv"))
print("\n", pca.to_string(index=False, float_format="{:.3f}".format))
print(f"  Kaiser keeps 1 in {(loo[:,1] <= 1).sum()}/35 leave-one-out runs;"
      f" excl. flagged As-Ni {rs[6,5]:.2f}, Cu-Ni {rs[0,5]:.2f}, As-Cu {rs[6,0]:.2f}")

# ---- non-detects ----
def ros(x, cens):
    """Regression on order statistics, lognormal, single censoring level (Helsel 2012)."""
    n = len(x); nc = int(cens.sum()); det = np.sort(x[~cens])
    pp_ = (np.arange(1, n + 1) - 0.375) / (n + 0.25)
    b, a = np.polyfit(stats.norm.ppf(pp_[nc:]), np.log(det), 1)
    return np.concatenate([np.exp(a + b * stats.norm.ppf(pp_[:nc])), det])
def km_mean(x, cens, dl):
    """Kaplan-Meier mean of left-censored data by flipping (Helsel 2012)."""
    v = np.where(cens, dl, x); M = v.max() + 1; f = M - v; e = ~cens
    s, prev, area = 1.0, 0.0, 0.0
    for t in np.unique(f[e]):
        area += (t - prev) * s; s *= 1 - ((f == t) & e).sum() / (f >= t).sum(); prev = t
    return M - area
rows = []
for m in metals:
    cens = df[m + "_bdl"].values
    if not cens.any(): continue
    x = df[m].values; dl = df.loc[~cens, m].min()
    r_ = ros(np.where(cens, dl, x), cens)
    rows.append(dict(Element=m, n_ND=int(cens.sum()), lowest_quantified=dl,
                     mean_zero=np.where(cens, 0, x).mean(), mean_half=x.mean(),
                     mean_full=np.where(cens, dl, x).mean(), mean_ROS=r_.mean(),
                     mean_KM=km_mean(x, cens, dl), median_half=np.median(x), median_ROS=np.median(r_)))
nd = pd.DataFrame(rows); nd.to_csv(os.path.join(OUT, "rev_nondetects.csv"), index=False)
print("\n", nd.to_string(index=False, float_format="{:.4f}".format))

# ---- soil loading with crop offtake and leaching ----
# dC/dt = R - k (C - Cbv)  =>  C(t) = Cbv + (R/k)(1 - e^{-kt}),  C_ss = Cbv + R/k
# k = k_off + k_leach;  k_off = Y*TF/W  (crop dry-matter offtake);
# k_leach = q / (h * rho_b * Kd)  (net percolation q through a 0.20 m layer).
# Kd: median soil log10 Kd (L/kg) from Allison & Allison (2005), EPA/600/R-05/074.
LOGKD = {"Cu": 2.7, "Cr": 3.9, "Pb": 3.7, "Cd": 2.9, "Zn": 3.1, "Ni": 3.1, "As": 3.4}
SCEN = {"central": dict(Y=10000, q=0.30), "low loss": dict(Y=5000, q=0.15)}
rows = []
for sn, s in SCEN.items():
    for m in metals:
        R = Cmean[m] * M0 / W0
        k_off = s["Y"] * P.TF[m] / W0
        k_le = s["q"] * 1000 / (0.20 * 1300 * 10 ** LOGKD[m])
        k = k_off + k_le; Css = CBV[m] + R / k
        def t_to(lim):
            x = 1 - (lim - CBV[m]) * k / R
            return np.inf if x <= 0 else -np.log(x) / k
        rows.append(dict(scenario=sn, Element=m, R=R, k_off=k_off, k_leach=k_le, logKd=LOGKD[m],
                         C_ss=Css, dC_100=(R / k) * (1 - np.exp(-k * 100)),
                         T_dutch_noloss=(CSV[m] - CBV[m]) / R, T_dutch_loss=t_to(CSV[m]),
                         T_ccme_noloss=(CSV_STRICT[m] - CBV[m]) / R, T_ccme_loss=t_to(CSV_STRICT[m])))
ls = pd.DataFrame(rows); ls.to_csv(os.path.join(OUT, "rev_losses.csv"), index=False)
print("\n", ls.to_string(index=False, float_format="{:.4g}".format))
print("\nSaved rev_*.csv")

# ---- Bangladeshi soil background in place of the world-soil means (R1.9) ----
# Sensitivity only: the main analysis keeps Kabata-Pendias. A non-positive Tmax means the
# background alone already meets or exceeds that limit.
def bg_set(bg):
    cf = {m: df[m] / bg[m] for m in metals}
    pli = np.exp(sum(np.log(cf[m]) for m in metals) / len(metals))
    er = {m: TR[m] * cf[m] for m in metals}
    ri = sum(er.values())
    return cf, pli, er, ri
rows = []
for name, bg in (("World", CBV), ("Bangladesh", CBV_BD)):
    cf, pli, er, ri = bg_set(bg)
    for m in metals:
        R = Cmean[m] * M0 / W0
        rows.append(dict(set=name, Element=m, Cbv=bg[m], CF=cf[m].mean(),
                         Igeo=np.log2(Cmean[m] / (1.5 * bg[m])), Er=er[m].mean(),
                         Er_share=er[m].mean() / ri.mean(),
                         T_dutch=(CSV[m] - bg[m]) / R, T_ccme=(CSV_STRICT[m] - bg[m]) / R))
    keep = P.BG_SOIL
    P.BG_SOIL = bg
    th, tc = hr.consumer_HQ_CR(Cmean); ih, ic = hr.consumer_HQ_CR(Cmean, background=False)
    P.BG_SOIL = keep
    rows.append(dict(set=name, Element="ALL", PLI=pli.mean(), RI=ri.mean(),
                     n_PLI_ge1=int((pli >= 1).sum()), n_RI_ge150=int((ri >= 150).sum()),
                     HI=S(th), incr_share=S(ih) / S(th),
                     CR_AsPb=tc["As"] + tc["Pb"], CR_Cr=tc["Cr"],
                     incr_share_CR=(ic["As"] + ic["Pb"]) / (tc["As"] + tc["Pb"])))
bd = pd.DataFrame(rows); bd.to_csv(os.path.join(OUT, "rev_bdsoil.csv"), index=False)
print("\n=== World vs Bangladeshi soil background ===")
print(bd.to_string(index=False, float_format="{:.4g}".format))


# ---- data-quality flags and Zn absorbance sensitivity (R1.6, 2026-11-08) ----
# Flags every result against the method LOQ and the calibration standards in
# data/calibration_standards.csv (MajorRevision/_RSD.xlsx, taken as the full series).
# No value is removed: flags are reported, and the Zn results whose implied absorbance
# exceeds 1.0 (beyond the reliable flame-AAS range) are scaled upward in a sensitivity
# check because non-linear response would understate them.
from qaqc import CAL, METHOD_LOQ, DIGEST_FACTOR
_cs = pd.read_csv(os.path.join(ROOT, "data", "calibration_standards.csv"), comment="#")
A_MAX = 1.0
qrows, absorb = [], {}
for m in metals:
    g = _cs[_cs.Element == m]; ug = g.Unit.iloc[0] == "ug/L"
    k = DIGEST_FACTOR[m] / (1000.0 if ug else 1.0)
    lo, hi = g.Level.min() * k, g.Level.max() * k
    slope = CAL.loc[m, "Slope (m)"]; icpt = float(CAL.loc[m, "Equation"].split("x")[1].replace(" ", ""))
    A = slope * df[m] / k + icpt; absorb[m] = A
    for i, r in df.iterrows():
        v = r[m]
        if r[m + "_bdl"] or v < METHOD_LOQ[m]: fl = "<LOQ"
        elif v < lo: fl = "below lowest standard"
        elif v > hi: fl = "above highest standard"
        else: fl = "within standards"
        if A[i] > A_MAX: fl = "above highest standard, absorbance > 1"
        qrows.append(dict(Sample=r.Sample, Type=r.Type, Element=m, value=v, absorbance=A[i], flag=fl))
qf = pd.DataFrame(qrows); qf.to_csv(os.path.join(OUT, "rev_qflags.csv"), index=False)
print("\n=== Data-quality flags (count by element) ===")
print(pd.crosstab(qf.Element, qf.flag).reindex(metals).to_string())

zn_hi = absorb["Zn"] > A_MAX
def zn_case(f):
    d = df.copy(); d.loc[zn_hi, "Zn"] = d.loc[zn_hi, "Zn"] * f
    cf = {m: d[m] / CBV[m] for m in metals}
    pli = np.exp(sum(np.log(cf[m]) for m in metals) / len(metals))
    ri = sum(TR[m] * cf[m] for m in metals)
    pi = pd.DataFrame({m: d[m] / MAL[m] for m in metals})
    pn = np.sqrt((pi.mean(axis=1) ** 2 + pi.max(axis=1) ** 2) / 2)
    C = d[metals].mean(); R = C["Zn"] * M0 / W0
    th, _ = hr.consumer_HQ_CR(C); ih, _ = hr.consumer_HQ_CR(C, background=False)
    return dict(factor=f, n_scaled=int(zn_hi.sum()), Zn_mean=C["Zn"], Zn_max=d.Zn.max(),
                Zn_over_MAL=int((d.Zn > MAL["Zn"]).sum()), Zn_CF=cf["Zn"].mean(),
                Zn_Igeo=np.log2(C["Zn"] / (1.5 * CBV["Zn"])), PLI=pli.mean(), n_PLI_ge1=int((pli >= 1).sum()),
                RI=ri.mean(), n_RI_ge150=int((ri >= 150).sum()), n_PN_gt1=int((pn > 1).sum()),
                T_Zn_dutch=(CSV["Zn"] - CBV["Zn"]) / R, T_Zn_ccme=(CSV_STRICT["Zn"] - CBV["Zn"]) / R,
                HI=S(th), incr_share=S(ih) / S(th), Zn_HQ=th["Zn"])
f_break = MAL["Zn"] / df.loc[zn_hi, "Zn"].max()
zs = pd.DataFrame([zn_case(f) for f in (1.0, 1.5, 2.0, f_break)])
zs.to_csv(os.path.join(OUT, "rev_zn_sensitivity.csv"), index=False)
print("\n=== Zn results with absorbance > 1 scaled upward ===")
print(zs.to_string(index=False, float_format="{:.4g}".format))
