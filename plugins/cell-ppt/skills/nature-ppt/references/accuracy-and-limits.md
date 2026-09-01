# Accuracy and limits

## What the profile optimizes

The pinned profile uses VTracer 1.0.0-alpha.4 with `photo` segmentation and `pixel` curve fitting. In the maintained 1013×524 LECO reference test it produced SSIM 0.9982763, PSNR 44.001786 dB, MAE 0.912993, and no pixels whose largest channel error exceeded 25. The output contained 87,432 paths.

These values establish why the profile is selected; they do not guarantee the same score on unrelated images. Always inspect the rendered SVG against its own source.

## Tradeoffs

- Pixel fitting preserves raster boundaries and avoids spline overshoot, but it can expose stair-stepping already present in a low-resolution source.
- Resolution-independent SVG scaling does not recreate information absent from the input.
- Complex gradients are represented by many solid regions because Cell_ppt currently accepts solid editable paths rather than SVG gradient, mask, or clipping structures.
- A dense figure may produce tens of thousands of PowerPoint objects. Visual fidelity increases while file size, drawing time, and interactive editing performance worsen.
- Semantic image-to-SVG models can produce cleaner and smaller artwork but may change geometry, labels, repeated elements, or scientific meaning. They are not a substitute for this exact-tracing profile.

If the user instead wants a publication-style redesign, use a semantic reconstruction workflow and describe it as a redraw, not a faithful trace.
