"""Helpers for rendering package-manager distribution files."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Dict


DEFAULT_REPOSITORY = "HackEAC/braver-tz"
WINDOWS_ZIP_NAME = "brave-updater-windows-x64.zip"


def normalize_version(version: str) -> str:
    return version.lstrip("v").strip()


def source_distribution_name(version: str) -> str:
    return "brave_updater-{}.tar.gz".format(normalize_version(version))


def windows_distribution_name() -> str:
    return WINDOWS_ZIP_NAME


def release_asset_url(repository: str, version: str, filename: str) -> str:
    clean_version = normalize_version(version)
    return "https://github.com/{}/releases/download/v{}/{}".format(repository, clean_version, filename)


def sha256_for_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def render_homebrew_formula(version: str, repository: str, source_sha256: str) -> str:
    clean_version = normalize_version(version)
    source_name = source_distribution_name(clean_version)
    source_url = release_asset_url(repository, clean_version, source_name)
    return """class BraveUpdater < Formula
  include Language::Python::Virtualenv

  desc "Unofficial CLI to download and update Brave Browser from Brave-controlled release sources"
  homepage "https://github.com/{repository}"
  version "{version}"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{{bin}}/brave-updater --help")
    assert_match "update", output
  end
end
""".format(repository=repository, version=clean_version, url=source_url, sha256=source_sha256)


def render_scoop_manifest(version: str, repository: str, windows_sha256: str) -> str:
    clean_version = normalize_version(version)
    url = release_asset_url(repository, clean_version, windows_distribution_name())
    payload = {
        "version": clean_version,
        "description": "Unofficial CLI to download and update Brave Browser from Brave-controlled release sources.",
        "homepage": "https://github.com/{}".format(repository),
        "license": "MIT",
        "url": url,
        "hash": windows_sha256,
        "bin": "brave-updater.exe",
        "checkver": {
            "github": "https://github.com/{}".format(repository),
        },
        "autoupdate": {
            "url": "https://github.com/{}/releases/download/v$version/{}".format(repository, windows_distribution_name()),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=False) + "\n"


def write_distribution_files(
    output_dir: Path,
    version: str,
    repository: str,
    source_sha256: str,
    windows_sha256: str,
) -> Dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    homebrew_dir = output_dir / "homebrew"
    scoop_dir = output_dir / "scoop"
    homebrew_dir.mkdir(parents=True, exist_ok=True)
    scoop_dir.mkdir(parents=True, exist_ok=True)

    homebrew_formula = homebrew_dir / "brave-updater.rb"
    homebrew_formula.write_text(render_homebrew_formula(version, repository, source_sha256))

    scoop_manifest = scoop_dir / "brave-updater.json"
    scoop_manifest.write_text(render_scoop_manifest(version, repository, windows_sha256))

    return {
        "homebrew": homebrew_formula,
        "scoop": scoop_manifest,
    }
