# WinGet

`brave-updater` is a good fit for WinGet once a tagged release publishes the Windows portable zip:

- `brave-updater-windows-x64.zip`

## Recommended package identity

- `HackEAC.BraveUpdater`

## Submission flow

1. Create a tagged release so the Windows portable zip exists on GitHub Releases.
2. Use `wingetcreate` to generate the manifest from the release asset URL.
3. Validate the manifest locally.
4. Submit the manifest PR to `microsoft/winget-pkgs`.

## Notes

- Treat WinGet as a distribution channel for the CLI, not for Brave Browser itself.
- Prefer the portable zip release asset instead of trying to wrap `pip install` in a package manager manifest.
- Keep the package description explicitly unofficial and non-affiliated.
