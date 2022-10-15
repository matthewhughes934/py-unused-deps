from __future__ import annotations

import logging
import pkgutil
from collections.abc import Collection, Generator
from itertools import chain
from pathlib import Path

from packaging.markers import UndefinedEnvironmentName
from packaging.requirements import Requirement

from unused_deps.compat import importlib_metadata

logger = logging.getLogger("unused-deps")


# swapping the order of https://github.com/python/cpython/blob/e8165d47b852e933c176209ddc0b5836a9b0d5f4/Lib/importlib/metadata/__init__.py#L1058
def distribution_packages(
    dist: importlib_metadata.Distribution,
) -> Generator[str, None, None]:
    top_level_declared = _top_level_declared(dist)
    if top_level_declared:
        yield from top_level_declared
    else:
        yield from _top_level_inferred(dist)


def required_dists(
    dist: importlib_metadata.Distribution,
) -> Generator[importlib_metadata.Distribution, None, None]:
    if dist.requires is None:
        return

    for raw_requirement in dist.requires:
        requirement = Requirement(raw_requirement)
        try:
            req_dist = dist.from_name(requirement.name)
        except importlib_metadata.PackageNotFoundError:
            logger.info("Cannot import %s, skipping", requirement.name)
            continue

        if requirement.marker is not None:
            try:
                requirement.marker.evaluate()
            except UndefinedEnvironmentName as e:
                logger.info(
                    "%s is not valid for the current environment, skipping: %s",
                    requirement.name,
                    e,
                )
                continue

        yield req_dist


def python_files_for_dist(
    dist: importlib_metadata.Distribution,
) -> Generator[importlib_metadata.PackagePath | Path, None, None]:
    if dist.files is not None:
        for path in dist.files:
            if path.suffix in (".py", ".pyi"):
                yield path
            elif path.suffix == ".pth":
                # maybe an editable install
                # https://setuptools.pypa.io/en/latest/userguide/development_mode.html
                # https://docs.python.org/3/library/site.html
                with open(path) as f:
                    yield from chain.from_iterable(
                        _files_from_editable_install(p) for p in f.read().splitlines()
                    )


def _files_from_editable_install(path: str) -> Generator[Path, None, None]:
    for module_info in pkgutil.iter_modules(path=[path]):
        if module_info.ispkg and module_info.name:
            for p in (Path(path) / module_info.name).iterdir():
                if p.suffix in (".py", ".pyi"):
                    yield p


def _top_level_declared(dist: importlib_metadata.Distribution) -> list[str]:
    return (dist.read_text("top_level.txt") or "").split()


def _top_level_inferred(dist: importlib_metadata.Distribution) -> set[str]:
    return {
        f.parts[0] if len(f.parts) > 1 else f.with_suffix("").name
        for f in dist.files or []
        if f.suffix == ".py"
    }
