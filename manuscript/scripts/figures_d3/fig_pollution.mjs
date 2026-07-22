// Pollution and ecological risk indices — two panels under one caption:
//   (a) Håkanson RI by type, stacked by each metal's contribution
//   (b) PLI, mCd and the Nemerow index by type, with their thresholds
// Together these replace the former indices table: (a) shows which metal drives
// the risk, (b) shows where each type sits against its interpretive cut-offs.
import { svgRoot, serialize, title, panelTag } from "./theme.mjs";
import { panel as riPanel } from "./fig_ri.mjs";
import { panel as idxPanel } from "./fig_indices.mjs";

const W = 540;

export function render(ri, idx) {
  const rowA = { top: 64, height: 132, mL: 50, mR: 92 };
  const rowB = { top: 268, height: 116, mL: 50, mR: 92 };
  const H = rowB.top + rowB.height + 60;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Pollution and ecological risk indices by fertilizer type",
        "All indices computed from mean concentrations against world-soil background (RI, PLI, mCd) or the Bangladesh MAL (Nemerow index).");

  panelTag(svg, rowA.mL, rowA.top - 10, "a",
           "Håkanson risk index (RI), stacked by metal contribution (Eᵣ)");
  riPanel(svg, ri, { W, ...rowA });

  panelTag(svg, rowB.mL, rowB.top - 10, "b",
           "Pollution load index, modified degree of contamination, Nemerow index");
  idxPanel(svg, idx, { W, ...rowB });

  return serialize(svg);
}
