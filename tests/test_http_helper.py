import functools
import http.server
import threading
from pathlib import Path

import pytest

from pbp.util.http_helper import read_url_head


class _RangeHandler(http.server.SimpleHTTPRequestHandler):
    """Like SimpleHTTPRequestHandler, but honoring "Range: bytes=0-N" (as S3/GCS do)."""

    def do_GET(self):
        range_header = self.headers.get("Range")
        if range_header is None:
            return super().do_GET()
        data = Path(self.translate_path(self.path)).read_bytes()
        end = min(int(range_header.split("-")[1]), len(data) - 1)
        self.send_response(206)
        self.send_header("Content-Range", f"bytes 0-{end}/{len(data)}")
        self.send_header("Content-Length", str(end + 1))
        self.end_headers()
        self.wfile.write(data[: end + 1])

    def log_message(self, *args):
        pass


@pytest.fixture(params=[_RangeHandler, http.server.SimpleHTTPRequestHandler])
def base_url(request, tmp_path):
    """Serves tmp_path with and without Range support."""
    handler = functools.partial(request.param, directory=str(tmp_path))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.mark.parametrize("size", [50_000, 20_000, 500])
def test_read_url_head(base_url, tmp_path, size):
    data = bytes(i % 251 for i in range(size))
    (tmp_path / "f.bin").write_bytes(data)
    head, total = read_url_head(f"{base_url}/f.bin")
    assert head == data[:20_000]
    assert total == size
