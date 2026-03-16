import hashlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from brave_updater.network import download_file, partial_download_path


CONTENT = b"brave-updater-test-payload" * 128


class DownloadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/resume-ignored":
            self.send_response(200)
            self.send_header("Content-Length", str(len(CONTENT)))
            self.end_headers()
            self.wfile.write(CONTENT)
            return

        if self.path == "/resume-supported":
            header = self.headers.get("Range")
            if header and header.startswith("bytes="):
                start = int(header.split("=", 1)[1].split("-", 1)[0])
                body = CONTENT[start:]
                self.send_response(206)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Content-Range", "bytes {}-{}/{}".format(start, len(CONTENT) - 1, len(CONTENT)))
                self.end_headers()
                self.wfile.write(body)
                return

        self.send_response(200)
        self.send_header("Content-Length", str(len(CONTENT)))
        self.end_headers()
        self.wfile.write(CONTENT)

    def log_message(self, format: str, *args) -> None:
        return


class FakeResponse:
    def __init__(self, final_url: str) -> None:
        self.status = 200
        self.headers = {"Content-Length": "3"}
        self._final_url = final_url
        self._sent = False

    def geturl(self) -> str:
        return self._final_url

    def read(self, size: int = -1) -> bytes:
        if self._sent:
            return b""
        self._sent = True
        return b"abc"

    def close(self) -> None:
        return

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class DownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DownloadHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = "http://127.0.0.1:{}".format(cls.server.server_port)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_resume_ignored_restarts_from_zero(self) -> None:
        checksum = hashlib.sha256(CONTENT).hexdigest()
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "brave-browser.zip"
            partial = partial_download_path(dest)
            partial.write_bytes(CONTENT[:32])

            download_file(
                self.base_url + "/resume-ignored",
                dest,
                log=lambda message: None,
                expected_hash=checksum,
                allowed_domains={"127.0.0.1", "localhost"},
            )

            self.assertEqual(dest.read_bytes(), CONTENT)
            self.assertFalse(partial.exists())

    def test_resume_supported_keeps_partial_and_finishes(self) -> None:
        checksum = hashlib.sha256(CONTENT).hexdigest()
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "brave-browser.zip"
            partial = partial_download_path(dest)
            partial.write_bytes(CONTENT[:64])

            download_file(
                self.base_url + "/resume-supported",
                dest,
                log=lambda message: None,
                expected_hash=checksum,
                allowed_domains={"127.0.0.1", "localhost"},
            )

            self.assertEqual(dest.read_bytes(), CONTENT)

    def test_rejects_disallowed_redirect_target(self) -> None:
        with TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "blocked.zip"
            with mock.patch("urllib.request.urlopen", return_value=FakeResponse("https://example.com/file.zip")):
                with self.assertRaises(RuntimeError):
                    download_file(
                        "https://github.com/example/file.zip",
                        dest,
                        log=lambda message: None,
                        max_retries=1,
                    )


if __name__ == "__main__":
    unittest.main()
