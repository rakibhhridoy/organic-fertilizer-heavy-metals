# -*- coding: utf-8 -*-
"""Monte Carlo simulation: probabilistic soil accumulation + probabilistic health
risk (crop-consumer pathway) + rank-regression global sensitivity analysis.
Run:  python3 scripts/06_montecarlo.py   (from manuscript/exploration/)
"""
import os, numpy as np, pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import params_hhra as P

HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
ROOT=os.path.dirname(EXP); OUT=os.path.join(EXP,"outputs")
rng=np.random.default_rng(42)
df=pd.read_pickle(os.path.join(ROOT,"data","clean_data.pkl"))
metals=P.metals
N=30000

# Fit lognormal (method of moments on logs) to each metal from the 35 samples
logfit={m:(np.log(df[m].clip(lower=1e-4)).mean(), np.log(df[m].clip(lower=1e-4)).std(ddof=1)) for m in metals}
def draw_conc(m,size): mu,sig=logfit[m]; return np.exp(rng.normal(mu,sig,size))

BG=P.BG_SOIL
from soil_refs import CSV        # data/soil_reference_values.csv

# ============ 1. Probabilistic soil accumulation ============
print("=== Monte Carlo soil accumulation (N=%d) ===" % N)
M   = rng.triangular(3000,5000,10000,N)         # application kg/ha/yr
h   = rng.uniform(0.15,0.25,N)                  # plough depth m
p   = rng.uniform(1200,1400,N)                  # bulk density kg/m3
W   = 10000*h*p
soil_rows=[]
for m in metals:
    C=draw_conc(m,N)
    R=M*C/W                                     # mg/kg/yr
    Tmax=(CSV[m]-BG[m])/R
    probs={t: float(np.mean(BG[m]+R*t > CSV[m])) for t in (10,20,50,100)}
    soil_rows.append((m, np.median(Tmax), np.percentile(Tmax,5),
                      probs[10],probs[20],probs[50],probs[100]))
soil=pd.DataFrame(soil_rows,columns=["Metal","Tmax_median","Tmax_P5",
     "P_exceed_10y","P_exceed_20y","P_exceed_50y","P_exceed_100y"]).round(4)
print(soil.to_string(index=False))
soil.to_csv(os.path.join(OUT,"mc_soil_accumulation.csv"),index=False)

# ============ 2. Probabilistic health risk (consumer pathway) ============
print("\n=== Monte Carlo health risk: crop-consumer pathway (N=%d) ===" % N)
IR = rng.triangular(0.2,0.345,0.5,N)
BW = np.clip(rng.normal(65,12,N),35,110)
ED = rng.triangular(20,30,50,N)
cr6= rng.uniform(0.05,0.30,N)                   # Cr(VI) fraction
appyr = rng.triangular(5,10,25,N)
HI=np.zeros(N); CR=np.zeros(N)
inputs={"IR":IR,"BW":BW,"ED":ED,"Cr6_frac":cr6,"apply_years":appyr}
conc_draw={}
for m in metals:
    C=draw_conc(m,N); conc_draw[m]=C
    TFm=np.exp(rng.normal(np.log(P.TF[m]),0.3,N))        # transfer factor uncertainty
    Rm=C*5000/2.6e6
    c_soil=BG[m]+Rm*appyr
    c_plant=c_soil*TFm
    ATn=ED*365; ATc=70*365
    dim=c_plant*P.CONSUMER["Cf"]*IR*365*ED/(BW*ATn)
    HI+=dim/P.RfD_o[m]
    if P.SF_o[m] is not None:
        cc=c_plant*cr6 if m=="Cr" else c_plant
        ldd=cc*P.CONSUMER["Cf"]*IR*365*ED/(BW*ATc)
        CR+=ldd*P.SF_o[m]
# Fertilizer concentrations are carried into the sensitivity analysis for the two
# elements that drive the carcinogenic term, so the comparison against the
# exposure parameters is explicit rather than assumed.
inputs["Conc_Cr"]=conc_draw["Cr"]
inputs["Conc_As"]=conc_draw["As"]
def summ(x): return dict(mean=np.mean(x),median=np.median(x),P95=np.percentile(x,95))
print("HI:", {k:round(v,3) for k,v in summ(HI).items()}, " P(HI>1)=%.3f"%np.mean(HI>1))
print("CR:", {k:f"{v:.2e}" for k,v in summ(CR).items()},
      " P(CR>1e-4)=%.3f"%np.mean(CR>1e-4), " P(CR>1e-6)=%.3f"%np.mean(CR>1e-6))
