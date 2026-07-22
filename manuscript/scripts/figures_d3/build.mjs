// Driver: read figures/data/*.json, render each figure to figures/svg/*.svg.
// Usage:  node build.mjs [name ...]   (no args = all)
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const DATA = path.join(ROOT, "figures", "data");
const SVG = path.join(ROOT, "figures", "svg");
fs.mkdirSync(SVG, { recursive: true });

const load = f => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));

const FIGS = {
  // Boxplot grid + Kruskal-Wallis effect sizes (the KW table absorbed).
  fig1_concentrations: async () =>
    (await import("./fig_concentrations.mjs")).render(load("fig1_box.json")),
  // Heatmap and correlation matrix share one figure: metal composition and
  // co-occurrence across the same sample set.
  fig_composition: async () =>
    (await import("./fig_composition.mjs")).render(load("fig2_heatmap.json"),
                                                   load("fig3_corr.json")),
  // PCA biplot and Ward clustering share one figure: same covariance structure.
  fig_multivariate: async () =>
    (await import("./fig_multivariate.mjs")).render(load("fig4_pca.json"),
                                                    load("fig_dendro.json")),
  // Indices table absorbed: RI stack + PLI/mCd/Nemerow bars.
  fig_pollution: async () =>
    (await import("./fig_pollution.mjs")).render(load("fig_ri.json"),
                                                  load("fig_indices.json")),
  // Soil-loading and Monte-Carlo accumulation tables absorbed.
  fig_soilrisk: async () =>
    (await import("./fig_soilrisk.mjs")).render(load("fig_tmax.json"),
                                                 load("fig_mc.json")),
  // Health-risk table absorbed alongside the Monte-Carlo distributions.
  fig_healthrisk: async () =>
    (await import("./fig_healthrisk.mjs")).render(load("fig_health.json"),
                                                   load("fig_mc.json")),
};

const want = process.argv.slice(2);
const names = want.length ? want : Object.keys(FIGS);
for (const name of names) {
  if (!FIGS[name]) { console.error("unknown figure:", name); process.exitCode = 1; continue; }
  const svg = await FIGS[name]();
  fs.writeFileSync(path.join(SVG, name + ".svg"), svg);
  console.log("  wrote figures/svg/" + name + ".svg");
}
