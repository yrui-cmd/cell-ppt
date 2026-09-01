# Live-text workflow

Use this mode when the reference contains labels, formulas, legends, axis text, or annotations that must remain sharp and editable.

## Required stages

1. Preserve the untouched source image.
2. Record every visible text run before cleanup. Include exact content, baseline position, bounding box, font family, font size, weight, style, color, opacity, rotation, alignment, and paint order. Verify scientific notation, Greek letters, subscripts, superscripts, signs, and units manually.
3. Use the available Image 2 or image-editing tool to remove text only. Preserve all non-text pixels, including lines crossing behind labels, arrows, frames, molecular bonds, axes, legends, and background colors. Never hide text with opaque rectangles.
4. Keep the cleaned image at exactly the source pixel dimensions. Compare it against the source outside recorded text boxes; unexpected changes require another cleanup pass.
5. Run `scripts/vectorize_with_live_text.py --source-input <original> --cleaned-input <cleaned> --text-manifest <json> --output <svg>`.
6. Require `status: PASS`, `raster_nodes: 0`, and the expected `live_text_count`. Inspect the Master SVG before sending it to `$cell-ppt`.

## Text manifest 1.0

The root object contains `schema_version: "1.0"` and a non-empty `text_elements` array. Each element requires:

- `id`, `content`, `x`, and `y`;
- `coordinate_space` (`normalized` is preferred);
- `font_size` and optionally `font_size_space: "normalized"`;
- `font_family`, `font_weight`, `font_style`, `fill`, `opacity`, `rotation`, `text_anchor`, and `dominant_baseline` as observed;
- `bbox_normalized` for placement auditing;
- `paint_order` so restored text returns to the correct layer.

Example:

```json
{
  "schema_version": "1.0",
  "text_elements": [
    {
      "id": "label-001",
      "content": "Eₐ",
      "x": 0.42,
      "y": 0.18,
      "coordinate_space": "normalized",
      "font_size": 0.035,
      "font_size_space": "normalized",
      "font_family": "Arial",
      "font_weight": "normal",
      "font_style": "italic",
      "fill": "#111111",
      "opacity": 1,
      "rotation": 0,
      "text_anchor": "start",
      "dominant_baseline": "alphabetic",
      "bbox_normalized": {"x": 0.42, "y": 0.145, "width": 0.04, "height": 0.045},
      "paint_order": 1200
    }
  ]
}
```

Plain VTracer parameter increases cannot reconstruct glyph information absent from a low-resolution image. Do not trace visible raster text when editable text is requested.
