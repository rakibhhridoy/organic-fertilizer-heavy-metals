// Human health risk — three panels under one caption:
//   (a) handler-pathway hazard index by fertilizer type (point estimate)
//   (b) Monte Carlo distribution of the consumer hazard index
//   (c) Monte Carlo distribution of the consumer cancer risk: As+Pb filled, the
//       Cr(VI) term (assumed fraction, not measured) as an outline (revision, R1.1)
// (a) replaces the health-risk table; (b) and (c) carry the propagated
// uncertainty that the point estimates cannot show.
import { svgRoot, serialize, title, panelTag, CAT, d3 } from "./theme.mjs";
import { panel as hiBars } from "./fig_health_bars.mjs";
import { histPanel } from "./fig_mc.mjs";

const W = 540;

export function render(health, mc) {
  const rowA = { top: 72, height: 122, mL: 52, mR: 22 };
  const rowB = { top: 264, height: 104, mL: 52, gap: 52 };
  const pw = (W - rowB.mL - 18 - rowB.gap) / 2;
  const H = rowB.top + rowB.height + 58;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Human health risk assessment",
        "USEPA framework. Red dashed = risk threshold; grey dotted = 95th percentile.");

  panelTag(svg, rowA.mL, rowA.top - 10, "a",
           "Hazard index by fertilizer type (handler pathway)");
  hiBars(svg, health, { W, ...rowA });

  panelTag(svg, rowB.mL, rowB.top - 10, "b", "Consumer hazard index (Monte Carlo)");
  histPanel(svg, mc.hi, {
    gx: rowB.mL, top: rowB.top, pw, height: rowB.height, xlabel: "HI",
    thresholds: [mc.hi.threshold], fmt: d3.format("~g"), hue: CAT[0],
    thresholdText: () => "HI = 1", H,
  });

  panelTag(svg, rowB.mL + pw + rowB.gap, rowB.top - 10, "c",
           "Consumer cancer risk (Monte Carlo)");
  histPanel(svg, mc.logcr, {
    gx: rowB.mL + pw + rowB.gap, top: rowB.top, pw, height: rowB.height,
    xlabel: "log₁₀(CR)", thresholds: mc.logcr.thresholds,
    fmt: d3.format("~g"), hue: CAT[7],
    thresholdText: t => (t === -4 ? "10⁻⁴" : "10⁻⁶"), H,
    overlay: mc.logcr_cr, overlayHue: "#333333", p95Side: "right",
    labels: [["As + Pb", CAT[7], 22], ["Cr(VI), assumed", "outline", 34]],
  });

  return serialize(svg);
}
