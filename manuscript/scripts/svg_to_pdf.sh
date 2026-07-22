#!/bin/sh
# Convert figures/svg/*.svg -> figures/*.pdf (vector, fonts converted to paths).
# Run from manuscript/ :  sh scripts/svg_to_pdf.sh
#
# Inkscape is used rather than rsvg-convert because --export-text-to-path
# removes the font dependency entirely, which is what journals want: the PDF
# renders identically regardless of the fonts installed on the reviewer's or
# typesetter's machine. Output stays fully vector (no rasterisation).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SVG="$ROOT/figures/svg"
OUT="$ROOT/figures"

command -v inkscape >/dev/null 2>&1 || {
  echo "inkscape not found; falling back to rsvg-convert (fonts NOT outlined)" >&2
  for f in "$SVG"/*.svg; do
    n=$(basename "$f" .svg)
    rsvg-convert -f pdf -o "$OUT/$n.pdf" "$f"
    echo "  wrote figures/$n.pdf (rsvg)"
  done
  exit 0
}

for f in "$SVG"/*.svg; do
  n=$(basename "$f" .svg)
  inkscape "$f" --export-type=pdf --export-filename="$OUT/$n.pdf" \
           --export-text-to-path >/dev/null 2>&1
  echo "  wrote figures/$n.pdf"
done
