#!/usr/bin/env python3
"""Assemble a flat, standalone copy of the manuscript source for one journal.

Usage:
    python3 scripts/build_upload.py            Environmental Advances (primary)
    python3 scripts/build_upload.py egah       Env. Geochemistry and Health

Figures are renamed to match their figure numbers, the \inputbody table bodies
are inlined so the folder has no subdirectories, and references.bib/.bbl are
copied across. The parent folder is never modified.

The two targets share one source. manuscript.tex defaults to Elsevier form; the
EGAH set gets \def\SPRINGERFORM{} prepended so the flat copy compiles in Springer
form (unnumbered headings, standalone Limitations, Ethics/Consent present)
without anyone having to remember the command-line flag.
"""
import re
import shutil
import sys
from pathlib import Path

ROOT = Path("/Volumes/SSD Rx/Research/OrangicFertilizer/manuscript")

TARGET = (sys.argv[1] if len(sys.argv) > 1 else "envadv").lower()
if TARGET not in {"envadv", "egah"}:
    sys.exit(f"unknown target {TARGET!r}; expected 'envadv' or 'egah'")

if TARGET == "egah":
    OUT = ROOT / "submissions" / "EGAH" / "upload"
    BBL = "manuscript_egah.bbl"
else:
    OUT = ROOT / "submissions" / "EnvironmentalAdvances" / "upload"
    BBL = "manuscript.bbl"
OUT.mkdir(parents=True, exist_ok=True)

# figure file -> figure number, taken from manuscript.aux
FIGMAP = {
    "fig1_concentrations.pdf": "Fig1.pdf",
    "fig_composition.pdf": "Fig2.pdf",
    "fig_multivariate.pdf": "Fig3.pdf",
    "fig_soilrisk.pdf": "Fig4.pdf",
    "fig_pollution.pdf": "Fig5.pdf",
    "fig_healthrisk.pdf": "Fig6.pdf",
}

src = (ROOT / "manuscript.tex").read_text(encoding="utf-8")

# 0. pin the journal form, so the flat copy needs no command-line flag
if TARGET == "egah":
    src = "\\def\\SPRINGERFORM{}\n" + src

# 1. flat folder: no graphicspath
src = src.replace("\\graphicspath{{figures/}}\n", "")

# 2. figure names follow figure numbers
for old, new in FIGMAP.items():
    n = src.count(old)
    assert n == 1, f"{old}: {n} occurrences"
    src = src.replace(old, new)

# 3. inline the table bodies so nothing lives in a subdirectory
def inline(m):
    body = (ROOT / m.group(1)).read_text(encoding="utf-8").rstrip("\n")
    return body

src, n = re.subn(r"\\inputbody\{([^}]+)\}", inline, src)
# Two main-text tables since 2026-08-21, when the calibration and detection-limit
# table moved to the supplementary; see CHANGES.txt, round 2b.
assert n == 2, n
# the \inputbody helper is now unused, but harmless; leave the definition in
# place so the file stays diffable against the parent source.

(OUT / "manuscript.tex").write_text(src, encoding="utf-8")

for old, new in FIGMAP.items():
    shutil.copy2(ROOT / "figures" / old, OUT / new)
shutil.copy2(ROOT / "references.bib", OUT / "references.bib")
# The SI carries its own \inputbody table bodies, thirteen of them. Copying it
# verbatim shipped a file that could not compile, because tables/ is not part of
# the flat set. Inline them the same way as the main text.
si = (ROOT / "supplementary.tex").read_text(encoding="utf-8")
si, n_si = re.subn(r"\\inputbody\{([^}]+)\}", inline, si)
assert n_si == 13, n_si
(OUT / "supplementary.tex").write_text(si, encoding="utf-8")
if (ROOT / "supplementary.bbl").exists():
    shutil.copy2(ROOT / "supplementary.bbl", OUT / "supplementary.bbl")
_bbl = ROOT / BBL
if _bbl.exists():
    shutil.copy2(_bbl, OUT / "manuscript.bbl")
else:
    print(f"  WARNING: {BBL} not found; run the build for this target first")

print(f"wrote {OUT}  (target: {TARGET})")
