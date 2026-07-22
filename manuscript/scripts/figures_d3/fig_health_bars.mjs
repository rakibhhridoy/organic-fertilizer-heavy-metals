// Hazard index by fertilizer type (handler pathway) with the consumer pathway
// and the HI = 1 threshold as reference rules.
//
// LOG y-axis: handler HI spans 0.004–0.031 while the consumer estimate is 0.58
// and the threshold is 1, roughly 250x across. On a linear axis the handler bars
// collapse onto the baseline and the ~8x variation between products — the one
// product-specific result in the health assessment — becomes invisible.
// Bars therefore start at the axis minimum, not zero, which is unavoidable on a
// log scale; the axis is labelled accordingly.
import { d3, axisBottom, axisLeft, axisLabel, decades, logFmt, typeColor,
         INK, INK2, MUTED, RULE, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;
  const rows = data.handler;
  const consumerHI = data.overall.Consumer.HI;

  const lo = 10 ** Math.floor(Math.log10(d3.min(rows, r => r.HI)));
  const x = d3.scaleBand().domain(rows.map(r => r.type)).range([0, iw]).padding(0.32);
  const y = d3.scaleLog().domain([lo, 1.6]).range([ih, 0]);

  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);
  axisLeft(g, y, { tickValues: decades(lo, 1.6), fmt: logFmt, grid: iw });
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { rotate: -30 });
  axisLabel(svg, 14, top + ih / 2, "Hazard index (log scale)", -90);

  rows.forEach(r => {
    g.append("rect").attr("x", x(r.type)).attr("width", x.bandwidth())
      .attr("y", y(r.HI)).attr("height", Math.max(0.5, ih - y(r.HI)))
      .attr("fill", typeColor(r.type)).attr("rx", 1);
    g.append("text").attr("x", x(r.type) + x.bandwidth() / 2).attr("y", y(r.HI) - 3)
      .attr("text-anchor", "middle").attr("font-size", FS.annot - 0.5)
      .attr("fill", INK2).text(d3.format(".3f")(r.HI));
  });

  // consumer pathway (single overall estimate) and the regulatory threshold
  g.append("line").attr("x1", 0).attr("x2", iw)
    .attr("y1", y(consumerHI)).attr("y2", y(consumerHI))
    .attr("stroke", MUTED).attr("stroke-width", 1).attr("stroke-dasharray", "5 3");
  // Label sits BELOW its rule: above it the text was wedged into the narrow gap
  // between this line and the HI = 1 threshold and read as if it belonged to
  // either. The band beneath is empty down to the bars.
  g.append("text").attr("x", 2).attr("y", y(consumerHI) + 11)
    .attr("font-size", FS.annot).attr("fill", INK)
    .text(`Consumer pathway, overall HI = ${d3.format(".2f")(consumerHI)}`);

  g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(1)).attr("y2", y(1))
    .attr("stroke", RULE).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");
  g.append("text").attr("x", iw - 1).attr("y", y(1) - 3).attr("text-anchor", "end")
    .attr("font-size", FS.annot).attr("fill", RULE).text("HI = 1 (threshold)");
}
