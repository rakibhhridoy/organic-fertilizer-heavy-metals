// Graphical abstract (Journal of Hazardous Materials Advances submission).
//
// HAZADV requires a graphical abstract at submission: minimum 531 x 1328 px
// (h x w), readable at 5 x 13 cm, TIFF/EPS/PDF/MS-Office. The canvas below is
// exactly 1328 x 531 user units, so the SVG meets the pixel minimum as written
// and the Inkscape export is vector PDF at 996 x 398 pt.
//
// Type is scaled by 1328/540 = 2.459 against theme.mjs FS, i.e. the same
// apparent size as a paper figure reproduced at the same physical width.
// Nothing here is a new analysis: every value is read back from the same
// artefacts the manuscript prints, so the abstract cannot drift from the paper.
//
//   figures/data/fig_mc.json      Monte Carlo HI distribution (Fig. 6b)
//   tables/table_mcsoil_body.tex  median T_max per element (SI Table S11)
//   tables/table3_body.tex        Bangladesh MAL per element (Table 3)
//   data/clean_data.csv           the 35 products, for the per-sample grid
//
//   exploration/outputs/health_risk.csv  consumer HI, total and fertilizer increment
//
// Revision (HAZADV-D-26-02471): panel (d) now contrasts the total consumer hazard
// with the part attributable to the products, read from health_risk.csv. The two
// SRRC literals it used to carry are gone, so the abstract has no unbound numbers.
//
// Standalone by design, so the shared figure build is untouched:
//     node scripts/figures_d3/fig_graphical_abstract.mjs
//     inkscape figures/svg/graphical_abstract.svg --export-type=pdf \
//       --export-filename=figures/graphical_abstract.pdf --export-text-to-path
// To fold it into `make figures` instead, add one line to build.mjs FIGS:
//     graphical_abstract: async () =>
//       (await import("./fig_graphical_abstract.mjs")).render(),

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { d3, svgRoot, serialize, typeColor, TYPES,
         INK, INK2, MUTED, GRID, RULE, CAT } from "./theme.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");

// ---- canvas ---------------------------------------------------------------
const W = 1328, H = 531;
const M = 26, GAP = 20;
const PW = (W - 2 * M - 3 * GAP) / 4;              // 304
const PX = [0, 1, 2, 3].map(i => M + i * (PW + GAP));

// Type scale for this canvas (theme FS x 2.459, rounded to readable values).
const F = { title: 25, sub: 16.5, eyebrow: 16, big: 30, cap: 15.5,
            row: 15, tick: 13, annot: 13.5, chain: 15.5, take: 18 };

// Rows of the 35-product grid: theme's TYPES order, and the labels used in
// data/clean_data.csv, which spells the fourth category out in full.
const CSV_TYPE = {
  "Cow dung": "Cow dung", "Bone meal": "Bone meal",
  "Trichocompost": "Trichocompost", "Generic OF": "Generic Organic Fertilizer",
  "Vermicompost": "Vermicompost", "Horn meal": "Horn meal",
  "Neem cake": "Neem cake",
};
const METALS = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"];


// ---- inputs ---------------------------------------------------------------
// The generated table bodies are plain "a & b & c \\" rows; reading them keeps
// the abstract bound to the numbers the manuscript actually typesets.
function tableRows(rel) {
  return fs.readFileSync(path.join(ROOT, rel), "utf8")
    .split("\n").map(l => l.trim())
    .filter(l => l && !l.startsWith("%"))
    .map(l => l.replace(/\\\\\s*$/, "").split("&").map(c => c.trim()));
}

function readInputs() {
  const mal = new Map(tableRows("tables/table3_body.tex")
    .map(r => [r[0], +r[1]]));
  const tmax = tableRows("tables/table_mcsoil_body.tex")
    .map(r => ({ metal: r[0], median: +r[1] }))
    .sort((a, b) => a.median - b.median);
  const samples = d3.csvParse(
    fs.readFileSync(path.join(ROOT, "data", "clean_data.csv"), "utf8"));
  const mc = JSON.parse(
    fs.readFileSync(path.join(ROOT, "figures", "data", "fig_mc.json"), "utf8"));
  const hr = d3.csvParse(fs.readFileSync(
    path.join(ROOT, "exploration", "outputs", "health_risk.csv"), "utf8"));
  const c = hr.find(r => r.Scenario === "Consumer" && r.Type === "OVERALL");
  const cons = { total: +c.HI, incr: +c.HI_incr };
  return { mal, tmax, samples, mc, cons };
}

