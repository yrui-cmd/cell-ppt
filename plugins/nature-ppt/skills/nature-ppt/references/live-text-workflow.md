# Live-text workflow

Use this workflow when labels, formulas, legends, axes, or annotations must remain sharp and editable.

1. Preserve the untouched source image.
2. Record each text run before cleanup: exact content, bounding box, baseline, font family, size, weight, style, color, opacity, rotation, alignment, and paint order. Verify scientific notation manually.
3. Build text masks and remove text only inside those masks. Do not cover text with opaque rectangles.
4. Require the cleaned image to retain the source dimensions. Compare pixels outside the masks; unexpected changes require another cleanup pass.
5. Vectorize the cleaned image, then restore the manifest with `scripts/restore_live_text.py`.
6. Validate the Master SVG and inspect text placement before local PowerPoint rendering.

## Manifest 1.0

The root contains `schema_version: "1.0"` and a `text_elements` array. Each item requires `id`, `content`, `x`, and `y`. Normalized coordinates are preferred. Useful fields include `font_size`, `font_size_space`, `font_family`, `font_weight`, `font_style`, `fill`, `opacity`, `rotation`, `text_anchor`, `dominant_baseline`, `bbox_normalized`, and `paint_order`.

Plain tracing cannot recover glyph information that is absent from the raster. Font identity and kerning may still require visual calibration.
