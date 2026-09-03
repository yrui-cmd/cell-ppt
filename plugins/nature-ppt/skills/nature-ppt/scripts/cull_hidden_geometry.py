#!/usr/bin/env python3
"""Remove exact duplicate drawing paths from a Nature PPT cache."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import prepare_geometry_cache as cache_builder


def signature(atom):
    payload = {
        "kind": atom.get("kind"),
        "subpaths": atom.get("subpaths"),
        "paintParts": atom.get("paintParts"),
        "text": atom.get("text"),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def write_json(path, payload):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True)
    parser.add_argument("--state", required=True)
    args = parser.parse_args()

    cache_path = Path(args.cache).resolve()
    state_path = Path(args.state).resolve()
    cache = json.loads(cache_path.read_text(encoding="utf-8-sig"))
    state = json.loads(state_path.read_text(encoding="utf-8-sig"))
    source_atoms = cache.get("atoms", [])
    # Keep compound paths intact. The OOXML renderer can place many disjoint
    # subpaths inside one editable custom-geometry shape, which is the main
    # object-count reduction used by light-native mode.
    atoms = source_atoms
    source_drawing_paths = sum(max(1, len(atom.get("subpaths") or [])) for atom in source_atoms)
    keep = [True] * len(atoms)
    seen = set()
    culled = []

    for position in range(len(atoms) - 1, -1, -1):
        atom = atoms[position]
        if atom.get("kind") == "text":
            continue
        atom_signature = signature(atom)
        if atom_signature in seen:
            keep[position] = False
            culled.append({"position": position, "source_index": atom.get("index"), "reason": "exact_duplicate"})
            continue
        seen.add(atom_signature)

    kept_atoms = [atom for index, atom in enumerate(atoms) if keep[index]]
    if not kept_atoms:
        raise ValueError("Duplicate-path filtering removed every atom")
    batches = cache_builder.build_batches(
        kept_atoms,
        str(cache["job_id"]),
        int(cache["min_batch_size"]),
        int(cache["max_batch_size"]),
        int(cache["complex_point_threshold"]),
        int(cache["max_batch_points"]),
    )
    cache_builder.validate_batch_contract(
        batches,
        kept_atoms,
        int(cache["min_batch_size"]),
        int(cache["max_batch_size"]),
        int(cache["complex_point_threshold"]),
    )
    cache["source_total_atoms"] = len(source_atoms)
    cache["source_total_drawing_paths"] = source_drawing_paths
    cache["culled_atom_count"] = len(atoms) - len(kept_atoms)
    cache["culled_atoms"] = sorted(culled, key=lambda item: item["position"])
    cache["atoms"] = kept_atoms
    cache["total_atoms"] = len(kept_atoms)
    cache["batches"] = batches
    write_json(cache_path, cache)

    state["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["total_atoms"] = len(kept_atoms)
    state["cache_sha256"] = sha256_file(cache_path)
    state["batches"] = [
        {
            "index": batch["index"],
            "group_name": batch["group_name"],
            "atom_indices": batch["atom_indices"],
            "atomic_count": batch["atomic_count"],
            "kind": batch["kind"],
            "completed": False,
            "completed_at": None,
            "attempts": 0,
            "last_error": None,
        }
        for batch in batches
    ]
    write_json(state_path, state)
    print(json.dumps({
        "ok": True,
        "source_atoms": len(source_atoms),
        "source_drawing_paths": source_drawing_paths,
        "kept_atoms": len(kept_atoms),
        "culled_atoms": len(atoms) - len(kept_atoms),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
