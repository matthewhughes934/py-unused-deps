from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Generator, Sequence
from itertools import chain
from pathlib import Path

from unused_deps.compat import importlib_metadata
from unused_deps.dist_info import distribution_packages, required_dists
from unused_deps.import_finder import get_import_bases
from unused_deps.package_detector import detect_package

logger = logging.getLogger("unused-deps")


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        "--package",
        required=False,
        help="The package to scan for unused dependencies",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=0,
        action="count",
    )

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    if args.package is not None:
        package = args.package
    else:
        package = detect_package(Path("."))
        if package is None:
            print(
                "Could not detect package in current directory. Consider specifying it with the `--package` flag",
                file=sys.stderr,
            )
            return 1
        else:
            logger.info("Detected package: %s", package)

    try:
        root_dist = importlib_metadata.Distribution.from_name(package)
    except importlib_metadata.PackageNotFoundError:
        print(
            f"Could not find metadata for package `{package}` is it installed?",
            file=sys.stderr,
        )
        return 1

    # python_files = locate_python_files(root_dist)
    # imported_packages = frozenset(get_imports_from_file(python_file) for file in python_files)
    # for missing_dist in find_missing_dists(root_dist, imported_packages): blah...
    python_files = locate_python_files(root_dist)
    imported_packages = frozenset(
        chain.from_iterable(get_import_bases(path) for path in python_files)
    )

    if not imported_packages:
        logger.info("Could not find any source files for: %s", package)

    success = True
    # if an import is missing, report that dist
    for dist in required_dists(root_dist):
        for package in distribution_packages(dist):
            if package not in imported_packages:
                print(f"No usage found for: {dist.name}", file=sys.stderr)
                success = False
                break

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


def locate_python_files(
    dist: importlib_metadata.Distribution,
) -> Generator[importlib_metadata.PackagePath, None, None]:
    if dist.files is not None:
        for path in dist.files:
            if path.suffix in (".py", ".pyi"):
                yield path
