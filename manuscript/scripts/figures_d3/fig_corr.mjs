// Spearman rank correlation matrix, strict lower triangle.
// Sequential blue over 0–1: every observed correlation here is positive
// (0.07–0.78), so magnitude is the data's job and one hue uses the full contrast
// range. NOTE this ramp cannot represent a negative correlation — if the data
// ever yield one, switch to a diverging scale. The self-correlation diagonal is
// omitted: it is 1.00 by construction and carries no information. Significant
// cells (p<0.05) carry a ring, so significance is never colour-alone.
//
// Exported as a panel so it can be composed into a multi-panel figure.
import { d3, seq, INK, INK2, MUTED, SURFACE, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR, gradId = "corrgrad" }) {
  const metals = data.metals;
  const iw = W - mL - mR, ih = height;

  // Rows drop the first metal and columns the last: with the diagonal removed
  // those bands would be empty, so omitting them keeps the triangle compact.
  const cols = metals.slice(0, -1), rows = metals.slice(1);
  const x = d3.scaleBand().domain(cols).range([0, iw]).padding(0.06);
  const y = d3.scaleBand().domain(rows).range([0, ih]).padding(0.06);
  const color = seq.domain([0, 1]);
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  data.cells.forEach(d => {
    const i = metals.indexOf(d.y), j = metals.indexOf(d.x);
    if (j >= i) return;                      // strict lower triangle, no diagonal
    const cx = x(d.x), cy = y(d.y);
    g.append("rect").attr("x", cx).attr("y", cy)
      .attr("width", x.bandwidth()).attr("height", y.bandwidth())
      .attr("fill", color(d.r)).attr("rx", 2)
      .attr("stroke", SURFACE).attr("stroke-width", 2);
    if (d.p < 0.05) {
      g.append("rect").attr("x", cx + 1.5).attr("y", cy + 1.5)
        .attr("width", x.bandwidth() - 3).attr("height", y.bandwidth() - 3)
        .attr("fill", "none").attr("stroke", INK).attr("stroke-width", 1).attr("rx", 1.5);
    }
    g.append("text").attr("x", cx + x.bandwidth() / 2)
      .attr("y", cy + y.bandwidth() / 2 + 3).attr("text-anchor", "middle")
      .attr("font-size", FS.tick)
      .attr("fill", d.r > 0.55 ? "#ffffff" : INK)
      .text(d3.format(".2f")(d.r));
  });

  g.selectAll(".cx").data(cols).join("text").attr("class", "cx")
    .attr("x", d => x(d) + x.bandwidth() / 2).attr("y", ih + 14)
    .attr("text-anchor", "middle").attr("font-size", FS.label)
    .attr("font-weight", 600).attr("fill", INK).text(d => d);
  g.selectAll(".cy").data(rows).join("text").attr("class", "cy")
    .attr("x", -8).attr("y", d => y(d) + y.bandwidth() / 2 + 3)
    .attr("text-anchor", "end").attr("font-size", FS.label)
    .attr("font-weight", 600).attr("fill", INK).text(d => d);

  // sequential legend
  const lx = mL + iw + 22, lw = 12, lh = ih;
  const grad = svg.append("defs").append("linearGradient").attr("id", gradId)
    .attr("x1", 0).attr("y1", 1).attr("x2", 0).attr("y2", 0);
  d3.range(0, 1.001, 0.05).forEach(t =>
    grad.append("stop").attr("offset", `${t * 100}%`).attr("stop-color", color(t)));
  svg.append("rect").attr("x", lx).attr("y", top).attr("width", lw).attr("height", lh)
    .attr("fill", `url(#${gradId})`).attr("stroke", MUTED).attr("stroke-width", 0.5);
  const ly = d3.scaleLinear().domain([0, 1]).range([top + lh, top]);
  [0, 0.25, 0.5, 0.75, 1].forEach(v =>
    svg.append("text").attr("x", lx + lw + 4).attr("y", ly(v) + 3)
      .attr("font-size", FS.tick).attr("fill", INK2).text(d3.format("~g")(v)));
  svg.append("text").attr("x", lx + lw / 2).attr("y", top - 8).attr("text-anchor", "middle")
    .attr("font-size", FS.annot).attr("font-weight", 600).attr("fill", INK2)
    .text("ρ");
}
