# -*- coding: utf-8 -*-
"""Calibration, detection limits and spike recovery -- single source of truth.

Reads the consolidated laboratory workbook directly (no intermediate CSV can
drift): data/OF_HM_TGTup.xlsx, Sheet2 calibration/LOD/LOQ, Sheet3 spike recovery.
Both sheets now carry arsenic alongside the six flame-AAS metals.

Import from anywhere in the pipeline:
    from qaqc import CAL, METHOD_LOD, METHOD_LOQ, DIGEST_FACTOR, RECOVERY

Two things are normalised here so that every consumer sees the same numbers:

1. NICKEL LOD/LOQ CORRECTION. TGT Sheet2 records Ni as LOD 0.09318 and LOQ
   0.28236 mg/L. The analyst's correction memo (2026-08-14) gives 0.0093 and
   0.0282 mg/L -- exactly one decimal place lower, with the ICH LOQ/LOD ratio of
   3.030 preserved, i.e. a transcription slip in the workbook. The corrected
   values are applied below and the original is kept alongside so the change is
   auditable. This matters: at the workbook value the method LOD (2.33 mg/kg)
   exceeded 14 of 35 reported Ni values; at the corrected value (0.233 mg/kg) it
   exceeds none.

2. UNITS. Sheet2 quotes the arsenic limits in ug/L (as the string "1.3213 (ppb)")
   and the other six in mg/L. All are normalised to mg/L here, then to a mg/kg
   method limit using the element's own digest-to-sample factor (25 for the
   flame-AAS metals; 125 for arsenic, whose aliquot is diluted five-fold before
   hydride generation).
"""
import os
import re
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(os.path.dirname(_HERE), "data")
_XLS = os.path.join(_DATA, "OF_HM_TGTup.xlsx")

METALS = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]

# Digest-to-sample factor, L/kg. 2 g -> 50 mL for every element; the arsenic
# aliquot is then diluted 1:5 for hydride generation.
DIGEST_FACTOR = {m: 25.0 for m in METALS}
DIGEST_FACTOR["As"] = 125.0

# Analyst correction memo, 2026-08-14. See note 1 in the module docstring.
NI_LOD_CORRECTION = {"LOD (mg/L)": 0.0093, "LOQ (mg/L)": 0.0282}


def _read_titled(sheet, first_col, usecols=None):
    """Both QA/QC sheets carry a title row and blank spacer rows above the real
    header. Locate the header by its first cell rather than hard-coding a row."""
    raw = pd.read_excel(_XLS, sheet_name=sheet, header=None, usecols=usecols)
    col0 = raw[raw.columns[0]]
    hdr = raw.index[col0.astype(str).str.strip() == first_col]
    if len(hdr) != 1:
        raise ValueError(f"{sheet}: expected one '{first_col}' header row, got {list(hdr)}")
    out = raw.iloc[hdr[0] + 1:].copy()
    out.columns = [str(c).strip() for c in raw.iloc[hdr[0]]]
    return out.dropna(how="all").reset_index(drop=True)


def _limit_mgL(cell):
    """Sheet2 mixes units: plain floats are mg/L, '1.3213 (ppb)' is ug/L."""
    if isinstance(cell, str):
        value = float(re.match(r"\s*([\d.eE+-]+)", cell).group(1))
        if "ppb" in cell.lower() or "µg" in cell or "ug" in cell.lower():
            return value / 1000.0
        return value
    return float(cell)


# ---- calibration table ----
_cal = _read_titled("Sheet2", "Metal").set_index("Metal")
for _c in ["R²", "Slope (m)"]:
    _cal[_c] = _cal[_c].astype(float)
for _c in ["LOD (mg/L)", "LOQ (mg/L)"]:
    _cal[_c] = [_limit_mgL(v) for v in _cal[_c]]

NI_LOD_WORKBOOK = {k: float(_cal.loc["Ni", k]) for k in NI_LOD_CORRECTION}
for _k, _v in NI_LOD_CORRECTION.items():
    _cal.loc["Ni", _k] = _v

CAL = _cal.loc[METALS]
METHOD_LOD = {m: CAL.loc[m, "LOD (mg/L)"] * DIGEST_FACTOR[m] for m in METALS}
METHOD_LOQ = {m: CAL.loc[m, "LOQ (mg/L)"] * DIGEST_FACTOR[m] for m in METALS}

# ---- spike recovery ----
# Sheet3 is summarised as "mean ± SD" strings, one row per matrix, one column per
# element. Its arsenic column is keyed correctly (cow dung carries the C-block
# statistics), unlike the arsenic column of Sheet1 -- see the note in 01_clean.py.
_TYPE_CANON = {"Cowdung": "Cow dung", "Bonemeal": "Bone meal",
               "Tricho-compost": "Trichocompost", "Hornmeal": "Horn meal",
               "Neem Cake": "Neem cake"}
_COL = {m: f"{m} (%)" for m in METALS}
_COL["As"] = "As(%)"       # no space in the consolidated sheet

_rec = _read_titled("Sheet3", "Fertilizer").rename(columns={"Fertilizer": "Type"})
_rec["Type"] = _rec["Type"].map(lambda t: _TYPE_CANON.get(str(t).strip(), str(t).strip()))


def _parse(cell):
    mean, sd = str(cell).replace("±", "|").split("|")
    return float(mean), float(sd)


RECOVERY = {}
for _, _r in _rec.iterrows():
    for _m in METALS:
        RECOVERY[(_r["Type"], _m)] = _parse(_r[_COL[_m]])

TYPES_QAQC = list(_rec["Type"])
N_SPIKE_REPLICATES = 3   # per matrix; corrected from 5 by the analyst, 2026-08-14

if __name__ == "__main__":
    print("Calibration (LOD/LOQ in mg/L; method limits in mg/kg):")
    for m in METALS:
        print(f"  {m:>2}  R2={CAL.loc[m,'R²']:.4f}  LOD={CAL.loc[m,'LOD (mg/L)']:.6f}"
              f"  ->  method LOD {METHOD_LOD[m]:.4f}  LOQ {METHOD_LOQ[m]:.4f}"
              f"  (x{DIGEST_FACTOR[m]:g})")
    print(f"\nNi workbook values {NI_LOD_WORKBOOK} superseded by {NI_LOD_CORRECTION}")
    print(f"LOQ/LOD ratios: " + ", ".join(
        f"{m} {CAL.loc[m,'LOQ (mg/L)']/CAL.loc[m,'LOD (mg/L)']:.3f}" for m in METALS))
