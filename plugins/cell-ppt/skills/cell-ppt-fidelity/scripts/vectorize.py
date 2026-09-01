#!/usr/bin/env python3
"""Run the pinned maximum-fidelity local vectorization profile."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from bootstrap_vtracer import default_cache, load_contract, resolve_binary
from normalize_svg import normalize


RASTER_TAGS = {"image", "foreignObject", "video", "canvas"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(svg: Path) -> dict:
    root = ET.parse(svg).getroot()
    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    number_pattern = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"
    if len(view_box) != 4 or any(not re.fullmatch(number_pattern, value) for value in view_box):
        raise ValueError("A finite four-number viewBox is required")
    numbers = [float(value) for value in view_box]
    if numbers[2] <= 0 or numbers[3] <= 0:
        raise ValueError("The viewBox width and height must be positive")
    paths = 0
    stable_ids = 0
    raster_nodes = 0
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "path":
            paths += 1
            stable_ids += int(bool(element.attrib.get("id")))
        elif tag in RASTER_TAGS:
            raster_nodes += 1
    if paths == 0 or stable_ids != paths or raster_nodes:
        raise ValueError(
            f"Invalid vector structure: paths={paths}, stable_ids={stable_ids}, raster_nodes={raster_nodes}"
        )
    return {"view_box": numbers, "paths": paths, "stable_ids": stable_ids, "raster_nodes": raster_nodes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, default=default_cache())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.input.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Input image does not exist: {source}")
    if source.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise SystemExit("Input must be PNG, JPEG, or WebP")
    if output.suffix.lower() != ".svg":
        raise SystemExit("Output must use the .svg extension")
    if output.exists() and not args.force:
        raise SystemExit(f"Output already exists: {output}. Use --force only when replacement is authorized.")

    contract = load_contract()
    executable, metadata = resolve_binary(args.cache_dir)
    profile = contract["profile"]
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cell-ppt-fidelity-", dir=output.parent) as raw_temp:
        raw_svg = Path(raw_temp) / "raw.svg"
        command = [str(executable), str(source), str(raw_svg), *profile["arguments"]]
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        normalize(raw_svg, output)

    result = validate(output)
    report = {
        "schema_version": "1.0",
        "status": "PASS",
        "engine": contract["engine"]["name"],
        "engine_version": metadata["version"],
        "profile": profile["name"],
        "input": str(source),
        "output": str(output),
        "sha256": sha256(output),
        **result,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
