"""Network and download helpers."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.error import HTTPError, URLError
import shutil

from brave_updater import __version__
from brave_updater.console import LogFn


DEFAULT_ALLOWED_DOMAINS = {
    "github.com",
    "githubusercontent.com",
}
USER_AGENT = "brave-updater/{}".format(__version__)


def validate_url(url: str, allowed_domains: Optional[Iterable[str]] = None) -> bool:
    """Validate a URL against the allowlist."""
    allowed = tuple((allowed_domains or DEFAULT_ALLOWED_DOMAINS))
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower().split(":", 1)[0]
        return any(domain == item or domain.endswith("." + item) for item in allowed)
    except Exception:
        return False


def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """Verify a file SHA256 hash."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest().lower() == expected_hash.lower().strip()


def http_get_text(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    max_retries: int = 3,
) -> str:
    """Fetch text content with retry logic."""
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)

    last_error = None
    for attempt in range(max_retries):
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (URLError, socket.timeout, socket.error, UnicodeDecodeError) as exc:
            last_error = exc
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError("Failed to fetch {}: {}".format(url, last_error))


def http_get_json(url: str, timeout: int = 30, max_retries: int = 3) -> Dict[str, Any]:
    """Fetch JSON from an API endpoint."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        token = token.strip()
        if token and "\n" not in token and " " not in token:
            headers["Authorization"] = "Bearer {}".format(token)

    text = http_get_text(url, headers=headers, timeout=timeout, max_retries=max_retries)
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object from {}".format(url))
    return payload


def partial_download_path(dest: Path) -> Path:
    """Return the sidecar path used for resumable downloads."""
    return dest.parent / (dest.name + ".part")


def _extract_total_size(content_range: Optional[str], content_length: int, resume_pos: int) -> int:
    if content_range:
        parts = content_range.rsplit("/", 1)
        if len(parts) == 2 and parts[1].isdigit():
            return int(parts[1])
    if content_length > 0:
        return content_length + resume_pos
    return 0


def download_file(
    url: str,
    dest: Path,
    log: LogFn,
    expected_hash: Optional[str] = None,
    timeout: int = 60,
    max_retries: int = 3,
    force: bool = False,
    allowed_domains: Optional[Iterable[str]] = None,
) -> Path:
    """Download a file safely with checksum verification and resumable partials."""
    if not validate_url(url, allowed_domains=allowed_domains):
        raise ValueError("URL not from allowed domain: {}".format(url))

    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = partial_download_path(dest)

    if force:
        if dest.exists():
            dest.unlink()
        if partial.exists():
            partial.unlink()

    if dest.exists() and not force:
        if expected_hash:
            if verify_file_hash(dest, expected_hash):
                log("Using existing verified download: {}".format(dest))
                return dest
            log("Existing file checksum mismatch, re-downloading: {}".format(dest))
        else:
            log("Using existing download: {}".format(dest))
            return dest

    free_bytes = shutil.disk_usage(dest.parent).free
    if free_bytes < 500 * 1024 * 1024:
        raise RuntimeError("Insufficient disk space: need at least 500MB free")

    last_error = None
    for attempt in range(max_retries):
        resume_pos = partial.stat().st_size if partial.exists() else 0
        headers = {}
        if resume_pos > 0:
            headers["Range"] = "bytes={}-".format(resume_pos)
            log("Resuming download from byte {}...".format(resume_pos))

        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                final_url = response.geturl()
                if not validate_url(final_url, allowed_domains=allowed_domains):
                    raise ValueError("Redirected to disallowed host: {}".format(final_url))

                status = getattr(response, "status", 200)
                if resume_pos > 0 and status == 200:
                    log("Server ignored resume request, restarting from byte 0...")
                    partial.unlink()
                    resume_pos = 0
                    request = urllib.request.Request(url)
                    response.close()
                    with urllib.request.urlopen(request, timeout=timeout) as fresh_response:
                        final_url = fresh_response.geturl()
                        if not validate_url(final_url, allowed_domains=allowed_domains):
                            raise ValueError("Redirected to disallowed host: {}".format(final_url))
                        _write_download_stream(
                            fresh_response,
                            partial,
                            dest,
                            log,
                            expected_hash=expected_hash,
                            resume_pos=resume_pos,
                        )
                        return dest

                _write_download_stream(
                    response,
                    partial,
                    dest,
                    log,
                    expected_hash=expected_hash,
                    resume_pos=resume_pos,
                )
                return dest
        except HTTPError as exc:
            last_error = exc
            if exc.code == 416 and partial.exists():
                log("Partial download no longer matches remote file, restarting...")
                partial.unlink()
                continue
            if attempt < max_retries - 1:
                log("Download attempt {} failed: {}. Retrying...".format(attempt + 1, exc))
                time.sleep(2 ** attempt)
        except (URLError, socket.timeout, socket.error, OSError, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt < max_retries - 1:
                log("Download attempt {} failed: {}. Retrying...".format(attempt + 1, exc))
                time.sleep(2 ** attempt)

    raise RuntimeError("Failed to download {} after {} attempts: {}".format(url, max_retries, last_error))


def _write_download_stream(
    response: Any,
    partial: Path,
    dest: Path,
    log: LogFn,
    expected_hash: Optional[str],
    resume_pos: int,
) -> None:
    content_length = int(response.headers.get("Content-Length", 0) or 0)
    total = _extract_total_size(response.headers.get("Content-Range"), content_length, resume_pos)
    mode = "ab" if resume_pos > 0 else "wb"
    log("Downloading:\n  {}\n-> {}".format(response.geturl(), dest))

    read = resume_pos
    with partial.open(mode) as handle:
        while True:
            chunk = response.read(1024 * 256)
            if not chunk:
                break
            handle.write(chunk)
            read += len(chunk)
            if total:
                pct = (read / total) * 100
                print("\r{:6.2f}% ({}/{})".format(pct, read, total), end="", flush=True)
    if total:
        print()

    actual_size = partial.stat().st_size
    if total and actual_size != total:
        raise RuntimeError("Size mismatch: expected {}, got {}".format(total, actual_size))

    if expected_hash:
        log("Verifying download integrity...")
        if not verify_file_hash(partial, expected_hash):
            raise RuntimeError("Download integrity check failed")
        log("Integrity check passed.")

    partial.replace(dest)
    log("Download complete.")
