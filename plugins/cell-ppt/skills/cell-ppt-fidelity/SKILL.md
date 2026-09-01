---
name: cell-ppt-fidelity
description: Convert PNG, JPEG, or WebP references into maximum-fidelity, locally traced, editable solid-path SVGs for Cell_ppt when exact visual matching matters more than path count or editing speed. Use for no-API raster tracing, not semantic redraw or invented detail.
---

# Cell_ppt Fidelity

Use this Skill when the user prioritizes faithful tracing over path economy. It runs VTracer locally, does not require an API key, and produces a Cell_ppt-compatible SVG containing independent solid paths with stable IDs.

## Workflow

1. Preserve the untouched source image.
2. If the final PowerPoint needs editable text, first use the text-manifest and text-only cleanup stage from `$cell-ppt`; do not trace visible text and later cover it.
3. Run `scripts/vectorize.py --input <image> --output <svg>`. The fixed maximum-fidelity profile is loaded from `references/fidelity-profile.json`.
4. Check the JSON result. Require `status: PASS`, `raster_nodes: 0`, a finite positive viewBox, and stable IDs for every path.
5. Inspect the SVG visually at the source size before PowerPoint import. High metric scores do not excuse visible curve overshoot or missing structures.
6. When native PowerPoint objects are requested, read the installed `cell-ppt/SKILL.md` and pass the verified SVG to its SVG workflow. Preserve source paint order and existing slide content.

## Accuracy contract

- Use the pinned `photo + pixel` profile. Do not silently replace it with spline fitting, a semantic image-to-SVG model, generative upscaling, or an online service.
- Treat “high definition” as resolution-independent reproduction of the supplied pixels. Never claim to restore detail absent from the source.
- Keep every traced region independent. Do not merge repeated elements or flatten the complete figure into a raster image.
- Expect large output. Maximum fidelity can create tens of thousands of paths and make PowerPoint drawing slow. Do not reduce detail unless the user explicitly prioritizes editability or speed.
- Never overwrite the source or an existing output unless the user explicitly authorizes replacement.

Read [references/accuracy-and-limits.md](references/accuracy-and-limits.md) when explaining fidelity, performance, or source-resolution limits. The VTracer binary is downloaded lazily from the pinned official release and verified against the hashes in [references/fidelity-profile.json](references/fidelity-profile.json).
