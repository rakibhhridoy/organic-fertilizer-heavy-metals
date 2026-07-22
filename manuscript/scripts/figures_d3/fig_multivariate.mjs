// Multivariate structure — two stacked panels under one caption:
//   (a) PCA biplot of log-transformed concentrations
//   (b) Ward-linkage hierarchical clustering of the fertilizer types
// Both describe the same covariance structure, so they belong together; the
// colour assignment for fertilizer type is shared between the panels.
import { svgRoot, serialize, title, panelTag } from "./theme.mjs";
import { panel as pcaPanel } from "./fig_pca.mjs";
import { panel as dendroPanel } from "./fig_dendro.mjs";

const W = 540;

export function render(pca, dendro) {
  const mL = 46;
  const rowA = { top: 62, height: 200, mR: 116 };   // mR leaves room for the legend
  const rowB = { top: 332, height: 132, mR: 116 };  // mR leaves room for leaf labels
  const H = rowB.top + rowB.height + 46;

  const svg = svgRoot(W, H);
  title(svg, 14, 18, "Multivariate structure of the heavy-metal profiles",
        "Both panels use log-transformed concentrations and share the fertilizer-type colours.");

  panelTag(svg, mL, rowA.top - 10, "a",
           "Principal component analysis (arrows = metal loadings)");
  pcaPanel(svg, pca, { W, top: rowA.top, height: rowA.height, mL, mR: rowA.mR });

  panelTag(svg, mL, rowB.top - 10, "b",
           "Hierarchical clustering of fertilizer types (Ward linkage)");
  dendroPanel(svg, dendro, { W, top: rowB.top, height: rowB.height, mL, mR: rowB.mR });

  return serialize(svg);
}
