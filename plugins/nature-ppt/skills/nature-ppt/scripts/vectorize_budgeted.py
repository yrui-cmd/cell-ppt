#!/usr/bin/env python3
"""Create the highest-detail native SVG that fits a PowerPoint object budget."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

from bootstrap_vtracer import default_cache, load_contract, resolve_binary
from normalize_svg import normalize
from optimize_svg_paths import optimize
from vectorize import sha256, validate


# Ordered from highest fidelity to strongest compression. The first candidate
# under the object budget wins, so simple inputs are not simplified needlessly.
PROFILES = (
    {"name": "quality", "colors": 96, "speckle": 2, "simplify": 1.0, "max_edge": None},
    {"name": "balanced", "colors": 64, "speckle": 4, "simplify": 1.5, "max_edge": None},
    {"name": "compact", "colors": 48, "speckle": 8, "simplify": 2.0, "max_edge": None},
    {"name": "lean", "colors": 32, "speckle": 12, "simplify": 2.5, "max_edge": 1600},
    {"name": "very-lean", "colors": 24, "speckle": 24, "simplify": 3.5, "max_edge": 1200},
    {"name": "ultra-lean", "colors": 16, "speckle": 48, "simplify": 5.0, "max_edge": 800},
    {"name": "last-resort", "colors": 12, "speckle": 96, "simplify": 7.0, "max_edge": 512},
)


def arguments(profile: dict) -> list[str]:
    return [
        "--preset", "photo",
        "--mode", "spline",
        "--hierarchical", "cutout",
        "--max-colors", str(profile["colors"]),
        "--filter-speckle", str(profile["speckle"]),
        "--simplify", str(profile["simplify"]),
        "--path-precision", "3",
        "--optimize", "1",
    ]


def prepare_source(source: Path, destination: Path, max_edge: int | None) -> tuple[Path, float]:
    if max_edge is None:
        return source, 1.0
    with Image.open(source) as opened:
        width, height = opened.size
        longest = max(width, height)
        if longest <= max_edge:
            return source, 1.0
        scale = max_edge / longest
        resized = opened.convert("RGBA")
        resized.thumbnail((max_edge, max_edge), Image.Resampling.LANCZOS)
        resized.save(destination, format="PNG")
    return destination, scale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--object-limit", type=int, default=50_000)
    parser.add_argument("--cache-dir", type=Path, default=default_cache())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file() or source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise SystemExit("Input must be an existing PNG, JPEG, or WebP")
    if output.suffix.lower() != ".svg":
        raise SystemExit("Output must use the .svg extension")
    if args.object_limit < 1:
        raise SystemExit("object-limit must be positive")
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists: {output}. Use --force only when replacement is authorized.")

    contract = load_contract()
    executable, metadata = resolve_binary(args.cache_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    attempts: list[dict] = []
    selected: tuple[Path, dict, dict, float] | None = None

    with tempfile.TemporaryDirectory(prefix="nature-ppt-budget-", dir=output.parent) as raw_temp:
        temporary = Path(raw_temp)
        for index, profile in enumerate(PROFILES):
            working_source, source_scale = prepare_source(
                source,
                temporary / f"source-{index}.png",
                profile["max_edge"],
            )
            raw_svg = temporary / f"raw-{index}.svg"
            normalized_svg = temporary / f"normalized-{index}.svg"
            optimized_svg = temporary / f"optimized-{index}.svg"
            command = [str(executable), str(working_source), str(raw_svg), *arguments(profile)]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            normalize(raw_svg, normalized_svg)
            optimization = optimize(normalized_svg, optimized_svg, cutout_mosaic=True)
            structure = validate(optimized_svg)
            attempt = {
                "profile": profile["name"],
                "paths": structure["paths"],
                "raw_regions": optimization["input_paths"],
                "path_reduction_ratio": optimization["reduction_ratio"],
                "colors": profile["colors"],
                "speckle": profile["speckle"],
                "simplify": profile["simplify"],
                "source_scale": round(source_scale, 6),
            }
            attempts.append(attempt)
            if structure["paths"] <= args.object_limit:
                selected = (optimized_svg, profile, structure, source_scale)
                break

        if selected is None:
            smallest = attempts[-1]["paths"] if attempts else "unknown"
            raise SystemExit(
                f"Could not fit the trace within {args.object_limit} native objects; "
                f"smallest candidate has {smallest}. No raster fallback was generated."
            )
        chosen_svg, profile, structure, source_scale = selected
        shutil.copyfile(chosen_svg, output)

    report = {
        "schema_version": "1.0",
        "status": "PASS",
        "engine": contract["engine"]["name"],
        "engine_version": metadata["version"],
        "profile": f"budgeted-{profile['name']}",
        "input": str(source),
        "output": str(output),
        "sha256": sha256(output),
        "object_limit": args.object_limit,
        "vector_element_count": structure["paths"],
        "source_scale": round(source_scale, 6),
        "native_only": True,
        "raster_layers": False,
        "attempts": attempts,
        **structure,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
