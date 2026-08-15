// Shared design system for the manuscript figures.
// Palette, type-scale, and SVG/axis helpers used by every figure.
// Categorical hues and their ordering are the validated data-viz default
// (dataviz skill reference palette); the 7-slot prefix passed the adjacent
// CVD/contrast gates (worst adjacent CVD ΔE 9.1, normal-vision 19.6).
import { JSDOM } from "jsdom";
import * as d3 from "d3";

export const dom = new JSDOM("<!DOCTYPE html><body></body>");
export const document = dom.window.document;
export { d3 };

// ---- colour ---------------------------------------------------------------
export const SURFACE = "#ffffff";
export const INK = "#1a1a19";        // primary text
export const INK2 = "#52514e";       // secondary text
export const MUTED = "#8a8984";      // axes / grid ink
export const GRID = "#e7e6e2";       // gridlines
export const RULE = "#c9302c";       // regulatory reference lines (MAL)

// 8-hue validated categorical order (light mode)
export const CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                    "#e87ba4", "#008300", "#4a3aa7", "#e34948"];

// Fixed identity → hue maps (colour follows the entity, never its rank/order)
export const TYPES = ["Cow dung", "Bone meal", "Trichocompost", "Generic OF",
                      "Vermicompost", "Horn meal", "Neem cake"];
export const typeColor = d3.scaleOrdinal().domain(TYPES).range(CAT.slice(0, 7));

export const METALS = ["Cu", "Cr", "Pb", "Cd", "Zn", "Ni", "As"];
export const metalColor = d3.scaleOrdinal().domain(METALS).range(CAT.slice(0, 7));

// Marker shapes — secondary encoding so scatter identity is never colour-alone
export const TYPE_SYMBOL = d3.scaleOrdinal().domain(TYPES).range([
  d3.symbolCircle, d3.symbolSquare, d3.symbolTriangle, d3.symbolDiamond,
  d3.symbolCross, d3.symbolWye, d3.symbolStar,
]);

// Sequential blue ramp (magnitude) — light→dark, near-zero recedes to surface
export const SEQ = ["#eaf2fc", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
                    "#256abf", "#184f95", "#0d366b"];
export const seq = d3.scaleSequential(t => d3.interpolateRgbBasis(SEQ)(t));

// Diverging blue↔red for correlation (−1 blue … 0 gray … +1 red)
export const div = d3.scaleDiverging()
  .domain([-1, 0, 1])
  .interpolator(d3.interpolateRgbBasis(["#184f95", "#6da7ec", "#f0efec",
                                        "#e8896a", "#c9302c"]));

// ---- typography (pt; the SVG user unit is 1pt so PDF sizes are physical) ---
export const FONT = "Helvetica, Arial, sans-serif";
export const FS = { title: 11, label: 9.5, tick: 8.5, annot: 8, legend: 9 };

// ---- svg scaffold ---------------------------------------------------------
// width/height in points → physical size after SVG→PDF (1 unit = 1pt).
export function svgRoot(width, height) {
  const svg = d3.select(document.body).append("svg")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("width", width).attr("height", height)
    .attr("viewBox", `0 0 ${width} ${height}`)
    .attr("font-family", FONT);
  svg.append("rect").attr("width", width).attr("height", height).attr("fill", SURFACE);
  return svg;
}

export function serialize(svg) {
  return '<?xml version="1.0" encoding="UTF-8"?>\n' + svg.node().outerHTML;
}

// Title + optional subtitle, top-left, ink tokens (never a series colour)
export function title(svg, x, y, text, subtitle) {
  svg.append("text").attr("x", x).attr("y", y)
    .attr("font-size", FS.title).attr("font-weight", 600).attr("fill", INK)
    .text(text);
  if (subtitle) {
    svg.append("text").attr("x", x).attr("y", y + 13)
      .attr("font-size", FS.annot).attr("fill", INK2).text(subtitle);
  }
}

