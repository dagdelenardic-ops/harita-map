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
import urllib.parse
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


def _accepts_gzip(header_value: str) -> bool:
    return "gzip" in (header_value or "").lower()


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