pd.DataFrame({"HI":HI,"CR":CR}).describe(percentiles=[.05,.5,.95]).to_csv(os.path.join(OUT,"mc_health_summary.csv"))

# ============ 3. Rank-regression global sensitivity (SRRC) on HI and CR ============
def srrc(inp, out):
    from scipy.stats import rankdata
    Xr=np.column_stack([rankdata(v) for v in inp.values()]); yr=rankdata(out)
    Xr=(Xr-Xr.mean(0))/Xr.std(0); yr=(yr-yr.mean())/yr.std()
    beta,_,_,_=np.linalg.lstsq(Xr,yr,rcond=None)
    return dict(zip(inp.keys(), np.round(beta,3)))
print("\n=== Global sensitivity (standardised rank regression coeff.) ===")
print("HI:", srrc(inputs,HI))
print("CR:", srrc(inputs,CR))

# ============ figures ============
# (a) exceedance probability curves
fig,ax=plt.subplots(figsize=(7,4.5))
tgrid=np.arange(1,201)
_curves={}
for m in metals:
    mu,sig=logfit[m]
    # analytic-ish: use MC medians of R
    C=draw_conc(m,5000); R=(rng.triangular(3000,5000,10000,5000)*C)/(10000*rng.uniform(.15,.25,5000)*rng.uniform(1200,1400,5000))
    pr=[np.mean(BG[m]+np.outer(R,[t]).ravel()>CSV[m]) for t in tgrid]
    _curves[m]=pr
    ax.plot(tgrid,pr,label=m)
ax.set_xlabel("Years of continuous application"); ax.set_ylabel("P(soil exceeds safe limit)")
ax.set_title("Monte Carlo probability of soil limit exceedance over time")
ax.legend(ncol=3,fontsize=8); ax.set_ylim(-0.02,1.02)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_mc_exceedance.pdf"),bbox_inches="tight")
fig.savefig(os.path.join(OUT,"fig_mc_exceedance.png"),dpi=150,bbox_inches="tight"); plt.close(fig)

# (b) HI and CR distributions
fig,axs=plt.subplots(1,2,figsize=(10,4))
axs[0].hist(HI,bins=60,color="#4C72B0"); axs[0].axvline(1,color="r",ls="--"); axs[0].axvline(np.percentile(HI,95),color="k",ls=":")
axs[0].set_title("Hazard Index (consumer)"); axs[0].set_xlabel("HI")
axs[1].hist(np.log10(CR),bins=60,color="#C44E52")
for thr,lab in [(-4,"1e-4"),(-6,"1e-6")]: axs[1].axvline(thr,color="r",ls="--")
axs[1].set_title("Cancer risk (log10)"); axs[1].set_xlabel("log10(CR)")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_mc_risk_dist.pdf"),bbox_inches="tight")
fig.savefig(os.path.join(OUT,"fig_mc_risk_dist.png"),dpi=150,bbox_inches="tight"); plt.close(fig)

# ---- data dumps for the D3 build (histograms + exceedance curves) ----
import json
def _hist(x, bins):
    cnt, edges = np.histogram(x, bins=bins)
    return {"edges": edges.round(5).tolist(), "counts": cnt.tolist()}
mc_json = {
    "tgrid": tgrid.tolist(),
    "exceedance": {m: [round(v,5) for v in _curves[m]] for m in metals},
    "hi": {**_hist(HI, 60), "p95": float(np.percentile(HI,95)),
           "threshold": 1.0, "mean": float(HI.mean())},
    "logcr": {**_hist(np.log10(CR), 60),
              "p95": float(np.percentile(np.log10(CR),95)),
              "thresholds": [-6, -4], "mean": float(np.log10(CR).mean())},
}
with open(os.path.join(OUT,"mc_figures.json"),"w") as f:
    json.dump(mc_json, f)
print("\nSaved mc_soil_accumulation.csv, mc_health_summary.csv, mc_figures.json, "
      "fig_mc_exceedance, fig_mc_risk_dist")
