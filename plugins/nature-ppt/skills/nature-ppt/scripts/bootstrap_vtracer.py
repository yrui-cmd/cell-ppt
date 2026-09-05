#!/usr/bin/env python3
"""Download and verify the pinned VTracer binary for the current platform."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
CONTRACT = SKILL_ROOT / "references" / "fidelity-profile.json"


def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def platform_key() -> str:
    os_name = {"win32": "windows", "darwin": "macos"}.get(
        sys.platform, "linux" if sys.platform.startswith("linux") else ""
    )
    machine = platform.machine().lower()
    arch = "aarch64" if machine in {"arm64", "aarch64"} else "x86_64" if machine in {"amd64", "x86_64"} else ""
    if not os_name or not arch:
        raise RuntimeError(f"Unsupported platform: {sys.platform}/{machine}")
    return f"{os_name}-{arch}"


def default_cache() -> Path:
    if sys.platform == "win32" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "nature-ppt"
    base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "nature-ppt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_members(names: list[str]) -> None:
    for name in names:
        candidate = Path(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise RuntimeError(f"Unsafe archive member: {name}")


def extract(archive: Path, destination: Path) -> None:
    if archive.suffix.lower() == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            safe_members(bundle.namelist())
            bundle.extractall(destination)
    else:
        with tarfile.open(archive, "r:gz") as bundle:
            members = bundle.getmembers()
            safe_members([member.name for member in members])
            bundle.extractall(destination, members=members, filter="data")


def resolve_binary(cache_dir: Path, download: bool = True) -> tuple[Path, dict]:
    contract = load_contract()
    key = platform_key()
    asset = contract["assets"].get(key)
    if not asset:
        raise RuntimeError(f"No pinned VTracer asset for {key}")
    version = contract["engine"]["version"]
    target = cache_dir.expanduser().resolve() / version / key
    executable = target / ("vtracer.exe" if key.startswith("windows-") else "vtracer")
    metadata = {"platform": key, "version": version, **asset}
    if executable.is_file():
        actual_binary = sha256(executable)
        if actual_binary.lower() != asset["binary_sha256"].lower():
            raise RuntimeError(
                f"Cached VTracer checksum mismatch: expected {asset['binary_sha256']}, got {actual_binary}"
            )
        return executable, metadata
    if not download:
        raise FileNotFoundError(f"Pinned VTracer is not cached: {executable}")

    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nature-ppt-", dir=target.parent) as raw_temp:
        temp = Path(raw_temp)
        archive = temp / asset["filename"]
        base_url = contract["engine"]["release_base_url"].rstrip("/")
        request = urllib.request.Request(
            f"{base_url}/{asset['filename']}", headers={"User-Agent": "nature-ppt"}
        )
        with urllib.request.urlopen(request, timeout=120) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        actual = sha256(archive)
        if actual.lower() != asset["sha256"].lower():
            raise RuntimeError(f"VTracer checksum mismatch: expected {asset['sha256']}, got {actual}")
        unpacked = temp / "unpacked"
        unpacked.mkdir()
        extract(archive, unpacked)
        found = next((path for path in unpacked.rglob(executable.name) if path.is_file()), None)
        if not found:
            raise RuntimeError(f"VTracer executable was not found in {asset['filename']}")
        actual_binary = sha256(found)
        if actual_binary.lower() != asset["binary_sha256"].lower():
            raise RuntimeError(
                f"VTracer binary checksum mismatch: expected {asset['binary_sha256']}, got {actual_binary}"
            )
        target.mkdir(parents=True, exist_ok=False)
        shutil.copy2(found, executable)
    if os.name != "nt":
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return executable, metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, default=default_cache())
    parser.add_argument("--no-download", action="store_true")
    parser.add_argument("--print-target", action="store_true", help="Print pinned target metadata without downloading")
    args = parser.parse_args()
    if args.print_target:
        contract = load_contract()
        key = platform_key()
        print(
            json.dumps(
                {"platform": key, "version": contract["engine"]["version"], **contract["assets"][key]},
                ensure_ascii=False,
            )
        )
        return 0
    executable, metadata = resolve_binary(args.cache_dir, download=not args.no_download)
    print(json.dumps({"status": "PASS", "executable": str(executable), **metadata}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
