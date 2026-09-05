# Changelog

## 0.6.0

- Replace automatic hybrid output with an all-native two-route policy: direct native for simple art and light-native for complex art.
- Add an object-budget search using palette quantization, cutout regions, speckle cleanup, spline simplification, and late-stage source downsampling.
- Add bounded compound-path packing and compound OOXML rendering so many same-style islands become one editable PowerPoint object.
- Allow configured remote SuperSVG/AdaVec-style services to feed the same local packing, validation, and budget pipeline with deterministic local fallback.
- Preserve the highest-detail candidate that fits the native-object limit and report the selected profile and source scale.
- Fail clearly instead of generating a raster background when no candidate fits a user-specified budget.

## 0.5.0

- Make `nature-ppt` the only installed Skill and plugin identity.
- Add image-complexity preflight with a 50,000-object native safety budget.
- Add explicit native, hybrid, and maximum-fidelity archive modes.
- Add an optional generic HTTPS raster-to-SVG adapter; local VTracer remains the no-key default.
- Add local PowerPoint COM drawing and cross-platform editable OOXML rendering under Nature PPT names.
- Add a hybrid PPTX builder with high-resolution background placement and live editable text.
- Preserve existing Skill configuration during forced reinstall and leave every other Skill untouched.
- Remove promotional messages, provider-specific credential flows, and inherited output naming.
