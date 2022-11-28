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
    required_dists,
)
from unused_deps.errors import InternalError, log_error
from unused_deps.files import find_files
from unused_deps.import_finder import get_import_bases

logger = logging.getLogger("unused-deps")


def main(argv: Sequence[str] | None = None) -> int:
    if argv is None:  # pragma: no cover
        argv = sys.argv[1:]

    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    try:
        root_dist = _get_dist(args.distribution)

        python_paths = chain.from_iterable(
            find_files(path, exclude=args.exclude, include=args.include)
            for path in args.filepaths
        )
        imported_packages = frozenset(
            chain.from_iterable(get_import_bases(path) for path in python_paths)
        )

        if not imported_packages:
            logger.info("Could not find any source files")

        success = True
        package_dists = (
            required_dists(root_dist, args.extra) if root_dist is not None else []
        )
        requirement_dists = (
            (
                dist
                for dist in _read_requirements(args.requirement, args.extra)
                if dist is not None
            )
            if args.requirement is not None
            else []
        )

        for dist in chain(package_dists, requirement_dists):
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
    extras: Iterable[str] | None,
) -> Generator[importlib_metadata.Distribution | None, None, None]:
    for requirement_file in requirements:
        with open(requirement_file) as f:
            for requirement in f:
                yield parse_requirement(requirement.rstrip(), extras)


def _build_arg_parser() -> argparse.ArgumentParser:
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
    parser.add_argument(
        "--include",
        required=False,
        default=("*.py", "*.pyi"),
        action="append",
        help="Pattern to match on files when measuring usage",
    )
    parser.add_argument(
        "--exclude",
        required=False,
        default=(
            ".svn",
            "CVS",
            ".bzr",
            ".hg",
            ".git",
            "__pycache__",
            ".tox",
            ".nox",
            ".eggs",
            "*.egg",
            ".venv",
            "venv",
        ),
        action="append",
        help="Pattern to match on files or directory to exclude when measuring usage",
    )
    parser.add_argument(
        "filepaths",
        default=".",
        nargs="*",
        help="Paths to scan for dependency usage",
    )

    return parser


def _get_dist(dist_name: str | None) -> importlib_metadata.Distribution | None:
    if dist_name is None:
        dist_name = detect_dist(Path("."))
        if dist_name is None:
            logger.info("Could not detected a distribution in current directory")
            return None
        else:
            logger.info("Detected distribution: %s", dist_name)

    try:
        root_dist = importlib_metadata.Distribution.from_name(dist_name)
    except importlib_metadata.PackageNotFoundError:
        raise InternalError(
            f"Could not find metadata for distribution `{dist_name}` is it installed?"
        )
    else:
        return root_dist
