# Homebrew

Use this directory as the source for the Homebrew tap repo, not as the tap repo itself.

## Target tap repo

- `HackEAC/homebrew-brave-updater`

## Intended install command

```bash
brew tap HackEAC/brave-updater
brew install HackEAC/brave-updater/brave-updater
```

## Release workflow

The release workflow generates a release-specific formula from the tagged sdist and uploads it as a release asset.

If you need to do it locally instead:

1. Create the tap repo `HackEAC/homebrew-brave-updater`.
2. Copy the rendered `brave-updater.rb` from the release assets into the tap repo's `Formula/` directory.
3. Commit and push the tap repo update.
4. Test locally:

```bash
brew tap HackEAC/brave-updater /path/to/homebrew-brave-updater
brew install brave-updater
brew test brave-updater
```

## Notes

- The formula installs the CLI, not Brave Browser itself.
- It relies on Homebrew-managed Python, so end users do not need to install Python manually.
- The static `brave-updater.rb` file in this repo is a template; use the rendered release asset for actual tap updates.
