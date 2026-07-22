// Time to reach the soil limit at the mean application rate (deterministic).
// Grouped horizontal bars on a LOG axis: the two reference bounds differ by up
// to ~70x (Cr: 9,918 yr Dutch vs 139 yr CCME), which a linear axis cannot show.
// Bars run from the axis minimum rather than zero because zero does not exist on
// a log scale; the axis is labelled so the baseline is unambiguous.
import { d3, axisBottom, axisLabel, CAT, INK, INK2, MUTED, FS } from "./theme.mjs";

const BOUND_COLOR = { dutch: CAT[0], strict: CAT[1] };

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;
  const rows = data.rows, bounds = data.bounds;

  const lo = 10 ** Math.floor(Math.log10(d3.min(rows, r => r.strict)));
  const hi = 10 ** Math.ceil(Math.log10(d3.max(rows, r => r.dutch)));
  const x = d3.scaleLog().domain([lo, hi]).range([0, iw]);
  const y = d3.scaleBand().domain(rows.map(r => r.metal)).range([0, ih]).padding(0.28);
  const sub = d3.scaleBand().domain(bounds.map(b => b.key))
    .range([0, y.bandwidth()]).padding(0.18);

  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  // decade gridlines
  const ticks = [];
  for (let e = Math.log10(lo); e <= Math.log10(hi); e++) ticks.push(10 ** e);
  ticks.forEach(t => g.append("line")
    .attr("x1", x(t)).attr("x2", x(t)).attr("y1", 0).attr("y2", ih)
    .attr("stroke", "#e7e6e2").attr("stroke-width", 0.6));

  rows.forEach(r => {
    bounds.forEach(b => {
      const v = r[b.key];
      const yy = y(r.metal) + sub(b.key);
      g.append("rect").attr("x", 0).attr("y", yy)
        .attr("width", Math.max(0.5, x(v))).attr("height", sub.bandwidth())
        .attr("fill", BOUND_COLOR[b.key]).attr("rx", 1);
      g.append("text").attr("x", x(v) + 3).attr("y", yy + sub.bandwidth() / 2 + 2.6)
        .attr("font-size", FS.annot - 0.5).attr("fill", INK2)
        .text(d3.format(",.0f")(v));
    });
    g.append("text").attr("x", -7).attr("y", y(r.metal) + y.bandwidth() / 2 + 3)
      .attr("text-anchor", "end").attr("font-size", FS.label)
      .attr("font-weight", 600).attr("fill", INK).text(r.metal);
  });

  g.append("line").attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", ih)
    .attr("stroke", MUTED).attr("stroke-width", 1);
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x,
             { tickValues: ticks, fmt: d3.format("~s") });
  axisLabel(svg, mL + iw / 2, top + ih + 32, "Years of continuous application (log scale)");

  // legend
  const lx = mL + iw + 12;
  bounds.forEach((b, i) => {
    const ly = top + 8 + i * 14;
    svg.append("rect").attr("x", lx).attr("y", ly - 7).attr("width", 10)
      .attr("height", 8).attr("fill", BOUND_COLOR[b.key]).attr("rx", 2);
    svg.append("text").attr("x", lx + 14).attr("y", ly)
      .attr("font-size", FS.legend - 0.5).attr("fill", INK2).text(b.label);
  });
}
