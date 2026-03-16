# PyPI

The release workflow is set up to publish the Python package to PyPI from tagged releases.

## Before the first release

Configure a Trusted Publisher for this repository on PyPI so the GitHub Actions release workflow can publish without storing a long-lived API token.

## Expected install commands

```bash
python3 -m pip install brave-updater
pipx install brave-updater
```

## Release artifacts

The PyPI publish step uses:

- `brave_updater-<version>.tar.gz`
- `brave_updater-<version>-py3-none-any.whl`