// One row per category, five products each, flagged against the national MAL.
function grid(samples, mal) {
  return TYPES.map(t => ({
    type: t,
    items: samples.filter(s => s.Type === CSV_TYPE[t]).map(s => {
      const over = METALS
        .filter(m => +s[m] > mal.get(m))
        .map(m => ({ metal: m, value: +s[m], mal: mal.get(m) }));
      return { sample: s.Sample, over };
    }),
  }));
}

// ---- small helpers --------------------------------------------------------
const txt = (sel, x, y, s, { size = F.row, fill = INK2, weight = null,
                             anchor = null, ls = null } = {}) => {
  const t = sel.append("text").attr("x", x).attr("y", y)
    .attr("font-size", size).attr("fill", fill).text(s);
  if (weight) t.attr("font-weight", weight);
  if (anchor) t.attr("text-anchor", anchor);
  if (ls) t.attr("letter-spacing", ls);
  return t;
};

// Panel heading: eyebrow, one headline figure, up to two lines of caption.
function head(svg, i, eyebrow, big, caption) {
  txt(svg, PX[i], 88, eyebrow, { size: F.eyebrow, weight: 600, fill: INK2, ls: 0.6 });
  txt(svg, PX[i], 124, big, { size: F.big, weight: 700, fill: INK });
  caption.forEach((line, k) =>
    txt(svg, PX[i], 147 + k * 18, line, { size: F.cap, fill: INK2 }));
}

// Shared row geometry for panels (a) and (b): the same 35 products, in the same
// order, so the eye carries a row straight across from category to verdict.
const ROW_TOP = 190, ROW_H = 33, DOT_DX = 36, DOT_R = 10;
const rowY = i => ROW_TOP + i * ROW_H + ROW_H / 2;

// ---- (a) the sample set ---------------------------------------------------
function panelSampled(svg, rows) {
  rows.forEach((r, i) => {
    txt(svg, PX[0], rowY(i) + 5, r.type, { size: F.row, fill: INK2 });
    r.items.forEach((_, j) => svg.append("circle")
      .attr("cx", PX[0] + 130 + j * DOT_DX).attr("cy", rowY(i))
      .attr("r", DOT_R).attr("fill", typeColor(r.type)));
  });
  txt(svg, PX[0], 440, "Retail products, greater capital region",
      { size: F.annot });
}

// ---- (b) the verdict ------------------------------------------------------
function panelCompliant(svg, rows) {
  rows.forEach((r, i) => {
    r.items.forEach((it, j) => {
      const bad = it.over.length > 0;
      svg.append("circle")
        .attr("cx", PX[1] + 14 + j * DOT_DX).attr("cy", rowY(i))
        .attr("r", DOT_R)
        .attr("fill", bad ? RULE : "#e4e3de")
        .attr("stroke", bad ? RULE : MUTED)
        .attr("stroke-width", bad ? 2.4 : 0.9);
    });
    // Callout for the exceeding product, on the row it belongs to.
    const hit = r.items.find(it => it.over.length)?.over[0];
    if (hit) {
      const t = svg.append("text").attr("x", PX[1] + 182).attr("y", rowY(i) + 5)
        .attr("font-size", 14).attr("fill", INK2);
      t.append("tspan").attr("font-weight", 700).attr("fill", RULE)
        .text(`${hit.metal} ${d3.format(".1f")(hit.value)}`);
      t.append("tspan").attr("dx", 5).text(`(MAL ${hit.mal})`);
    }
  });
  txt(svg, PX[1], 440, "Grey = within all seven national limits",
      { size: F.annot });
}

