// PCA biplot of log-transformed concentrations.
// Seven categories exceed the 3-slot all-pairs cap for scatter, so identity is
// carried by BOTH hue and marker shape (secondary encoding, per the palette rule).
//
// Exported as a panel so it can be composed into a multi-panel figure; the
// caller supplies the canvas and the box to draw into.
import { d3, axisBottom, axisLeft, axisLabel, typeColor, TYPE_SYMBOL,
         CAT, INK, INK2, MUTED, GRID, SURFACE, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;

  const xs = data.points.map(d => d.pc1), ys = data.points.map(d => d.pc2);
  const padx = (d3.max(xs) - d3.min(xs)) * 0.10;
  const pady = (d3.max(ys) - d3.min(ys)) * 0.12;
  const x = d3.scaleLinear().domain([d3.min(xs) - padx, d3.max(xs) + padx])
    .range([0, iw]).nice();
  const y = d3.scaleLinear().domain([d3.min(ys) - pady, d3.max(ys) + pady])
    .range([ih, 0]).nice();
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  axisLeft(g, y, { ticks: 5, grid: iw });
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { ticks: 6 });
  axisLabel(svg, mL + iw / 2, top + ih + 32, `PC1 (${data.varPC1}%)`);
  axisLabel(svg, 14, top + ih / 2, `PC2 (${data.varPC2}%)`, -90);

  // origin rules
  g.append("line").attr("x1", x(0)).attr("x2", x(0)).attr("y1", 0).attr("y2", ih)
    .attr("stroke", GRID).attr("stroke-width", 1);
  g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(0)).attr("y2", y(0))
    .attr("stroke", GRID).attr("stroke-width", 1);

  // Loading arrows, scaled so the longest arrow (plus its label) stays inside
  // the panel on every side, solved against the actual axis domains.
  const LABEL_PAD = 0.86;
  const scale = LABEL_PAD * d3.min(data.loadings, L => {
    const sx = L.pc1 > 0 ? x.domain()[1] / L.pc1
             : L.pc1 < 0 ? x.domain()[0] / L.pc1 : Infinity;
    const sy = L.pc2 > 0 ? y.domain()[1] / L.pc2
             : L.pc2 < 0 ? y.domain()[0] / L.pc2 : Infinity;
    return Math.min(sx, sy);
  });
  data.loadings.forEach(L => {
    const ex = x(L.pc1 * scale), ey = y(L.pc2 * scale);
    g.append("line").attr("x1", x(0)).attr("y1", y(0)).attr("x2", ex).attr("y2", ey)
      .attr("stroke", MUTED).attr("stroke-width", 1.2).attr("opacity", 0.85);
    g.append("circle").attr("cx", ex).attr("cy", ey).attr("r", 1.6).attr("fill", MUTED);
    const dx = ex - x(0), dy = ey - y(0), len = Math.hypot(dx, dy) || 1;
    g.append("text").attr("x", ex + (dx / len) * 9).attr("y", ey + (dy / len) * 9 + 3)
      .attr("text-anchor", "middle").attr("font-size", FS.annot)
      .attr("font-weight", 600).attr("fill", INK).text(L.metal);
  });

  // sample markers: hue + shape
  const sym = d3.symbol().size(34);
  data.points.forEach(p => {
    g.append("path")
      .attr("d", sym.type(TYPE_SYMBOL(p.type))())
      .attr("transform", `translate(${x(p.pc1)},${y(p.pc2)})`)
      .attr("fill", typeColor(p.type)).attr("fill-opacity", 0.9)
      .attr("stroke", SURFACE).attr("stroke-width", 1.2);
  });

  // legend (always present for ≥2 series)
  const lx = mL + iw + 16;
  data.types.forEach((t, i) => {
    const ly = top + 6 + i * 15;
    svg.append("path").attr("d", d3.symbol().size(34).type(TYPE_SYMBOL(t))())
      .attr("transform", `translate(${lx + 5},${ly - 3})`)
      .attr("fill", typeColor(t)).attr("stroke", SURFACE).attr("stroke-width", 1);
    svg.append("text").attr("x", lx + 14).attr("y", ly)
      .attr("font-size", FS.legend - 0.5).attr("fill", INK2).text(t);
  });

  if (data.structureLoadings) loadingInset(g, data.structureLoadings, iw, ih);
}

// Inset: PC1 structure loadings as horizontal bars, sorted high to low, in the
// bottom-right of the scatter (verified empty of sample points). Bars run from
// zero — a truncated bar baseline would exaggerate differences across the
// narrow 0.60–0.84 range. Drawn transparent, so it is placed clear of the
// data and its own baseline replaces a frame.
function loadingInset(g, loadings, iw, ih) {
  const rows = loadings.slice().sort((a, b) => b.pc1 - a.pc1);
  const barW = 52, rowH = 9.5, labW = 15, valW = 20;
  const boxW = labW + barW + valW, boxH = rows.length * rowH + 14;
  const x0 = iw - boxW - 2, y0 = ih - boxH - 4;

  const ins = g.append("g").attr("transform", `translate(${x0},${y0})`);
  const x = d3.scaleLinear().domain([0, 1]).range([0, barW]);

  ins.append("text").attr("x", 0).attr("y", 0)
    .attr("font-size", FS.annot).attr("font-weight", 600).attr("fill", INK)
    .text("PC1 loading");

  rows.forEach((d, i) => {
    const cy = 10 + i * rowH;
    ins.append("text").attr("x", labW - 4).attr("y", cy + 3.2)
      .attr("text-anchor", "end").attr("font-size", FS.annot - 0.5)
      .attr("fill", INK2).text(d.metal);
    ins.append("rect").attr("x", labW).attr("y", cy - 2.6)
      .attr("width", Math.max(0.5, x(d.pc1))).attr("height", 5.2)
      .attr("fill", CAT[0]).attr("rx", 1);
    ins.append("text").attr("x", labW + x(d.pc1) + 3).attr("y", cy + 3.2)
      .attr("font-size", FS.annot - 0.5).attr("fill", INK2)
      .text(d3.format(".2f")(d.pc1));
  });

  // zero baseline stands in for a frame
  ins.append("line").attr("x1", labW).attr("x2", labW)
    .attr("y1", 5).attr("y2", 10 + rows.length * rowH - 4)
    .attr("stroke", MUTED).attr("stroke-width", 0.8);
}
