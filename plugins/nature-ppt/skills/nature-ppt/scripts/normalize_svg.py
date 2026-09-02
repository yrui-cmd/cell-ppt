#!/usr/bin/env python3
"""Normalize a VTracer SVG for strict Nature PPT validation."""

from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path


def normalize(source: Path, output: Path) -> int:
    text = source.read_text(encoding="utf-8")
    root = re.search(r"<svg\b([^>]*)>", text)
    if not root:
        raise ValueError("SVG root is missing")
    attrs = root.group(1)
    width = re.search(r'\bwidth="([\d.]+)', attrs)
    height = re.search(r'\bheight="([\d.]+)', attrs)
    if not width or not height or float(width.group(1)) <= 0 or float(height.group(1)) <= 0:
        raise ValueError("Finite positive SVG width and height are required")
    if "viewBox=" not in attrs:
        attrs += f' viewBox="0 0 {width.group(1)} {height.group(1)}"'
        text = text[: root.start()] + f"<svg{attrs}>" + text[root.end() :]

    counter = 0

    def add_id(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        tag = match.group(0)
        if re.search(r"\bid=", tag):
            return tag
        suffix = "/>" if tag.endswith("/>") else ">"
        return tag[: -len(suffix)] + f' id="vtracer-path-{counter:06d}"' + suffix

    text = re.sub(r"<path\b[^>]*>", add_id, text)
    if counter == 0:
        raise ValueError("SVG contains no paths")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".svg", dir=output.parent, delete=False
    ) as stream:
        temporary = Path(stream.name)
        stream.write(text)
    temporary.replace(output)
    return counter


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    count = normalize(args.input.resolve(), args.output.expanduser().resolve())
    print(f"OK|output={args.output.expanduser().resolve()}|paths={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
