"""High-level update orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from brave_updater.console import LogFn, prompt_yes_no
from brave_updater.download import sanitize_filename
from brave_updater.installers import get_installer
from brave_updater.models import ReleaseAsset, ReleaseInfo, SystemInfo, UpdateCheckResult
from brave_updater.network import download_file
from brave_updater.providers import (
    extract_chromium_version,
    pick_asset,
    resolve_expected_hash,
    resolve_provider,
)
from brave_updater.system import compare_versions, detect_installed_version, detect_system


class BraveUpdater:
    def __init__(self, source: str, log: LogFn):
        self.log = log
        self.provider = resolve_provider(source, log)

    def load_release(self) -> ReleaseInfo:
        return self.provider.fetch_latest_release()

    def _resolve_target(self) -> Tuple[SystemInfo, ReleaseInfo, ReleaseAsset, str]:
        system_info = detect_system()
        release = self.load_release()
        asset, reason = pick_asset(release.assets, system_info)
        return system_info, release, asset, reason

    def check(self) -> UpdateCheckResult:
        system_info, release, asset, reason = self._resolve_target()
        installed_version = detect_installed_version(system_info)
        latest_version = release.version.lstrip("v")
        update_available = installed_version is None or compare_versions(installed_version, latest_version) < 0
        return UpdateCheckResult(
            system=system_info,
            installed_version=installed_version,
            latest_version=latest_version,
            update_available=update_available,
            selected_asset=asset,
            selection_reason=reason,
            release_source=release.source,
            chromium_version=extract_chromium_version(release.body),
        )

    def download_latest(
        self,
        directory: Path,
        skip_verify: bool = False,
        force: bool = False,
    ) -> Path:
        _, release, asset, _ = self._resolve_target()
        expected_hash = None if skip_verify else resolve_expected_hash(asset, release, self.log)
        destination = directory / sanitize_filename(asset.name)
        return download_file(
            asset.url,
            destination,
            log=self.log,
            expected_hash=expected_hash,
            force=force,
        )

    def update(
        self,
        directory: Path,
        skip_verify: bool = False,
        force: bool = False,
        assume_yes: bool = False,
    ) -> Optional[Path]:
        system_info, release, asset, reason = self._resolve_target()
        installed_version = detect_installed_version(system_info)
        latest_version = release.version.lstrip("v")
        update_available = installed_version is None or compare_versions(installed_version, latest_version) < 0

        check = UpdateCheckResult(
            system=system_info,
            installed_version=installed_version,
            latest_version=latest_version,
            update_available=update_available,
            selected_asset=asset,
            selection_reason=reason,
            release_source=release.source,
            chromium_version=extract_chromium_version(release.body),
        )
        if not force and not check.update_available:
            self.log("Brave is already up to date ({}).".format(check.latest_version))
            return None

        expected_hash = None if skip_verify else resolve_expected_hash(check.selected_asset, release, self.log)
        destination = directory / sanitize_filename(check.selected_asset.name)
        download_file(
            check.selected_asset.url,
            destination,
            log=self.log,
            expected_hash=expected_hash,
            force=force,
        )

        if assume_yes or prompt_yes_no("Install {} now?".format(destination.name), default_no=True):
            installer = get_installer(check.system, self.log)
            installer.install(destination)
            self.log("Done.")
        else:
            self.log("Install skipped.")

        return destination

    def install(self, package_path: Path) -> None:
        installer = get_installer(detect_system(), self.log)
        installer.install(package_path)
