#!/usr/bin/env python3
"""Deterministic tests for the Nature PPT skill."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "cell-ppt" / "skills" / "nature-ppt"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    profile = json.loads((SKILL / "references" / "fidelity-profile.json").read_text(encoding="utf-8"))
    assert profile["engine"]["version"] == "1.0.0-alpha.4"
    arguments = profile["profile"]["arguments"]
    assert arguments[arguments.index("--mode") + 1] == "pixel"
    assert profile["reference_benchmark"]["ssim"] > 0.99
    assert all(
        len(asset["sha256"]) == 64 and len(asset["binary_sha256"]) == 64
        for asset in profile["assets"].values()
    )

    normalizer = load_module("normalize_svg", SCRIPTS / "normalize_svg.py")
    restorer = load_module("restore_live_text", SCRIPTS / "restore_live_text.py")
    text_aware = load_module("vectorize_with_live_text", SCRIPTS / "vectorize_with_live_text.py")
    with tempfile.TemporaryDirectory(prefix="nature-ppt-test-") as raw:
        temp = Path(raw)
        source = temp / "raw.svg"
        output = temp / "normalized.svg"
        source.write_text(
            '<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg" width="12" height="8">'
            '<path d="M0 0H12V8H0Z" fill="#fff"/><path d="M1 1H2V2H1Z" fill="#000"/></svg>',
            encoding="utf-8",
        )
        assert normalizer.normalize(source, output) == 2
        root = ET.parse(output).getroot()
        assert root.attrib["viewBox"] == "0 0 12 8"
        paths = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "path"]
        assert [path.attrib["id"] for path in paths] == ["vtracer-path-000001", "vtracer-path-000002"]

        master = temp / "master.svg"
        restore_report = restorer.restore(
            output,
            ROOT / "tests" / "fixtures" / "nature-text-manifest.json",
            master,
        )
        assert restore_report["status"] == "PASS"
        assert restore_report["live_text_count"] == 1
        assert not restore_report["warnings"]
        master_root = ET.parse(master).getroot()
        assert not any(node.tag.rsplit("}", 1)[-1] == "image" for node in master_root.iter())
        live_text = [
            node for node in master_root.iter()
            if node.tag.rsplit("}", 1)[-1] == "text"
            and node.attrib.get("data-nature-ppt-live-text") == "true"
        ]
        assert len(live_text) == 1 and live_text[0].text == "Eₐ"

        png = temp / "size.png"
        png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (12).to_bytes(4, "big") + (8).to_bytes(4, "big"))
        assert text_aware.image_size(png) == (12, 8)
        jpeg = temp / "size.jpg"
        jpeg.write_bytes(b"\xff\xd8\xff\xc0\x00\x0b\x08\x00\x08\x00\x0c\x01\x01\x11\x00")
        assert text_aware.image_size(jpeg) == (12, 8)
        webp = temp / "size.webp"
        webp.write_bytes(
            b"RIFF" + (22).to_bytes(4, "little") + b"WEBPVP8X" + (10).to_bytes(4, "little")
            + b"\x00\x00\x00\x00" + (11).to_bytes(3, "little") + (7).to_bytes(3, "little")
        )
        assert text_aware.image_size(webp) == (12, 8)
        mismatched = temp / "mismatched.png"
        mismatched.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + (13).to_bytes(4, "big") + (8).to_bytes(4, "big"))
        mismatch = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "vectorize_with_live_text.py"),
                "--source-input", str(png),
                "--cleaned-input", str(mismatched),
                "--text-manifest", str(ROOT / "tests" / "fixtures" / "nature-text-manifest.json"),
                "--output", str(temp / "must-not-exist.svg"),
            ],
            capture_output=True,
            text=True,
        )
        assert mismatch.returncode != 0
        assert "identical pixel dimensions" in mismatch.stderr

    target = subprocess.run(
        [sys.executable, str(SCRIPTS / "bootstrap_vtracer.py"), "--print-target"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(target.stdout)["sha256"]
    subprocess.run([sys.executable, str(SCRIPTS / "vectorize.py"), "--help"], check=True, capture_output=True)
    subprocess.run([sys.executable, str(SCRIPTS / "vectorize_with_live_text.py"), "--help"], check=True, capture_output=True)
    print("NATURE_PPT_OK|profile=maximum-fidelity|normalization=true|live_text=true|download_target=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
