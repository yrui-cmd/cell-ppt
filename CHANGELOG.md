# Changelog

## 0.4.0 - 2026-09-01

- Add a text-aware Nature PPT workflow modeled on Cell_ppt: record text, remove text only, trace the cleaned image, and restore labels as live editable SVG text.
- Add deterministic manifest validation, same-dimension source/cleanup checks, raster-node rejection, editable-text markers, and an end-to-end wrapper.
- Keep the existing local no-API maximum-fidelity tracing mode unchanged for text-free references and path-only output.

## 0.3.1 - 2026-09-01

- Rename `$cell-ppt-fidelity` to the shorter `$nature-ppt` name without changing its tested tracing engine or maximum-fidelity profile.
- Update installation, packaging, documentation, CI, and local cache naming for the new Skill identity.

## 0.3.0 - 2026-09-01

- Add the independent `$cell-ppt-fidelity` Skill for local, no-API, maximum-fidelity raster-to-SVG tracing.
- Pin VTracer 1.0.0-alpha.4 and verify official release assets with per-platform SHA-256 hashes before first use.
- Select the benchmarked `photo + pixel` profile to avoid spline overshoot and preserve raster boundaries as editable solid paths.
- Normalize viewBox and stable path IDs for strict Cell_ppt compatibility without bundling binaries or user data.
- Install and test both Skills while preserving the existing Cell_ppt API, credential, and PowerPoint workflows.

## 0.2.0 - 2026-08-31

- Use one reconstruction, text, SVG parsing, culling, cache, batching, and native-object contract on Windows and macOS.
- Keep live PowerPoint COM drawing on Windows and add native editable OOXML output for saved PPTX files on macOS.
- Add macOS Keychain credential storage, cross-platform installation, and diagnostics.
- Move stable runtime values into `platform-contract.json`; remove frozen manifests and fixed-tag installation requirements.
- Allow a user-supplied chat API key to be configured automatically through stdin without echoing it.
- Add install-time OS, Python, PowerPoint/WPS, credential, and backend matching with a non-secret runtime profile.
- Add automatic dependency installation and native editable OOXML fallback when live presentation automation is unavailable.

## 0.1.1 - 2026-08-27

- Describe the product consistently as live PowerPoint drawing rather than path presentation.
- Rename drawing-cache state and runtime contract fields while preserving bottom-to-top editable drawing behavior.
- Align the GitHub homepage with the established stable-plugin documentation structure.

## 0.1.0 - 2026-08-27

- Freeze the tested Cell_ppt PowerPoint drawing workflow.
- Add live editable text, native freeform paths, single-cache drawing, hidden-path culling, and existing-slide protection.
- Add locked dependencies, DPAPI credential storage, package tests, PowerPoint end-to-end tests, release ZIP, and SHA256 verification.
