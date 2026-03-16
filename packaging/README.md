# Packaging

This directory contains packaging assets and release-channel notes for `brave-updater`.

## Current channels

- `PyPI`
- `Homebrew`
- `Windows portable zip`
- `Scoop`
- `WinGet` submission notes

Linux users can use Homebrew on Linux or Python package managers such as `pipx`, so there is no separate distro-specific Linux packaging here right now.

## Layout

- `homebrew/`: tap template and notes
- `pypi/`: PyPI release notes
- `scoop/`: Scoop manifest template and notes
- `winget/`: WinGet submission notes
- `windows/`: Windows portable build entrypoint and notes

## Release outputs

On each tagged release, the release workflow should publish:

- `brave_updater-<version>.tar.gz`
- `brave_updater-<version>-py3-none-any.whl`
- `brave-updater-windows-x64.zip`
- `SHA256SUMS.txt`
- rendered Homebrew formula
- rendered Scoop manifest

## Cross-repo sync

The Homebrew tap and Scoop bucket live in separate repositories:

- `HackEAC/homebrew-brave-updater`
- `HackEAC/scoop-bucket`

`HackEAC/braver-tz` can notify both repos immediately after a tagged release by using the `PACKAGING_SYNC_TOKEN` repository secret. Without that secret, the external repos still poll the latest release on a 6-hour schedule.
