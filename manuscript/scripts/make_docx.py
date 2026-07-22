# -*- coding: utf-8 -*-
"""Build docx/manuscript.docx from manuscript.tex.

Run:  python3 scripts/make_docx.py        (from manuscript/)
Requires: pandoc, and docx/figures/*.png (see the `docx` Makefile target).

Four things in the LaTeX source do not survive a plain pandoc run and are dealt
with here:

  1. `\\inputbody{tables/x_body.tex}` -- a custom \\@input wrapper. Pandoc does
     not expand it, so every table would come out empty. The bodies are inlined.
  2. siunitx (`\\SI`, `\\si`, `\\num`) -- rendered to plain text with the unit
     spelled out, since Word has no siunitx.
  3. mhchem (`\\ce`) -- formulae rewritten with Unicode subscripts.
  4. elsarticle frontmatter (`\\author`/`\\affiliation`/`\\ead`/`\\corref`) --
     pandoc emits nothing useful, so it is replaced by a plain title block.

Everything else (sections, equations, citations, tables, captions) is left for
pandoc, which handles it natively.
"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docx")
os.makedirs(OUT, exist_ok=True)

src = open(os.path.join(ROOT, "manuscript.tex")).read()

# ---------------------------------------------------------------- 1. tables --
def inline_body(m):
    path = os.path.join(ROOT, m.group(1))
    if not os.path.exists(path):
        print(f"  WARNING: missing table body {m.group(1)}", file=sys.stderr)
        return ""
    return open(path).read().rstrip()

src = re.sub(r"\\inputbody\{([^}]+)\}", inline_body, src)

# ------------------------------------------------------------- 2. siunitx ---
UNIT = {
    "mg.kg^{-1}": "mg kg⁻¹", "mg.L^{-1}": "mg L⁻¹",
    "mg.kg^{-1}.yr^{-1}": "mg kg⁻¹ yr⁻¹",
    "mg.kg^{-1}.day^{-1}": "mg kg⁻¹ day⁻¹",
    "g.ha^{-1}.yr^{-1}": "g ha⁻¹ yr⁻¹",
    "kg.ha^{-1}.yr^{-1}": "kg ha⁻¹ yr⁻¹",
    "kg.ha^{-1}": "kg ha⁻¹", "t.ha^{-1}.yr^{-1}": "t ha⁻¹ yr⁻¹",
    "t.ha^{-1}": "t ha⁻¹", "mS.cm^{-1}": "mS cm⁻¹",
    "g.cm^{-3}": "g cm⁻³", "kg.day^{-1}": "kg day⁻¹",
    "mg.day^{-1}": "mg day⁻¹", "day.yr^{-1}": "day yr⁻¹",
    "mg.cm^{-2}": "mg cm⁻²", "cm^2": "cm²", "km": "km",
    "mm": "mm", "kg": "kg", "g": "g", "mL": "mL", "yr": "yr", "m": "m",
    "percent": "%",
}
def unit(u):
    return UNIT.get(u.strip(), u.replace("^{-1}", "⁻¹")
                                 .replace(".", " ").strip())

def expand(text, macro, nargs, fn):
    """Replace \\macro{..}{..} with fn(args). Brace-matched, so nested groups
    such as \\si{mg.kg^{-1}} are captured whole -- a plain [^}]* stops at the
    first closing brace and leaves a stray '}' in the output."""
    out, i, tag = [], 0, "\\" + macro
    while True:
        j = text.find(tag, i)
        # reject a longer macro name that merely starts with this one
        while j != -1 and j + len(tag) < len(text) and text[j + len(tag)].isalpha():
            j = text.find(tag, j + 1)
        if j == -1:
            out.append(text[i:]); break
        out.append(text[i:j])
        k, args = j + len(tag), []
        for _ in range(nargs):
            while k < len(text) and text[k] in " \n":
                k += 1
            if k >= len(text) or text[k] != "{":
                break
            depth, start = 1, k + 1
            k += 1
            while k < len(text) and depth:
                if text[k] == "{": depth += 1
                elif text[k] == "}": depth -= 1
                k += 1
            args.append(text[start:k - 1])
        if len(args) != nargs:
            out.append(tag); i = j + len(tag); continue
        out.append(fn(*args)); i = k
    return "".join(out)

src = expand(src, "SI", 2, lambda v, u: f"{v} {unit(u)}")
src = expand(src, "si", 1, unit)
src = expand(src, "num", 1, lambda v: v)

# ------------------------------------------------------------- 3. mhchem ----
SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
def chem(f):
    return re.sub(r"(?<=[A-Za-z\)])(\d+)", lambda d: d.group(1).translate(SUB),
                  f).replace("->", "→")
src = expand(src, "ce", 1, chem)

# --------------------------------------------------- 4. frontmatter block ---
TITLE = ("Assessment of Heavy Metal Contamination in Commercial Organic "
         "Fertilizers in Bangladesh and Its Compliance with National "
         "Regulatory Limits")
FRONT = r"""\title{%s}
\author{Ahnaf Ibne Nasir\textsuperscript{a,1} \and
Md Rakib Hasan\textsuperscript{a,b,1,*} \and
Md Harun Mia\textsuperscript{a} \and
Md Raisuddin Sikder\textsuperscript{a}}
\date{}
\maketitle

