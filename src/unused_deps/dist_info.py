from __future__ import annotations

from collections.abc import Generator
from itertools import chain

from unused_deps.compat import importlib_metadata


# swapping the order of https://github.com/python/cpython/blob/e8165d47b852e933c176209ddc0b5836a9b0d5f4/Lib/importlib/metadata/__init__.py#L1058
def distribution_packages(
    dist: importlib_metadata.Distribution,
) -> Generator[str, None, None]:
    top_level_declared = _top_level_declared(dist)
    if top_level_declared:
        yield from top_level_declared
    else:
        yield from _top_level_inferred(dist)


def _top_level_declared(dist: importlib_metadata.Distribution) -> list[str]:
    return (dist.read_text("top_level.txt") or "").split()


def _top_level_inferred(dist: importlib_metadata.Distribution) -> set[str]:
    return {
        f.parts[0] if len(f.parts) > 1 else f.with_suffix("").name
        for f in dist.files or []
        if f.suffix == ".py"
    }
