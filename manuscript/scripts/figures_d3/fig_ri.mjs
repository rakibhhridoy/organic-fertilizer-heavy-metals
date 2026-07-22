// Håkanson potential ecological risk index by type, stacked by metal Er.
// Stacked segments carry a 2px surface gap; legend + direct total labels.
//
// Exported as a panel so it can be composed into a multi-panel figure.
import { d3, axisBottom, axisLeft, axisLabel,
         metalColor, INK, INK2, SURFACE, RULE, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR }) {
  const metals = data.metals, types = data.types;
  const mT = top, iw = W - mL - mR, ih = height;

  const stack = d3.stack().keys(metals)(data.stacks);
  const maxTotal = d3.max(data.stacks, d => d3.sum(metals, m => d[m]));
  const x = d3.scaleBand().domain(types).range([0, iw]).padding(0.3);
  const y = d3.scaleLinear().domain([0, Math.max(maxTotal * 1.15, data.threshold * 1.1)])
    .range([ih, 0]).nice();
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  axisLeft(g, y, { ticks: 5, grid: iw });
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { rotate: -30 });
  axisLabel(svg, 14, top + ih / 2, "Risk index (RI)", -90);

  stack.forEach(layer => {
    layer.forEach(seg => {
      const t = seg.data.type;
      const h = Math.max(0, y(seg[0]) - y(seg[1]));
      if (h <= 0) return;
      g.append("rect").attr("x", x(t)).attr("width", x.bandwidth())
        .attr("y", y(seg[1])).attr("height", h)
        .attr("fill", metalColor(layer.key))
        .attr("stroke", SURFACE).attr("stroke-width", 1)   // 2px-equiv gap between segments
        .attr("rx", 1);
    });
  });

  // total labels above each bar (selective direct labels)
  data.stacks.forEach(d => {
    const tot = d3.sum(metals, m => d[m]);
    g.append("text").attr("x", x(d.type) + x.bandwidth() / 2).attr("y", y(tot) - 4)
      .attr("text-anchor", "middle").attr("font-size", FS.annot).attr("fill", INK)
      .text(d3.format(".0f")(tot));
  });

  // threshold rule
  g.append("line").attr("x1", 0).attr("x2", iw)
    .attr("y1", y(data.threshold)).attr("y2", y(data.threshold))
    .attr("stroke", RULE).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");
  g.append("text").attr("x", iw - 1).attr("y", y(data.threshold) - 3)
    .attr("text-anchor", "end").attr("font-size", FS.annot).attr("fill", RULE)
    .text("RI = 150");

  // legend
  const lx = mL + iw + 16;
  metals.forEach((m, i) => {
    const ly = top + 6 + i * 15;
    svg.append("rect").attr("x", lx).attr("y", ly - 7).attr("width", 10).attr("height", 10)
      .attr("fill", metalColor(m)).attr("rx", 2);
    svg.append("text").attr("x", lx + 15).attr("y", ly + 1.5)
      .attr("font-size", FS.legend).attr("fill", INK2).text(m);
  });
}
