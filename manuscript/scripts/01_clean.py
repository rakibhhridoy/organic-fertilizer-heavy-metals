# -*- coding: utf-8 -*-
"""Clean the raw dataset and apply standard rules. Reproduces data/clean_data.*
Run:  python3 scripts/01_clean.py   (from manuscript/)

Sources:

data/OF_HM_TGTup.xlsx -- the consolidated laboratory file, and the dataset of
record. Supersedes OF_HM_TGT.xlsx, whose seven shared columns it reproduces
exactly while adding arsenic.
  Sheet1  reagent-blank-corrected concentrations with the supplier identity of
          each sample; non-detects recorded as the string "BDL"; arsenic in
          ug/kg ("As ppb").
  Sheet2  calibration / LOD / LOQ  -> read via qaqc.py
  Sheet3  spike recovery           -> read via qaqc.py

data/OF_HM_As.xlsx -- the primary hydride-generation record for arsenic, kept as
  the provenance for the As column and used to cross-check it.
  Sheet1  columns A-F  calibration / LOD / LOQ (ug/L) and per-spike recovery;
          columns J-N  per-sample reading, blank and blank-corrected value.
  Arsenic uses its own sample coding (C=cow dung, B=bone meal, T=Trichocompost,
  unprefixed 1-5=generic OF, V=vermicompost, H=horn meal, N=neem cake), with the
  numbering following the Sheet1 row order within each category. AS_ID_PREFIX
  below maps it onto the CO1..NE5 codes; the merge asserts a complete 35-way
  bijection, so a mis-ordered file cannot pass silently.

Per-metal reagent-blank offsets already subtracted in Sheet1 (mg/kg):
  Cu 0.0321, Cr 0.0237, Pb 0.2771, Cd 0.0306, Zn 9.5510, Ni 0.0796.
The arsenic blank is 0.01729 ug/L, subtracted before the ug/kg conversion.

Steps: derive Type/Brand/Pack from the supplier label; merge arsenic; coerce BDL
to non-detect and substitute half the lowest quantified value (NOT half the method
LOD, which is a different quantity); flag outliers (Grubbs) but RETAIN them as valid.
"""
import os, re, sys, pandas as pd, numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
from qaqc import METHOD_LOD, METHOD_LOQ

metals = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]
types = ["Cow dung", "Bone meal", "Trichocompost", "Generic Organic Fertilizer",
         "Vermicompost", "Horn meal", "Neem cake"]

# Arsenic sample-code prefix -> fertilizer category (see module docstring).
AS_ID_PREFIX = {"C": "Cow dung", "B": "Bone meal", "T": "Trichocompost",
                "": "Generic Organic Fertilizer", "V": "Vermicompost",
                "H": "Horn meal", "N": "Neem cake"}
# Digest-to-sample factor for the arsenic aliquot: 2 g -> 50 mL as for the other
# elements (25), with a further five-fold dilution before hydride generation.
# Readings are in ug/L, so mg/kg = ug/L * 125 / 1000.
AS_FACTOR = 25 * 5

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

df = pd.read_excel(os.path.join(DATA, "OF_HM_TGTup.xlsx"), sheet_name="Sheet1")
df.columns = [c.strip() for c in df.columns]
label = df[df.columns[0]].astype(str).str.strip()
df = df.rename(columns={df.columns[0]: "Label", "Ph": "pH", "Ec (mS/cm)": "EC",
    "Cu ppm": "Cu", "Cr ppm": "Cr", "Pb ppm": "Pb", "Cd ppm": "Cd",
    "Zn ppm": "Zn", "Ni ppm": "Ni", "As ppb": "As_ugkg"})

# Seven categories in fixed blocks of five distinct products (not replicates).
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

# ---- Arsenic ----
# As arrives on the consolidated sheet in ug/kg ("As ppb"). It is cross-checked
# against OF_HM_As.xlsx, the primary hydride-generation record, which carries the
# raw reading and blank for every sample under its own coding.
df["As"] = pd.to_numeric(df["As_ugkg"], errors="raise") / 1000.0
df = df.drop(columns=["As_ugkg"])

_as = pd.read_excel(os.path.join(DATA, "OF_HM_As.xlsx"), sheet_name="Sheet1",
                    usecols="J:N", header=0)
_as.columns = ["ID", "Reading", "Blank", "Corrected", "Final_ugkg"]
_as = _as.dropna(subset=["ID", "Reading"])


