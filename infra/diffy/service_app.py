#!/usr/bin/env python3
"""Tiny HTTP service used by the Diffy shadow-testing example.

The primary and secondary instances return the same business payload but with
different timestamps, which gives Diffy a harmless noise signal to suppress.
The candidate instance intentionally changes the schema so the proxy can flag
the regression.
"""

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


def build_search_response(query: str, variant: str):
    """Simulates a search engine response."""
    results = [
        {"id": "trail-01", "name": "Trailhead XT V1", "tags": ["outdoor", "running"]},
        {"id": "trail-02", "name": "Mountain Master", "tags": ["hiking", "waterproof"]}
    ]
    
    # Intentional 'Fix' Simulation: Candidate returns more relevant results
    if variant == "candidate":
        results.append({"id": "trail-03", "name": "Hydro-Shield Pro", "tags": ["waterproof", "trail"]})
    
    return {
        "status": "success",
        "query": query,
        "variant": variant,
        "results_count": len(results),
        "results": results,
        "latency_ms": 45.2 if variant != "candidate" else 55.8, # Candidate is slower (to trigger latency check)
        "generated_at": time.time()
    }

class DiffyDemoHandler(BaseHTTPRequestHandler):
    server_version = "MagellanSearchMock/1.0"

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        variant = os.getenv("SERVICE_VARIANT", "primary")

        if parsed.path == "/search":
            query = "waterproof trail shoes" # Simplified for demo
            self._send_json(200, build_search_response(query, variant))
            return
        
        self._send_json(404, {"status": "error", "message": "use /search"})


def main() -> None:
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), DiffyDemoHandler)
    print(f"listening on :{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
