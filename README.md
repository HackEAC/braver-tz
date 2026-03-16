# brave-updater

`brave-updater` is an unofficial cross-platform CLI for checking, downloading, and updating Brave Browser from Brave-controlled release sources.

This project is intended for environments where the usual Brave installation flow is inconvenient or blocked, but GitHub-hosted Brave releases are still reachable.

Important:
- This project is not affiliated with or endorsed by Brave Software.
- It does not rehost Brave binaries.
- It downloads Brave installers directly from Brave-controlled GitHub release assets at runtime.
- Homebrew already ships the official macOS `brave-browser` cask. This project is a separate updater/downloader CLI, not a replacement for that cask.

## Current status

- Packaged Python CLI with a `src/` layout and console entrypoint: `brave-updater`
- Backward-compatible wrapper retained: `python3 braver.py ...`
- True updater behavior:
  - Detects installed Brave version when possible
  - Compares it to the latest stable release
  - Skips update work when the installed version is already current
- Cross-platform installer selection:
  - macOS: `.dmg` / `.pkg`
  - Windows: `.exe`
  - Linux: `.deb` / `.rpm` on Debian-like and RHEL-like systems
- Safer downloads:
  - SHA256 verification
  - redirect host validation
  - temp-file download + atomic replace
  - safe recovery when resume requests are ignored

## Repository transfer

The canonical repository is now `HackEAC/braver-tz`.

Post-transfer notes:
- keep `origin` pointed at `git@github.com:HackEAC/braver-tz.git`
- do not recreate the previous repository path after the transfer, because that would break GitHub's redirect
- follow the post-transfer checklist in [`docs/repository-transfer.md`](docs/repository-transfer.md)

## Installation

### From source

```bash
git clone git@github.com:HackEAC/braver-tz.git
cd braver-tz
python3 -m pip install .
```

After installation:

```bash
brave-updater check
```

### Legacy wrapper

You can still use the old entrypoint directly from the repo:

```bash
python3 braver.py --print-only
python3 braver.py --install
```

### Homebrew tap

The intended tap command once the tap is published is:

```bash
brew install HackEAC/brave-updater/brave-updater
```

The starter formula and tap notes live under [`packaging/homebrew`](packaging/homebrew).

## Usage

### Check installed vs latest version

```bash
brave-updater check
brave-updater check --json
```

### Download the latest installer

```bash
brave-updater download
brave-updater download --dir ~/Downloads
```

### Update only when needed

```bash
brave-updater update
brave-updater update --yes
```

### Install a package you already downloaded

```bash
brave-updater install /path/to/Brave-Browser-universal.dmg
```

### Source strategy

`brave-updater` currently defaults to GitHub Releases because that is the supported product direction for this project.

Available source modes:
- `github`
- `official`
- `auto`

At the moment, `official` and `auto` resolve through Brave's official GitHub release feed. The code is structured so distinct official non-GitHub providers can be added later without redesigning the CLI.

### Linux support

Linux installs are currently supported on:
- Debian-like distributions
- RHEL-like distributions

Arch-like and other unsupported Linux families fail fast with a clear error instead of downloading the wrong package format.

## Development

Run the test suite:

```bash
python3 -m unittest discover -v
```

Build distributions:

```bash
python3 -m pip install build
python3 -m build
```

## CI and release flow

- CI runs deterministic unit tests on Linux, macOS, and Windows.
- A scheduled smoke workflow hits the live Brave release endpoint with read-only checks.
- Tagging `v*` builds and uploads sdist/wheel artifacts to GitHub Releases.

## Legal and policy notes

- This project should avoid Brave logos and branded artwork unless you have explicit permission.
- The project should continue to present itself as unofficial and non-affiliated.
- The project should continue to download installers from Brave-controlled endpoints rather than mirror them.

## License

MIT. See [`LICENSE`](LICENSE).
