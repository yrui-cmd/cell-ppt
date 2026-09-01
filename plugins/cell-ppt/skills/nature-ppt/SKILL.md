---
name: nature-ppt
description: Convert PNG, JPEG, or WebP references into maximum-fidelity editable SVGs for Cell_ppt, with optional text-only cleanup and sharp live-text restoration. Use for faithful local tracing, not semantic redraw or invented detail.
---

# Nature PPT

Use this Skill when the user prioritizes faithful tracing over path economy. Its tracing engine runs locally without an API key and produces a Cell_ppt-compatible SVG containing independent solid paths with stable IDs. When editable text is requested, separate raster text before tracing and restore it as live text.

## Workflow

1. Preserve the untouched source image.
2. If the reference has visible text and the output needs sharp editable text, read [references/live-text-workflow.md](references/live-text-workflow.md). Record the complete text manifest before removing text, remove text only, and run `scripts/vectorize_with_live_text.py`. Never trace visible text and later cover it.
3. If there is no text, or the user explicitly wants every source pixel traced as paths, run `scripts/vectorize.py --input <image> --output <svg>`. The fixed maximum-fidelity profile is loaded from `references/fidelity-profile.json`.
4. Check the JSON result. Require `status: PASS`, `raster_nodes: 0`, a finite positive viewBox, stable IDs for every path, and the expected live-text count when text-aware mode is used.
5. Inspect the SVG visually at the source size before PowerPoint import. Verify formulas, Greek letters, subscripts, superscripts, signs, units, placement, and paint order against the untouched source.
6. When native PowerPoint objects are requested, read the installed `cell-ppt/SKILL.md` and pass the verified Master SVG to its SVG workflow. Preserve source paint order and existing slide content.

## Accuracy contract

- Use the pinned `photo + pixel` profile. Do not silently replace it with spline fitting, a semantic image-to-SVG model, generative upscaling, or an online service.
- Treat “high definition” as resolution-independent reproduction of the supplied pixels. Never claim to restore detail absent from the source.
- Use live editable text for labels whenever the user requests clarity or editability. Parameter increases cannot turn low-resolution raster glyphs into clean typography.
- Text cleanup must preserve non-text content and source dimensions. Do not use opaque covering boxes or accept an edit that changes arrows, bonds, axes, frames, legends, or scientific subjects.
- Keep every traced region independent. Do not merge repeated elements or flatten the complete figure into a raster image.
- Expect large output. Maximum fidelity can create tens of thousands of paths and make PowerPoint drawing slow. Do not reduce detail unless the user explicitly prioritizes editability or speed.
- Never overwrite the source or an existing output unless the user explicitly authorizes replacement.

Read [references/accuracy-and-limits.md](references/accuracy-and-limits.md) when explaining fidelity, performance, or source-resolution limits. The VTracer binary is downloaded lazily from the pinned official release and verified against the hashes in [references/fidelity-profile.json](references/fidelity-profile.json).
