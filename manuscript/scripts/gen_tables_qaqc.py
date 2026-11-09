# -*- coding: utf-8 -*-
"""Emit the QA/QC LaTeX table bodies from the consolidated laboratory workbook.

All reading, unit normalisation and the nickel LOD correction live in qaqc.py,
which is the single source of truth; this script only formats.

Run:  python3 scripts/gen_tables_qaqc.py   (from manuscript/)
"""
import os, sys
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
TBL = os.path.join(ROOT, "tables")
sys.path.insert(0, HERE)
from qaqc import (CAL, METHOD_LOD, METHOD_LOQ, RECOVERY, TYPES_QAQC,
                  DIGEST_FACTOR, NI_LOD_WORKBOOK, NI_LOD_CORRECTION)

metals = ["Pb", "Cd", "Cr", "Cu", "Zn", "Ni", "As"]      # reporting order

# ---- Single supplementary QA/QC table. The whole calibration and detection-limit
# block now lives in the SI (decision 2026-08-21); the main text carries no
# calibration table at all. One row per element, running left to right from the
# calibration through to the method limit on a dry-sample basis, so that
# 3.3*sigma/m and the digest-to-sample rescaling can both be checked in place.
# See the note in qaqc.py on why BOTH limit pairs are the *method* limit.
with open(os.path.join(TBL, "si_calib_solution_body.tex"), "w") as f:
    for m in metals:
        r = CAL.loc[m]
        eq = str(r["Equation"]).replace(" ", "")
        eq = "$" + eq.replace("y=", "y = ").replace("+", " + ").replace("-", " - ") + "$"
        f.write(f"{m} & {eq} & {r['R²']:.4f} & {r['Slope (m)']:.4f} & "
                f"{r['LOD (mg/L)']:.4f} & {r['LOQ (mg/L)']:.4f} & "
                f"{DIGEST_FACTOR[m]:.0f} & "
                f"{METHOD_LOD[m]:.3f} & {METHOD_LOQ[m]:.3f} \\\\\n")

# The main-text calibration table body is no longer produced. If a reviewer asks
# for it back, restore the six-column form from git history at CHANGES.txt entry
# "INTERNAL CORRECTION ROUND 2".
_stale = os.path.join(TBL, "table_qaqc_calib_body.tex")
if os.path.exists(_stale):
    os.remove(_stale)
    print("  removed stale table_qaqc_calib_body.tex (main-text Table 1 retired)")

# ---- spike recovery, one row per matrix ----
means = {m: [] for m in metals}
with open(os.path.join(TBL, "si_recovery_body.tex"), "w") as f:
    for t in TYPES_QAQC:
        cells = []
        for m in metals:
            mu, sd = RECOVERY[(t, m)]
            means[m].append(mu)
            cells.append(f"{mu:.2f} $\\pm$ {sd:.2f}")
        f.write(f"{t} & " + " & ".join(cells) + " \\\\\n")
    f.write("\\midrule\n")
    cells = [f"{pd.Series(means[m]).mean():.2f} $\\pm$ "
             f"{pd.Series(means[m]).std():.2f}" for m in metals]
    f.write("\\textbf{Overall} & " + " & ".join(cells) + " \\\\\n")

allv = [(v, m, t) for m in metals for v, t in zip(means[m], TYPES_QAQC)]
elem = {m: pd.Series(means[m]).mean() for m in metals}
lo, hi = min(allv), max(allv)
print("Wrote QA/QC table bodies to", TBL)
print(f"  R2 range          : {CAL['R²'].min():.4f}-{CAL['R²'].max():.4f} "
      f"(low {CAL['R²'].idxmin()}, high {CAL['R²'].idxmax()})")
print(f"  LOD, solution (mg/L): {CAL['LOD (mg/L)'].min():.4f} ({CAL['LOD (mg/L)'].idxmin()})"
      f" - {CAL['LOD (mg/L)'].max():.4f} ({CAL['LOD (mg/L)'].idxmax()})")
print(f"  method LOD (mg/kg): {min(METHOD_LOD.values()):.3f} "
      f"({min(METHOD_LOD, key=METHOD_LOD.get)}) - {max(METHOD_LOD.values()):.3f} "
      f"({max(METHOD_LOD, key=METHOD_LOD.get)})")
print(f"  recovery, single  : {lo[0]:.2f}% ({lo[1]} in {lo[2]}) - "
      f"{hi[0]:.2f}% ({hi[1]} in {hi[2]})")
print(f"  recovery, element : {min(elem.values()):.2f}-{max(elem.values()):.2f} % "
      f"(low {min(elem, key=elem.get)}, high {max(elem, key=elem.get)})")
print(f"  Ni LOD/LOQ        : workbook {NI_LOD_WORKBOOK['LOD (mg/L)']:.5f}/"
      f"{NI_LOD_WORKBOOK['LOQ (mg/L)']:.5f} -> corrected "
      f"{NI_LOD_CORRECTION['LOD (mg/L)']}/{NI_LOD_CORRECTION['LOQ (mg/L)']} mg/L")
print("  LOQ/LOD ratios    :",
      ", ".join(f"{m} {CAL.loc[m,'LOQ (mg/L)']/CAL.loc[m,'LOD (mg/L)']:.3f}" for m in metals))
