# -*- coding: utf-8 -*-
"""Deterministic human-health risk assessment (USEPA framework), both scenarios.
A: fertilizer handlers (ingestion+dermal+inhalation of fertilizer solid)
B: consumers of crops grown on fertilized soil (soil->plant transfer)
Run:  python3 scripts/05_health_risk.py   (from manuscript/exploration/)
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

def handler_HQ_CR(C):   # C in mg/kg
    A=P.HANDLER; ATn=A["ED"]*365; ATc=70*365
    HQ=0.0; CR=0.0; hq_by={}
    for m in metals:
        c=C[m]
        add_ing = c*A["IngR"]*A["EF"]*A["ED"]*CF/(A["BW"]*ATn)
        add_der = c*A["SA"]*A["AF"]*P.ABS_d[m]*A["EF"]*A["ED"]*CF/(A["BW"]*ATn)
        add_inh = c*A["InhR"]*A["EF"]*A["ED"]/(A["PEF"]*A["BW"]*ATn)
        rfd_der = P.RfD_o[m]*P.GIABS[m]
        hq = add_ing/P.RfD_o[m] + add_der/rfd_der + add_inh/P.RfD_o[m]
        hq_by[m]=hq; HQ+=hq
        if P.SF_o[m] is not None:
            cc = c*P.CR6_FRACTION if m=="Cr" else c
            ldd = cc*A["IngR"]*A["EF"]*A["ED"]*CF/(A["BW"]*ATc)
            CR += ldd*P.SF_o[m]
    return HQ, CR, hq_by

def consumer_HQ_CR(C):
    A=P.CONSUMER; ATn=A["ED"]*365; ATc=70*365
    HQ=0.0; CR=0.0; hq_by={}
    for m in metals:
        # crude soil model: background + accumulated increment from fertilizer over APPLY_YEARS
        # increment uses same loading logic (M=5 t/ha, W=2.6e6 kg/ha)
        R = C[m]*5000/2.6e6
        c_soil = P.BG_SOIL[m] + R*A["APPLY_YEARS"]
        c_plant = c_soil*P.TF[m]                     # mg/kg dry
        dim = c_plant*A["Cf"]*A["IR"]*A["EF"]*A["ED"]/(A["BW"]*ATn)
        hq = dim/P.RfD_o[m]; hq_by[m]=hq; HQ+=hq
        if P.SF_o[m] is not None:
            cc = c_plant*P.CR6_FRACTION if m=="Cr" else c_plant
            ldd = cc*A["Cf"]*A["IR"]*A["EF"]*A["ED"]/(A["BW"]*ATc)
            CR += ldd*P.SF_o[m]
    return HQ, CR, hq_by

rows=[]
for scen,fn in [("Handler",handler_HQ_CR),("Consumer",consumer_HQ_CR)]:
    for t in types:
        C=df[df["Type"]==t][metals].mean()
        HI,CR,_=fn(C)
        rows.append((scen,t,round(HI,3),f"{CR:.2e}"))
    # overall
    C=df[metals].mean(); HI,CR,hqb=fn(C)
    rows.append((scen,"OVERALL",round(HI,3),f"{CR:.2e}"))
    print(f"\n=== Scenario {scen}: overall HQ by metal ===")
    print({k:round(v,3) for k,v in hqb.items()})
res=pd.DataFrame(rows,columns=["Scenario","Type","HI","CancerRisk"])
print("\n=== Hazard Index (HI) and total ingestion Cancer Risk (CR) ===")
print(res.to_string(index=False))
res.to_csv(os.path.join(OUT,"health_risk.csv"),index=False)
print("\nThresholds: HI>1 -> non-carcinogenic concern ; CR>1e-4 -> unacceptable, 1e-6-1e-4 tolerable.")
print("Saved health_risk.csv")
