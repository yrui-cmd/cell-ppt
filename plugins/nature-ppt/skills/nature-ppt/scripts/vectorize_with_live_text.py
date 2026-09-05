#!/usr/bin/env python3
"""Trace a text-cleaned image, then restore recorded text as live SVG text."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

from restore_live_text import restore

JPEG_SOF_MARKERS = {
    0xC0, 0xC1, 0xC2, 0xC3,
    0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB,
    0xCD, 0xCE, 0xCF,
}
JPEG_STANDALONE_MARKERS = {0x01, 0xD0, 0xD1, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9}


def image_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(32)
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return struct.unpack(">II", header[16:24])
        if header[:2] == b"\xff\xd8":
            stream.seek(2)
            while True:
                marker_start = stream.read(1)
                if not marker_start:
                    break
                if marker_start != b"\xff":
                    continue
                marker_raw = stream.read(1)
                while marker_raw == b"\xff":
                    marker_raw = stream.read(1)
                if not marker_raw:
                    break
                marker = marker_raw[0]
                if marker in JPEG_SOF_MARKERS:
                    length = struct.unpack(">H", stream.read(2))[0]
                    data = stream.read(length - 2)
                    return struct.unpack(">HH", data[1:5])[::-1]
                if marker in JPEG_STANDALONE_MARKERS:
                    continue
                length_raw = stream.read(2)
                if len(length_raw) != 2:
                    break
                stream.seek(struct.unpack(">H", length_raw)[0] - 2, 1)
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            kind = header[12:16]
            if kind == b"VP8X":
                return (1 + int.from_bytes(header[24:27], "little"), 1 + int.from_bytes(header[27:30], "little"))
            if kind == b"VP8L":
                bits = int.from_bytes(header[21:25], "little")
                return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
            if kind == b"VP8 " and header[23:26] == b"\x9d\x01\x2a":
                return (
                    int.from_bytes(header[26:28], "little") & 0x3FFF,
                    int.from_bytes(header[28:30], "little") & 0x3FFF,
                )
    raise ValueError(f"unsupported or unreadable image dimensions: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-input", required=True, type=Path, help="Untouched source image.")
    parser.add_argument("--cleaned-input", required=True, type=Path, help="Same-size image with text only removed.")
    parser.add_argument("--text-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cache-dir", type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source = args.source_input.expanduser().resolve(strict=True)
    cleaned = args.cleaned_input.expanduser().resolve(strict=True)
    manifest = args.text_manifest.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    if output.exists() and not args.force:
        raise ValueError(f"output already exists: {output}")
    if image_size(source) != image_size(cleaned):
        raise ValueError("source and text-cleaned images must have identical pixel dimensions")

    scripts = Path(__file__).resolve().parent
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nature-ppt-live-text-", dir=output.parent) as raw:
        traced = Path(raw) / "text-cleaned-trace.svg"
        command = [
            sys.executable,
            str(scripts / "vectorize.py"),
            "--input", str(cleaned),
            "--output", str(traced),
        ]
        if args.cache_dir:
            command.extend(["--cache-dir", str(args.cache_dir.expanduser().resolve())])
        process = subprocess.run(command, check=True, capture_output=True, text=True)
        trace_report = json.loads(process.stdout)
        restored = restore(traced, manifest, output, force=args.force)

    report = {
        "schema_version": "1.0",
        "status": "PASS",
        "source_input": str(source),
        "cleaned_input": str(cleaned),
        "source_dimensions": list(image_size(source)),
        "output": str(output),
        "paths": trace_report["paths"],
        "stable_ids": trace_report["stable_ids"],
        "raster_nodes": trace_report["raster_nodes"],
        "live_text_count": restored["live_text_count"],
        "warnings": restored["warnings"],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as error:
        print(f"TEXT_AWARE_TRACE_ERROR|{error}", file=sys.stderr)
        raise SystemExit(1)
