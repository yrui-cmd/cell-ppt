# Cell_ppt

Rebuild a scientific image as native editable PowerPoint paths and text while preserving everything already on the target slide.

`Cell_ppt` records the original labels and positions, removes only the text from a working copy, recognizes the remaining graphic paths, restores live text, and writes objects in the source layer order. It removes only exact duplicate paths, preserving occlusion, transparency, and compound holes.

## What you get

- individually selectable PowerPoint paths;
- editable labels with recorded source positions;
- source aspect ratio and paint order preserved;
- live Windows drawing or a native editable PPTX on macOS;
- an optional hidden-watermark treatment step.

## Optional hidden-watermark treatment

Setup also installs or updates the independently open-source [cell_no_ai](https://github.com/yrui-cmd/cell_no_ai). After text cleanup, the user may choose to download its processed result before path recognition. Declining uses the verified cleaned image directly. This step is provided by a third-party service, so effectiveness depends on the returned file and subsequent verification.

Cell_ppt supports Windows and macOS with one shared core pipeline:

`text manifest → Image 2 text-only cleanup → optional hidden-watermark treatment and image download → Xiaomiao path-return SVG → editable text merge → one parse → duplicate-path removal → literal source order from back to front → native editable PPTX`

- Windows supports PowerPoint 2016, 2019, 2021, LTSC 2021, LTSC 2024, and Microsoft 365 desktop through the common `PowerPoint.Application` COM interface.
- macOS supports desktop PowerPoint 2019, 2021, 2024, and Microsoft 365 versions that open standard `.pptx` files. It writes the same geometry cache as native editable DrawingML custom geometry into a saved PPTX; file-backed output is not presented as fake live animation.
- WPS Presentation remains experimental.

## Fixed defaults

- Python 3.11–3.14.
- `python-pptx==1.0.2`, `fonttools==4.61.1`, `shapely==2.1.2`.
- Geometry cache schema 3; text manifest schema 1.0.
- Ordinary batches contain 20–50 paths; slide margin is 18 pt.
- Output names use `shibielujingN`.
- Windows credentials use DPAPI; macOS credentials use Keychain service `cell-ppt-xiaomiao`.

## Codex-managed installation

The user may provide the API key directly in chat. Codex must never repeat or display it. Codex passes it to setup through standard input; setup installs dependencies, copies the Skill, detects the operating system and available presentation host, writes `runtime-profile.json`, stores the credential with DPAPI or Keychain, runs a zero-credit authentication check, and selects the backend automatically. The user is not asked to choose Python, a PowerPoint version, a ProgID, or a backend.
- Existing slide objects are preserved.

## Windows install

```powershell
git clone https://github.com/yrui-cmd/cell-ppt.git
Set-Location .\cell-ppt
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

## macOS install

```bash
git clone https://github.com/yrui-cmd/cell-ppt.git
cd cell-ppt
bash ./setup.sh
```

Restart Codex after installation. For an existing macOS deck, save it first and provide its PPTX path.

## Cross-platform test

```bash
python3 ./tests/test_cross_platform.py
```
