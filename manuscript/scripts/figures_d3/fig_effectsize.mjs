// Kruskal-Wallis effect size by metal, sorted high to low.
// Bars run from zero (a truncated baseline would exaggerate the differences),
// and the conventional small/medium/large cut-offs are drawn as reference rules
// so a bar length is interpretable without consulting the text. Significance is
// carried by an asterisk and the p_BH value, never by colour alone.
import { d3, axisBottom, axisLabel, CAT, INK, INK2, MUTED, FS } from "./theme.mjs";

// Cohen's conventional benchmarks for eta-squared.
const CUTS = [{ v: 0.01, label: "small" },
              { v: 0.06, label: "medium" },
              { v: 0.14, label: "large" }];

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;
  const rows = data.slice().sort((a, b) => b.eta2 - a.eta2);

  const x = d3.scaleLinear().domain([0, Math.max(0.42, d3.max(rows, r => r.eta2) * 1.28)])
    .range([0, iw]);
  const y = d3.scaleBand().domain(rows.map(r => r.metal)).range([0, ih]).padding(0.3);
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  // effect-size benchmarks
  CUTS.forEach(c => {
    if (c.v > x.domain()[1]) return;
    g.append("line").attr("x1", x(c.v)).attr("x2", x(c.v))
      .attr("y1", -2).attr("y2", ih)
      .attr("stroke", MUTED).attr("stroke-width", 0.7).attr("stroke-dasharray", "2 2");
    g.append("text").attr("x", x(c.v) + 2).attr("y", -4)
      .attr("font-size", FS.annot - 1).attr("fill", INK2).text(c.label);
  });

  rows.forEach(r => {
    const yy = y(r.metal);
    g.append("rect").attr("x", 0).attr("y", yy)
      .attr("width", Math.max(0.5, x(r.eta2))).attr("height", y.bandwidth())
      .attr("fill", r.sig ? CAT[0] : "#b9c6d4").attr("rx", 1);
    g.append("text").attr("x", -7).attr("y", yy + y.bandwidth() / 2 + 3)
      .attr("text-anchor", "end").attr("font-size", FS.label)
      .attr("font-weight", 600).attr("fill", INK).text(r.metal);
    const lab = `${d3.format(".3f")(r.eta2)}   p = ${d3.format(".3f")(r.pBH)}${r.sig ? " *" : ""}`;
    g.append("text").attr("x", x(r.eta2) + 4).attr("y", yy + y.bandwidth() / 2 + 3)
      .attr("font-size", FS.annot - 0.5)
      .attr("fill", r.sig ? INK : INK2).text(lab);
  });

  g.append("line").attr("x1", 0).attr("x2", 0).attr("y1", 0).attr("y2", ih)
    .attr("stroke", MUTED).attr("stroke-width", 1);
  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { ticks: 5 });
  axisLabel(svg, mL + iw / 2, top + ih + 32,
            "Eta-squared effect size (filled bar and * = significant after BH correction)");
}
