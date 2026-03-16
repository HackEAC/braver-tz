# Homebrew Tap Starter

This repository is not itself the Homebrew tap.

The intended tap repository is:

- `HackEAC/homebrew-brave-updater`

## Intended install command

```bash
brew install HackEAC/brave-updater/brave-updater
```

## How to use these files

1. Create the tap repository `HackEAC/homebrew-brave-updater`.
2. Copy [`brave-updater.rb`](brave-updater.rb) into the tap repo's `Formula/` directory.
3. Replace the release URL and `sha256` with the actual tagged release archive and checksum.
4. Test with:

```bash
brew tap HackEAC/brave-updater /path/to/homebrew-brave-updater
brew install brave-updater
brew test brave-updater
```

## Notes

- Homebrew already provides the official `brave-browser` cask on macOS.
- This formula packages the updater CLI, not the browser itself.
- The formula uses Homebrew-managed Python so end users do not need to manually install Python first.
