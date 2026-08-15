// Fig 1 — heavy-metal concentration by fertilizer type, one panel per metal.
// Log y-axis (concentrations span 3+ orders of magnitude and are right-skewed),
// with the Bangladesh MAL kept as a reference rule. Boxes = IQR, whisker =
// min/max, jittered dots = the five products. Colour identifies type but is
// redundant with the x-axis, so the light-fill contrast WARN is covered.
import { d3, axisBottom, axisLeft, axisLabel,
         decades, logFmt, typeColor, INK, INK2, MUTED, RULE, FS } from "./theme.mjs";

// Grid geometry. The panel count is data-driven (it grew from six to seven when
// arsenic was added), so rows, row offsets and the canvas height are all derived
// rather than fixed. A row needs the taller gap only when one of its panels
// carries the rotated category axis, i.e. has no panel directly beneath it.
export const COLS = 3, PANEL_H = 92, GAP_TIGHT = 34, GAP_AXIS = 60;

const hasAxis = (i, n) => i + COLS >= n;
const rowHasAxis = (row, n) =>
  d3.range(row * COLS, Math.min((row + 1) * COLS, n)).some(i => hasAxis(i, n));

export function gridHeightFor(n) {
  const rows = Math.ceil(n / COLS);
  let h = rows * PANEL_H;
  for (let r = 0; r < rows - 1; r++) h += rowHasAxis(r, n) ? GAP_AXIS : GAP_TIGHT;
  return h;
}

export function panel(svg, data, { W, top, mL, mR, gridHeight }) {
  const metals = data.metals, types = data.types, MAL = data.MAL;
  const n = metals.length;
  const cols = COLS, rows = Math.ceil(n / cols);
  const mT = top;
  const gapX = 30;
  const pw = (W - mL - mR - gapX * (cols - 1)) / cols;
  const ph = PANEL_H;
  const dunn = data.dunn || [];

  // Cumulative y offset of each row.
  const rowY = [0];
  for (let r = 1; r < rows; r++) {
    rowY[r] = rowY[r - 1] + ph + (rowHasAxis(r - 1, n) ? GAP_AXIS : GAP_TIGHT);
  }

  axisLabel(svg, 14, mT + gridHeight / 2, "Concentration (mg kg⁻¹, log scale)", -90);

  const x = d3.scaleBand().domain(types).range([0, pw]).padding(0.35);

  metals.forEach((m, i) => {
    const panel = data.panels[m];
    const col = i % cols, row = Math.floor(i / cols);
    const gx = mL + col * (pw + gapX), gy = mT + rowY[row];
    const g = svg.append("g").attr("transform", `translate(${gx},${gy})`);

    const lo = d3.min(panel, d => d.min);
    const hi = Math.max(d3.max(panel, d => d.max), MAL[m]);
    const y = d3.scaleLog().domain([lo * 0.7, hi * 1.25]).range([ph, 0]);

    axisLeft(g, y, { tickValues: decades(lo * 0.7, hi * 1.25), fmt: logFmt, grid: pw });

    // MAL reference rule + label
    const ym = y(MAL[m]);
    if (ym >= -2 && ym <= ph + 2) {
      g.append("line").attr("x1", 0).attr("x2", pw).attr("y1", ym).attr("y2", ym)
        .attr("stroke", RULE).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");
      g.append("text").attr("x", pw - 1).attr("y", ym - 3).attr("text-anchor", "end")
        .attr("font-size", FS.annot).attr("fill", RULE).text(`MAL ${MAL[m]}`);
    }

    // boxes
    panel.forEach(d => {
      const cx = x(d.type) + x.bandwidth() / 2;
      const bw = x.bandwidth();
      const c = typeColor(d.type);
      g.append("line").attr("x1", cx).attr("x2", cx)
        .attr("y1", y(d.min)).attr("y2", y(d.max))
        .attr("stroke", MUTED).attr("stroke-width", 1);
      g.append("rect").attr("x", cx - bw / 2).attr("width", bw)
        .attr("y", y(d.q3)).attr("height", Math.max(1, y(d.q1) - y(d.q3)))
        .attr("fill", c).attr("fill-opacity", 0.55)
        .attr("stroke", c).attr("stroke-width", 1).attr("rx", 1.5);
      g.append("line").attr("x1", cx - bw / 2).attr("x2", cx + bw / 2)
        .attr("y1", y(d.med)).attr("y2", y(d.med))
        .attr("stroke", INK).attr("stroke-width", 1.4);
      d.points.forEach((p, k) => {
        const jx = cx + (((k * 2654435761) % 1000) / 1000 - 0.5) * bw * 0.5;
        g.append("circle").attr("cx", jx).attr("cy", y(p)).attr("r", 1.5)
          .attr("fill", INK).attr("fill-opacity", 0.5);
      });
    });

    // panel metal label, above the panel
    g.append("text").attr("x", pw / 2).attr("y", -7).attr("text-anchor", "middle")
      .attr("font-size", FS.label + 0.5).attr("font-weight", 600).attr("fill", INK)
      .text(m);

    // Dunn post-hoc brackets: only categories that differ significantly after
    // BH correction are linked. Stacked upward so multiple pairs never overlap.
    const pairs = dunn.filter(d => d.metal === m);
    pairs.forEach((d, k) => {
      const xa = x(d.a) + x.bandwidth() / 2, xb = x(d.b) + x.bandwidth() / 2;
      const yb = 8 + k * 9;
      g.append("path")
        .attr("d", `M${xa},${yb + 3} V${yb} H${xb} V${yb + 3}`)
        .attr("fill", "none").attr("stroke", INK).attr("stroke-width", 0.8);
      g.append("text").attr("x", (xa + xb) / 2).attr("y", yb - 1.5)
        .attr("text-anchor", "middle").attr("font-size", FS.annot)
        .attr("fill", INK).text("*");
    });

    if (hasAxis(i, n)) {
      axisBottom(g.append("g").attr("transform", `translate(0,${ph})`), x, { rotate: -35 });
    } else {
      g.append("line").attr("x1", 0).attr("x2", pw).attr("y1", ph).attr("y2", ph)
        .attr("stroke", MUTED).attr("stroke-width", 1);
    }
  });
}
