from __future__ import annotations

from typing import TextIO


class InternalError(Exception):
    pass


def log_error(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, InternalError):
        return 1, f"Error: {exc}"
    elif isinstance(exc, KeyboardInterrupt):
        return 130, f"Interrupted (^C)"
    else:
        return 2, f"Fatal: unexpected error: '{exc}'"
