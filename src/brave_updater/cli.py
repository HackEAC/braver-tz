"""CLI entrypoint for brave-updater."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional

from brave_updater.console import make_logger, prompt_yes_no
from brave_updater.download import sanitize_filename
from brave_updater.providers import extract_chromium_version, pick_asset
from brave_updater.service import BraveUpdater
from brave_updater.system import detect_system


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and update Brave Browser from Brave-controlled release sources."
    )
    parser.add_argument("--dir", default=str(Path.home() / "Downloads"), help="Download directory (default: ~/Downloads)")
    parser.add_argument("--install", action="store_true", help="Legacy mode: prompt to install after download")
    parser.add_argument("--print-only", action="store_true", help="Legacy mode: print the selected download URL only")
    parser.add_argument("--skip-verify", action="store_true", help="Skip integrity verification (not recommended)")
    parser.add_argument("--source", default="github", choices=("github", "official", "auto"), help="Release source strategy")

    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Inspect the installed version and the latest available release")
    check_parser.add_argument("--json", action="store_true", help="Emit machine-readable output")
    check_parser.add_argument("--source", default="github", choices=("github", "official", "auto"), help="Release source strategy")

    download_parser = subparsers.add_parser("download", help="Download the best installer for this system")
    download_parser.add_argument("--dir", default=str(Path.home() / "Downloads"), help="Download directory")
    download_parser.add_argument("--skip-verify", action="store_true", help="Skip integrity verification")
    download_parser.add_argument("--force", action="store_true", help="Re-download even if the target file already exists")
    download_parser.add_argument("--source", default="github", choices=("github", "official", "auto"), help="Release source strategy")

    update_parser = subparsers.add_parser("update", help="Download and optionally install a new version when available")
    update_parser.add_argument("--dir", default=str(Path.home() / "Downloads"), help="Download directory")
    update_parser.add_argument("--skip-verify", action="store_true", help="Skip integrity verification")
    update_parser.add_argument("--force", action="store_true", help="Update even if the installed version matches the latest")
    update_parser.add_argument("--yes", action="store_true", help="Install without prompting")
    update_parser.add_argument("--source", default="github", choices=("github", "official", "auto"), help="Release source strategy")

    install_parser = subparsers.add_parser("install", help="Install an already-downloaded Brave package")
    install_parser.add_argument("path", help="Path to a downloaded installer package")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return run_check(args)
    if args.command == "download":
        return run_download(args)
    if args.command == "update":
        return run_update(args)
    if args.command == "install":
        return run_install(args)
    return run_legacy(args)


def run_check(args: argparse.Namespace) -> int:
    logger = make_logger(print_only_mode=args.json)
    updater = BraveUpdater(source=args.source, log=logger)
    result = updater.check()

    if args.json:
        payload = {
            "os": result.system.os_name,
            "arch": result.system.arch,
            "linux_family": result.system.linux_family,
            "installed_version": result.installed_version,
            "latest_version": result.latest_version,
            "update_available": result.update_available,
            "asset_name": result.selected_asset.name,
            "asset_url": result.selected_asset.url,
            "selection_reason": result.selection_reason,
            "release_source": result.release_source,
            "chromium_version": result.chromium_version,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    logger(
        "Detected system: os={}, arch={}, linux_family={}".format(
            result.system.os_name,
            result.system.arch,
            result.system.linux_family,
        )
    )
    logger("Installed version: {}".format(result.installed_version or "not found"))
    logger("Latest stable release: {}".format(result.latest_version))
    logger("Chosen asset: {}".format(result.selected_asset.name))
    logger("Reason: {}".format(result.selection_reason))
    if result.chromium_version:
        logger("Chromium base: {}".format(result.chromium_version))
    if result.update_available:
        logger("Update available.")
    else:
        logger("Already up to date.")
    return 0


def run_download(args: argparse.Namespace) -> int:
    logger = make_logger()
    updater = BraveUpdater(source=args.source, log=logger)
    destination = updater.download_latest(
        directory=Path(args.dir).expanduser().resolve(),
        skip_verify=args.skip_verify,
        force=args.force,
    )
    logger("Saved installer to {}".format(destination))
    return 0


def run_update(args: argparse.Namespace) -> int:
    logger = make_logger()
    updater = BraveUpdater(source=args.source, log=logger)
    updater.update(
        directory=Path(args.dir).expanduser().resolve(),
        skip_verify=args.skip_verify,
        force=args.force,
        assume_yes=args.yes,
    )
    return 0


def run_install(args: argparse.Namespace) -> int:
    logger = make_logger()
    updater = BraveUpdater(source="github", log=logger)
    updater.install(Path(args.path).expanduser().resolve())
    return 0


def run_legacy(args: argparse.Namespace) -> int:
    logger = make_logger(print_only_mode=args.print_only)
    updater = BraveUpdater(source=args.source, log=logger)
    release = updater.load_release()
    system_info = detect_system()
    asset, reason = pick_asset(release.assets, system_info)

    logger(
        "Detected system: os={}, arch={}, linux_family={}".format(
            system_info.os_name, system_info.arch, system_info.linux_family
        )
    )
    logger("Latest stable release: {}  ({})".format(release.version, release.name))
    logger("Chosen asset: {}".format(asset.name))
    logger("Reason: {}".format(reason))
    chromium_version = extract_chromium_version(release.body)
    if chromium_version:
        logger("Chromium base: {}".format(chromium_version))

    if args.print_only:
        print(asset.url)
        return 0

    destination = Path(args.dir).expanduser().resolve() / sanitize_filename(asset.name)
    updater.download_latest(
        directory=Path(args.dir).expanduser().resolve(),
        skip_verify=args.skip_verify,
        force=False,
    )

    if args.install:
        if prompt_yes_no("Install {} now?".format(destination.name), default_no=True):
            updater.install(destination)
            logger("Done.")
        else:
            logger("Install skipped.")
    return 0
