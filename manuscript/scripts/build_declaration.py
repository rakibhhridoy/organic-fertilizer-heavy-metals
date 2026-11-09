"""Declaration of Interest statement, one per journal.

Elsevier requires this as a .doc/.docx upload at the attach-files step; the PDF is
built alongside for reading. Title and author list are read from manuscript.tex so
they cannot drift from the manuscript, which is how a stale title reached a built
file once before.
"""
import re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = (ROOT / "manuscript.tex").read_text(encoding="utf-8")

m = re.search(r"\\title\{(.+?)\}\s*\n\s*\n", SRC, re.S) or re.search(r"\\title\{(.+?)\}", SRC, re.S)
if not m:
    sys.exit("build_declaration: no \\title{} in manuscript.tex")
TITLE = " ".join(m.group(1).split())

AFF = {
    "inst1": "Department of Soil, Water and Environment, University of Dhaka, Dhaka 1000, Bangladesh",
    "inst2": "Fermium Systems, Dhaka 1207, Bangladesh",
    "inst3": "Department of Disaster Science and Climate Resilience, University of Dhaka, Dhaka 1000, Bangladesh",
    "inst4": "Institute of National Analytical Research and Service (INARS), BCSIR, Dhaka, Bangladesh",
}

AUTHORS = []
for keys, raw in re.findall(r"\\author\[([^\]]+)\]\{(.+?)\}\n", SRC):
    name = re.sub(r"\\,?\\orcidlink\{[^}]*\}", "", raw)
    name = re.sub(r"\\(cor|fn)ref\{[^}]*\}", "", name).strip()
    corr = "\\corref" in raw
    AUTHORS.append((name, [AFF[k.strip()] for k in keys.split(",")], corr))
if len(AUTHORS) != 7:
    sys.exit(f"build_declaration: expected 7 authors, parsed {len(AUTHORS)}")

FUNDING = "This work was not supported by any funding source."

JOURNALS = {"EnvironmentalAdvances": "Environmental Advances",
            "EGAH": "Environmental Geochemistry and Health"}

for folder, journal in JOURNALS.items():
    items = "\n".join(
        "    \\item %s%s, %s" % (n, " (Corresponding author)" if c else "", "; ".join(a))
        for n, a, c in AUTHORS)
    tex = r"""\documentclass[11pt]{article}
\usepackage[T1]{fontenc}
\usepackage[a4paper,margin=1in]{geometry}
\usepackage{times}
\usepackage{parskip}

\begin{document}

\begin{center}
\Large\textbf{Declaration of Interest Statement}
\end{center}

\vspace{0.5cm}

\textbf{Manuscript Title:} %s

\textbf{Journal:} %s

\vspace{0.5cm}

All authors declare that they have no known competing financial interests or
personal relationships that could have appeared to influence the work reported in
this paper.

\vspace{1cm}

\textbf{Authors:}
\begin{itemize}
    \itemsep -2pt
%s
\end{itemize}

\vspace{0.5cm}

\textbf{Funding:} %s

\end{document}
""" % (TITLE, journal, items, FUNDING)

    out = ROOT / "submissions" / folder
    (out / "Declaration_of_Interest.tex").write_text(tex, encoding="utf-8")
    for _ in range(2):
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "Declaration_of_Interest.tex"],
                       cwd=out, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if shutil.which("pandoc"):
        subprocess.run(["pandoc", "Declaration_of_Interest.tex", "-o", "Declaration_of_Interest.docx"],
                       cwd=out, check=True)
    for ext in ("aux", "log", "out"):
        (out / f"Declaration_of_Interest.{ext}").unlink(missing_ok=True)
    print(f"  {folder}: Declaration_of_Interest.tex/.pdf/.docx")

print("done")
