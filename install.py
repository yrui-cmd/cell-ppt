#!/usr/bin/env python3
"""Cross-platform Cell_ppt skill installer."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = Path(__file__).resolve().parent
    source_root = project / "plugins" / "cell-ppt" / "skills"
    skill_names = ("cell-ppt", "cell-ppt-fidelity")
    target_root = args.destination.expanduser().resolve()
    for skill_name in skill_names:
        source = source_root / skill_name
        if not source.is_dir():
            raise SystemExit(f"Plugin skill directory is missing: {source}")
        target = target_root / skill_name
        if target.exists() and not args.force:
            raise SystemExit(f"Skill already exists: {target}. Re-run with --force only if replacement is intended.")
    target_root.mkdir(parents=True, exist_ok=True)
    for skill_name in skill_names:
        source = source_root / skill_name
        target = target_root / skill_name
        if target.exists():
            if target.is_symlink():
                target.unlink()
            else:
                shutil.rmtree(target)
        shutil.copytree(
            source,
            target,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        print(f"INSTALLED|skill={skill_name}|destination={target}|copy=true")
    target = target_root / "cell-ppt"
    subprocess.run(
        [sys.executable, str(target / "scripts" / "configure_runtime.py"), "--output", str(target / "runtime-profile.json")],
        check=True,
    )
    print("Restart Codex and start a new task before first use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
