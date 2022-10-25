from __future__ import annotations

import logging
import pkgutil
from collections.abc import Collection, Generator, Iterable
from itertools import chain
from pathlib import Path

from packaging.markers import UndefinedEnvironmentName
from packaging.requirements import InvalidRequirement, Requirement

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
    extras: Iterable[str] | None,
) -> Generator[importlib_metadata.Distribution, None, None]:
    if dist.requires is None:
        return

    for raw_requirement in dist.requires:
        req_dist = _dist_from_requirement(Requirement(raw_requirement), extras, dist)
        if req_dist is not None:
            yield req_dist


def python_files_for_dist(
    dist: importlib_metadata.Distribution, extra_sources: Iterable[str] | None
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
                        _recurse_modules(p) for p in f.read().splitlines()
                    )
    if extra_sources is not None:
        yield from chain.from_iterable(
            _find_python_files(Path(p)) for p in extra_sources
        )


def parse_requirement(
    dist: importlib_metadata.Distribution,
    raw_requirement: str,
    extras: Iterable[str] | None,
) -> importlib_metadata.Distribution | None:
    raw_requirement = raw_requirement.lstrip()
    if raw_requirement.startswith("#"):
        return None

    try:
        requirement = Requirement(raw_requirement)
    except InvalidRequirement as e:
        # requirement.txt format used by pip supports a lot more than just a list of requirements,
        # but we don't want to try to handle all these https://pip.pypa.io/en/stable/reference/requirements-file-format/
        logger.debug("Skipping requirement %s: %s", raw_requirement, e)
        return None
    else:
        return _dist_from_requirement(requirement, extras, dist)


def _recurse_modules(path: str) -> Generator[Path, None, None]:
    for module_info in pkgutil.iter_modules(path=[path]):
        if module_info.ispkg and module_info.name:
            yield from _find_python_files(Path(path, module_info.name))


def _find_python_files(path: Path) -> Generator[Path, None, None]:
    for p in path.iterdir():
        if p.suffix in (".py", ".pyi"):
            yield p
        elif p.is_dir():
            yield from _recurse_modules(str(path))


def _top_level_declared(dist: importlib_metadata.Distribution) -> list[str]:
    return (dist.read_text("top_level.txt") or "").split()


def _top_level_inferred(dist: importlib_metadata.Distribution) -> set[str]:
    return {
        f.parts[0] if len(f.parts) > 1 else f.with_suffix("").name
        for f in dist.files or []
        if f.suffix == ".py"
    }


def _dist_from_requirement(
    requirement: Requirement,
    extras: Iterable[str] | None,
    root_dist: importlib_metadata.Distribution,
) -> importlib_metadata.Distribution | None:
    try:
        req_dist = root_dist.from_name(requirement.name)
    except importlib_metadata.PackageNotFoundError:
        logger.info("Cannot import %s, skipping", requirement.name)
        return None

    if requirement.marker is not None:
        if extras is None:
            extras = ("",)

        if any(requirement.marker.evaluate({"extra": extra}) for extra in extras):
            return req_dist
        else:
            logger.info(
                "%s is not valid for the current environment, skipping",
                requirement.name,
            )
            return None
    else:
        return req_dist
