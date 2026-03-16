# brave-updater

`brave-updater` is an unofficial cross-platform CLI for checking, downloading, and updating Brave Browser from Brave-controlled release sources.

It is meant for situations where the normal Brave install flow is inconvenient, blocked, or harder to automate.

Important:
- This project is not affiliated with or endorsed by Brave Software.
- It does not bundle or mirror Brave binaries.
- It downloads Brave installers directly from Brave-controlled release assets at runtime.

## Install

### Homebrew

Available now on macOS and Linux with Homebrew:

```bash
brew tap HackEAC/brave-updater
brew install HackEAC/brave-updater/brave-updater
```

### Scoop

Available now on Windows with Scoop:

```powershell
scoop bucket add hackeac https://github.com/HackEAC/scoop-bucket
scoop install brave-updater
```

### PyPI

Coming soon. Once the PyPI publisher approval is complete, the intended install flows will be:

```bash
pipx install brave-updater
```

or:

```bash
python3 -m pip install brave-updater
```

Until PyPI is live, use Homebrew, Scoop, or install from source.

### From source

```bash
git clone git@github.com:HackEAC/braver-tz.git
cd braver-tz
python3 -m pip install .
```

### Legacy wrapper

The original entrypoint still works from the repository:

```bash
python3 braver.py --print-only
python3 braver.py --install
```

### Release channels

This repository now includes release packaging for:

- `Homebrew`
- `Scoop`
- `PyPI` / `pipx` coming soon
- Windows portable releases for `WinGet`

Release-channel notes and packaging assets live in [packaging/README.md](/Users/maotora/Projects/brave-updater/packaging/README.md).

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

## Platform notes

- macOS: `.dmg` and `.pkg` installers are supported
- Windows: `.exe` installers are supported
- Linux: `.deb` and `.rpm` installers are supported on Debian-like and RHEL-like systems

Unsupported Linux families fail fast instead of downloading the wrong package type.

## Development

Run the test suite:

```bash
python3 -m unittest discover -v
```

Build Python distributions:

```bash
python3 -m pip install build
python3 -m build
```

## License

MIT. See [LICENSE](/Users/maotora/Projects/brave-updater/LICENSE).
