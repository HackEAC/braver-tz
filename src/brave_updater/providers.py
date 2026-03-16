"""Release-provider implementations and asset selection."""

from __future__ import annotations

import re
from typing import List, Optional, Protocol, Tuple

from brave_updater.console import LogFn
from brave_updater.models import ReleaseAsset, ReleaseInfo, SystemInfo
from brave_updater.network import http_get_json, http_get_text


GITHUB_API_LATEST = "https://api.github.com/repos/brave/brave-browser/releases/latest"


class ReleaseProvider(Protocol):
    source_name: str

    def fetch_latest_release(self) -> ReleaseInfo:
        raise NotImplementedError


class GitHubReleaseProvider:
    source_name = "github"

    def fetch_latest_release(self) -> ReleaseInfo:
        payload = http_get_json(GITHUB_API_LATEST)
        return release_from_payload(payload, source=self.source_name)


class OfficialReleaseProvider(GitHubReleaseProvider):
    source_name = "official-github"


def resolve_provider(source: str, log: LogFn) -> ReleaseProvider:
    normalized = source.lower()
    if normalized == "github":
        return GitHubReleaseProvider()
    if normalized in ("official", "auto"):
        log("Using Brave's official GitHub release feed for source={!r}.".format(source))
        return OfficialReleaseProvider()
    raise ValueError("Unsupported source: {}".format(source))


def validate_release_data(payload: dict) -> None:
    required_fields = ("tag_name", "assets")
    for field in required_fields:
        if field not in payload:
            raise ValueError("Invalid release payload: missing {}".format(field))
    if not isinstance(payload["assets"], list):
        raise ValueError("Invalid release payload: assets must be a list")


def release_from_payload(payload: dict, source: str) -> ReleaseInfo:
    validate_release_data(payload)
    assets: List[ReleaseAsset] = []
    for raw_asset in payload["assets"]:
        if not isinstance(raw_asset, dict):
            raise ValueError("Invalid release payload: asset must be a mapping")
        name = raw_asset.get("name")
        url = raw_asset.get("browser_download_url")
        if not name or not url:
            raise ValueError("Invalid release payload: asset missing name or URL")
        assets.append(
            ReleaseAsset(
                name=name,
                url=url,
                digest=raw_asset.get("digest"),
            )
        )
    return ReleaseInfo(
        version=str(payload.get("tag_name", "")),
        name=str(payload.get("name", "")),
        body=str(payload.get("body", "")),
        assets=assets,
        source=source,
    )


def pick_asset(assets: List[ReleaseAsset], system_info: SystemInfo) -> Tuple[ReleaseAsset, str]:
    """Pick the best installer asset for the current platform."""
    names = [asset.name for asset in assets]

    def find(predicate) -> Optional[ReleaseAsset]:
        for asset in assets:
            name = asset.name.lower()
            if predicate(name):
                return asset
        return None

    if system_info.os_name == "macos":
        asset = find(lambda name: name.endswith(".dmg") and "universal" in name)
        if asset:
            return asset, "macOS: chose universal .dmg"
        if system_info.arch == "arm64":
            asset = find(lambda name: name.endswith(".dmg") and ("arm64" in name or "aarch64" in name))
            if asset:
                return asset, "macOS ARM: chose arm64 .dmg"
        if system_info.arch == "x64":
            asset = find(lambda name: name.endswith(".dmg") and ("x64" in name or "amd64" in name or "x86_64" in name))
            if asset:
                return asset, "macOS Intel: chose x64 .dmg"
        asset = find(lambda name: name.endswith(".dmg"))
        if asset:
            return asset, "macOS: chose first available .dmg"
        asset = find(lambda name: name.endswith(".pkg"))
        if asset:
            return asset, "macOS: chose .pkg (no .dmg found)"

    if system_info.os_name == "windows":
        asset = find(lambda name: name.endswith(".exe") and "standalone" in name and "setup" in name)
        if asset:
            return asset, "Windows: chose StandaloneSetup.exe (offline installer)"
        asset = find(lambda name: name.endswith(".exe") and "setup" in name)
        if asset:
            return asset, "Windows: chose Setup.exe"
        asset = find(lambda name: name.endswith(".exe"))
        if asset:
            return asset, "Windows: chose first available .exe"

    if system_info.os_name == "linux":
        arch_tokens: List[str] = []
        if system_info.arch == "x64":
            arch_tokens = ["amd64", "x86_64"]
        elif system_info.arch == "arm64":
            arch_tokens = ["arm64", "aarch64"]

        if system_info.linux_family == "debian":
            for token in arch_tokens:
                asset = find(lambda name, item=token: name.endswith(".deb") and item in name)
                if asset:
                    return asset, "Linux Debian-like: chose .deb matching {}".format(token)
            asset = find(lambda name: name.endswith(".deb"))
            if asset:
                return asset, "Linux Debian-like: chose first available .deb"

        if system_info.linux_family == "rhel":
            for token in arch_tokens:
                asset = find(lambda name, item=token: name.endswith(".rpm") and item in name)
                if asset:
                    return asset, "Linux RHEL-like: chose .rpm matching {}".format(token)
            asset = find(lambda name: name.endswith(".rpm"))
            if asset:
                return asset, "Linux RHEL-like: chose first available .rpm"

        asset = find(lambda name: name.endswith(".deb"))
        if asset:
            return asset, "Linux: fallback to .deb"
        asset = find(lambda name: name.endswith(".rpm"))
        if asset:
            return asset, "Linux: fallback to .rpm"
        asset = find(lambda name: name.endswith(".zip") or name.endswith(".tar.gz"))
        if asset:
            return asset, "Linux: fallback to archive"

    raise RuntimeError(
        "Could not find a suitable asset for {}. Assets seen: {}".format(system_info, names[:30])
    )


def extract_chromium_version(body: str) -> Optional[str]:
    match = re.search(r"Chromium:\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", body)
    if match:
        return match.group(1)
    return None


def parse_sha256_digest(digest: Optional[str]) -> Optional[str]:
    if digest and digest.startswith("sha256:"):
        return digest.split(":", 1)[1]
    return None


def parse_checksum_text(text: str, asset_name: str) -> Optional[str]:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(r"([a-fA-F0-9]{64})\s+[* ]?(.+)$", line)
        if not match:
            continue
        checksum, name = match.groups()
        if name.strip() == asset_name:
            return checksum.lower()
    return None


def resolve_expected_hash(asset: ReleaseAsset, release: ReleaseInfo, log: LogFn) -> Optional[str]:
    digest = parse_sha256_digest(asset.digest)
    if digest:
        return digest

    checksum_asset = release.find_asset(asset.name + ".sha256")
    if not checksum_asset:
        checksum_asset = release.find_asset(asset.name + ".sha256.txt")
    if not checksum_asset:
        return None

    log("Fetching checksum sidecar for {}...".format(asset.name))
    checksum_text = http_get_text(checksum_asset.url)
    return parse_checksum_text(checksum_text, asset.name)
