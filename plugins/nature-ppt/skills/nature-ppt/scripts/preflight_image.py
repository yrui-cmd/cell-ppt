#!/usr/bin/env python3
"""Estimate whether an image is practical as native PowerPoint vector objects."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat


SUPPORTED = {".png", ".jpg", ".jpeg", ".webp"}


def analyze(path: Path, native_limit: int = 50_000) -> dict:
    source = path.expanduser().resolve(strict=True)
    if source.suffix.lower() not in SUPPORTED:
        raise ValueError("input must be PNG, JPEG, or WebP")
    with Image.open(source) as opened:
        image = opened.convert("RGB")
        width, height = image.size
        sample = image.copy()
        sample.thumbnail((384, 384), Image.Resampling.LANCZOS)
    quantized = sample.quantize(colors=256)
    histogram = quantized.histogram()
    total = max(1, sum(histogram))
    entropy = -sum((count / total) * math.log2(count / total) for count in histogram if count)
    unique = len(sample.getcolors(maxcolors=sample.width * sample.height) or [])
    edge_image = sample.filter(ImageFilter.FIND_EDGES).convert("L")
    edge_mean = float(ImageStat.Stat(edge_image).mean[0])
    color_ratio = min(1.0, unique / max(1.0, sample.width * sample.height * 0.45))
    entropy_ratio = min(1.0, entropy / 8.0)
    edge_ratio = min(1.0, edge_mean / 45.0)
    complexity = 0.42 * color_ratio + 0.38 * entropy_ratio + 0.20 * edge_ratio
    projected_paths = max(100, round(width * height * (0.006 + 0.48 * complexity)))
    photographic = entropy >= 6.7 or unique >= 20_000 or complexity >= 0.68
    recommended = "light-native" if photographic or projected_paths > native_limit else "native"
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "input": str(source),
        "dimensions": [width, height],
        "sample_dimensions": list(sample.size),
        "entropy": round(entropy, 4),
        "sample_unique_colors": unique,
        "edge_mean": round(edge_mean, 4),
        "complexity_score": round(complexity, 4),
        "projected_native_paths": projected_paths,
        "native_object_limit": native_limit,
        "classification": "photographic-or-gradient-heavy" if photographic else "diagram-or-flat-art",
        "recommended_mode": recommended,
        "reason": (
            "use budgeted color reduction, region cleanup, and curve simplification to stay natively editable"
            if recommended == "light-native"
            else "estimated vector complexity is within the native-editing budget"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--native-object-limit", type=int, default=50_000)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.native_object_limit < 1:
        raise SystemExit("native-object-limit must be positive")
    report = analyze(args.input, args.native_object_limit)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        destination = args.report.expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
