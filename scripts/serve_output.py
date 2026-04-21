#!/usr/bin/env python3
"""
Serve output/ as a static site with gzip sidecar support.

Simple `python -m http.server` does not gzip. Cloud Run does not gzip for you, so large
HTML/JSON payloads can intermittently fail on mobile/Chrome networks. This server:
- Serves precompressed <file>.gz when client accepts gzip
- Sets Content-Encoding + Vary headers
- Adds conservative Cache-Control for static assets
"""

from __future__ import annotations

import mimetypes
import os
import json
import subprocess
import time
import urllib.parse
import urllib.error
import urllib.request
from collections import defaultdict, deque
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Any, Optional


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
PRIMARY_HOST = os.environ.get("PRIMARY_HOST", "jeopolitik.com.tr")
REDIRECT_WWW_HOST = os.environ.get("REDIRECT_WWW_HOST", f"www.{PRIMARY_HOST}")

VERTEX_SEARCH_ENABLED = os.environ.get("VERTEX_SEARCH_ENABLED", "1").lower() not in {"0", "false", "no"}
VERTEX_PROJECT = os.environ.get("VERTEX_PROJECT", "project-2d4834e6-d656-4df9-909")
VERTEX_LOCATION = os.environ.get("VERTEX_LOCATION", "global")
VERTEX_COLLECTION = os.environ.get("VERTEX_COLLECTION", "default_collection")
VERTEX_ENGINE = os.environ.get("VERTEX_ENGINE", "jeopolitik-search")
VERTEX_SEARCH_URL = (
    f"https://discoveryengine.googleapis.com/v1/projects/{VERTEX_PROJECT}"
    f"/locations/{VERTEX_LOCATION}/collections/{VERTEX_COLLECTION}"
    f"/engines/{VERTEX_ENGINE}/servingConfigs/default_search:search"
)

SEARCH_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("SEARCH_RATE_LIMIT_WINDOW_SECONDS", "60"))
SEARCH_RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("SEARCH_RATE_LIMIT_MAX_REQUESTS", "30"))
SEARCH_CACHE_TTL_SECONDS = int(os.environ.get("SEARCH_CACHE_TTL_SECONDS", "60"))

_search_cache: dict[tuple[str, int], tuple[float, dict[str, Any]]] = {}
_search_cache_lock = Lock()
_rate_limit_hits: dict[str, deque[float]] = defaultdict(deque)
_rate_limit_lock = Lock()


def _accepts_gzip(header_value: str) -> bool:
    return "gzip" in (header_value or "").lower()


def _get_access_token() -> Optional[str]:
    metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
    try:
        req = urllib.request.Request(metadata_url, headers={"Metadata-Flavor": "Google"})
        with urllib.request.urlopen(req, timeout=2) as resp:
            return json.loads(resp.read()).get("access_token")
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None

    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _client_key(handler: SimpleHTTPRequestHandler) -> str:
    forwarded_for = handler.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    return handler.client_address[0] if handler.client_address else "unknown"


def _rate_limited(client: str) -> bool:
    now = time.monotonic()
    with _rate_limit_lock:
        hits = _rate_limit_hits[client]
        while hits and now - hits[0] > SEARCH_RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= SEARCH_RATE_LIMIT_MAX_REQUESTS:
            return True
        hits.append(now)
    return False


def _cached_search(query: str, page_size: int) -> Optional[dict[str, Any]]:
    key = (query.lower(), page_size)
    now = time.monotonic()
    with _search_cache_lock:
        cached = _search_cache.get(key)
        if cached and now - cached[0] <= SEARCH_CACHE_TTL_SECONDS:
            return cached[1]
        if cached:
            _search_cache.pop(key, None)
    return None


def _store_cached_search(query: str, page_size: int, payload: dict[str, Any]) -> None:
    key = (query.lower(), page_size)
    with _search_cache_lock:
        _search_cache[key] = (time.monotonic(), payload)


