from __future__ import annotations

import importlib.metadata
import logging
from collections.abc import Generator, Iterable

from packaging.requirements import InvalidRequirement, Requirement

logger = logging.getLogger("unused-deps")


# swapping the order of https://github.com/python/cpython/blob/e8165d47b852e933c176209ddc0b5836a9b0d5f4/Lib/importlib/metadata/__init__.py#L1058
def distribution_packages(
    dist: importlib.metadata.Distribution,
) -> Generator[str, None, None]:
    top_level_declared = _top_level_declared(dist)
    if top_level_declared:
        yield from top_level_declared
    else:
        yield from _top_level_inferred(dist)


def required_dists(
    dist: importlib.metadata.Distribution,
    extras: Iterable[str] | None,
) -> Generator[importlib.metadata.Distribution, None, None]:
    if dist.requires is None:
        return

    for raw_requirement in dist.requires:
        req_dist = _dist_from_requirement(Requirement(raw_requirement), extras)
        if req_dist is not None:
            yield req_dist


def parse_requirement(
    raw_requirement: str,
    extras: Iterable[str] | None,
) -> importlib.metadata.Distribution | None:
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
        return _dist_from_requirement(requirement, extras)


def _top_level_declared(dist: importlib.metadata.Distribution) -> list[str]:
    return (dist.read_text("top_level.txt") or "").split()


def _top_level_inferred(dist: importlib.metadata.Distribution) -> set[str]:
    return {
        f.parts[0] if len(f.parts) > 1 else f.with_suffix("").name
        for f in dist.files or []
        if f.suffix == ".py"
    }


def _dist_from_requirement(
    requirement: Requirement,
    extras: Iterable[str] | None,
) -> importlib.metadata.Distribution | None:
    try:
        req_dist = importlib.metadata.Distribution.from_name(requirement.name)
    except importlib.metadata.PackageNotFoundError:
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
