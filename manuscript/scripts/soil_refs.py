# -*- coding: utf-8 -*-
"""Loader for data/soil_reference_values.csv -- the single source of truth for
soil background (Cbv), safe ceiling (Csv), the strict sensitivity ceiling and
the Hakanson toxic-response factors.

Import from anywhere in the pipeline:
    from soil_refs import CBV, CSV, CSV_STRICT, TR, METALS
Scripts living in exploration/scripts/ should add manuscript/scripts to sys.path
first; see 03_indices.py for the pattern.
"""
import os
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA = os.path.join(os.path.dirname(_HERE), "data")
_PATH = os.path.join(_DATA, "soil_reference_values.csv")

_df = pd.read_csv(_PATH, comment="#").set_index("Metal")

METALS = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni"]
CBV = _df["Cbv_mgkg"].to_dict()
CSV = _df["Csv_mgkg"].to_dict()
CSV_STRICT = _df["Csv_strict_mgkg"].to_dict()
TR = _df["Tr_hakanson"].to_dict()

# Fail loudly if the CSV and the pipeline disagree about which metals exist.
_missing = [m for m in METALS if m not in CBV]
if _missing:
    raise ValueError(f"soil_reference_values.csv is missing metals: {_missing}")

SOURCES = {
    "Cbv": "Kabata-Pendias (2011), world-soil means",
    "Csv": "VROM (2000), Dutch soil-remediation intervention values",
    "Csv_strict": "CCME (2003/2007), Canadian agricultural soil quality guidelines",
    "Tr": "Hakanson (1980)",
}
