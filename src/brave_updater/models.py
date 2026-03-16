"""Data models for brave_updater."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class SystemInfo:
    os_name: str
    arch: str
    linux_family: str = "unknown"


@dataclass(frozen=True)
class ReleaseAsset:
    name: str
    url: str
    digest: Optional[str] = None


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    name: str
    body: str
    assets: List[ReleaseAsset]
    source: str = "github"

    def find_asset(self, asset_name: str) -> Optional[ReleaseAsset]:
        for asset in self.assets:
            if asset.name == asset_name:
                return asset
        return None


@dataclass(frozen=True)
class UpdateCheckResult:
    system: SystemInfo
    installed_version: Optional[str]
    latest_version: str
    update_available: bool
    selected_asset: ReleaseAsset
    selection_reason: str
    release_source: str
    chromium_version: Optional[str] = None
