from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

import pytest

from unused_deps.compat import importlib_metadata
from unused_deps.dist_info import distribution_packages


class InMemoryDistribution(importlib_metadata.Distribution):
    def __init__(self, file_lines_map: Mapping[str, Iterable[str]]) -> None:
        self.file_map = {
            filename: StringIO("\n".join(lines))
            for filename, lines in file_lines_map.items()
        }

    def read_text(self, filename: str) -> str | None:
        try:
            return self.file_map[filename].read()
        except KeyError:
            return None

    @property
    def files(self) -> list[importlib_metadata.PackagePath] | None:
        return [
            importlib_metadata.PackagePath(filename)
            for filename in self.file_map.keys()
        ]

    def locate_file(self, path: str | os.PathLike[str]) -> os.PathLike[str]:
        # throw-away implementation of abstract method
        return Path(path)


@pytest.mark.parametrize(
    ("file_lines_map", "expected_packages"),
    (
        (
            {"top_level.txt": ["pytest", "_pytest"]},
            ["pytest", "_pytest"],
        ),
        (
            {"tomli/__init__.py": [], "tomli/_re.py": []},
            ["tomli"],
        ),
        (
            {
                "pytest/__init__.py": [],
                "pytest/_version.py": [],
                "top_level.txt": ["pytest", "_pytest"],
            },
            ["pytest", "_pytest"],
        ),
    ),
)
def test_distribution_packages(file_lines_map, expected_packages):
    dist = InMemoryDistribution(file_lines_map)
    assert list(distribution_packages(dist)) == expected_packages
