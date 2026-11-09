# -*- coding: utf-8 -*-
"""Loader for the reference-value tables -- the single source of truth for soil
background (Cbv), safe ceiling (Csv), the strict sensitivity ceiling, the
Hakanson toxic-response factors and the Bangladesh fertilizer limits (MAL).

Import from anywhere in the pipeline:
    from soil_refs import CBV, CSV, CSV_STRICT, TR, MAL, METALS
Scripts living in exploration/scripts/ should add manuscript/scripts to sys.path
first; see 03_indices.py for the pattern.
"""
import os
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(os.path.dirname(_HERE), "data")
_PATH = os.path.join(_DATA, "soil_reference_values.csv")
_LIMITS = os.path.join(_DATA, "fertilizer_limits.csv")

_df = pd.read_csv(_PATH, comment="#").set_index("Metal")
_lim = pd.read_csv(_LIMITS, comment="#").set_index("Element")

METALS = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"]
CBV = _df["Cbv_mgkg"].to_dict()
CBV_BD = _df["Cbv_BD_mgkg"].to_dict()   # sensitivity only
CSV = _df["Csv_mgkg"].to_dict()
CSV_STRICT = _df["Csv_strict_mgkg"].to_dict()
TR = _df["Tr_hakanson"].to_dict()
MAL = _lim["MAL_mgkg"].to_dict()

# Fail loudly if a table and the pipeline disagree about which elements exist.
for _name, _table in (("soil_reference_values.csv", CBV),
                      ("fertilizer_limits.csv", MAL)):
    _missing = [m for m in METALS if m not in _table]
    if _missing:
        raise ValueError(f"{_name} is missing elements: {_missing}")

SOURCES = {
    "Cbv": "Kabata-Pendias (2011), world-soil means",
    "Csv": "VROM (2000), Dutch soil-remediation intervention values",
    "Csv_strict": "CCME (2003/2007), Canadian agricultural soil quality guidelines",
    "Tr": "Hakanson (1980)",
    "MAL": "BARC Fertilizer Recommendation Guide (2024), App.-3; MoA gazette (2008)",
}
