"""Local file helpers used by the updater service."""

from __future__ import annotations

import os


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    for item in ("..", "/", "\\", "\x00"):
        filename = filename.replace(item, "")
    if len(filename) > 255:
        name, extension = os.path.splitext(filename)
        filename = name[:255 - len(extension)] + extension
    return filename
