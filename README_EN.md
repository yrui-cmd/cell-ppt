# Nature PPT

Nature PPT reconstructs PNG, JPEG, WebP, or SVG references as practical PowerPoint content. It preflights complexity before choosing a representation, because a deck containing a million technically editable paths is not a usable editable deck.

## Modes

- Native: flat scientific diagrams and limited-color artwork become PowerPoint shapes and live text.
- Hybrid: photographs, 3D renders, glass, glow, soft shadows, and dense gradients remain a sharp background while text and important scientific elements are rebuilt above it.
- Archive: produces a maximum-fidelity SVG without forcing an impractical object count into PowerPoint.

The default native-object safety limit is 50,000.

## Vectorization

Local operation needs no API key and uses a pinned, checksum-verified VTracer 1.0.0-alpha.4 binary. An optional HTTPS adapter can call a separately configured vectorization service. The service returns SVG only; normalization, validation, and PowerPoint rendering remain local. Nothing is uploaded unless a remote endpoint is configured and selected.

## Install

```powershell
git clone https://github.com/Gerry2024-hub/nature-ppt.git
Set-Location .\nature-ppt
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

On macOS, run `bash ./setup.sh`. Add `-Force` or `--force` to replace an older Nature PPT installation. The installer updates only `nature-ppt` and preserves its runtime configuration.

## Use

```text
Use $nature-ppt to reconstruct this reference as a practical editable PowerPoint. Preflight native versus hybrid mode and disclose every raster layer.
```

The command-line entry point is `scripts/run_pipeline.py`. On Windows, `scripts/reconstruct_from_svg.ps1` can append verified SVG geometry to the active PowerPoint slide. Saved-PPTX generation uses the cross-platform OOXML renderer.

## Tests

```text
python tests/test_nature_ppt.py
python tests/test_cross_platform.py
```

Hybrid output is editable by layer and annotation, not pixel-by-pixel. Nature PPT always reports that distinction.
