// Metal composition and co-occurrence — two stacked panels under one caption:
//   (a) mean concentration by fertilizer type, shaded by percent of the MAL
//   (b) Spearman rank correlation among the metals
//
// Both panels use the same blue ramp but encode DIFFERENT quantities (percent of
// a regulatory limit vs a correlation coefficient). They therefore carry their
// own labelled legends and the caption states the scales are independent; a
// dark cell in (a) is not comparable to a dark cell in (b). Distinct gradient
// ids keep the two <linearGradient> defs from colliding in one document.
import { svgRoot, serialize, title, panelTag } from "./theme.mjs";
import { panel as heatPanel } from "./fig_heatmap.mjs";
import { panel as corrPanel } from "./fig_corr.mjs";

const W = 540;

export function render(heat, corr) {
  const rowA = { top: 66, height: 168, mL: 96, mR: 76 };
  const rowB = { top: 300, height: 150, mL: 96, mR: 76 };
  const H = rowB.top + rowB.height + 40;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Metal composition and co-occurrence",
        "Both panels use the same blue ramp for different quantities; the two scales are independent.");

  panelTag(svg, rowA.mL, rowA.top - 12, "a",
           "Mean concentration (mg kg⁻¹), shaded by percent of the MAL");
  heatPanel(svg, heat, { W, ...rowA, gradId: "gradMAL" });

  panelTag(svg, rowB.mL, rowB.top - 12, "b",
           "Spearman rank correlation (ringed cells: p < 0.05)");
  corrPanel(svg, corr, { W, ...rowB, gradId: "gradRho" });

  return serialize(svg);
}
