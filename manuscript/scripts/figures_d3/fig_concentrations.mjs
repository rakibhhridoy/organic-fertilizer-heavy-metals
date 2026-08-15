// Concentrations and between-type differences — two panels under one caption:
//   (a) per-metal distributions by fertilizer type (log scale, MAL reference)
//   (b) Kruskal-Wallis effect size by metal
// (b) replaces the former Kruskal-Wallis table: it states how much of the
// variation in (a) is attributable to fertilizer type, next to the distributions
// themselves. Significant pairwise contrasts appear as brackets in (a).
import { svgRoot, serialize, title, panelTag } from "./theme.mjs";
import { panel as boxPanel, gridHeightFor } from "./fig_boxplots.mjs";
import { panel as effectPanel } from "./fig_effectsize.mjs";

const W = 540;

export function render(data) {
  // Panel (a) grows with the number of elements; everything below it follows.
  const rowA = { top: 80, gridHeight: gridHeightFor(data.metals.length), mL: 52, mR: 14 };
  const rowB = { top: rowA.top + rowA.gridHeight + 84, height: 104, mL: 52, mR: 96 };
  const H = rowB.top + rowB.height + 56;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Heavy-metal concentration by organic fertilizer type",
        "Red dashed = Bangladesh MAL. Box = IQR, whisker = range, dots = the five products. Brackets mark Dunn pairs at p < 0.05.");

  panelTag(svg, rowA.mL, rowA.top - 26, "a", "Distribution by metal and fertilizer type");
  boxPanel(svg, data, { W, ...rowA });

  panelTag(svg, rowB.mL, rowB.top - 14, "b",
           "Kruskal–Wallis effect size: variation explained by fertilizer type");
  effectPanel(svg, data.kw, { W, ...rowB });

  return serialize(svg);
}
