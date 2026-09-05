#!/usr/bin/env python3
"""Reduce SVG object count by packing compatible paths into compound paths."""

from __future__ import annotations

import argparse
import json
import tempfile
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def style_key(element: ET.Element) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, value) for key, value in element.attrib.items() if key not in {"d", "id"}))


def merge_chunk(chunk: list[ET.Element]) -> ET.Element:
    merged = ET.Element(chunk[0].tag, dict(chunk[0].attrib))
    merged.set("d", " ".join(element.get("d", "").strip() for element in chunk if element.get("d", "").strip()))
    return merged


def pack_paths(paths: list[ET.Element], max_subpaths: int) -> list[ET.Element]:
    packed: list[ET.Element] = []
    for start in range(0, len(paths), max_subpaths):
        packed.append(merge_chunk(paths[start:start + max_subpaths]))
    return packed


def optimize_parent(parent: ET.Element, cutout_mosaic: bool, max_subpaths: int) -> None:
    children = list(parent)
    for child in children:
        optimize_parent(child, cutout_mosaic, max_subpaths)
    direct_paths = [child for child in children if local_name(child.tag) == "path"]
    if len(direct_paths) < 2:
        return

    only_paths = len(direct_paths) == len(children)
    replacement: list[ET.Element] = []
    if cutout_mosaic and only_paths:
        buckets: OrderedDict[tuple[tuple[str, str], ...], list[ET.Element]] = OrderedDict()
        for path in direct_paths:
            buckets.setdefault(style_key(path), []).append(path)
        for bucket in buckets.values():
            replacement.extend(pack_paths(bucket, max_subpaths))
    else:
        run: list[ET.Element] = []
        run_key: tuple[tuple[str, str], ...] | None = None
        for child in children:
            if local_name(child.tag) != "path":
                if run:
                    replacement.extend(pack_paths(run, max_subpaths))
                    run = []
                    run_key = None
                replacement.append(child)
                continue
            key = style_key(child)
            if run and key != run_key:
                replacement.extend(pack_paths(run, max_subpaths))
                run = []
            run.append(child)
            run_key = key
        if run:
            replacement.extend(pack_paths(run, max_subpaths))

    parent[:] = replacement


def optimize(source: Path, output: Path, cutout_mosaic: bool, max_subpaths: int = 64) -> dict:
    if max_subpaths < 1:
        raise ValueError("max_subpaths must be positive")
    tree = ET.parse(source)
    root = tree.getroot()
    namespace = root.tag.partition("}")[0].lstrip("{") if "}" in root.tag else ""
    if namespace:
        ET.register_namespace("", namespace)
    before = sum(local_name(element.tag) == "path" for element in root.iter())
    optimize_parent(root, cutout_mosaic, max_subpaths)
    after = sum(local_name(element.tag) == "path" for element in root.iter())
    if before < 1 or after < 1:
        raise ValueError("SVG must contain at least one path before and after optimization")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", suffix=".svg", dir=output.parent, delete=False) as stream:
        temporary = Path(stream.name)
        tree.write(stream, encoding="utf-8", xml_declaration=True)
    temporary.replace(output)
    return {
        "input_paths": before,
        "optimized_paths": after,
        "reduction_ratio": round(1.0 - after / before, 6),
        "cutout_mosaic": cutout_mosaic,
        "max_subpaths_per_object": max_subpaths,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cutout-mosaic", action="store_true")
    parser.add_argument("--max-subpaths-per-object", type=int, default=64)
    args = parser.parse_args()
    report = optimize(
        args.input.expanduser().resolve(strict=True),
        args.output.expanduser().resolve(),
        args.cutout_mosaic,
        args.max_subpaths_per_object,
    )
    print(json.dumps({"status": "PASS", **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
