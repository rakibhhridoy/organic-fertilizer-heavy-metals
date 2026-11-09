#!/usr/bin/env python3
"""Assemble submissions/<Journal>/ : one complete, uploadable folder per journal.

    python3 scripts/build_submissions.py              both journals
    python3 scripts/build_submissions.py EGAH         just one

There is ONE canonical source at the manuscript root. Each journal folder is a
generated bundle built from it, so the folders can be self-contained without the
sources diverging. The two forms of the manuscript come from the \\SPRINGERFORM
switch in manuscript.tex, not from two files.

GENERATED, overwritten on every run:
    manuscript.pdf      the right FORM for this journal, under a plain name
    supplementary.pdf
    supplementary.tex   copy of the shared source, marked DO NOT EDIT
    cover_letter.pdf    compiled from this folder's own cover_letter.tex
    upload/             flat standalone source set
    Turnitin/           similarity-check copy

HAND-MAINTAINED, never touched by this script:
    UPLOAD.txt  Submission_Info.txt  SUBMISSION_FORM_FIELDS.md
    Submission_Questionnaire.txt  Highlights.txt  cover_letter.tex

Run the PDF builds first (make manuscript, make egah, make supp); this script
copies, it does not typeset the manuscript.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBS = ROOT / "submissions"

JOURNALS = {
    "EnvironmentalAdvances": {
        "name": "Environmental Advances",
        "pdf": "manuscript.pdf",        # Elsevier form: the default build
        "bbl": "manuscript.bbl",
        "springer": False,
    },
    "EGAH": {
        "name": "Environmental Geochemistry and Health",
        "pdf": "manuscript_egah.pdf",   # Springer form: built by `make egah`
        "bbl": "manuscript_egah.bbl",
        "springer": True,
    },
}

# Never regenerate these; they hold hand-written text.
PROTECTED = {"UPLOAD.txt", "Submission_Info.txt", "SUBMISSION_FORM_FIELDS.md",
             "Submission_Questionnaire.txt", "Highlights.txt", "cover_letter.tex",
             "Response_to_Editor.tex", "highlights.docx"}

targets = sys.argv[1:] or list(JOURNALS)
for t in targets:
    if t not in JOURNALS:
        sys.exit(f"unknown journal {t!r}; expected one of {', '.join(JOURNALS)}")


def run(cmd, cwd):
    subprocess.run(cmd, cwd=cwd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


for key in targets:
    J = JOURNALS[key]
    OUT = SUBS / key
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"\n{key}  ({J['name']})")

    # ---- 1. the manuscript, in this journal's form, under a plain name ----
    src_pdf = ROOT / J["pdf"]
    if not src_pdf.exists():
        sys.exit(f"  {J['pdf']} missing. Run `make {'egah' if J['springer'] else 'manuscript'}` first.")
    shutil.copy2(src_pdf, OUT / "manuscript.pdf")
    print(f"  manuscript.pdf      <- {J['pdf']}")

    # ---- 2. the supplementary, identical for both journals ----
    for f in ("supplementary.pdf",):
        if (ROOT / f).exists():
            shutil.copy2(ROOT / f, OUT / f)
    (OUT / "supplementary.tex").write_text(
        (ROOT / "supplementary.tex").read_text(encoding="utf-8"), encoding="utf-8")
    print("  supplementary.pdf, supplementary.tex")

    # ---- 3. the flat, standalone source set ----
    run([sys.executable, str(ROOT / "scripts" / "build_upload.py"),
         "egah" if J["springer"] else "envadv"], cwd=ROOT)
    print("  upload/")

    # ---- 4. the cover letter and, where present, the appeal letter ----
    for stem in ("cover_letter", "Response_to_Editor"):
        if not (OUT / f"{stem}.tex").exists():
            continue
        for _ in range(2):
            run(["pdflatex", "-interaction=nonstopmode", f"{stem}.tex"], cwd=OUT)
        for ext in ("aux", "log", "out"):
            (OUT / f"{stem}.{ext}").unlink(missing_ok=True)
        print(f"  {stem}.pdf")

    # ---- 4b. the Word single-file manuscript ----
    # Editorial Manager asks for one file holding the manuscript and can pull the
    # title, abstract, author list and references out of a Word file automatically.
    # Shipped per journal so the folder is self-contained. The DOCX build only ever
    # emits the Elsevier form, so EGAH gets the Elsevier wording here; that matters
    # only if EGAH is ever submitted from Word rather than from upload/.
    for d in ("manuscript.docx", "supplementary.docx"):
        src = ROOT / "docx" / d
        if src.exists():
            shutil.copy2(src, OUT / d)
    if (OUT / "manuscript.docx").exists():
        print("  manuscript.docx, supplementary.docx")
    else:
        print("  manuscript.docx  SKIPPED (run `make docx` first)")

    # ---- 4c. the Declaration of Interest ----
    print("  Declaration_of_Interest.tex/.pdf/.docx")

    # ---- 5. the Turnitin copy ----
    # Turnitin strips the title, authors, back matter and references, which is
    # exactly where the two journal forms differ, so the checkable text is the
    # same either way. Each folder gets its own copy for self-containment.
    tsrc = ROOT / "Turnitin" / "Turnitin_Combined.pdf"
    if tsrc.exists():
        (OUT / "Turnitin").mkdir(exist_ok=True)
        shutil.copy2(tsrc, OUT / "Turnitin" / "Turnitin_Combined.pdf")
        (OUT / "Turnitin" / "README.txt").write_text(
            "TURNITIN CHECK COPY -- NOT FOR SUBMISSION\n"
            "=========================================\n"
            "Generated copy. The build lives at ../../../Turnitin/ and is shared by both\n"
            "journals: Turnitin strips the title, authors, back matter and reference list,\n"
            "which is precisely where the Elsevier and Springer forms differ, so the\n"
            "checkable text is identical for both.\n\n"
            "Rebuild:  cd ../../../Turnitin && python3 build_turnitin.py\n"
            "then:     python3 scripts/build_submissions.py\n", encoding="utf-8")
        print("  Turnitin/")
    else:
        print("  Turnitin/  SKIPPED (run Turnitin/build_turnitin.py first)")

    # Highlights are an Elsevier item; Springer does not ask for them.
    expected = PROTECTED - ({"highlights.docx", "Highlights.txt"} if J["springer"] else set())
    missing = sorted(f for f in expected if not (OUT / f).exists())
    if missing:
        print("  note, hand-written files not present:", ", ".join(missing))

run([sys.executable, str(ROOT / "scripts" / "build_declaration.py")], cwd=ROOT)

print("\ndone")
