# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Updated repository ownership references to `HackEAC/braver-tz`
- Removed Brave-logo-based branding from the documentation and repository root

## [1.1.0] - 2026-03-16

### Added
- Packaged Python CLI with `pyproject.toml`, `setup.py`, and `src/brave_updater/`
- `brave-updater` console entrypoint
- Explicit `check`, `download`, `update`, and `install` commands
- Installed-version detection for macOS, Linux, and Windows
- Unit tests for provider logic, version detection, download safety, and CLI compatibility
- Deterministic CI workflow across Linux, macOS, and Windows
- Release workflow for building and publishing wheels/sdists
- Live smoke workflow for read-only endpoint validation
- Homebrew formula starter files and repository transfer checklist docs

### Changed
- Retained `python3 braver.py ...` as a compatibility wrapper instead of the primary implementation
- Reworked download logic to use resumable `.part` files and atomic final replacement
- Added redirect validation against allowed hosts
- Added safer macOS app replacement flow using staged copies
- Updated documentation to describe the new CLI and the `HackEAC` ownership path

### Fixed
- Resume downloads no longer append corrupt data when a server ignores `Range` and returns a full `200`
- Version comparisons now treat `1.2.3` and `1.2.3.0` as equivalent

## [1.0.0] - 2024-12-19

### Added
- Cross-platform Python script to download latest stable Brave Browser from GitHub Releases
- Automatic OS detection (macOS, Windows, Linux)
- Automatic CPU architecture detection (x64, ARM64, x86)
- Linux distribution family detection (Debian-based, RHEL-based, Arch-based)
- Intelligent installer selection:
  - `.dmg` / `.pkg` for macOS
  - `.exe` for Windows
  - `.deb` for Debian-based Linux distributions
  - `.rpm` for RHEL-based Linux distributions
- Download functionality with progress indication
- Optional installation step via `--install` flag
- `--print-only` flag to output download URL for automation
- `--dir` flag to specify custom download directory
- GitHub API token support via `GITHUB_TOKEN`
- Basic macOS, Windows, and Linux installation support
- Uses only Python standard library
