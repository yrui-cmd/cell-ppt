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

    target = subprocess.run(
        [sys.executable, str(SCRIPTS / "bootstrap_vtracer.py"), "--print-target"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(target.stdout)["sha256"]
    subprocess.run([sys.executable, str(SCRIPTS / "vectorize.py"), "--help"], check=True, capture_output=True)
    print("NATURE_PPT_OK|profile=maximum-fidelity|normalization=true|download_target=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
