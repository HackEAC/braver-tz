#!/usr/bin/env python3
"""Render release-specific package-manager files from built assets."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brave_updater import __version__
from brave_updater.distribution import DEFAULT_REPOSITORY, sha256_for_file, write_distribution_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render Homebrew and Scoop files for a release.")
    parser.add_argument("--version", default=__version__, help="Release version (default: package version)")
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, help="GitHub repository path, e.g. HackEAC/braver-tz")
    parser.add_argument("--source-archive", required=True, help="Path to the release sdist tar.gz")
    parser.add_argument("--windows-zip", required=True, help="Path to the Windows portable zip")
    parser.add_argument("--output-dir", required=True, help="Directory to write rendered files into")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    source_archive = Path(args.source_archive).expanduser().resolve()
    windows_zip = Path(args.windows_zip).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not source_archive.exists():
        raise FileNotFoundError("Source archive not found: {}".format(source_archive))
    if not windows_zip.exists():
        raise FileNotFoundError("Windows zip not found: {}".format(windows_zip))

    written = write_distribution_files(
        output_dir=output_dir,
        version=args.version,
        repository=args.repo,
        source_sha256=sha256_for_file(source_archive),
        windows_sha256=sha256_for_file(windows_zip),
    )

    for label, path in written.items():
        print("{}: {}".format(label, path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
