"""Platform-specific installer adapters."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Protocol

from brave_updater.console import LogFn
from brave_updater.models import SystemInfo


class Installer(Protocol):
    def install(self, package_path: Path) -> None:
        raise NotImplementedError


class MacOSInstaller:
    def __init__(self, log: LogFn):
        self.log = log

    def install(self, package_path: Path) -> None:
        if not package_path.exists():
            raise FileNotFoundError("Install file not found: {}".format(package_path))

        suffix = package_path.suffix.lower()
        if suffix == ".pkg":
            self.log("Installing .pkg via macOS installer...")
            subprocess.check_call(["sudo", "installer", "-pkg", str(package_path), "-target", "/"], timeout=600)
            self.log("Install finished.")
            return

        if suffix != ".dmg":
            raise RuntimeError("macOS install expects .dmg or .pkg")

        mountpoint = Path("/Volumes/BraveTmpMount")
        mounted = False
        try:
            if mountpoint.exists():
                subprocess.run(["hdiutil", "detach", str(mountpoint), "-quiet"], capture_output=True, timeout=5, check=False)

            mountpoint.mkdir(parents=True, exist_ok=True)
            self.log("Mounting DMG...")
            subprocess.check_call(
                ["hdiutil", "attach", str(package_path), "-mountpoint", str(mountpoint), "-nobrowse", "-quiet"],
                timeout=60,
            )
            mounted = True

            app_path = mountpoint / "Brave Browser.app"
            if not app_path.exists():
                apps = list(mountpoint.glob("*.app"))
                if not apps:
                    raise RuntimeError("Could not find .app inside the DMG")
                app_path = apps[0]

            target = Path("/Applications") / app_path.name
            with tempfile.TemporaryDirectory(prefix="brave-updater-") as temp_dir:
                staged_app = Path(temp_dir) / app_path.name
                self.log("Staging application bundle...")
                subprocess.check_call(["cp", "-R", str(app_path), str(staged_app)], timeout=300)

                temp_target = Path("/Applications") / (app_path.name + ".new")
                if temp_target.exists():
                    subprocess.check_call(["sudo", "rm", "-rf", str(temp_target)], timeout=30)
                subprocess.check_call(["sudo", "cp", "-R", str(staged_app), str(temp_target)], timeout=300)
                _replace_macos_app_bundle(target, temp_target)

            self.log("Brave copied to /Applications.")
        finally:
            if mounted:
                self.log("Unmounting DMG...")
                for _ in range(3):
                    try:
                        subprocess.run(["hdiutil", "detach", str(mountpoint), "-quiet"], timeout=10, capture_output=True, check=False)
                        break
                    except Exception:
                        time.sleep(1)


class WindowsInstaller:
    def __init__(self, log: LogFn):
        self.log = log

    def install(self, package_path: Path) -> None:
        if not package_path.exists():
            raise FileNotFoundError("Install file not found: {}".format(package_path))
        self.log("Launching installer...")
        os.startfile(str(package_path))  # type: ignore[attr-defined]


class LinuxInstaller:
    def __init__(self, log: LogFn, family: str):
        self.log = log
        self.family = family

    def install(self, package_path: Path) -> None:
        if not package_path.exists():
            raise FileNotFoundError("Install file not found: {}".format(package_path))

        if self.family not in {"debian", "rhel"}:
            raise RuntimeError(
                "Unsupported Linux distribution family: {}. Only Debian-like and RHEL-like systems are supported.".format(
                    self.family
                )
            )

        suffix = package_path.suffix.lower()
        if suffix == ".deb":
            self.log("Installing .deb package...")
            if shutil.which("apt-get"):
                subprocess.check_call(["sudo", "apt-get", "install", "-y", str(package_path)], timeout=600)
            else:
                subprocess.check_call(["sudo", "dpkg", "-i", str(package_path)], timeout=600)
            self.log("Install finished.")
            return

        if suffix == ".rpm":
            self.log("Installing .rpm package...")
            if shutil.which("dnf"):
                subprocess.check_call(["sudo", "dnf", "install", "-y", str(package_path)], timeout=600)
            elif shutil.which("yum"):
                subprocess.check_call(["sudo", "yum", "install", "-y", str(package_path)], timeout=600)
            else:
                subprocess.check_call(["sudo", "rpm", "-Uvh", str(package_path)], timeout=600)
            self.log("Install finished.")
            return

        raise RuntimeError("Unsupported Linux installer: {} ({})".format(package_path.name, self.family))


def get_installer(system_info: SystemInfo, log: LogFn) -> Installer:
    if system_info.os_name == "macos":
        return MacOSInstaller(log)
    if system_info.os_name == "windows":
        return WindowsInstaller(log)
    if system_info.os_name == "linux":
        return LinuxInstaller(log, system_info.linux_family)
    raise RuntimeError("Unsupported operating system: {}".format(system_info.os_name))


def _replace_macos_app_bundle(target: Path, temp_target: Path) -> None:
    """Replace an app bundle while preserving a rollback path on failure."""
    if not target.exists():
        subprocess.check_call(["sudo", "mv", str(temp_target), str(target)], timeout=60)
        return

    backup_target = Path("/Applications") / (target.name + ".old")
    if backup_target.exists():
        subprocess.check_call(["sudo", "rm", "-rf", str(backup_target)], timeout=30)

    subprocess.check_call(["sudo", "mv", str(target), str(backup_target)], timeout=60)
    try:
        subprocess.check_call(["sudo", "mv", str(temp_target), str(target)], timeout=60)
    except Exception as exc:
        try:
            subprocess.check_call(["sudo", "mv", str(backup_target), str(target)], timeout=60)
        except Exception as restore_exc:
            raise RuntimeError(
                "Failed to replace {} and restore the previous Brave app. Backup remains at {}.".format(
                    target, backup_target
                )
            ) from restore_exc
        raise RuntimeError("Failed to replace {}; restored the previous Brave app.".format(target)) from exc

    subprocess.check_call(["sudo", "rm", "-rf", str(backup_target)], timeout=30)
