# Windows Packaging

The release workflow builds a standalone Windows portable zip named:

- `brave-updater-windows-x64.zip`

The zip is intended to contain:

- `brave-updater.exe`
- `LICENSE`
- `README.md`

## Why this exists

Windows package managers work much better with a real installer or a portable executable archive than with a `pip install` command.

This portable zip is the release asset used for:

- `Scoop`
- `WinGet` submissions

## Build source

The executable is built with `PyInstaller` using [`entrypoint.py`](entrypoint.py), which calls the packaged CLI directly.
