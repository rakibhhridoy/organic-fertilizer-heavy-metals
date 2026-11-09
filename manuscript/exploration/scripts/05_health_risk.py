# -*- coding: utf-8 -*-
"""Deterministic human-health risk assessment (USEPA framework), both scenarios.
A: fertilizer handlers (ingestion+dermal+inhalation of fertilizer solid)
B: consumers of crops grown on fertilized soil (soil->plant transfer)
Run:  python3 scripts/05_health_risk.py   (from manuscript/exploration/)

Chromium is split by valence in both the hazard quotient and the cancer term (see
params_hhra.py). Cancer risk is reported as As + Pb, with the Cr(VI) term reported
separately because it rests on an assumed, unmeasured Cr(VI) fraction.

For consumers the soil burden is background + the fertilizer increment over
APPLY_YEARS. The increment alone (background set to zero) is reported as the
fertilizer-attributable risk, because the total is dominated by the background.
"""
import os, numpy as np, pandas as pd
import params_hhra as P

HERE=os.path.dirname(os.path.abspath(__file__)); EXP=os.path.dirname(HERE)
ROOT=os.path.dirname(EXP); OUT=os.path.join(EXP,"outputs")
df=pd.read_pickle(os.path.join(ROOT,"data","clean_data.pkl"))
metals=P.metals
types=["Cow dung","Bone meal","Trichocompost","Generic Organic Fertilizer",
       "Vermicompost","Horn meal","Neem cake"]
CF=1e-6  # mg->kg

def handler_HQ_CR(C, f6=None, f_ias=1.0):   # C in mg/kg
    f6 = P.CR6_FRACTION if f6 is None else f6
    A=P.HANDLER; ATn=A["ED"]*365; ATc=70*365
    hq_by={}; cr_by={}
    for m in metals:
        c=C[m]
        add_ing = c*A["IngR"]*A["EF"]*A["ED"]*CF/(A["BW"]*ATn)
        add_der = c*A["SA"]*A["AF"]*P.ABS_d[m]*A["EF"]*A["ED"]*CF/(A["BW"]*ATn)
        add_inh = c*A["InhR"]*A["EF"]*A["ED"]/(A["PEF"]*A["BW"]*ATn)
        if m=="Cr":
            hq = (add_ing+add_inh)*P.cr_inv_rfd(f6) + add_der*P.cr_inv_rfd_dermal(f6)
        else:
            hq = (add_ing+add_inh)/P.RfD_o[m] + add_der/(P.RfD_o[m]*P.GIABS[m])
        hq_by[m]=hq
        if P.SF_o[m] is not None:
            frac = f6 if m=="Cr" else (f_ias if m=="As" else 1.0)
            ldd = c*frac*A["IngR"]*A["EF"]*A["ED"]*CF/(A["BW"]*ATc)
            cr_by[m] = ldd*P.SF_o[m]
    return hq_by, cr_by

def consumer_HQ_CR(C, f6=None, f_ias=1.0, background=True, years=None):
    f6 = P.CR6_FRACTION if f6 is None else f6
    A=P.CONSUMER; ATn=A["ED"]*365; ATc=70*365
    years = A["APPLY_YEARS"] if years is None else years
    hq_by={}; cr_by={}
    for m in metals:
        # soil = background + accumulated increment from fertilizer over `years`
        # (same loading logic as 02_risk.py: M = 5 t/ha, W = 2.6e6 kg/ha)
        R = C[m]*5000/2.6e6
        c_soil = (P.BG_SOIL[m] if background else 0.0) + R*years
        c_plant = c_soil*P.TF[m]                     # mg/kg dry
        dim = c_plant*A["Cf"]*A["IR"]*A["EF"]*A["ED"]/(A["BW"]*ATn)
        hq_by[m] = dim*P.cr_inv_rfd(f6) if m=="Cr" else dim/P.RfD_o[m]
        if P.SF_o[m] is not None:
            frac = f6 if m=="Cr" else (f_ias if m=="As" else 1.0)
            ldd = c_plant*frac*A["Cf"]*A["IR"]*A["EF"]*A["ED"]/(A["BW"]*ATc)
            cr_by[m] = ldd*P.SF_o[m]
    return hq_by, cr_by

def summarise(hq, cr):
    return sum(hq.values()), cr["As"]+cr["Pb"], cr["Cr"]

if __name__ == "__main__":
    rows=[]
    for scen,fn in [("Handler",handler_HQ_CR),("Consumer",consumer_HQ_CR)]:
        for t in types+["OVERALL"]:
            C = df[metals].mean() if t=="OVERALL" else df[df["Type"]==t][metals].mean()
            HI,CRap,CRcr = summarise(*fn(C))
            row=dict(Scenario=scen,Type=t,HI=HI,CR_AsPb=CRap,CR_Cr=CRcr)
            if scen=="Consumer":
                iHI,iCRap,iCRcr = summarise(*consumer_HQ_CR(C, background=False))
                row.update(HI_incr=iHI,CR_AsPb_incr=iCRap,CR_Cr_incr=iCRcr)
            rows.append(row)
        hqb,_=fn(df[metals].mean())
        print(f"\n=== Scenario {scen}: overall HQ by metal ===")
        print({k:round(v,4) for k,v in hqb.items()})
    res=pd.DataFrame(rows)
    print("\n=== Hazard index (HI) and ingestion cancer risk (CR: As+Pb; Cr(VI) separate) ===")
    with pd.option_context("display.float_format","{:.3g}".format):
        print(res.to_string(index=False))
    res.to_csv(os.path.join(OUT,"health_risk.csv"),index=False)
    print("\nThresholds: HI>1 -> non-carcinogenic concern ; CR>1e-4 -> unacceptable, 1e-6-1e-4 tolerable.")
    print("Saved health_risk.csv")
