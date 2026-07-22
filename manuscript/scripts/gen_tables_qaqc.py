# -*- coding: utf-8 -*-
"""Emit the QA/QC LaTeX table bodies straight from the final laboratory file
data/OF_HM_TGT.xlsx (Sheet2 = calibration/LOD/LOQ, Sheet3 = spike recovery).
Reading the workbook directly keeps a single source of truth -- there is no
intermediate CSV to drift out of date.

Run:  python3 scripts/gen_tables_qaqc.py   (from manuscript/)
"""
import os, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data"); TBL = os.path.join(ROOT, "tables")
XLS = os.path.join(DATA, "OF_HM_TGT.xlsx")

metals = ["Pb", "Cd", "Cr", "Cu", "Zn", "Ni"]      # reporting order
TYPE_CANON = {"Cowdung": "Cow dung", "Bonemeal": "Bone meal",
              "Tricho-compost": "Trichocompost", "Hornmeal": "Horn meal",
              "Neem Cake": "Neem cake"}

def read_titled(sheet, first_col):
    """Both QA/QC sheets carry a title row and blank spacer rows above the real
    header. Locate the header by its first cell rather than hard-coding a row."""
    raw = pd.read_excel(XLS, sheet_name=sheet, header=None)
    hdr = raw.index[raw[0].astype(str).str.strip() == first_col]
    if len(hdr) != 1:
        raise ValueError(f"{sheet}: expected one '{first_col}' header row, got {list(hdr)}")
    out = raw.iloc[hdr[0] + 1:].copy()
    out.columns = [str(c).strip() for c in raw.iloc[hdr[0]]]
    return out.dropna(how="all").reset_index(drop=True)


# ---- Sheet2: calibration, R^2, slope, LOD, LOQ ----
cal = read_titled("Sheet2", "Metal").set_index("Metal")
for c in ["R²", "Slope (m)", "LOD (mg/L)", "LOQ (mg/L)"]:
    cal[c] = cal[c].astype(float)

with open(os.path.join(TBL, "table_qaqc_calib_body.tex"), "w") as f:
    for m in metals:
        r = cal.loc[m]
        eq = str(r["Equation"]).replace(" ", "")
        eq = "$" + eq.replace("y=", "y = ").replace("+", " + ").replace("-", " - ") + "$"
        f.write(f"{m} & {eq} & {r['R²']:.4f} & {r['Slope (m)']:.4f} & "
                f"{r['LOD (mg/L)']:.4f} & {r['LOQ (mg/L)']:.4f} \\\\\n")

# ---- Sheet3: spike recovery, cells are "mean ± SD" strings ----
rec = read_titled("Sheet3", "Fertilizer").rename(columns={"Fertilizer": "Type"})
rec["Type"] = rec["Type"].map(lambda t: TYPE_CANON.get(str(t).strip(), str(t).strip()))

def parse(cell):
    mean, sd = str(cell).replace("±", "|").split("|")
    return float(mean), float(sd)

means = {m: [] for m in metals}
with open(os.path.join(TBL, "si_recovery_body.tex"), "w") as f:
    for _, r in rec.iterrows():
        cells = []
        for m in metals:
            mu, sd = parse(r[f"{m} (%)"]); means[m].append(mu)
            cells.append(f"{mu:.2f} $\\pm$ {sd:.2f}")
        f.write(f"{r['Type']} & " + " & ".join(cells) + " \\\\\n")
    f.write("\\midrule\n")
    cells = [f"{pd.Series(means[m]).mean():.2f} $\\pm$ "
             f"{pd.Series(means[m]).std():.2f}" for m in metals]
    f.write("\\textbf{Overall} & " + " & ".join(cells) + " \\\\\n")

allv = [(v, m, t) for m in metals for v, t in zip(means[m], rec["Type"])]
elem = {m: pd.Series(means[m]).mean() for m in metals}
lo, hi = min(allv), max(allv)
print("Wrote QA/QC table bodies to", TBL)
print(f"  R2 range          : {cal['R²'].min():.4f}-{cal['R²'].max():.4f} "
      f"(low {cal['R²'].idxmin()}, high {cal['R²'].idxmax()})")
print(f"  LOD range (mg/L)  : {cal['LOD (mg/L)'].min():.4f} ({cal['LOD (mg/L)'].idxmin()})"
      f" - {cal['LOD (mg/L)'].max():.4f} ({cal['LOD (mg/L)'].idxmax()})")
print(f"  recovery, single  : {lo[0]:.2f}% ({lo[1]} in {lo[2]}) - "
      f"{hi[0]:.2f}% ({hi[1]} in {hi[2]})")
print(f"  recovery, element : {min(elem.values()):.2f}-{max(elem.values()):.2f} % "
      f"(low {min(elem, key=elem.get)}, high {max(elem, key=elem.get)})")
print("  LOQ/LOD ratios    :",
      ", ".join(f"{m} {cal.loc[m,'LOQ (mg/L)']/cal.loc[m,'LOD (mg/L)']:.3f}" for m in metals))
