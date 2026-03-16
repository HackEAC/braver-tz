"""Console helpers shared by the CLI and service layer."""

from __future__ import annotations

import sys
from typing import Callable

LogFn = Callable[[str], None]


def make_logger(print_only_mode: bool = False) -> LogFn:
    """Create a simple line-oriented logger."""

    def log(message: str) -> None:
        stream = sys.stderr if print_only_mode else sys.stdout
        print(message, file=stream, flush=True)

    return log


def prompt_yes_no(question: str, default_no: bool = True) -> bool:
    """Prompt for confirmation when stdin is interactive."""
    if not sys.stdin.isatty():
        return not default_no

    suffix = " [y/N]: " if default_no else " [Y/n]: "
    answer = input(question + suffix).strip().lower()
    if not answer:
        return not default_no
    return answer in ("y", "yes")