\noindent\textsuperscript{a}\,Department of Soil, Water and Environment, University of Dhaka, Dhaka 1000, Bangladesh

\noindent\textsuperscript{b}\,Fermium Systems, Dhaka 1207, Bangladesh

\noindent\textsuperscript{*}\,Corresponding author. Email: rakibhhridoy@fermium.systems

\noindent\textsuperscript{1}\,Ahnaf Ibne Nasir and Md Rakib Hasan contributed equally to this work.

""" % TITLE

# Replace everything from \begin{frontmatter} to \end{frontmatter}, keeping the
# abstract and keywords as ordinary headed sections.
fm = re.search(r"\\begin\{frontmatter\}(.*?)\\end\{frontmatter\}", src, re.S)
assert fm, "frontmatter not found"
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", fm.group(1), re.S)
keyword = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", fm.group(1), re.S)
block = FRONT
if abstract:
    block += "\\section*{Abstract}\n" + abstract.group(1).strip() + "\n\n"
if keyword:
    kw = keyword.group(1).strip().replace("\\sep", ";")
    block += "\\section*{Keywords}\n" + " ".join(kw.split()) + "\n\n"
src = src[:fm.start()] + block + src[fm.end():]

# ------------------------------------------------------------- 5. cleanup ---
src = re.sub(r"\\orcidlink\{[^}]*\}", "", src)
src = src.replace("\\linenumbers", "")
src = re.sub(r"\\includegraphics\[[^]]*\]\{([^}]+)\.pdf\}",
             r"\\includegraphics{docx/figures/\1.png}", src)
src = re.sub(r"\\resizebox\{[^}]*\}\{[^}]*\}\{%?\s*", "", src)
src = src.replace("\\end{tabular}}", "\\end{tabular}")
src = re.sub(r"\\(footnotesize|scriptsize|small|normalsize)\b", "", src)
src = re.sub(r"\\setlength\{[^}]*\}\{[^}]*\}", "", src)
# "$>$\\allowbreak\\ " -> "> " : keep the space the escape provided.
src = src.replace("\\allowbreak\\ ", " ").replace("\\allowbreak", "")

# Demote trivial inline math to plain Unicode. pandoc turns every $...$ into an
# OMML equation; Word renders those correctly but LibreOffice drops bare
# relational operators, so "$<$LOD" came out as "¿LOD". Anything needing real
# maths (superscripts, subscripts, macros) is left as an equation.
# NB: "\%" is deliberately NOT mapped to a bare "%". The demoted text is fed
# back through pandoc's LaTeX reader, where an unescaped % starts a comment and
# silently swallows the rest of the line.
MATHSYM = {r"\pm": "±", r"\approx": "≈", r"\le": "≤", r"\ge": "≥",
           r"\leq": "≤", r"\geq": "≥", r"\times": "×", r"\sim": "~",
           r"\ll": "≪", r"\gg": "≫", r"\,": " ", "{}": "",
           r"\eta": "η", r"\rho": "ρ", r"\alpha": "α", r"\beta": "β",
           r"\sigma": "σ", r"\mu": "μ", r"\Delta": "Δ", r"\delta": "δ"}
SUP = str.maketrans("-+0123456789", "⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹")

def demote(m):
    body = m.group(1)
    for k, v in MATHSYM.items():
        body = body.replace(k, v)
    # simple exponents -> Unicode superscripts, e.g. 10^{-4} -> 10⁻⁴, R^2 -> R²
    body = re.sub(r"\^\{([-+]?\d+)\}", lambda e: e.group(1).translate(SUP), body)
    body = re.sub(r"\^(\d)", lambda e: e.group(1).translate(SUP), body)
    probe = body.replace(r"\%", "")      # an escaped percent is fine in text
    if re.search(r"[\\^_]", probe):      # real maths: leave for pandoc
        return m.group(0)
    body = re.sub(r"\s*([=<>≤≥≈])\s*", r" \1 ", body)
    body = re.sub(r"\s{2,}", " ", body).strip()
    # "HI${}=1$" leaves the relation first; strip() would glue it to the
    # preceding word ("HI= 1"), so restore the space a relation needs.
    return (" " + body) if body[:1] in "=<>≤≥≈" else body

src = re.sub(r"\$([^$]{1,40})\$", demote, src)
# a LaTeX tie next to demoted text yields "CF~ \u2248~10"; collapse the doubled gap
src = re.sub(r"~\s+", "~", re.sub(r"\s+~", "~", src))

# Caption labels. pandoc resolves \ref to the right numbers but writes captions
# without a "Table N"/"Figure N" prefix, so the text would cite numbers the
# captions never show. Numbering here in document order matches pandoc's own,
# which counts tables and figures separately as they appear.
_cnt = {"table": 0, "figure": 0}
def _label_caption(m):
    env, body = m.group(1), m.group(2)
    _cnt[env] += 1
    tag = ("Table" if env == "table" else "Figure") + f" {_cnt[env]}. "
    body = body.replace("\\caption{", "\\caption{" + tag, 1)
    return f"\\begin{{{env}}}{body}\\end{{{env}}}"

src = re.sub(r"\\begin\{(table|figure)\}(.*?)\\end\{\1\}", _label_caption,
             src, flags=re.S)

# citeproc appends the bibliography at the end of the document but emits no
# heading for it; supply one where the LaTeX bibliography commands were.
src = re.sub(r"\\bibliographystyle\{[^}]*\}\s*\\bibliography\{[^}]*\}",
             r"\\section*{References}", src)

tmp = os.path.join(OUT, "_manuscript_pandoc.tex")
open(tmp, "w").write(src)

cmd = ["pandoc", tmp, "-f", "latex", "-o", os.path.join(OUT, "manuscript.docx"),
       "--citeproc", "--bibliography", os.path.join(ROOT, "references.bib"),
       "--resource-path", ROOT, "--number-sections", "--wrap=none"]
ref = os.path.join(OUT, "reference.docx")
if os.path.exists(ref):
    cmd += ["--reference-doc", ref]
print("  " + " ".join(os.path.basename(c) if c.startswith("/") else c for c in cmd))
subprocess.run(cmd, check=True, cwd=ROOT)

# ------------------------------------------------- 6. apply Word styling ----
# pandoc leaves the Normal style empty and emits no page setup, so the styling
# is applied here by patching the package directly: 12pt serif, 1.5 line
# spacing, 1in margins and continuous line numbering (needed for review and by
# most submission systems). Editing the XML is more reliable than shipping a
# reference.docx, because it cannot silently drift from the source document.
import shutil, zipfile

DOCX = os.path.join(OUT, "manuscript.docx")

TNR = ('<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" '
       'w:cs="Times New Roman" w:eastAsia="Times New Roman"/>')
BLACK = '<w:color w:val="000000"/>'

def para_style(sid, name, based, ppr, rpr, custom=False):
    cust = ' w:customStyle="1"' if custom else ""
    return (f'<w:style{cust} w:styleId="{sid}" w:type="paragraph">'
            f'<w:name w:val="{name}"/>'
            + (f'<w:basedOn w:val="{based}"/>' if based else "")
            + '<w:qFormat/>'
            f'<w:pPr>{ppr}</w:pPr><w:rPr>{TNR}{BLACK}{rpr}</w:rPr></w:style>')

SP = '<w:spacing w:after="120" w:line="360" w:lineRule="auto"/>'
JUST = '<w:jc w:val="both"/>'
CENTER = '<w:jc w:val="center"/>'
LEFT = '<w:jc w:val="left"/>'
SZ = lambda n: f'<w:sz w:val="{n}"/><w:szCs w:val="{n}"/>'

# 11pt = 22 half-points. Body justified; headings and captions left; title and
# author block centred. Everything black Times New Roman -- pandoc's defaults
# use a blue accent colour and a theme font, neither of which suits a manuscript.
STYLES = {
    "Normal":       para_style("Normal", "Normal", None, SP + JUST, SZ(22)),
    "BodyText":     para_style("BodyText", "Body Text", "Normal", SP + JUST, SZ(22)),
    "FirstParagraph": para_style("FirstParagraph", "First Paragraph", "BodyText",
                                 SP + JUST, SZ(22), custom=True),
    "Compact":      para_style("Compact", "Compact", "BodyText", SP + JUST, SZ(22),
                               custom=True),
    "Title":        para_style("Title", "Title", "Normal",
                               '<w:spacing w:after="160" w:line="276" w:lineRule="auto"/>'
                               + CENTER + '<w:keepNext/>',
                               SZ(28) + "<w:b/>"),
    "Author":       para_style("Author", "Author", "Normal",
                               '<w:spacing w:after="40" w:line="276" w:lineRule="auto"/>'
                               + CENTER, SZ(22), custom=True),
    "Abstract":     para_style("Abstract", "Abstract", "Normal", SP + JUST, SZ(22),
                               custom=True),
    "Heading1":     para_style("Heading1", "heading 1", "Normal",
                               '<w:keepNext/><w:spacing w:before="280" w:after="120"/>'
                               + LEFT, SZ(24) + "<w:b/>"),
    "Heading2":     para_style("Heading2", "heading 2", "Normal",
                               '<w:keepNext/><w:spacing w:before="240" w:after="100"/>'
                               + LEFT, SZ(22) + "<w:b/>"),
    "Heading3":     para_style("Heading3", "heading 3", "Normal",
                               '<w:keepNext/><w:spacing w:before="200" w:after="80"/>'
                               + LEFT, SZ(22) + "<w:b/><w:i/>"),
    "Caption":      para_style("Caption", "Caption", "Normal",
                               '<w:spacing w:before="120" w:after="200"/>' + JUST,
                               SZ(20)),
    "Bibliography": para_style("Bibliography", "Bibliography", "Normal",
                               '<w:spacing w:after="80" w:line="276" w:lineRule="auto"/>'
                               '<w:ind w:hanging="360" w:left="360"/>' + LEFT, SZ(22)),
}
SECTPR = (
    '<w:sectPr>'
    '<w:pgSz w:h="15840" w:w="12240"/>'
    '<w:pgMar w:bottom="1440" w:footer="720" w:gutter="0" w:header="720" '
    'w:left="1440" w:right="1440" w:top="1440"/>'
    '<w:lnNumType w:countBy="1" w:restart="continuous" w:distance="360"/>'
    '<w:docGrid w:linePitch="360"/>'
    '</w:sectPr>'
)


def centre_affiliations(xml):
    """Centre the affiliation / corresponding-author / equal-contribution lines.

    They are ordinary body paragraphs emitted between the author block and the
    Abstract heading, so they cannot be reached through a named style. Keying on
    that structural position is stable; a fixed paragraph index would not be."""
    paras = list(re.finditer(r"<w:p\b.*?</w:p>", xml, re.S))
    stop = next((i for i, m in enumerate(paras)
                 if 'w:val="Heading' in m.group(0) or 'w:val="Abstract"' in m.group(0)),
                len(paras))
    out, last = [], 0
    for m in paras[:stop]:
        blk = m.group(0)
        if 'w:val="Author"' in blk or 'w:val="Title"' in blk:
            continue
        if "<w:t" not in blk:
            continue
        new = blk.replace("<w:pPr>", "<w:pPr>" + CENTER + SZ11, 1) \
            if "<w:pPr>" in blk else blk.replace(
                ">", "><w:pPr>" + CENTER + SZ11 + "</w:pPr>", 1)
        out.append(xml[last:m.start()]); out.append(new); last = m.end()
    out.append(xml[last:])
    return "".join(out)

SZ11 = '<w:rPr><w:sz w:val="20"/><w:szCs w:val="20"/></w:rPr>'

tmp_zip = DOCX + ".tmp"
with zipfile.ZipFile(DOCX) as zin, \
     zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename == "word/styles.xml":
            x = data.decode("utf8")
            # replace the styles we care about outright
            for sid, block in STYLES.items():
                pat = re.compile(r'<w:style[^>]*w:styleId="' + sid +
                                 r'"[^>]*>.*?</w:style>', re.S)
                x, n = pat.subn(block, x, count=1)
                if not n:
                    x = x.replace("</w:styles>", block + "</w:styles>")
            # nothing anywhere should be a theme font or a coloured accent
            x = re.sub(r'w:(ascii|hAnsi|cs|eastAsia)Theme="[^"]*"', "", x)
            x = re.sub(r'<w:color w:val="(?!000000)[0-9A-Fa-f]{6}"\s*/>',
                       BLACK, x)
            x = x.replace("<w:rPrDefault><w:rPr>",
                          "<w:rPrDefault><w:rPr>" + TNR + BLACK)
            x = x.replace("<w:pPrDefault/>",
                          "<w:pPrDefault><w:pPr>" + SP + JUST + "</w:pPr></w:pPrDefault>")
            data = x.encode("utf8")
        elif item.filename == "word/document.xml":
            x = data.decode("utf8")
            x = re.sub(r"<w:sectPr>.*?</w:sectPr>", SECTPR, x, count=1, flags=re.S)
            x = centre_affiliations(x)
            data = x.encode("utf8")
        zout.writestr(item, data)
shutil.move(tmp_zip, DOCX)

print("  wrote docx/manuscript.docx  (11pt Times New Roman, justified, 1.5 spacing, "
      "continuous line numbers)")
