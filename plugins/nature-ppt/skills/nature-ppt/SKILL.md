---
name: nature-ppt
description: Reconstruct PNG, JPEG, WebP, or SVG references as practical editable PowerPoint content. Use direct native shapes for simple artwork and budgeted native vectorization for complex or photographic artwork; never hide a raster background beneath editable overlays. Use for image-to-PPT tracing, scientific figure reconstruction, and local PowerPoint drawing.
---

# Nature PPT

Turn a visual reference into a PowerPoint that remains useful after conversion. Treat editability as an object-budget problem: a million technically editable paths are not a usable slide.

## Route the job

1. Preserve the untouched source.
2. Run `scripts/preflight_image.py` for raster input. Use its recommendation unless the user explicitly requests a different tradeoff.
3. Choose one mode:
   - `native`: diagrams and flat artwork within the 50,000-object budget. Vectorize at full detail, restore live text, then draw native PowerPoint shapes.
   - `light-native`: complex, photographic, gradient-heavy, or over-budget artwork. Search progressively smaller palettes, larger speckle filters, stronger curve simplification, and—only at the final levels—a reduced tracing resolution. Select the highest-detail candidate within the object budget, then draw only native PowerPoint shapes.
   - `archive`: create a maximum-fidelity SVG without expanding it into PowerPoint.
4. For raster-to-SVG conversion, use the pinned local engine by default. A configured remote adapter may run a stronger engine such as SuperSVG or AdaVec; its SVG still passes local normalization, safe path packing, validation, and the object budget. Never upload an image merely because a remote backend exists.
5. For Windows and an already open presentation, use `scripts/reconstruct_from_svg.ps1` to append native objects to the active slide. For a saved or headless presentation, use `scripts/render_pptx_ooxml.py` through `scripts/run_pipeline.py`.
6. Render and inspect the PPTX. Report the native object count, selected light-native profile, any source-scale reduction, and the fidelity compromise.

For mode boundaries and architecture, read [references/architecture.md](references/architecture.md). For current engine choices and their implementation status, read [references/algorithm-selection.md](references/algorithm-selection.md). For an optional hosted vectorizer, read [references/remote-backend.md](references/remote-backend.md). For editable text, read [references/live-text-workflow.md](references/live-text-workflow.md).

## Required behavior

- Do not generate a raster-background-plus-editable-overlay result. Automatic routing is native-only.
- Keep labels, formulas, legends, arrows, and key scientific structures as independent objects when they are rebuilt.
- Preserve repeated elements as separate objects. Preserve source paint order and existing slide content.
- Before native rendering, enforce the 50,000-object default limit. If a full-detail result exceeds it, rerun the budgeted native search. Never silently switch to a raster fallback.
- In light-native mode, prefer shared-boundary cutout regions, palette reduction, small-region cleanup, and spline simplification. Keep the first candidate that fits the object budget so uncomplicated images retain more detail.
- Pack compatible, non-overlapping, same-style regions into bounded compound paths. Preserve at most 64 source subpaths per PowerPoint object so the result remains selectable and does not become one monolithic shape.
- Never globally merge paths from a layered or overlapping engine. For those SVGs, only pack adjacent paths with identical paint; global style packing is allowed only when the engine guarantees a cutout mosaic.
- Do not use generative text removal without a mask or an outside-mask difference check when non-text geometry must remain unchanged.
- Never overwrite the source or an existing output without explicit authorization.
- Do not require an API key for local operation. Remote credentials are optional, user-specific, and must not enter the repository, logs, output files, or command arguments.

## Common commands

```powershell
python scripts/preflight_image.py --input reference.png
python scripts/run_pipeline.py --input-image reference.png --output-root outputs
powershell -ExecutionPolicy Bypass -File scripts/reconstruct_from_svg.ps1 -InputSvg figure.svg -OutputRoot outputs -UseActivePresentation
```

Use `--mode archive` for an SVG-only fidelity record. Use `--mode native` for direct full-detail tracing, or `--mode light-native` to enforce the object budget explicitly. Automatic mode selects between those two editable PowerPoint routes.
