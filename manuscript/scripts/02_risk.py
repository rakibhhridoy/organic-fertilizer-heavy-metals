# -*- coding: utf-8 -*-
"""Soil-loading risk model (after Su et al. 2025). Reproduces data/risk_loading.csv
Run:  python3 scripts/02_risk.py   (from manuscript/)
Model: R = M*C/W ; W = A*h*p/1000 (0-20 cm) ; Tmax = (Csv-Cbv)/R
Cbv/Csv come from data/soil_reference_values.csv (see that file for sources).
Tmax is also reported against the stricter CCME agricultural ceiling as a
sensitivity bound.
"""
import os, sys, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
from soil_refs import CBV as Cbv, CSV as Csv, CSV_STRICT as Csv_strict, METALS as metals

df = pd.read_pickle(os.path.join(DATA,"clean_data.pkl"))

APP_RATE = 5000            # M, kg/ha/yr (dry) ; BARC 5-10 t/ha
W = 10000 * 0.20 * 1300    # A*h*p ; 0-20 cm, 1.3 g/cm3 -> ~2.6e6 kg/ha

mean = df[metals].mean()
rows=[]
for m in metals:
    C=mean[m]; load=C*APP_RATE/1000.0; R=(C*APP_RATE)/W
    tmax=(Csv[m]-Cbv[m])/R if R>0 else np.inf
    tmax_s=(Csv_strict[m]-Cbv[m])/R if R>0 else np.inf
    rows.append((m, round(C,4), round(load,4), round(R,6),
                 round(tmax,1), round(tmax_s,1)))
out=pd.DataFrame(rows, columns=["Metal","Conc_mgkg","Load_g_ha_yr","dSoil_mgkg_yr",
                                "Yrs_to_limit","Yrs_to_limit_strict"])
out.to_csv(os.path.join(DATA,"risk_loading.csv"), index=False)
print(out.to_string(index=False))
print("\nWrote data/risk_loading.csv (W = %.3e kg/ha)" % W)
