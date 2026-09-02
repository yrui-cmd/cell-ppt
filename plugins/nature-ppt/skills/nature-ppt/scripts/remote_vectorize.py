#!/usr/bin/env python3
"""Send a raster image to an optional HTTPS vectorization service."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from normalize_svg import normalize
from validate_vector_svg import audit_svg


MAX_RESPONSE_BYTES = 256 * 1024 * 1024


def read_token(path: Path | None) -> str | None:
    candidate = path or (Path(os.environ["NATURE_PPT_VECTOR_TOKEN_FILE"]) if os.environ.get("NATURE_PPT_VECTOR_TOKEN_FILE") else None)
    if not candidate:
        return None
    token = candidate.expanduser().resolve(strict=True).read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("remote token file is empty")
    return token


def extract_svg(payload: bytes, content_type: str) -> bytes:
    if "json" in content_type.lower():
        parsed = json.loads(payload.decode("utf-8"))
        value = parsed.get("svg") if isinstance(parsed, dict) else None
        if not isinstance(value, str):
            raise ValueError("remote JSON response must contain an svg string")
        payload = value.encode("utf-8")
    if b"<svg" not in payload[:4096]:
        raise ValueError("remote response is not an SVG document")
    return payload


def vectorize_remote(
    source: Path,
    output: Path,
    endpoint: str,
    token_file: Path | None = None,
    profile: str = "editable",
    timeout: int = 180,
    allow_http_localhost: bool = False,
) -> dict:
    parsed = urllib.parse.urlparse(endpoint)
    local_http = parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme != "https" and not (allow_http_localhost and local_http):
        raise ValueError("remote vectorization requires HTTPS; HTTP is allowed only for an explicitly enabled localhost test")
    source = source.expanduser().resolve(strict=True)
    output = output.expanduser().resolve()
    payload = source.read_bytes()
    headers = {
        "Content-Type": "application/octet-stream",
        "Accept": "image/svg+xml, application/json",
        "User-Agent": "nature-ppt/0.5",
        "X-Nature-PPT-Profile": profile,
        "X-Source-Filename": source.name,
    }
    token = read_token(token_file)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            result = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"remote vectorization returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"remote vectorization could not connect: {exc.reason}") from exc
    if len(result) > MAX_RESPONSE_BYTES:
        raise ValueError("remote SVG exceeds the 256 MB safety limit")
    svg = extract_svg(result, content_type)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nature-ppt-remote-", dir=output.parent) as raw:
        raw_svg = Path(raw) / "response.svg"
        raw_svg.write_bytes(svg)
        normalize(raw_svg, output)
    audit = audit_svg(output, strict_ids=True, allow_raster=False)
    if audit["status"] != "PASS":
        output.unlink(missing_ok=True)
        raise ValueError("remote SVG failed structural validation: " + "; ".join(audit["errors"]))
    return {
        "schema_version": "1.0",
        "status": "PASS",
        "backend": "remote",
        "endpoint_host": parsed.hostname,
        "profile": profile,
        "output": str(output),
        "vector_element_count": audit["vector_element_count"],
        "raster_node_count": audit["raster_node_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--endpoint", default=os.environ.get("NATURE_PPT_VECTOR_URL"))
    parser.add_argument("--token-file", type=Path)
    parser.add_argument("--profile", choices=("editable", "maximum-fidelity"), default="editable")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--allow-http-localhost", action="store_true")
    args = parser.parse_args()
    if not args.endpoint:
        raise SystemExit("remote endpoint is not configured")
    report = vectorize_remote(
        args.input,
        args.output,
        args.endpoint,
        args.token_file,
        args.profile,
        args.timeout,
        args.allow_http_localhost,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