// Recessive axis: thin baseline, muted ticks, no top/right spines.
//
// NOTE both helpers render into their OWN child <g>. d3's axis generators set
// `text-anchor` (and fill/font) on the element they are called on; calling them
// directly on a panel group makes every later label in that group inherit the
// axis's alignment (axisLeft sets text-anchor="end", which silently right-shifts
// captions off-canvas). Isolating them in a child group prevents that.
export function axisBottom(g, scale, { ticks = 5, fmt = null, rotate = 0,
                                       tickValues = null } = {}) {
  const _a = d3.axisBottom(scale).tickSizeOuter(0).tickFormat(fmt || (d => d));
  if (tickValues) _a.tickValues(tickValues); else _a.ticks(ticks);
  const ax = g.append("g").call(_a);
  ax.select(".domain").attr("stroke", MUTED).attr("stroke-width", 1);
  ax.selectAll(".tick line").attr("stroke", MUTED);
  ax.selectAll(".tick text").attr("fill", INK2).attr("font-size", FS.tick);
  if (rotate) ax.selectAll(".tick text")
    .attr("transform", `rotate(${rotate})`).attr("text-anchor", "end")
    .attr("dx", "-0.5em").attr("dy", "0.15em");
  return ax;
}

export function axisLeft(g, scale, { ticks = 5, fmt = null, grid = 0,
                                     tickValues = null } = {}) {
  const axis = d3.axisLeft(scale).tickSizeOuter(0).tickFormat(fmt || (d => d));
  if (tickValues) axis.tickValues(tickValues); else axis.ticks(ticks);
  const ax = g.append("g").call(axis);
  ax.select(".domain").attr("stroke", MUTED).attr("stroke-width", 1);
  ax.selectAll(".tick line").attr("stroke", MUTED);
  ax.selectAll(".tick text").attr("fill", INK2).attr("font-size", FS.tick);
  if (grid) ax.selectAll(".tick line").clone()
    .attr("x2", grid).attr("stroke", GRID).attr("stroke-width", 0.6)
    .lower();
  return ax;
}

// Decade tick values (powers of ten) spanning a log domain [lo,hi].
export function decades(lo, hi) {
  const a = Math.floor(Math.log10(lo)), b = Math.ceil(Math.log10(hi));
  const out = [];
  for (let e = a; e <= b; e++) { const v = Math.pow(10, e); if (v >= lo && v <= hi) out.push(v); }
  return out;
}
export function logFmt(d) {
  if (d >= 1000) return d3.format("~s")(d);
  if (d >= 1) return d3.format("~g")(d);
  return d3.format("~g")(d);
}

// Panel tag for multi-panel figures: (a)/(b)/(c) + label, aligned with the
// panel's plot-area left edge.
// The gap is set with `dx`, not a literal space: SVG renderers collapse
// leading/trailing whitespace in tspans, and jsdom serialises `xml:space` as a
// bare `space` attribute (namespace prefix dropped), so that escape hatch is
// inert here. dx is a real positioning attribute and always survives.
export function panelTag(svg, x, y, letter, label) {
  const t = svg.append("text").attr("x", x).attr("y", y)
    .attr("font-size", FS.label).attr("fill", INK);
  t.append("tspan").attr("font-weight", 700).text(`(${letter})`);
  t.append("tspan").attr("font-weight", 600).attr("dx", 4).text(label);
  return t;
}

// Subscript built from tspans rather than a Unicode subscript codepoint.
// Helvetica/Arial cover the digit subscripts (₁₀) and ᵣ, but NOT ₙ (U+2099),
// which renders as tofu. Composing the subscript keeps every label safe
// regardless of which glyphs the rendering font happens to carry.
export function subLabel(sel, base, sub, after = "") {
  sel.append("tspan").text(base);
  sel.append("tspan").attr("dy", "0.22em")
    .attr("font-size", "0.75em").text(sub);
  if (after) sel.append("tspan").attr("dy", "-0.22em").text(after);
  return sel;
}

export function axisLabel(svg, x, y, text, rotate = 0) {
  const t = svg.append("text").attr("x", x).attr("y", y)
    .attr("font-size", FS.label).attr("fill", INK2).attr("text-anchor", "middle")
    .text(text);
  if (rotate) t.attr("transform", `rotate(${rotate},${x},${y})`);
  return t;
}
