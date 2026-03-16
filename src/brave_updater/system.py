"""System detection and installed-version helpers."""

from __future__ import annotations

import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

from brave_updater.models import SystemInfo


def detect_linux_family(os_release_path: Path = Path("/etc/os-release")) -> str:
    if not os_release_path.exists():
        return "unknown"

    text = os_release_path.read_text(errors="ignore")
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"')

    distro_id = values.get("ID", "").lower()
    distro_like = values.get("ID_LIKE", "").lower()

    def contains_any(haystack: str, words: Sequence[str]) -> bool:
        return any(word in haystack for word in words)

    if contains_any(distro_id, ("debian", "ubuntu", "linuxmint", "pop")) or contains_any(distro_like, ("debian", "ubuntu")):
        return "debian"
    if contains_any(distro_id, ("fedora", "rhel", "centos", "rocky", "almalinux", "opensuse", "sles")) or contains_any(distro_like, ("rhel", "fedora", "suse")):
        return "rhel"
    if contains_any(distro_id, ("arch", "manjaro", "endeavouros")) or contains_any(distro_like, ("arch",)):
        return "arch"
    return "unknown"


def detect_system() -> SystemInfo:
    sys_platform = sys.platform.lower()
    machine = platform.machine().lower()

    if sys_platform.startswith("darwin"):
        os_name = "macos"
    elif sys_platform.startswith("win"):
        os_name = "windows"
    elif sys_platform.startswith("linux"):
        os_name = "linux"
    else:
        os_name = "unknown"

    if machine in ("arm64", "aarch64"):
        arch = "arm64"
    elif machine in ("x86_64", "amd64"):
        arch = "x64"
    elif machine in ("i386", "i686", "x86"):
        arch = "x86"
    else:
        arch = "unknown"

    linux_family = detect_linux_family() if os_name == "linux" else "unknown"
    return SystemInfo(os_name=os_name, arch=arch, linux_family=linux_family)


def parse_version_string(text: str) -> Optional[str]:
    match = re.search(r"(\d+(?:\.\d+)+)", text)
    if not match:
        return None
    return match.group(1)


def version_tuple(version: Optional[str]) -> Tuple[int, ...]:
    if not version:
        return tuple()
    parsed = parse_version_string(version) or version
    return tuple(int(part) for part in parsed.strip().lstrip("v").split(".") if part.isdigit())


def compare_versions(current: Optional[str], latest: Optional[str]) -> int:
    left = version_tuple(current)
    right = version_tuple(latest)
    max_len = max(len(left), len(right))
    padded_left = left + (0,) * (max_len - len(left))
    padded_right = right + (0,) * (max_len - len(right))
    if padded_left == padded_right:
        return 0
    if padded_left < padded_right:
        return -1
    return 1


def read_macos_version(plist_paths: Optional[Iterable[Path]] = None) -> Optional[str]:
    candidates = list(plist_paths or [
        Path("/Applications/Brave Browser.app/Contents/Info.plist"),
        Path.home() / "Applications/Brave Browser.app/Contents/Info.plist",
    ])
    for plist_path in candidates:
        if not plist_path.exists():
            continue
        with plist_path.open("rb") as handle:
            data = plistlib.load(handle)
        version = normalize_macos_app_version(
            data.get("CFBundleShortVersionString"),
            data.get("CFBundleVersion"),
        )
        if version:
            return str(version)
    return None


def normalize_macos_app_version(short_version: Optional[str], bundle_version: Optional[str]) -> Optional[str]:
    short_text = str(short_version) if short_version else None
    bundle_text = str(bundle_version) if bundle_version else None

    short_tuple = version_tuple(short_text)
    if short_tuple and short_tuple[0] >= 100 and bundle_text:
        match = re.fullmatch(r"(\d+)\.(\d+)", bundle_text)
        if match:
            major_minor, patch = match.groups()
            if len(major_minor) > 1:
                major = int(major_minor[0])
                minor = int(major_minor[1:])
                return "{}.{}.{}".format(major, minor, int(patch))

    if short_text:
        return short_text
    if bundle_text:
        return bundle_text
    return None


def read_linux_version(
    commands: Optional[Iterable[Sequence[str]]] = None,
    runner=subprocess.run,
    which=shutil.which,
) -> Optional[str]:
    for command in commands or (("brave-browser", "--version"), ("brave-browser-stable", "--version")):
        executable = command[0]
        if which(executable) is None:
            continue
        result = runner(command, capture_output=True, text=True, check=False)
        version = parse_version_string(result.stdout or result.stderr or "")
        if version:
            return version
    return None


def read_windows_version(
    executable_paths: Optional[Iterable[Path]] = None,
    runner=subprocess.run,
    powershell: str = "powershell",
) -> Optional[str]:
    candidates = list(executable_paths or [
        Path(os.environ.get("ProgramFiles", "")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
        Path(os.environ.get("ProgramFiles(x86)", "")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware/Brave-Browser/Application/brave.exe",
    ])
    for executable in candidates:
        if not executable.exists():
            continue
        command = [
            powershell,
            "-NoProfile",
            "-Command",
            "(Get-Item '{}').VersionInfo.ProductVersion".format(str(executable).replace("'", "''")),
        ]
        result = runner(command, capture_output=True, text=True, check=False)
        version = parse_version_string(result.stdout or result.stderr or "")
        if version:
            return version
    return None


def detect_installed_version(system_info: Optional[SystemInfo] = None) -> Optional[str]:
    info = system_info or detect_system()
    if info.os_name == "macos":
        return read_macos_version()
    if info.os_name == "linux":
        return read_linux_version()
    if info.os_name == "windows":
        return read_windows_version()
    return None
