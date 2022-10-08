from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

import pytest

from unused_deps.compat import importlib_metadata
from unused_deps.dist_info import distribution_packages, required_dists

dist_map = {
    "some-package": {"METADATA": ["name: some-package"]},
}


class InMemoryDistribution(importlib_metadata.Distribution):
    def __init__(self, file_lines_map: Mapping[str, Iterable[str]]) -> None:
        self.file_map = {
            filename: StringIO("\n".join(lines))
            for filename, lines in file_lines_map.items()
        }

    def read_text(self, filename: str) -> str | None:
        try:
            file_data = self.file_map[filename]
        except KeyError:
            return None
        contents = file_data.read()
        # rewind the stream for future reads
        file_data.seek(0)
        return contents

    @property
    def files(self) -> list[importlib_metadata.PackagePath] | None:
        return [
            importlib_metadata.PackagePath(filename)
            for filename in self.file_map.keys()
        ]

    def locate_file(
        self, path: str | os.PathLike[str]
    ) -> os.PathLike[str]:  # pragma: no cover
        raise NotImplementedError("Implemented unused abstractmethod")

    @classmethod
    def from_name(cls, name: str) -> InMemoryDistribution:
        try:
            return InMemoryDistribution(dist_map[name])
        except KeyError:
            raise importlib_metadata.PackageNotFoundError(name)


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


def test_required_dists_single_package():
    # specify requirements via requires.txt
    # https://setuptools.pypa.io/en/latest/deprecated/python_eggs.html#requires-txt
    file_lines_map = {"requires.txt": ["some-package"]}
    expected_dist_names = ["some-package"]

    got = list(required_dists(InMemoryDistribution(file_lines_map)))

    assert [dist.name for dist in got] == expected_dist_names


def test_required_dist_non_importable_package(caplog):
    package_name = "missing-pacakge"
    file_lines_map = {"requires.txt": [package_name]}

    with caplog.at_level(logging.INFO):
        got = list(required_dists(InMemoryDistribution(file_lines_map)))

    assert got == []
    assert caplog.record_tuples == [
        ("unused-deps", logging.INFO, f"Cannot import {package_name}, skipping")
    ]


def test_required_dist_invalid_marker(caplog):
    package_name = "some-package"
    file_lines_map = {"requires.txt": [f"{package_name}; extra == 'foo'"]}

    with caplog.at_level(logging.INFO):
        got = list(required_dists(InMemoryDistribution(file_lines_map)))

    assert got == []
    assert caplog.record_tuples == [
        (
            "unused-deps",
            logging.INFO,
            # asserting on an error message from another package is maybe a bad idea
            f"{package_name} is not valid for the current environment, skipping: 'extra' does not exist in evaluation environment.",
        )
    ]
