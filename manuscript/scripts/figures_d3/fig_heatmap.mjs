// Mean concentration by type × metal, cell colour = % of the MAL
// (sequential magnitude, one blue hue light→dark). Cell text = mean mg/kg.
//
// Exported as a panel so it can be composed into a multi-panel figure.
import { d3, seq, INK, INK2, MUTED, SURFACE, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR, gradId = "heatgrad" }) {
  const metals = data.metals, types = data.types, cells = data.cells;
  const iw = W - mL - mR, ih = height;

  const x = d3.scaleBand().domain(metals).range([0, iw]).padding(0.06);
  const y = d3.scaleBand().domain(types).range([0, ih]).padding(0.06);
  const color = seq.domain([0, 100]);
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  cells.forEach(d => {
    const cx = x(d.metal), cy = y(d.type);
    g.append("rect").attr("x", cx).attr("y", cy)
      .attr("width", x.bandwidth()).attr("height", y.bandwidth())
      .attr("fill", color(Math.min(100, d.pctMAL))).attr("rx", 2)
      .attr("stroke", SURFACE).attr("stroke-width", 2);   // 2px surface gap
    g.append("text").attr("x", cx + x.bandwidth() / 2)
      .attr("y", cy + y.bandwidth() / 2 + 3).attr("text-anchor", "middle")
      .attr("font-size", FS.tick)
      .attr("fill", d.pctMAL > 55 ? "#ffffff" : INK)
      .text(d3.format(d.value >= 100 ? ".0f" : ".1f")(d.value));
  });

  // Metal labels sit BELOW the grid, so they read as a conventional x-axis and
  // align with the correlation panel's column labels underneath.
  g.selectAll(".mx").data(metals).join("text").attr("class", "mx")
    .attr("x", d => x(d) + x.bandwidth() / 2).attr("y", ih + 14)
    .attr("text-anchor", "middle").attr("font-size", FS.label)
    .attr("font-weight", 600).attr("fill", INK).text(d => d);
  g.selectAll(".ty").data(types).join("text").attr("class", "ty")
    .attr("x", -8).attr("y", d => y(d) + y.bandwidth() / 2 + 3)
    .attr("text-anchor", "end").attr("font-size", FS.tick).attr("fill", INK2)
    .text(d => d);

  // colour legend (vertical gradient bar)
  const lx = mL + iw + 22, lw = 12, lh = ih;
  const grad = svg.append("defs").append("linearGradient").attr("id", gradId)
    .attr("x1", 0).attr("y1", 1).attr("x2", 0).attr("y2", 0);
  d3.range(0, 1.001, 0.1).forEach(t =>
    grad.append("stop").attr("offset", `${t * 100}%`).attr("stop-color", color(t * 100)));
  svg.append("rect").attr("x", lx).attr("y", top).attr("width", lw).attr("height", lh)
    .attr("fill", `url(#${gradId})`).attr("stroke", MUTED).attr("stroke-width", 0.5);
  const ly = d3.scaleLinear().domain([0, 100]).range([top + lh, top]);
  [0, 25, 50, 75, 100].forEach(v => {
    svg.append("text").attr("x", lx + lw + 4).attr("y", ly(v) + 3)
      .attr("font-size", FS.tick).attr("fill", INK2).text(v === 100 ? "≥100" : v);
  });
  svg.append("text").attr("x", lx + lw / 2).attr("y", top - 8).attr("text-anchor", "middle")
    .attr("font-size", FS.annot).attr("font-weight", 600).attr("fill", INK2)
    .text("% MAL");
}
