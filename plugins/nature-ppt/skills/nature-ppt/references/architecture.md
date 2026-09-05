# Architecture and mode selection

## Pipeline

```text
raster reference
  -> complexity preflight
  -> optional text/region masks
  -> direct trace, configured SuperSVG/AdaVec adapter, OR local budgeted trace
  -> normalized and validated Master SVG
  -> safe same-style compound-path packing
  -> geometry cache
  -> local PowerPoint COM or saved-PPTX OOXML renderer
```

The vectorizer is an intermediate stage. The final quality depends on choosing a PowerPoint representation that remains editable at normal workstation scale.

## Native mode

Use for flat scientific diagrams, plots, mechanisms, icons, flowcharts, and screenshots with limited colors and hard edges. Every supported SVG path and live text run becomes a PowerPoint object.

Default limit: 50,000 native objects. The limit is a safety boundary, not a fidelity target. A lower count is usually easier to edit.

## Light-native mode

Use for photographs, rendered journal covers, glass, metal, bloom, soft shadows, fog, particles, and continuous gradients. The pipeline searches ordered vectorization profiles and keeps the first trace under the object budget.

Each local profile combines a bounded palette, shared-boundary cutout regions, removal of tiny regions, spline simplification, and compound-path packing. Stronger profiles may also reduce the raster resolution used for tracing. A configured remote research engine is accepted only as vector SVG and receives the same local validation and object-budget checks. The output contains native PowerPoint objects only; the price is controlled loss of microtexture and continuous-tone precision.

## Archive mode

Use the pinned maximum-fidelity trace for inspection, printing, or later vector editing. Do not expand an archive SVG into PowerPoint when its path count exceeds the safe limit unless the user explicitly accepts the performance cost.

## Text and semantic regions

Text cleanup should be mask-constrained. Compare pixels outside each mask with the untouched source; reject cleanup that changes unrelated structures. For important objects that cannot be traced cleanly, use a deliberate native redraw and record that it is a reconstruction rather than an exact trace.

See [budgeted-native.md](budgeted-native.md) for the search order and algorithm rationale.
