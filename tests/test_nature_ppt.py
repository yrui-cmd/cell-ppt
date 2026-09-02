#!/usr/bin/env python3
"""Deterministic tests for tracing, routing, live text, and remote SVG validation."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import threading
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugins" / "nature-ppt" / "skills" / "nature-ppt"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SvgHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        payload = b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="10" viewBox="0 0 20 10"><path id="remote-path" d="M0 0H20V10H0Z" fill="#fff"/></svg>'
        self.send_response(200)
        self.send_header("Content-Type", "image/svg+xml")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_):
        return


def main() -> int:
    profile = json.loads((SKILL / "references" / "fidelity-profile.json").read_text(encoding="utf-8"))
    assert profile["engine"]["version"] == "1.0.0-alpha.4"
    assert profile["profile"]["arguments"][profile["profile"]["arguments"].index("--mode") + 1] == "pixel"
    preflight = load("preflight_image")
    normalizer = load("normalize_svg")
    restorer = load("restore_live_text")
    remote = load("remote_vectorize")

    with tempfile.TemporaryDirectory(prefix="nature-ppt-test-") as raw:
        temp = Path(raw)
        flat = temp / "flat.png"
        image = Image.new("RGB", (240, 120), "white")
        drawing = ImageDraw.Draw(image)
        drawing.rectangle((20, 20, 100, 100), fill="#1aa6a6")
        drawing.rectangle((130, 30, 220, 90), fill="#ff805f")
        image.save(flat)
        assert preflight.analyze(flat)["recommended_mode"] == "native"

        gradient = temp / "gradient.png"
        gradient_image = Image.new("RGB", (400, 300))
        pixels = gradient_image.load()
        for y in range(300):
            for x in range(400):
                pixels[x, y] = (x * 255 // 399, y * 255 // 299, (x + y) * 255 // 698)
        gradient_image.save(gradient)
        assert preflight.analyze(gradient)["recommended_mode"] == "hybrid"

        raw_svg = temp / "raw.svg"
        normalized = temp / "normalized.svg"
        raw_svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="8"><path d="M0 0H12V8H0Z" fill="#fff"/></svg>',
            encoding="utf-8",
        )
        assert normalizer.normalize(raw_svg, normalized) == 1
        assert ET.parse(normalized).getroot().attrib["viewBox"] == "0 0 12 8"
        master = temp / "master.svg"
        report = restorer.restore(normalized, ROOT / "tests" / "fixtures" / "nature-text-manifest.json", master)
        assert report["live_text_count"] == 1

        server = ThreadingHTTPServer(("127.0.0.1", 0), SvgHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            remote_svg = temp / "remote.svg"
            remote_report = remote.vectorize_remote(
                flat,
                remote_svg,
                f"http://127.0.0.1:{server.server_port}/vectorize",
                allow_http_localhost=True,
            )
            assert remote_report["status"] == "PASS" and remote_report["vector_element_count"] == 1
        finally:
            server.shutdown()
            server.server_close()

    print("NATURE_PPT_OK|preflight=true|live_text=true|remote_contract=true|local_profile=pinned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
