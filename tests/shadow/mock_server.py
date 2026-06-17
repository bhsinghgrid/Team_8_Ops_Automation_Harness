"""
mock_server.py — Threaded mock HTTP server simulating OCS Search API.

Routing logic
~~~~~~~~~~~~~
The real OCS API reads an ``X-OCS-Route`` header and returns results from
the matching backend (baseline-a, baseline-b, or candidate).

This server does the same: it reads the routing header and returns the
product list configured for the active scenario.

Usage (standalone):
    from tests.shadow.mock_server import MockOCSServer
    server = MockOCSServer(port=8765, routes={...})
    server.start()
    ...
    server.stop()

Or use as a context manager:
    with MockOCSServer(port=8765, routes=scenario["routes"]) as srv:
        # run your evaluator here
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List

from feedback_agent.config import OCS_SHADOW_ROUTING_HEADER


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------
class _OCSHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the mock OCS Search endpoint."""

    # Injected by MockOCSServer before starting
    routes: Dict[str, List[str]] = {}

    def do_POST(self):
        if self.path != "/search-api/v1/search":
            self.send_response(404)
            self.end_headers()
            return

        route = self.headers.get(OCS_SHADOW_ROUTING_HEADER, "baseline-a")
        products = self.routes.get(route, [])

        results = [{"id": pid} for pid in products]
        body = json.dumps({"results": results}).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default per-request stdout noise
        route = self.headers.get(OCS_SHADOW_ROUTING_HEADER, "?") if hasattr(self, "headers") else "?"
        print(f"  [MockServer] {args[0]}  route={route}")


# ---------------------------------------------------------------------------
# Server wrapper
# ---------------------------------------------------------------------------
class MockOCSServer:
    """
    Starts a real HTTP server on localhost that mimics the OCS Search API.

    Parameters
    ----------
    port:
        TCP port to listen on. Pick any free port (default 8765).
    routes:
        Mapping of route header value → ordered list of product ID strings.
        Example::
            {
                "baseline-a": ["sku-001", "sku-002"],
                "baseline-b": ["sku-001", "sku-002"],
                "candidate":  ["sku-001", "sku-002", "sku-003"],
            }
    """

    def __init__(self, port: int, routes: Dict[str, List[str]]):
        self.port = port
        self.routes = routes
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        # Build a handler subclass that carries the route data
        routes = self.routes

        class BoundHandler(_OCSHandler):
            pass

        BoundHandler.routes = routes  # type: ignore[attr-defined]

        self._server = HTTPServer(("127.0.0.1", self.port), BoundHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"  [MockServer] Listening on http://127.0.0.1:{self.port}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server = None
        print(f"  [MockServer] Stopped (port {self.port})")

    # Context manager support
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *_):
        self.stop()