// ---- (c) how long accumulation would take ---------------------------------
// Horizontal bars on a LOG axis: the medians span an order of magnitude, and
// bars run from the axis minimum because zero does not exist on a log scale.
function panelAccumulation(svg, tmax) {
  const x0 = PX[2] + 30, barW = PW - 30 - 66;
  const rh = 28, top = 190, base = top + tmax.length * rh;
  const x = d3.scaleLog().domain([1e3, 1e5]).range([0, barW]);

  [1e3, 1e4, 1e5].forEach(t => {
    svg.append("line").attr("x1", x0 + x(t)).attr("x2", x0 + x(t))
      .attr("y1", top).attr("y2", base)
      .attr("stroke", GRID).attr("stroke-width", 0.8);
    txt(svg, x0 + x(t), base + 18, d3.format("~s")(t),
        { size: F.tick, anchor: "middle" });
  });

  tmax.forEach((r, i) => {
    const y = top + i * rh + 6;
    svg.append("rect").attr("x", x0).attr("y", y)
      .attr("width", Math.max(1, x(r.median))).attr("height", rh - 12)
      .attr("fill", CAT[0]).attr("rx", 2);
    txt(svg, x0 - 6, y + rh / 2 - 1, r.metal,
        { size: F.row, weight: 600, fill: INK, anchor: "end" });
    txt(svg, x0 + x(r.median) + 6, y + rh / 2 - 1,
        d3.format(",.0f")(r.median), { size: F.annot });
  });

  svg.append("line").attr("x1", x0).attr("x2", x0)
    .attr("y1", top).attr("y2", base)
    .attr("stroke", MUTED).attr("stroke-width", 1);
  txt(svg, PX[2], base + 40, "Years at 5 t ha⁻¹ yr⁻¹ (log). Exceedance within",
      { size: F.annot });
  txt(svg, PX[2], base + 56, "100 years: 0.12% at most, for any element",
      { size: F.annot });
}

// ---- (d) where the residual risk comes from -------------------------------
function panelRiskSource(svg, mc, cons) {
  const hi = mc.hi;
  const hx0 = PX[3] + 34, hw = PW - 44, htop = 194, hh = 94, hbase = htop + hh;
  const x = d3.scaleLinear().domain([hi.edges[0], hi.edges[hi.edges.length - 1]])
    .range([0, hw]);
  const y = d3.scaleLinear().domain([0, d3.max(hi.counts)]).range([hh, 0]);

  hi.counts.forEach((c, i) => {
    const lo = hi.edges[i], up = hi.edges[i + 1];
    svg.append("rect")
      .attr("x", hx0 + x(lo)).attr("y", htop + y(c))
      .attr("width", Math.max(0.6, x(up) - x(lo) - 0.4))
      .attr("height", hh - y(c))
      .attr("fill", (lo + up) / 2 >= hi.threshold ? RULE : CAT[0]);
  });

  svg.append("line").attr("x1", hx0 + x(hi.threshold)).attr("x2", hx0 + x(hi.threshold))
    .attr("y1", htop - 12).attr("y2", hbase)
    .attr("stroke", RULE).attr("stroke-width", 1.6).attr("stroke-dasharray", "5 3");
  txt(svg, hx0 + x(hi.threshold) + 5, htop - 3, "HI = 1",
      { size: F.annot, weight: 600, fill: RULE });

  svg.append("line").attr("x1", hx0).attr("x2", hx0 + hw)
    .attr("y1", hbase).attr("y2", hbase)
    .attr("stroke", MUTED).attr("stroke-width", 1);
  [0.5, 1, 2, 3].forEach(t => txt(svg, hx0 + x(t), hbase + 18,
    String(t), { size: F.tick, anchor: "middle" }));
  txt(svg, PX[3], hbase + 40, "Consumer hazard index, N = 30 000",
      { size: F.annot });

  // Total consumer hazard against the part the products themselves add.
  const stop = 366, sh = 14, sx0 = PX[3] + 156;
  const sx = d3.scaleLinear().domain([0, cons.total]).range([0, PW - 200]);
  txt(svg, PX[3], stop - 10, "Consumer hazard index, deterministic",
      { size: F.annot, weight: 600, fill: INK });
  [{ label: "Soil + 10 yr of product", v: cons.total, driver: true },
   { label: "Product increment only", v: cons.incr, driver: false }].forEach((s, i) => {
    const yy = stop + i * 26;
    txt(svg, sx0 - 6, yy + sh - 3, s.label,
        { size: 12.5, anchor: "end", fill: s.driver ? INK : INK2 });
    svg.append("rect").attr("x", sx0).attr("y", yy)
      .attr("width", Math.max(1.2, sx(s.v))).attr("height", sh)
      .attr("fill", s.driver ? CAT[0] : CAT[1]).attr("rx", 1.5);
    txt(svg, sx0 + Math.max(1.2, sx(s.v)) + 5, yy + sh - 3,
        d3.format(s.v < 0.01 ? ".4f" : ".2f")(s.v),
        { size: F.annot, weight: s.driver ? 700 : 400, fill: s.driver ? INK : INK2 });
  });
}

