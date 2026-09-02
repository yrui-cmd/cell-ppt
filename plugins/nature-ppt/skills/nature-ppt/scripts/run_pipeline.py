#!/usr/bin/env python3
"""Route one raster reference to a practical editable PowerPoint workflow."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from preflight_image import analyze


def execute(command: list[str]) -> dict:
    process = subprocess.run(command, check=True, capture_output=True, text=True)
    output = process.stdout.strip()
    return json.loads(output) if output else {}


def next_job(root: Path) -> str:
    process = subprocess.run(
        [sys.executable, str(Path(__file__).with_name("allocate_job_name.py")), "--root", str(root)],
        check=True,
        capture_output=True,
        text=True,
    )
    return process.stdout.strip().splitlines()[-1]


def vectorize(source: Path, output: Path, backend: str, endpoint: str | None, token_file: Path | None) -> dict:
    scripts = Path(__file__).resolve().parent
    selected = backend
    if selected == "auto":
        selected = "remote" if endpoint or os.environ.get("NATURE_PPT_VECTOR_URL") else "local"
    if selected == "remote":
        command = [
            sys.executable,
            str(scripts / "remote_vectorize.py"),
            "--input", str(source),
            "--output", str(output),
            "--profile", "editable",
        ]
        if endpoint:
            command.extend(["--endpoint", endpoint])
        if token_file:
            command.extend(["--token-file", str(token_file)])
        return execute(command)
    report = execute([
        sys.executable,
        str(scripts / "vectorize.py"),
        "--input", str(source),
        "--output", str(output),
    ])
    report["backend"] = "local"
    return report


def restore_text(vector_svg: Path, manifest: Path, output: Path) -> dict:
    scripts = Path(__file__).resolve().parent
    return execute([
        sys.executable,
        str(scripts / "restore_live_text.py"),
        "--input-svg", str(vector_svg),
        "--text-manifest", str(manifest),
        "--output-svg", str(output),
    ])


def render_native(svg: Path, output: Path, cache_root: Path, job_name: str, input_pptx: Path | None, slide_index: int) -> dict:
    scripts = Path(__file__).resolve().parent
    execute([
        sys.executable,
        str(scripts / "validate_vector_svg.py"),
        "--svg", str(svg),
        "--strict-ids",
    ])
    execute([
        sys.executable,
        str(scripts / "prepare_geometry_cache.py"),
        "--input", str(svg),
        "--output-dir", str(cache_root),
        "--job-id", job_name,
    ])
    execute([
        sys.executable,
        str(scripts / "cull_hidden_geometry.py"),
        "--cache", str(cache_root / "geometry-cache.json"),
        "--state", str(cache_root / "drawing-state.json"),
    ])
    command = [
        sys.executable,
        str(scripts / "render_pptx_ooxml.py"),
        "--geometry-cache", str(cache_root / "geometry-cache.json"),
        "--output-pptx", str(output),
        "--slide-index", str(slide_index),
    ]
    if input_pptx:
        command.extend(["--input-pptx", str(input_pptx)])
    return execute(command)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-image", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--mode", choices=("auto", "native", "hybrid", "archive"), default="auto")
    parser.add_argument("--vector-backend", choices=("auto", "local", "remote"), default="auto")
    parser.add_argument("--remote-url")
    parser.add_argument("--remote-token-file", type=Path)
    parser.add_argument("--cleaned-image", type=Path)
    parser.add_argument("--text-manifest", type=Path)
    parser.add_argument("--input-pptx", type=Path)
    parser.add_argument("--slide-index", type=int, default=0)
    parser.add_argument("--native-object-limit", type=int, default=50_000)
    parser.add_argument("--allow-large-native", action="store_true")
    parser.add_argument("--also-svg", action="store_true")
    args = parser.parse_args()

    source = args.input_image.expanduser().resolve(strict=True)
    cleaned = args.cleaned_image.expanduser().resolve(strict=True) if args.cleaned_image else source
    manifest = args.text_manifest.expanduser().resolve(strict=True) if args.text_manifest else None
    if (args.cleaned_image is None) != (manifest is None):
        raise SystemExit("cleaned-image and text-manifest must be supplied together")
    root = args.output_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    job_name = next_job(root)
    job = root / job_name
    job.mkdir()
    preflight = analyze(source, args.native_object_limit)
    (job / "preflight.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mode = preflight["recommended_mode"] if args.mode == "auto" else args.mode
    pptx = job / f"{job_name}.pptx"
    master_svg = job / f"{job_name}.svg"
    vector_report = None
    render_report = None

    if mode == "hybrid":
        render_report = execute([
            sys.executable,
            str(Path(__file__).with_name("build_hybrid_pptx.py")),
            "--background-image", str(cleaned),
            "--output-pptx", str(pptx),
            *(["--text-manifest", str(manifest)] if manifest else []),
            *(["--input-pptx", str(args.input_pptx.resolve())] if args.input_pptx else []),
            "--slide-index", str(args.slide_index),
        ])
        if args.also_svg:
            raw_svg = job / f"{job_name}-trace.svg"
            vector_report = vectorize(cleaned, raw_svg, args.vector_backend, args.remote_url, args.remote_token_file)
            if manifest:
                restore_text(raw_svg, manifest, master_svg)
            else:
                raw_svg.replace(master_svg)
    else:
        raw_svg = job / f"{job_name}-trace.svg"
        vector_report = vectorize(cleaned, raw_svg, args.vector_backend, args.remote_url, args.remote_token_file)
        if manifest:
            restore_text(raw_svg, manifest, master_svg)
        else:
            raw_svg.replace(master_svg)
        if mode == "native":
            vector_count = int(vector_report.get("vector_element_count", vector_report.get("paths", 0)))
            if vector_count > args.native_object_limit and not args.allow_large_native:
                render_report = execute([
                    sys.executable,
                    str(Path(__file__).with_name("build_hybrid_pptx.py")),
                    "--background-image", str(cleaned),
                    "--output-pptx", str(pptx),
                    *(["--text-manifest", str(manifest)] if manifest else []),
                    *(["--input-pptx", str(args.input_pptx.resolve())] if args.input_pptx else []),
                    "--slide-index", str(args.slide_index),
                ])
                mode = "hybrid-after-vector-limit"
            else:
                render_report = render_native(
                    master_svg,
                    pptx,
                    job / ".nature-ppt-cache",
                    job_name,
                    args.input_pptx.resolve() if args.input_pptx else None,
                    args.slide_index,
                )

    report = {
        "schema_version": "1.0",
        "status": "PASS",
        "job": job_name,
        "mode": mode,
        "preflight": preflight,
        "vectorization": vector_report,
        "render": render_report,
        "pptx": str(pptx) if pptx.exists() else None,
        "svg": str(master_svg) if master_svg.exists() else None,
    }
    (job / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
