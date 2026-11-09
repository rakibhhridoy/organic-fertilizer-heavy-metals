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

  // Logarithmic time axis to 10^6 years (revision, R3.2). Within 0-200 years six of
  // the seven curves sit at 0% and were indistinguishable; over the full horizon each
  // element traces its own S-curve, and the 100-year marker shows where the window
  // of practical interest lies on it.
  const x = d3.scaleLog().domain([10, d3.max(tgrid)]).range([0, iw]);
  const y = d3.scaleLinear().domain([0, 1]).range([height, 0]);

  axisLeft(g, y, { tickValues: [0, 0.25, 0.5, 0.75, 1], grid: iw,
                   fmt: d3.format(".0%") });
  axisBottom(g.append("g").attr("transform", `translate(0,${height})`), x,
             { tickValues: [10, 100, 1e3, 1e4, 1e5, 1e6], fmt: d3.format("~s") });
  axisLabel(svg, mL + iw / 2, top + height + 32,
            "Years of continuous application (log scale)");
  axisLabel(svg, 14, top + height / 2, "P(soil exceeds limit)", -90);

  g.append("line").attr("x1", x(100)).attr("x2", x(100)).attr("y1", 0).attr("y2", height)
    .attr("stroke", INK).attr("stroke-width", 1).attr("stroke-dasharray", "1.5 2");
  g.append("text").attr("x", x(100) + 3).attr("y", 10).attr("font-size", FS.annot)
    .attr("fill", INK).text("100 yr");

  metals.forEach(m => {
    const ys = data.exceedance[m];
    g.append("path").datum(tgrid.map((t, i) => [t, ys[i]]).filter(d => d[0] >= 10))
      .attr("fill", "none").attr("stroke", metalColor(m)).attr("stroke-width", 2)
      .attr("stroke-linejoin", "round").attr("stroke-linecap", "round")
      .attr("d", d3.line().x(d => x(d[0])).y(d => y(d[1])));
  });

  // legend ordered by the 10^4-year value, the order in which the curves stack
  const i4 = tgrid.indexOf(10000);
  const order = metals.slice().sort((a, b) => data.exceedance[b][i4] - data.exceedance[a][i4]);
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
                                    thresholdText, H: Hc = null, overlay = null,
                                    overlayHue = INK, labels = null, p95Side = "left" }) {
  const g = svg.append("g").attr("transform", `translate(${gx},${top})`);
  const edges = h.edges, counts = h.counts;
  const x = d3.scaleLinear().domain([edges[0], edges[edges.length - 1]]).range([0, pw]);
  const ymax = d3.max(overlay ? counts.concat(overlay.counts) : counts);
  const y = d3.scaleLinear().domain([0, ymax * 1.14]).range([height, 0]).nice();

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

  // Optional second distribution on the same bins, drawn as a step outline so the
  // filled histogram stays readable underneath (Fig. 6c: Cr(VI) over As+Pb).
  if (overlay) {
    const e = overlay.edges, c = overlay.counts, pts = [];
    c.forEach((v, i) => { pts.push([x(e[i]), y(v)]); pts.push([x(e[i + 1]), y(v)]); });
    g.append("path").datum(pts).attr("fill", "none").attr("stroke", overlayHue)
      .attr("stroke-width", 1.4).attr("d", d3.line());
  }
  if (labels) labels.forEach(([txt, col, dy]) => {
    g.append("rect").attr("x", 4).attr("y", dy - 7).attr("width", 9).attr("height", 7)
      .attr("fill", col === "outline" ? "none" : col).attr("stroke", col === "outline" ? overlayHue : "none");
    g.append("text").attr("x", 17).attr("y", dy).attr("font-size", FS.annot)
      .attr("fill", INK2).text(txt);
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
  // one line below the threshold labels, which otherwise collide when P95 is near them
  const right = p95Side === "right";
  g.append("text").attr("x", x(h.p95) + (right ? 6 : -3)).attr("y", 24)
    .attr("text-anchor", right ? "start" : "end")
    .attr("font-size", FS.annot).attr("fill", INK).text("P95");
}
