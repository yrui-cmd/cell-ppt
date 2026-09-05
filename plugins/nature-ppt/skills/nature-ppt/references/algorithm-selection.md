# Algorithm selection

This routing reflects public research and implementations available in September 2026. No single engine is best for every raster domain.

## Production routes

### Local, dependency-light default

Use the pinned VTracer engine with cutout segmentation, palette budgeting, speckle cleanup, spline simplification, and compound-path packing. It is deterministic, runs on CPU, needs no model weights, and is the fallback when a configured research backend fails or exceeds the PowerPoint object budget.

### SuperSVG adapter for complex natural images

[SuperSVG (CVPR 2024)](https://github.com/sjtuplayer/SuperSVG) decomposes the image into superpixels, reconstructs coarse structure, refines local detail, and optionally optimizes the SVG with a differentiable renderer. Its official experiments target fixed budgets such as 500, 2,000, and 4,000 paths. Prefer it when a CUDA service and model weights are already configured. Treat its output as layered unless the adapter explicitly proves non-overlap, so use adjacent-only path packing.

### AdaVec adapter for flat and illustrated artwork

[AdaVec (CVPR 2025)](https://github.com/IMU-Group/AdaVec) adaptively assigns both paths and control points according to layer complexity, then optimizes geometry and color through differentiable rendering. Prefer it for icons, clip art, cartoons, and scientific illustrations when its DiffVG environment is available.

## Promising but not a default backend

- [Image Vectorization via Gradient Reconstruction (Eurographics 2025)](https://research.adobe.com/publication/image-vectorization-via-gradient-reconstruction/) replaces many solid color bands with solid, linear-gradient, or radial-gradient regions. This is the strongest published direction for shaded illustration, but a directly integrable public implementation was not identified and the current PowerPoint renderer supports solid fills only.
- [VectorArk (CVPR 2026)](https://openaccess.thecvf.com/content/CVPR2026/html/Gehlaut_VectorArk_Learning_Practical_Image_Vectorization_with_Rounded_Polygon_Representation_CVPR_2026_paper.html) uses a compact rounded-polygon representation, degradation training, and test-time candidate ranking for robust real-world geometry. Do not claim it is installed: no official public inference code or weights were identified.
- [Optimize & Reduce (AAAI 2024)](https://github.com/ajevnisek/optimize-and-reduce) iteratively optimizes Bézier parameters and removes shapes using an importance measure. Its top-down reduction concept informs the optional high-fidelity-then-reduce route, but its research environment is much heavier than the local default.

## Universal post-processing

All engines must emit vector-only SVG. Run normalization, remove degenerate geometry, pack compatible paths, validate stable IDs and view boxes, count the resulting PowerPoint objects, and render a visual check. If a remote result remains over budget, retain its report and use the deterministic local light-native fallback; never generate a raster background.
