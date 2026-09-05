# Budgeted native vectorization

The target is not the largest possible SVG. It is the highest-detail SVG that remains usable as native PowerPoint geometry.

## Search strategy

`scripts/vectorize_budgeted.py` evaluates an ordered set of profiles. The first candidate at or below the native-object limit is selected.

1. Quantize the raster to a bounded palette so nearly identical colors do not become separate regions.
2. Segment as a `cutout` mosaic so neighboring shapes share boundaries instead of stacking redundant hidden shapes.
3. Remove small connected regions with the speckle threshold.
4. Fit spline paths and simplify them within a pixel tolerance.
5. Pack same-style regions into compound paths. A cutout mosaic permits global same-style packing because its regions do not overlap; layered SVGs receive adjacent-only packing to preserve paint order.
6. Limit each compound object to 64 source subpaths. This reduces PowerPoint object count without turning the whole image into one uneditable monolith.
7. At the strongest profiles only, reduce tracing resolution to suppress microtexture before segmentation.
8. Normalize and validate every SVG; reject raster nodes, missing stable path IDs, invalid view boxes, and over-budget results.

The profiles run from 96 colors with gentle cleanup to a final 12-color, 512-pixel-edge fallback. Because selection stops at the first passing candidate, simple or moderately complex artwork does not receive the strongest compression.

## Quality boundary

The method preserves scalable edges, editable fills, paint order, and independent PowerPoint shapes. It cannot preserve every photographic pixel while also keeping the object count small. Fine texture, noise, subtle gradients, bloom, and reflections become progressively flatter as the budget tightens.

If even the final profile exceeds the requested limit, fail clearly and preserve the source. Do not generate a raster background or claim that layered overlays are fully editable.
