#!/usr/bin/env python3
"""Run non-mutating Nature PPT diagnostics."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import subprocess
import sys
from pathlib import Path


LOCKED = {"python-pptx": "1.0.2", "fonttools": "4.61.1", "shapely": "2.1.2", "Pillow": "10.4.0"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check-vectorizer", action="store_true")
    args = parser.parse_args()
    if not ((3, 10) <= sys.version_info[:2] < (3, 15)):
        raise SystemExit("Python 3.10-3.14 is required.")
    root = Path(__file__).resolve().parent
    skill = root / "plugins" / "nature-ppt" / "skills" / "nature-ppt"
    required = [
        skill / "SKILL.md",
        skill / "scripts" / "preflight_image.py",
        skill / "scripts" / "run_pipeline.py",
        skill / "scripts" / "reconstruct_from_svg.ps1",
        skill / "scripts" / "render_pptx_ooxml.py",
        skill / "scripts" / "remote_vectorize.py",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("Missing: " + ", ".join(missing))
    versions = {name: importlib.metadata.version(name) for name in LOCKED}
    if versions != LOCKED:
        raise SystemExit(f"Locked dependency mismatch: {versions}")
    runtime = subprocess.run(
        [sys.executable, str(skill / "scripts" / "configure_runtime.py"), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    profile = json.loads(runtime.stdout)
    vectorizer_ready = None
    if args.check_vectorizer:
        checked = subprocess.run(
            [sys.executable, str(skill / "scripts" / "bootstrap_vtracer.py"), "--no-download"],
            capture_output=True,
            text=True,
        )
        vectorizer_ready = checked.returncode == 0
    result = {
        "ok": True,
        "skill": "nature-ppt",
        "platform": platform.system().lower(),
        "backend": profile["backend"],
        "powerPointRegistered": profile["powerPointRegistered"],
        "localVectorizerChecked": args.check_vectorizer,
        "localVectorizerCached": vectorizer_ready,
        "remoteBackendOptional": True,
        "apiKeyRequired": False,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")) if args.json else "DOCTOR_OK|" + "|".join(f"{key}={str(value).lower()}" for key, value in result.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
