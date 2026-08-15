# -*- coding: utf-8 -*-
"""Human-health risk assessment parameters (USEPA framework).
Values are standard literature/USEPA defaults; VERIFY and localise before submission.
Concentrations in mg/kg; doses in mg/kg-day.
"""
metals = ["Cu","Cr","Pb","Cd","Zn","Ni","As"]

# Oral reference doses RfD_o (mg/kg-day) -- USEPA IRIS/RSL
RfD_o  = {"Cu":0.04,"Cr":0.003,"Pb":0.0035,"Cd":0.001,"Zn":0.30,"Ni":0.02,"As":0.0003}
# Gastro-intestinal absorption factor (for dermal RfD = RfD_o * GIABS)
GIABS  = {"Cu":1.0,"Cr":0.025,"Pb":1.0,"Cd":0.05,"Zn":1.0,"Ni":1.0,"As":1.0}
# Dermal absorption fraction ABS_d. 0.03 for arsenic is the USEPA RSL value;
# the others take the default 0.001 for inorganic species.
ABS_d  = {"Cu":0.001,"Cr":0.001,"Pb":0.001,"Cd":0.001,"Zn":0.001,"Ni":0.001,"As":0.03}
# Oral cancer slope factors SF_o (per mg/kg-day); None = not via oral ingestion.
# Arsenic 1.5 is the IRIS value for INORGANIC As, applied to total As here, which
# is conservative: some fraction of the total is organic and far less toxic.
SF_o   = {"Cu":None,"Cr":0.5,"Pb":0.0085,"Cd":None,"Zn":None,"Ni":None,"As":1.5}
# Fraction of total Cr assumed present as carcinogenic Cr(VI)
CR6_FRACTION = 1.0/7.0

# --- Exposure parameters ---
# Scenario A: fertilizer handlers (occupational, direct contact with fertilizer solid)
HANDLER = dict(
    IngR = 100,      # mg/day  (incidental ingestion of solid)
    InhR = 20,       # m3/day
    SA   = 3300,     # cm2 exposed skin (hands+forearms)
    AF   = 0.2,      # mg/cm2 adherence
    EF   = 250,      # days/year (occupational)
    ED   = 25,       # years
    BW   = 70,       # kg
    PEF  = 1.36e9,   # m3/kg particle emission factor
)
# Scenario B: consumers via crops grown on fertilized soil
CONSUMER = dict(
    IR   = 0.345,    # kg/day vegetable intake (fresh)
    Cf   = 0.085,    # fresh->dry conversion
    EF   = 365,      # days/year
    ED   = 30,       # years
    BW   = 70,       # kg
    APPLY_YEARS = 10,   # years of fertilization assumed accumulated in soil
)
# Soil background (Cbv) -- from data/soil_reference_values.csv, see that file for
# sources. Soil->plant transfer factors (dimensionless) are literature values.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "scripts"))
from soil_refs import CBV as BG_SOIL
# Arsenic is poorly translocated to edible tissue relative to Cd or Zn; 0.02 sits
# in the middle of the 0.01-0.04 range reported for leafy and fruiting vegetables.
TF      = {"Cu":0.10,"Cr":0.04,"Pb":0.02,"Cd":0.30,"Zn":0.40,"Ni":0.08,"As":0.02}
