from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Generator, Sequence
from itertools import chain
from pathlib import Path

from unused_deps.compat import importlib_metadata
from unused_deps.dist_detector import detect_dist
from unused_deps.dist_info import (
    distribution_packages,
    python_files_for_dist,
    required_dists,
)
from unused_deps.errors import InternalError
from unused_deps.import_finder import get_import_bases

logger = logging.getLogger("unused-deps")


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d",
        "--distribution",
        required=False,
        help="The distribution to scan for unused dependencies",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
    )

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    try:
        if args.distribution is not None:
            dist_name = args.distribution
        else:
            dist_name = detect_dist(Path("."))
            if dist_name is None:
                raise InternalError(
                    "Could not detect package in current directory. Consider specifying it with the `--distribution` flag"
                )
            else:
                logger.info("Detected distribution: %s", dist_name)

        try:
            root_dist = importlib_metadata.Distribution.from_name(dist_name)
        except importlib_metadata.PackageNotFoundError:
            raise InternalError(
                f"Could not find metadata for distribution `{dist_name}` is it installed?"
            )

        python_paths = python_files_for_dist(root_dist)
        imported_packages = frozenset(
            chain.from_iterable(get_import_bases(path) for path in python_paths)
        )

        if not imported_packages:
            logger.info("Could not find any source files for: %s", dist_name)

        success = True
        # if an import is missing, report that dist
        for dist in required_dists(root_dist):
            if not any(
                package in imported_packages for package in distribution_packages(dist)
            ):
                print(f"No usage found for: {dist.name}", file=sys.stderr)
                success = False
    except Exception as e:
        return _log_error(e)

    return 0 if success else 1


def _configure_logging(verbosity: int) -> None:
    if verbosity == 0:
        return
    if verbosity > 2:
        verbosity = 2

    log_level = {
        1: logging.INFO,
        2: logging.DEBUG,
    }[verbosity]

    logging.basicConfig(level=log_level)
    logger.setLevel(log_level)


def _log_error(exc: Exception) -> int:
    if isinstance(exc, InternalError):
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    elif isinstance(exc, KeyboardInterrupt):
        print("Interrupted (^C)", file=sys.stderr)
        return 130
    else:
        breakpoint()
        print(f"Fatal: unexpected error {exc}", file=sys.stderr)
        return 2
