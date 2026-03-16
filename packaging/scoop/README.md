# Scoop

The Scoop manifest in this directory is a template.

For real releases, use the release-generated manifest uploaded by the release workflow. It will already contain the correct version and SHA256 for `brave-updater-windows-x64.zip`.

## Intended bucket

- `HackEAC/scoop-bucket`

## Intended install flow

```bash
scoop bucket add hackeac https://github.com/HackEAC/scoop-bucket
scoop install brave-updater
```

## Notes

- Scoop packages the Windows CLI only.
- It does not bundle Brave Browser.
- The manifest points at the portable zip from GitHub Releases.
- If `HackEAC/braver-tz` has the `PACKAGING_SYNC_TOKEN` secret configured, releases can notify `HackEAC/scoop-bucket` immediately by `repository_dispatch`; otherwise the bucket repo falls back to its scheduled sync job.
