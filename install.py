#!/usr/bin/env python3
"""Install only the Nature PPT skill while preserving its local configuration."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path


PRESERVE = ("runtime-profile.json", "remote-backend.json")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    source = project / "plugins" / "nature-ppt" / "skills" / "nature-ppt"
    if not source.is_dir():
        raise SystemExit(f"skill directory is missing: {source}")
    target_root = args.destination.expanduser().resolve()
    target = target_root / "nature-ppt"
    if target.exists() and not args.force:
        raise SystemExit(f"skill already exists: {target}. Use --force only when replacement is intended.")
    target_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nature-ppt-install-", dir=target_root) as raw:
        staged = Path(raw) / "nature-ppt"
        shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        if target.is_dir():
            for name in PRESERVE:
                existing = target / name
                if existing.is_file():
                    shutil.copy2(existing, staged / name)
        backup = Path(raw) / "previous"
        if target.exists():
            target.rename(backup)
        try:
            staged.rename(target)
        except Exception:
            if backup.exists() and not target.exists():
                backup.rename(target)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    print(f"INSTALLED|skill=nature-ppt|destination={target}|preserved_config=true")
    print("Restart Codex and start a new task before first use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
