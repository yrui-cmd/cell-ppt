#!/usr/bin/env python3
"""Restore a Nature PPT text manifest as live editable SVG text."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def finite(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def parse_viewbox(root: ET.Element) -> tuple[float, float, float, float]:
    raw = root.get("viewBox", "")
    values = [float(item) for item in re.split(r"[\s,]+", raw.strip()) if item]
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise ValueError("input SVG requires a finite positive viewBox")
    return values[0], values[1], values[2], values[3]


def solid_color(value: object) -> str:
    rendered = str(value or "#000000").strip()
    if not re.fullmatch(r"#[0-9A-Fa-f]{3,8}|[A-Za-z]+|none", rendered):
        raise ValueError(f"unsupported text color: {rendered}")
    return rendered


def coordinate(item: dict, key: str, origin: float, extent: float, normalized: bool) -> float:
    value = finite(item[key], key)
    return origin + value * extent if normalized else value


def bbox_of(item: dict) -> tuple[dict | None, bool]:
    box = item.get("bbox_normalized")
    normalized = isinstance(box, dict)
    if not normalized:
        box = item.get("bbox")
    if not isinstance(box, dict):
        return None, False
    values = {key: finite(box.get(key), f"bbox.{key}") for key in ("x", "y", "width", "height")}
    if values["width"] <= 0 or values["height"] <= 0:
        raise ValueError(f"text element {item.get('id')} has a non-positive bbox")
    if normalized and (
        values["x"] < 0
        or values["y"] < 0
        or values["x"] + values["width"] > 1
        or values["y"] + values["height"] > 1
    ):
        raise ValueError(f"text element {item.get('id')} has a bbox outside the normalized canvas")
    return values, normalized


def text_element(item: dict, viewbox: tuple[float, float, float, float]) -> ET.Element:
    for required in ("id", "content", "x", "y"):
        if required not in item:
            raise ValueError(f"text element is missing {required}")
    if not isinstance(item["content"], str) or not item["content"]:
        raise ValueError(f"text element {item['id']} has empty content")

    x0, y0, width, height = viewbox
    normalized = item.get("coordinate_space", "normalized") == "normalized"
    x = coordinate(item, "x", x0, width, normalized)
    y = coordinate(item, "y", y0, height, normalized)
    font_size = finite(item.get("font_size", 12), "font_size")
    if normalized and item.get("font_size_space") == "normalized":
        font_size *= height
    if font_size <= 0:
        raise ValueError(f"text element {item['id']} has non-positive font_size")

    attributes = {
        "id": str(item["id"]),
        "x": f"{x:g}",
        "y": f"{y:g}",
        "fill": solid_color(item.get("fill", "#000000")),
        "font-family": str(item.get("font_family", "Arial")),
        "font-size": f"{font_size:g}",
        "font-weight": str(item.get("font_weight", "normal")),
        "font-style": str(item.get("font_style", "normal")),
        "text-anchor": str(item.get("text_anchor", "start")),
        "dominant-baseline": str(item.get("dominant_baseline", "alphabetic")),
        "letter-spacing": f"{finite(item.get('letter_spacing', 0), 'letter_spacing'):g}",
        "opacity": f"{finite(item.get('opacity', 1), 'opacity'):g}",
        "data-paint-order": str(int(item.get("paint_order", 1_000_000))),
        "data-nature-ppt-live-text": "true",
    }
    box, box_normalized = bbox_of(item)
    if box:
        attributes["data-bbox"] = ",".join(f"{box[key]:g}" for key in ("x", "y", "width", "height"))
        attributes["data-bbox-space"] = "normalized" if box_normalized else "absolute"
    rotation = finite(item.get("rotation", 0), "rotation")
    if rotation:
        attributes["transform"] = f"rotate({rotation:g} {x:g} {y:g})"

    lines = item["content"].splitlines() or [""]
    if len(lines) == 1:
        element = ET.Element(f"{{{SVG_NS}}}text", attributes)
        element.text = lines[0]
        return element

    group = ET.Element(
        f"{{{SVG_NS}}}g",
        {
            "id": attributes["id"],
            "data-paint-order": attributes["data-paint-order"],
            "data-nature-ppt-live-text": "true",
        },
    )
    line_height = finite(item.get("line_height", 1.2), "line_height") * font_size
    for index, line in enumerate(lines):
        line_y = y + index * line_height
        line_attributes = dict(attributes)
        line_attributes["id"] = f"{attributes['id']}-line-{index + 1}"
        line_attributes["y"] = f"{line_y:g}"
        if rotation:
            line_attributes["transform"] = f"rotate({rotation:g} {x:g} {line_y:g})"
        child = ET.SubElement(group, f"{{{SVG_NS}}}text", line_attributes)
        child.text = line
    return group


def restore(input_svg: Path, manifest_path: Path, output_svg: Path, force: bool = False) -> dict:
    input_svg = input_svg.resolve(strict=True)
    manifest_path = manifest_path.resolve(strict=True)
    output_svg = output_svg.expanduser().resolve()
    if output_svg.exists() and not force:
        raise ValueError(f"output already exists: {output_svg}")

    tree = ET.parse(input_svg)
    root = tree.getroot()
    if root.tag.rsplit("}", 1)[-1] != "svg":
        raise ValueError("input root is not svg")
    if any(node.tag.rsplit("}", 1)[-1] in {"image", "foreignObject"} for node in root.iter()):
        raise ValueError("input SVG contains a raster or foreign node")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema_version") != "1.0":
        raise ValueError("text manifest schema_version must be 1.0")
    items = manifest.get("text_elements")
    if not isinstance(items, list) or not items:
        raise ValueError("text_elements must be a non-empty array")

    viewbox = parse_viewbox(root)
    existing_ids = {node.get("id") for node in root.iter() if node.get("id")}
    manifest_ids: set[str] = set()
    additions: list[tuple[int, ET.Element]] = []
    warnings: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"text_elements[{index}] must be an object")
        item_id = str(item.get("id", ""))
        if not item_id or item_id in manifest_ids or item_id in existing_ids:
            raise ValueError(f"missing or duplicate text id: {item_id}")
        manifest_ids.add(item_id)
        if not isinstance(item.get("bbox") or item.get("bbox_normalized"), dict):
            warnings.append(f"{item_id} has no bbox; placement cannot be independently audited")
        paint_order = int(item.get("paint_order", len(root) + index))
        additions.append((paint_order, text_element(item, viewbox)))

    for paint_order, element in sorted(additions, key=lambda pair: pair[0]):
        root.insert(max(0, min(paint_order, len(root))), element)
    root.set("data-nature-ppt-text-manifest", manifest_path.name)
    root.set("data-nature-ppt-live-text-count", str(len(additions)))

    output_svg.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb", suffix=".svg", dir=output_svg.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        tree.write(stream, encoding="utf-8", xml_declaration=True)
    temporary.replace(output_svg)
    return {
        "status": "PASS",
        "output_svg": str(output_svg),
        "live_text_count": len(additions),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-svg", required=True, type=Path)
    parser.add_argument("--text-manifest", required=True, type=Path)
    parser.add_argument("--output-svg", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            restore(args.input_svg, args.text_manifest, args.output_svg, args.force),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, ET.ParseError, json.JSONDecodeError) as error:
        print(f"LIVE_TEXT_RESTORE_ERROR|{error}", file=sys.stderr)
        raise SystemExit(1)
