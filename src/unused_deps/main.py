from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Generator, Sequence
from pathlib import Path

from packaging.markers import UndefinedEnvironmentName
from packaging.requirements import Requirement

from unused_deps.compat import importlib_metadata
from unused_deps.dist_info import distribution_packages
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

    try:
        root_dist = importlib_metadata.Distribution.from_name(package)
    except importlib_metadata.PackageNotFoundError:
        print(
            f"Could not find metadata for package `{package}` is it installed?",
            file=sys.stderr,
        )
        return 1

    imported_packages: set[str] = set()
    if root_dist.files is not None:
        for path in root_dist.files:
            if path.suffix in (".py", ".pyi"):
                with open(path) as f:
                    imported_packages.update(get_import_bases(f.read(), path.name))
    else:
        # TODO: logging
        pass

    success = True
    # if an import is missing, report that dist
    for dist in _iter_required(root_dist):
        for package in distribution_packages(dist):
            if package not in imported_packages:
                print(f"No usage found for: {dist.name}", file=sys.stderr)
                success = False
                break

    return 0 if success else 1


# TODO: pass down any 'extras' we consider
# TODO: allow overriding environment
def _iter_required(
    dist: importlib_metadata.Distribution,
) -> Generator[importlib_metadata.Distribution, None, None]:
    if dist.requires is None:
        return

    for raw_requirement in dist.requires:
        requirement = Requirement(raw_requirement)
        if requirement.marker is not None:
            try:
                # TODO: let user pass in an environment for `.evaluate()`?
                # Note: can only specify one `extra` in this case
                matches_environment = requirement.marker.evaluate()
            except UndefinedEnvironmentName:
                logger.info(
                    "Skipping '%s' since marker '%s' doesn't match the environment",
                    requirement.name,
                    requirement.marker,
                )
                continue
        yield importlib_metadata.Distribution.from_name(requirement.name)


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
