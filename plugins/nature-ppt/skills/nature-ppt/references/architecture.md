# Architecture and mode selection

## Pipeline

```text
raster reference
  -> complexity preflight
  -> optional text/region masks
  -> local VTracer or configured HTTPS vectorizer
  -> normalized and validated Master SVG
  -> geometry cache
  -> local PowerPoint COM or saved-PPTX OOXML renderer
```

The vectorizer is an intermediate stage. The final quality depends on choosing a PowerPoint representation that remains editable at normal workstation scale.

## Native mode

Use for flat scientific diagrams, plots, mechanisms, icons, flowcharts, and screenshots with limited colors and hard edges. Every supported SVG path and live text run becomes a PowerPoint object.

Default limit: 50,000 native objects. The limit is a safety boundary, not a fidelity target. A lower count is usually easier to edit.

## Hybrid mode

Use for photographs, rendered journal covers, glass, metal, bloom, soft shadows, fog, particles, and continuous gradients. Preserve continuous-tone pixels as one high-resolution background. Rebuild text, arrows, labels, equations, legends, and scientifically important structures as native objects above it.

Hybrid mode must be disclosed. It is editable by layer and annotation, not pixel-by-pixel.

## Archive mode

Use the pinned maximum-fidelity trace for inspection, printing, or later vector editing. Do not expand an archive SVG into PowerPoint when its path count exceeds the safe limit unless the user explicitly accepts the performance cost.

## Text and semantic regions

Text cleanup should be mask-constrained. Compare pixels outside each mask with the untouched source; reject cleanup that changes unrelated structures. For important objects that cannot be traced cleanly, use a deliberate native redraw and record that it is a reconstruction rather than an exact trace.