def as_code(raw):
    """'C3' / '4' -> the CO1..NE5 code used throughout the pipeline."""
    s = str(raw).strip()
    pre = "".join(c for c in s if c.isalpha()).upper()
    num = "".join(c for c in s if c.isdigit())
    if pre not in AS_ID_PREFIX or not num:
        raise ValueError(f"unrecognised arsenic sample code: {raw!r}")
    return f"{AS_ID_PREFIX[pre][:2].upper()}{int(num)}"


_as["Sample"] = [as_code(v) for v in _as["ID"]]
# Recompute from the raw reading rather than trusting the workbook's own ug/kg
# column; the two must agree to within rounding.
_as["As_primary"] = (_as["Reading"] - _as["Blank"]) * AS_FACTOR / 1000.0
_delta = (_as["As_primary"] * 1000 - _as["Final_ugkg"]).abs().max()
if _delta > 1e-6:
    raise ValueError(f"arsenic recomputation disagrees with its workbook by {_delta:.4g} ug/kg")
if sorted(_as["Sample"]) != sorted(df["Sample"]):
    raise ValueError("arsenic sample codes are not a bijection onto the sample list")

# Reconcile the two records. OF_HM_TGTup.xlsx Sheet1 duplicated the generic-OF
# arsenic block into the cow-dung rows, dropping the measured cow-dung values;
# its own Sheet3 contradicts this, giving cow dung the recovery statistics of the
# C-prefixed block (101.53 +/- 8.86 %, i.e. C1-C3). The primary record therefore
# wins on any disagreement. This check clears itself once the consolidated sheet
# is corrected -- it warns only while the two actually differ.
_chk = df[["Sample", "As"]].merge(_as[["Sample", "As_primary"]], on="Sample",
                                  validate="one_to_one")
_bad = _chk[(_chk["As"] - _chk["As_primary"]).abs() > 1e-9]
if len(_bad):
    print(f"  !! As: {len(_bad)} sample(s) disagree between the consolidated sheet and "
          f"OF_HM_As.xlsx; using the latter:")
    for _, r in _bad.iterrows():
        print(f"       {r['Sample']}: sheet {r['As']:.4f} -> primary {r['As_primary']:.4f} mg/kg")
    df = df.drop(columns=["As"]).merge(_as[["Sample", "As_primary"]], on="Sample",
                                       validate="one_to_one").rename(
                                           columns={"As_primary": "As"})
print(f"  As: {len(_as)} samples, {df['As'].min():.3f}-{df['As'].max():.3f} mg/kg")

# Non-detects: "BDL" in the source. Record the flag before numeric coercion.
for m in metals:
    df[m + "_bdl"] = df[m].astype(str).str.strip().str.upper().eq("BDL")
    df[m] = pd.to_numeric(df[m], errors="coerce")

# Rule 1: non-detects -> half the lowest quantified value for that element. This is
# deliberately NOT half the method LOD from qaqc.py; see CHANGES.txt round 2. The
# 'lod' name below is historical and means 'lowest quantified value' for that
# element on the reported (mg/kg) scale.
#
# Non-detects are classified operationally -- a value is a non-detect when blank
# subtraction leaves it indistinguishable from zero, which is how BDL is flagged
# in Sheet1 -- so that one criterion applies to every element. The method limits
# computed below are reported alongside it in Section 2.4 as a cross-check.
lod = {m: df.loc[df[m] > 0, m].min() for m in metals}
for m in metals:
    n_bdl = int(df[m + "_bdl"].sum())
    df.loc[df[m].isna(), m] = lod[m] / 2.0
    if n_bdl:
        print(f"  {m}: LOD(empirical) = {lod[m]:.4f} mg/kg, non-detects = {n_bdl}"
              f" -> substituted {lod[m]/2:.4f}")

# Cross-check the operational rule against the instrumental limits rescaled by
# each element's digest-to-sample factor. Section 2.4 quotes these counts, so
# they are computed rather than transcribed.
print("\nMethod limits vs reported values (n of 35 below):")
for m in metals:
    n_lod = int((df.loc[~df[m + "_bdl"], m] < METHOD_LOD[m]).sum())
    n_loq = int((df.loc[~df[m + "_bdl"], m] < METHOD_LOQ[m]).sum())
    print(f"  {m:>2}: method LOD {METHOD_LOD[m]:6.3f}  LOQ {METHOD_LOQ[m]:7.3f} mg/kg"
          f"  -> {n_lod} < LOD, {n_loq} < LOQ")

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
