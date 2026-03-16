#!/usr/bin/env python3
"""
Compatibility wrapper for the packaged brave-updater CLI.

This keeps `python3 braver.py ...` working during the transition away from the
original single-file script layout.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from brave_updater.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
