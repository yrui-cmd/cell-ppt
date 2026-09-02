---
name: nature-ppt
description: Reconstruct PNG, JPEG, WebP, or SVG references as practical editable PowerPoint content, using native shapes and live text for diagrams and a deliberate hybrid mode for photographic or gradient-heavy artwork. Use for image-to-PPT tracing, scientific figure reconstruction, and local PowerPoint drawing.
---

# Nature PPT

Turn a visual reference into a PowerPoint that remains useful after conversion. Treat editability as an object-budget problem: a million technically editable paths are not a usable slide.

## Route the job

1. Preserve the untouched source.
2. Run `scripts/preflight_image.py` for raster input. Use its recommendation unless the user explicitly requests a different tradeoff.
3. Choose one mode:
   - `native`: diagrams and flat artwork within the 50,000-object budget. Vectorize, restore live text, then draw native PowerPoint shapes.
   - `hybrid`: photographs, 3D renders, soft shadows, glass, glow, or dense gradients. Keep those continuous-tone regions as a sharp background; rebuild text and important scientific objects as native PowerPoint elements.
   - `archive`: create a maximum-fidelity SVG without claiming that it is practical to expand into PowerPoint.
4. For raster-to-SVG conversion, use `local` by default. Use the optional `remote` backend only when an endpoint is already configured or the user asks for it. Never upload an image merely because a remote backend exists.
5. For Windows and an already open presentation, use `scripts/reconstruct_from_svg.ps1` to append native objects to the active slide. For a saved or headless presentation, use `scripts/render_pptx_ooxml.py` through `scripts/run_pipeline.py`.
6. Render and inspect the PPTX. Report which layers are native, which remain raster, the object count, and any fidelity compromise.

For mode boundaries and architecture, read [references/architecture.md](references/architecture.md). For an optional hosted vectorizer, read [references/remote-backend.md](references/remote-backend.md). For editable text, read [references/live-text-workflow.md](references/live-text-workflow.md).

## Required behavior

- Do not silently describe a raster background as fully editable.
- Keep labels, formulas, legends, arrows, and key scientific structures as independent objects when they are rebuilt.
- Preserve repeated elements as separate objects. Preserve source paint order and existing slide content.
- Before native rendering, enforce the 50,000-object default limit. If a result exceeds it, keep the SVG and switch to hybrid mode unless the user explicitly accepts a slow, very large native deck.
- Do not use generative text removal without a mask or an outside-mask difference check when non-text geometry must remain unchanged.
- Never overwrite the source or an existing output without explicit authorization.
- Do not require an API key for local operation. Remote credentials are optional, user-specific, and must not enter the repository, logs, output files, or command arguments.

## Common commands

```powershell
python scripts/preflight_image.py --input reference.png
python scripts/run_pipeline.py --input-image reference.png --output-root outputs
powershell -ExecutionPolicy Bypass -File scripts/reconstruct_from_svg.ps1 -InputSvg figure.svg -OutputRoot outputs -UseActivePresentation
```

Use `--mode archive` for an SVG-only fidelity record. Use `--mode native` only when the preflight and actual vector count stay within budget. Use `--mode hybrid --also-svg` when both a practical PPTX and a full vector archive are useful.
