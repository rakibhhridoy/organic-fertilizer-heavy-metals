// Pollution indices by fertilizer type: PLI, mCd and the Nemerow index.
// Grouped vertical bars with each index's interpretive threshold drawn as a
// rule, so "unpolluted vs polluted" is readable without consulting a class column.
import { d3, axisBottom, axisLeft, axisLabel, subLabel, CAT, INK, INK2, RULE, FS }
  from "./theme.mjs";

const SERIES_COLOR = { PLI: CAT[0], mCd: CAT[2], PN: CAT[3] };

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;
  const rows = data.rows, series = data.series;

  const x = d3.scaleBand().domain(data.types).range([0, iw]).padding(0.24);
  const sub = d3.scaleBand().domain(series.map(s => s.key))
    .range([0, x.bandwidth()]).padding(0.12);
  const maxV = d3.max(rows, r => d3.max(series, s => r[s.key]));
  const y = d3.scaleLinear().domain([0, Math.max(maxV * 1.18, 1.6)])
    .range([ih, 0]).nice();

  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);
  axisLeft(g, y, { ticks: 4, grid: iw });
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { rotate: -30 });
  axisLabel(svg, 14, top + ih / 2, "Index value", -90);

  rows.forEach(r => {
    series.forEach(s => {
      const v = r[s.key];
      g.append("rect").attr("x", x(r.type) + sub(s.key))
        .attr("width", sub.bandwidth())
        .attr("y", y(v)).attr("height", Math.max(0.5, ih - y(v)))
        .attr("fill", SERIES_COLOR[s.key]).attr("rx", 1);
    });
  });

  // Threshold at 1 applies to both PLI and the Nemerow index (unpolluted /
  // clean below, polluted / slight above); drawn once to avoid a second rule.
  g.append("line").attr("x1", 0).attr("x2", iw).attr("y1", y(1)).attr("y2", y(1))
    .attr("stroke", RULE).attr("stroke-width", 1).attr("stroke-dasharray", "4 3");
  subLabel(g.append("text").attr("x", iw - 1).attr("y", y(1) - 3)
    .attr("text-anchor", "end").attr("font-size", FS.annot).attr("fill", RULE),
    "PLI / P", "N", " = 1");

  // legend
  const lx = mL + iw + 12;
  series.forEach((s, i) => {
    const ly = top + 8 + i * 14;
    svg.append("rect").attr("x", lx).attr("y", ly - 7).attr("width", 10)
      .attr("height", 8).attr("fill", SERIES_COLOR[s.key]).attr("rx", 2);
    const lt = svg.append("text").attr("x", lx + 14).attr("y", ly)
      .attr("font-size", FS.legend - 0.5).attr("fill", INK2);
    if (s.key === "PN") subLabel(lt, "P", "N", " (vs MAL)"); else lt.text(s.key);
  });
}
