// Ward-linkage dendrogram of fertilizer types by standardised metal profile.
// Leaf labels carry identity (with a colour chip matching the PCA panel), so no
// legend is required.
//
// Exported as a panel so it can be composed into a multi-panel figure.
import { d3, axisBottom, axisLabel, typeColor, INK, MUTED, FS } from "./theme.mjs";

export function panel(svg, data, { W, top, height, mL, mR }) {
  const iw = W - mL - mR, ih = height;

  const root = d3.hierarchy(data.tree);
  const leaves = root.leaves();
  const yStep = ih / leaves.length;
  let li = 0;
  root.eachAfter(n => {
    if (!n.children) { n.yPos = yStep * (li + 0.5); li++; }
    else n.yPos = d3.mean(n.children, c => c.yPos);
  });
  const x = d3.scaleLinear().domain([0, data.maxHeight * 1.05]).range([0, iw]);
  const g = svg.append("g").attr("transform", `translate(${mL},${top})`);

  // Elbow links. A terminal branch carries its fertilizer type's colour, so the
  // line matches the chip beside its label; internal merges stay neutral,
  // because a merged node no longer belongs to a single type.
  root.each(n => {
    if (!n.children) return;
    const hx = x(n.data.height);
    n.children.forEach(c => {
      const cx = x(c.data.height || 0);
      const leaf = !c.children;
      g.append("line").attr("x1", cx).attr("y1", c.yPos)
        .attr("x2", hx).attr("y2", c.yPos)
        .attr("stroke", leaf ? typeColor(c.data.name) : MUTED)
        .attr("stroke-width", leaf ? 1.8 : 1.2)
        .attr("stroke-linecap", "round");
      g.append("line").attr("x1", hx).attr("y1", c.yPos)
        .attr("x2", hx).attr("y2", n.yPos)
        .attr("stroke", MUTED).attr("stroke-width", 1.2);
    });
  });

  // leaf labels with a colour chip (identity redundant with the text)
  leaves.forEach(l => {
    g.append("rect").attr("x", iw + 5).attr("y", l.yPos - 4)
      .attr("width", 8).attr("height", 8).attr("rx", 2)
      .attr("fill", typeColor(l.data.name));
    g.append("text").attr("x", iw + 18).attr("y", l.yPos + 3)
      .attr("font-size", FS.legend).attr("fill", INK).text(l.data.name);
  });

  axisBottom(g.append("g").attr("transform", `translate(0,${ih})`), x, { ticks: 5 });
  axisLabel(svg, mL + iw / 2, top + ih + 32, "Ward linkage distance");
}