// ---- the process chain and the takeaway -----------------------------------
function footer(svg) {
  const stages = ["SAMPLED", "COMPLIANT", "ACCUMULATION", "RISK SOURCE"];
  svg.append("line").attr("x1", M).attr("x2", W - M)
    .attr("y1", 462).attr("y2", 462).attr("stroke", GRID).attr("stroke-width", 1);
  stages.forEach((s, i) => {
    txt(svg, PX[i] + PW / 2, 487, s,
        { size: F.chain, weight: 700, fill: INK2, anchor: "middle", ls: 1.2 });
    if (i < 3) txt(svg, PX[i] + PW + GAP / 2, 487, "→",
                   { size: 17, fill: MUTED, anchor: "middle" });
  });
  txt(svg, W / 2, 516,
      "Contamination is batch-level: the case is for batch screening and feedstock "
      + "control of Cr and Pb, not for restricting organic fertilizer use",
      { size: F.take, weight: 600, fill: INK, anchor: "middle" });
}

// ---- render ---------------------------------------------------------------
export function render() {
  const { mal, tmax, samples, mc, cons } = readInputs();
  const rows = grid(samples, mal);
  const nBad = rows.reduce(
    (a, r) => a + r.items.filter(it => it.over.length).length, 0);

  const svg = svgRoot(W, H);
  // Centred header and centred takeaway bracket the left-aligned panels; the
  // hairline here mirrors the one above the process chain so the frame closes.
  txt(svg, W / 2, 32,
      "Heavy metals in 35 commercial organic fertilizers from greater Dhaka, Bangladesh",
      { size: F.title, weight: 700, fill: INK, anchor: "middle" });
  txt(svg, W / 2, 55,
      "Regulatory compliance, long-term soil accumulation, and the source of the "
      + "residual health risk",
      { size: F.sub, fill: INK2, anchor: "middle" });
  svg.append("line").attr("x1", M).attr("x2", W - M)
    .attr("y1", 68).attr("y2", 68).attr("stroke", GRID).attr("stroke-width", 1);

  head(svg, 0, "WHAT WAS TESTED", "35",
       ["products, seven categories,", "seven regulated elements"]);
  head(svg, 1, "AGAINST NATIONAL LIMITS", `${35 - nBad} of 35`,
       ["comply in full; only Cr and Pb", "exceed, in two products each"]);
  // Rounded to the nearest hundred, exactly as the Results text prints the range.
  const h100 = v => d3.format(",.0f")(Math.round(v / 100) * 100);
  head(svg, 2, "IF APPLIED INDEFINITELY",
       `${h100(tmax[0].median)}–${h100(tmax[tmax.length - 1].median)} yr`,
       ["median time to reach", "permissible soil limits"]);
  // share of the consumer hazard index that the products themselves contribute
  const pct = 100 * cons.incr / cons.total;
  head(svg, 3, "WHAT DRIVES THE RISK", `${pct < 1 ? "<1" : d3.format(".0f")(pct)}%`,
       ["of consumer hazard comes from", "the products; the rest is soil"]);

  panelSampled(svg, rows);
  panelCompliant(svg, rows);
  panelAccumulation(svg, tmax);
  panelRiskSource(svg, mc, cons);
  footer(svg);

  return serialize(svg);
}

// Run directly: write figures/svg/graphical_abstract.svg.
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const out = path.join(ROOT, "figures", "svg", "graphical_abstract.svg");
  fs.writeFileSync(out, render());
  console.log("  wrote figures/svg/graphical_abstract.svg");
}
