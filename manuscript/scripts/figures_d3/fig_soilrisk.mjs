// Soil accumulation risk — two panels under one caption:
//   (a) deterministic time to reach the soil limit, by metal and reference bound
//   (b) Monte Carlo probability of exceedance over time
// (a) replaces the soil-loading table, (b) the Monte Carlo accumulation table:
// the point estimate and the propagated uncertainty for the same quantity.
import { svgRoot, serialize, title, panelTag } from "./theme.mjs";
import { panel as tmaxPanel } from "./fig_tmax.mjs";
import { exceedancePanel } from "./fig_mc.mjs";

const W = 540;

export function render(tmax, mc) {
  const rowA = { top: 66, height: 128, mL: 40, mR: 116 };
  const rowB = { top: 272, height: 118, mL: 52, mR: 76 };
  const H = rowB.top + rowB.height + 58;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Soil accumulation risk at 5 t ha⁻¹ yr⁻¹",
        "Plough layer 0–20 cm. (a) point estimate at mean concentrations; (b) full parameter uncertainty propagated.");

  panelTag(svg, rowA.mL, rowA.top - 10, "a",
           "Years to reach the soil limit (mean concentrations)");
  tmaxPanel(svg, tmax, { W, ...rowA });

  panelTag(svg, rowB.mL, rowB.top - 10, "b",
           "Monte Carlo probability of exceedance (N = 30 000)");
  exceedancePanel(svg, mc, { W, top: rowB.top, height: rowB.height,
                             mL: rowB.mL, mR: rowB.mR });

  return serialize(svg);
}
