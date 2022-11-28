from __future__ import annotations

import traceback


class InternalError(Exception):
    pass


def log_error(exc: Exception) -> tuple[int, str]:
    if isinstance(exc, InternalError):
        return 1, f"Error: {exc}"
    elif isinstance(exc, KeyboardInterrupt):
        return 130, "Interrupted (^C)"
    else:
        return (
            2,
            f"Fatal: unexpected error: '{exc}'\n"
            + "Please report this bug with the following traceback:\n"
            + "".join(traceback.format_exception(None, exc, exc.__traceback__)),
        )
