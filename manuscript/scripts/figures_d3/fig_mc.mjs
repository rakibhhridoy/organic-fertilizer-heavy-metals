// Monte Carlo panel builders, composed by fig_soilrisk.mjs (exceedance) and
// fig_healthrisk.mjs (the HI and cancer-risk distributions).
import { d3, axisBottom, axisLeft, axisLabel,
         metalColor, INK, RULE, INK2, FS } from "./theme.mjs";

const W = 540;

// ---- (a) exceedance probability curves ------------------------------------
export function exceedancePanel(svg, data, { W: Wc = W, top, height, mL, mR }) {
  const metals = data.metals, tgrid = data.tgrid;
  const iw = Wc - mL - mR;
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  // Fixed 0–0.4% window: the largest exceedance reached is ~0.28%, so this
  // keeps the curves legible instead of squashing them against the axis.
  const x = d3.scaleLinear().domain([0, d3.max(tgrid)]).range([0, iw]);
  const y = d3.scaleLinear().domain([0, 0.004]).range([height, 0]);

  axisLeft(g, y, { tickValues: [0, 0.001, 0.002, 0.003, 0.004], grid: iw,
                   fmt: d3.format(".1%") });
  axisBottom(g.append("g").attr("transform", `translate(0,${height})`), x, { ticks: 6 });
  axisLabel(svg, mL + iw / 2, top + height + 32, "Years of continuous application");
  axisLabel(svg, 14, top + height / 2, "P(soil exceeds limit)", -90);

  const line = d3.line().x((d, i) => x(tgrid[i])).y(d => y(Math.min(d, 0.004)));
  metals.forEach(m => {
    g.append("path").datum(data.exceedance[m])
      .attr("fill", "none").attr("stroke", metalColor(m)).attr("stroke-width", 2)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
      .attr("d", line);
  });

  // legend ordered by final value, so it reads in the same order as the curves
  const order = metals.slice().sort((a, b) =>
    d3.max(data.exceedance[b]) - d3.max(data.exceedance[a]));
  const lx = mL + iw + 14;
  order.forEach((m, i) => {
    const ly = top + 8 + i * 14;
    svg.append("line").attr("x1", lx).attr("x2", lx + 12)
      .attr("y1", ly - 3).attr("y2", ly - 3)
      .attr("stroke", metalColor(m)).attr("stroke-width", 2);
    svg.append("text").attr("x", lx + 17).attr("y", ly)
      .attr("font-size", FS.legend).attr("fill", INK2).text(m);
  });
}

// ---- (b)/(c) distribution panels -------------------------------------------
export function histPanel(svg, h, { gx, top, pw, height, xlabel, thresholds, fmt, hue,
                                    thresholdText, H: Hc = null }) {
  const g = svg.append("g").attr("transform", `translate(${gx},${top})`);
  const edges = h.edges, counts = h.counts;
  const x = d3.scaleLinear().domain([edges[0], edges[edges.length - 1]]).range([0, pw]);
  const y = d3.scaleLinear().domain([0, d3.max(counts) * 1.14]).range([height, 0]).nice();

  axisLeft(g, y, { ticks: 4, grid: pw, fmt: d3.format("~s") });
  axisBottom(g.append("g").attr("transform", `translate(0,${height})`), x,
             { ticks: 5, fmt });
  axisLabel(svg, gx + pw / 2, top + height + 32, xlabel);

  counts.forEach((c, i) => {
    if (!c) return;
    const x0 = x(edges[i]), x1 = x(edges[i + 1]);
    g.append("rect").attr("x", x0 + 0.35).attr("width", Math.max(0.3, x1 - x0 - 0.7))
      .attr("y", y(c)).attr("height", height - y(c))
      .attr("fill", hue).attr("fill-opacity", 0.85).attr("rx", 0.8);
  });

  thresholds.forEach(t => {
    if (t < x.domain()[0] || t > x.domain()[1]) return;
    g.append("line").attr("x1", x(t)).attr("x2", x(t)).attr("y1", 0).attr("y2", height)
      .attr("stroke", RULE).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");
    const lab = thresholdText(t);
    if (lab) g.append("text").attr("x", x(t) - 3).attr("y", 11).attr("text-anchor", "end")
      .attr("font-size", FS.annot).attr("fill", RULE).text(lab);
  });

  g.append("line").attr("x1", x(h.p95)).attr("x2", x(h.p95))
    .attr("y1", 0).attr("y2", height)
    .attr("stroke", INK).attr("stroke-width", 1).attr("stroke-dasharray", "1.5 2");
  g.append("text").attr("x", x(h.p95) + 3).attr("y", 11)
    .attr("font-size", FS.annot).attr("fill", INK).text("P95");
}
