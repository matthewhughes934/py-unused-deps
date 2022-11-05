from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Generator, Iterable, Sequence
from itertools import chain
from pathlib import Path

from unused_deps.compat import importlib_metadata
from unused_deps.dist_detector import detect_dist
from unused_deps.dist_info import (
    distribution_packages,
    parse_requirement,
    python_files_for_dist,
    required_dists,
)
from unused_deps.errors import InternalError, log_error
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
    parser.add_argument(
        "-i",
        "--ignore",
        required=False,
        action="append",
        help="Dependencies to ignore when scanning for usage. "
        "For example, you might want to ignore a linter that you run but don't import",
    )
    parser.add_argument(
        "-s",
        "--source",
        required=False,
        action="append",
        help="Extra directories to scan for python files to check for dependency usage",
    )
    parser.add_argument(
        "-e",
        "--extra",
        required=False,
        action="append",
        help="Extra environment to consider when loading dependencies",
    )
    parser.add_argument(
        "-r",
        "--requirement",
        required=False,
        action="append",
        help="File listing extra requirements to scan for",
    )

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    try:
        if args.distribution is not None:
            root_dist_name = args.distribution
        else:
            root_dist_name = detect_dist(Path("."))
            if root_dist_name is None:
                raise InternalError(
                    "Could not detect package in current directory. Consider specifying it with the `--distribution` flag"
                )
            else:
                logger.info("Detected distribution: %s", root_dist_name)

        try:
            root_dist = importlib_metadata.Distribution.from_name(root_dist_name)
        except importlib_metadata.PackageNotFoundError:
            raise InternalError(
                f"Could not find metadata for distribution `{root_dist_name}` is it installed?"
            )

        python_paths = python_files_for_dist(root_dist, args.source)
        imported_packages = frozenset(
            chain.from_iterable(get_import_bases(path) for path in python_paths)
        )

        if not imported_packages:
            logger.info("Could not find any source files for: %s", root_dist_name)

        success = True
        dists = required_dists(root_dist, args.extra)
        if args.requirement is not None:
            # being with lazy, mostly because mypy doesn't do narrowing from the `filter`
            dists = chain(  # type: ignore[union-attr,assignment]
                dists,
                filter(
                    lambda x: x is not None,
                    (_read_requirements(args.requirement, root_dist, args.extra)),
                ),
            )
        for dist in dists:
            dist_name = dist.metadata["Name"]
            if args.ignore is not None and dist_name in args.ignore:
                logger.info("Ignoring: %s", dist_name)
                continue

            if not any(
                package in imported_packages for package in distribution_packages(dist)
            ):
                print(f"No usage found for: {dist_name}", file=sys.stderr)
                success = False
    except Exception as e:
        returncode, msg = log_error(e)
        print(msg, file=sys.stderr)
        return returncode

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


def _read_requirements(
    requirements: Iterable[str],
    dist: importlib_metadata.Distribution,
    extras: Iterable[str] | None,
) -> Generator[importlib_metadata.Distribution | None, None, None]:
    for requirement_file in requirements:
        with open(requirement_file) as f:
            for requirement in f:
                yield parse_requirement(dist, requirement.rstrip(), extras)
