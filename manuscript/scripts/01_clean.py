# -*- coding: utf-8 -*-
"""Clean the raw dataset and apply standard rules. Reproduces data/clean_data.*
Run:  python3 scripts/01_clean.py   (from manuscript/)

Source: data/OF_HM_TGT.xlsx -- the final consolidated laboratory file.
  Sheet1  reagent-blank-corrected concentrations with the supplier identity of
          each sample; non-detects recorded as the string "BDL".
  Sheet2  calibration / LOD / LOQ  -> read by gen_tables_qaqc.py
  Sheet3  spike recovery           -> read by gen_tables_qaqc.py

Per-metal reagent-blank offsets already subtracted in Sheet1 (mg/kg):
  Cu 0.0321, Cr 0.0237, Pb 0.2771, Cd 0.0306, Zn 9.5510, Ni 0.0796.

Steps: derive Type/Brand/Pack from the supplier label; coerce BDL to non-detect
and substitute LOD/2; flag outliers (Grubbs) but RETAIN them as valid.
"""
import os, re, pandas as pd, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

metals = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni"]
types = ["Cow dung", "Bone meal", "Trichocompost", "Generic Organic Fertilizer",
         "Vermicompost", "Horn meal", "Neem cake"]

# Supplier label -> Brand. Bengali trade names are transliterated for typesetting;
# the original strings are preserved in Brand_orig.
TRANSLIT = {
    "সেবক": "Sebok",
    "একমি": "ACME",
    "অন্নপূর্ণ জৈব সার": "Annapurna Jaib Sar",
    "স্মার্ট অ্যাগ্রো পার্ক প্রাইভেট লিমিটেড": "Smart Agro Park Pvt. Ltd.",
    "কৃষিবিদ উপকরণ নার্সারি": "Krishibid Upakaran Nursery",
    "মেসার্স মধু শুধন অ্যাগ্রো ফার্ম": "Messrs Madhu Shudhan Agro Farm",
}
CAT_PREFIX = re.compile(
    r"^\s*(cow\s*dung|bone\s*meal|tricho\s*-?\s*compost|generic\s+organic\s+fertilizer"
    r"|vermicompost|horn\s*meal|neem\s*cake)\s*[:\-–]+\s*", re.I)
PACK = re.compile(r"\s*[-–=]\s*([\d.]+)\s*(kg|gm|g)\s*$", re.I)

df = pd.read_excel(os.path.join(DATA, "OF_HM_TGT.xlsx"), sheet_name="Sheet1")
df.columns = [c.strip() for c in df.columns]
label = df[df.columns[0]].astype(str).str.strip()
df = df.rename(columns={df.columns[0]: "Label", "Ph": "pH", "Ec (mS/cm)": "EC",
    "Cu ppm": "Cu", "Cr ppm": "Cr", "Pb ppm": "Pb", "Cd ppm": "Cd",
    "Zn ppm": "Zn", "Ni ppm": "Ni"})

# Seven categories in fixed blocks of five replicates.
if len(df) != 35:
    raise ValueError(f"expected 35 samples, found {len(df)}")
df["Type"] = np.repeat(types, 5)
df["Sample"] = [f"{t[:2].upper()}{i+1}" for t in types for i in range(5)]


def split_label(s):
    s = CAT_PREFIX.sub("", s).strip()
    m = PACK.search(s)
    pack = f"{m.group(1)} {m.group(2).lower().replace('gm', 'g')}" if m else ""
    brand = PACK.sub("", s).strip(" -–=")
    return brand, pack


df["Brand_orig"], df["Pack"] = zip(*[split_label(s) for s in label])
df["Brand"] = [TRANSLIT.get(b, b) for b in df["Brand_orig"]]

# Non-detects: "BDL" in the source. Record the flag before numeric coercion.
for m in metals:
    df[m + "_bdl"] = df[m].astype(str).str.strip().str.upper().eq("BDL")
    df[m] = pd.to_numeric(df[m], errors="coerce")

# Rule 1: non-detects -> LOD/2, LOD taken as the lowest quantified value for that
# element on the reported (mg/kg) scale.
#
# NOTE the digestion factor is 25 (2 g -> 50 mL), so the Sheet2 instrument LODs
# rescale to 0.15 (Cd) - 6.10 (Zn) mg/kg. At that factor Cu and Zn are fully
# consistent with the reported data and Cr/Pb nearly so (1 and 3 values below),
# but Ni still has 14/35 values under its 2.33 mg/kg method limit. Non-detects are
# therefore still classified operationally -- a value is a non-detect when blank
# subtraction leaves it indistinguishable from zero, which is how BDL is flagged
# in Sheet1 -- so that one criterion applies to every element. Section 2.4 of the
# manuscript states this and names Ni as the exception.
lod = {m: df.loc[df[m] > 0, m].min() for m in metals}
for m in metals:
    n_bdl = int(df[m + "_bdl"].sum())
    df.loc[df[m].isna(), m] = lod[m] / 2.0
    if n_bdl:
        print(f"  {m}: LOD(empirical) = {lod[m]:.4f} mg/kg, non-detects = {n_bdl}"
              f" -> substituted {lod[m]/2:.4f}")

# Rule 2: Grubbs outlier flags within each type (reported, not removed)
def grubbs(x):
    x=np.asarray(x,float); n=len(x)
    if n<3: return np.zeros(n,bool)
    z=np.abs(x-x.mean())/(x.std(ddof=1)+1e-12); G=z.max()
    t2=stats.t.ppf(1-0.05/(2*n),n-2)**2
    Gc=(n-1)/np.sqrt(n)*np.sqrt(t2/(n-2+t2))
    f=np.zeros(n,bool)
    if G>Gc: f[z.argmax()]=True
    return f
flags=[]
for m in metals:
    for t,g in df.groupby("Type"):
        for idx,o in zip(g.index, grubbs(g[m].values)):
            if o: flags.append((m,t,round(df.loc[idx,m],3)))
print("Grubbs-flagged (retained):", flags)

cols = ["Type", "Sample", "Brand", "Brand_orig", "Pack", "pH", "EC"] + \
       metals + [m + "_bdl" for m in metals]
df = df[cols]
df.to_csv(os.path.join(DATA,"clean_data.csv"), index=False)
df.to_pickle(os.path.join(DATA,"clean_data.pkl"))
print("Wrote data/clean_data.csv and .pkl ; rows =", len(df),
      "; total non-detects =", int(df[[m+'_bdl' for m in metals]].sum().sum()))