def _run_vertex_search(query: str, page_size: int) -> tuple[int, dict[str, Any]]:
    access_token = _get_access_token()
    if not access_token:
        return HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Vertex AI Search kimlik dogrulamasi hazir degil."}

    search_body = json.dumps(
        {
            "query": query,
            "pageSize": page_size,
            "queryExpansionSpec": {"condition": "AUTO"},
            "spellCorrectionSpec": {"mode": "AUTO"},
            "contentSearchSpec": {
                "snippetSpec": {"returnSnippet": True},
                "summarySpec": {
                    "summaryResultCount": 3,
                    "languageCode": "tr",
                },
            },
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        VERTEX_SEARCH_URL,
        data=search_body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        return HTTPStatus.BAD_GATEWAY, {"error": f"Vertex Search {exc.code}", "detail": detail}
    except Exception as exc:
        return HTTPStatus.BAD_GATEWAY, {"error": str(exc)}

    results = []
    for result in data.get("results", []):
        document = result.get("document", {})
        struct_data = document.get("structData", {})
        snippets = document.get("derivedStructData", {}).get("snippets", [])
        snippet = ""
        if snippets:
            snippet = snippets[0].get("snippet") or snippets[0].get("htmlSnippet") or ""
        results.append(
            {
                **struct_data,
                "snippet": snippet,
                "score": result.get("rankSignals", {}).get("semanticSimilarityScore", 0),
            }
        )

    payload = {
        "query": query,
        "total": len(results),
        "summary": data.get("summary", {}).get("summaryText", ""),
        "results": results,
    }
    _store_cached_search(query, page_size, payload)
    return HTTPStatus.OK, payload


class GzipStaticHandler(SimpleHTTPRequestHandler):
    # Make logging less noisy on Cloud Run.
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        if os.environ.get("QUIET_LOGS") == "1":
            return
        super().log_message(format, *args)

    def end_headers(self) -> None:
        # Always vary on Accept-Encoding when we might serve gzip.
        self.send_header("Vary", "Accept-Encoding")
        super().end_headers()

    def _cache_control(self, path: str) -> str:
        # Keep HTML relatively fresh; cache other static assets longer.
        p = path.lower()
        if p.endswith((".html", ".htm", "/")):
            return "public, max-age=60"
        if p.endswith((".json", ".xml", ".txt")):
            return "public, max-age=300"
        return "public, max-age=86400"

    def _send_file(self, fs_path: Path, ctype: str, *, gzip_encoded: bool) -> Optional[object]:
        try:
            st = fs_path.stat()
            f = fs_path.open("rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(st.st_size))
        self.send_header("Last-Modified", self.date_time_string(st.st_mtime))
        self.send_header("Cache-Control", self._cache_control(self.path))
        if gzip_encoded:
            self.send_header("Content-Encoding", "gzip")
        self.end_headers()
        return f

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _maybe_redirect_primary_host(self) -> bool:
        host = (self.headers.get("Host") or "").split(":", 1)[0].strip().lower()
        if not host or host != REDIRECT_WWW_HOST.lower():
            return False
        self.send_response(HTTPStatus.MOVED_PERMANENTLY)
        self.send_header("Location", f"https://{PRIMARY_HOST}{self.path}")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        return True

    def _handle_search(self, parsed: urllib.parse.SplitResult) -> None:
        if not VERTEX_SEARCH_ENABLED:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "Arama gecici olarak kapali."})
            return

        client = _client_key(self)
        if _rate_limited(client):
            self._send_json(HTTPStatus.TOO_MANY_REQUESTS, {"error": "Cok fazla arama istegi."})
            return

        params = urllib.parse.parse_qs(parsed.query)
        query = (params.get("q") or [""])[0].strip()
        if len(query) < 2:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "q parametresi en az 2 karakter olmali."})
            return
        if len(query) > 200:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "q parametresi en fazla 200 karakter olabilir."})
            return

        try:
            page_size = int((params.get("limit") or ["10"])[0])
        except ValueError:
            page_size = 10
        page_size = max(1, min(page_size, 20))

        cached = _cached_search(query, page_size)
        if cached:
            self._send_json(HTTPStatus.OK, cached)
            return

        status, payload = _run_vertex_search(query, page_size)
        self._send_json(status, payload)

    def do_GET(self) -> None:
        if self._maybe_redirect_primary_host():
            return
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/api/search":
            self._handle_search(parsed)
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if self._maybe_redirect_primary_host():
            return
        super().do_HEAD()

    def do_OPTIONS(self) -> None:
        if self._maybe_redirect_primary_host():
            return
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/api/search":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Allow", "GET, OPTIONS")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return
        self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Unsupported method")

    def send_head(self):  # noqa: ANN001
        # Mostly copied from SimpleHTTPRequestHandler.send_head, with gzip sidecar support.
        path = self.translate_path(self.path)
        fs_path = Path(path)

        if fs_path.is_dir():
            parts = urllib.parse.urlsplit(self.path)
            if not parts.path.endswith("/"):
                # Redirect browser to include trailing slash.
                self.send_response(HTTPStatus.MOVED_PERMANENTLY)
                new_parts = (parts.scheme, parts.netloc, parts.path + "/", parts.query, parts.fragment)
                self.send_header("Location", urllib.parse.urlunsplit(new_parts))
                self.end_headers()
                return None

            for index in ("index.html", "index.htm"):
                index_path = fs_path / index
                if index_path.exists():
                    fs_path = index_path
                    break
            else:
                return self.list_directory(str(fs_path))

        # If client accepts gzip and we have a sidecar, serve it.
        accept = self.headers.get("Accept-Encoding", "")
        if _accepts_gzip(accept):
            gz_path = Path(str(fs_path) + ".gz")
            if gz_path.exists():
                ctype = mimetypes.guess_type(str(fs_path))[0] or "application/octet-stream"
                return self._send_file(gz_path, ctype, gzip_encoded=True)

        ctype = self.guess_type(str(fs_path))
        return self._send_file(fs_path, ctype, gzip_encoded=False)


def main() -> None:
    port = int(os.environ.get("PORT") or "8080")
    directory = os.environ.get("STATIC_DIR") or str(OUTPUT_DIR)
    if not Path(directory).exists():
        raise SystemExit(f"static dir not found: {directory}")

    # Ensure handler serves from the output directory.
    handler = lambda *args, **kwargs: GzipStaticHandler(*args, directory=directory, **kwargs)  # noqa: E731
    httpd = ThreadingHTTPServer(("", port), handler)
    print(f"Serving {directory} on 0.0.0.0:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
