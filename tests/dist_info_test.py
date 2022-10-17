from __future__ import annotations

import logging

import pytest

from tests.utils import InMemoryDistribution
from unused_deps.dist_info import (
    distribution_packages,
    python_files_for_dist,
    required_dists,
)


@pytest.mark.parametrize(
    ("file_lines_map", "expected_packages"),
    (
        (
            {},
            [],
        ),
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
    package_name = "some-package"
    file_lines_map = {"requires.txt": [package_name]}
    expected_dist_names = [package_name]
    root_dist = InMemoryDistribution(file_lines_map)
    root_dist.add_package(package_name)

    got = list(required_dists(root_dist))

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
    package_name = "package-bad-env"
    file_lines_map = {"requires.txt": [f"{package_name}; extra == 'foo'"]}
    root_dist = InMemoryDistribution(file_lines_map)
    root_dist.add_package(package_name)

    with caplog.at_level(logging.INFO):
        got = list(required_dists(root_dist))

    assert got == []
    assert caplog.record_tuples == [
        (
            "unused-deps",
            logging.INFO,
            # asserting on an error message from another package is maybe a bad idea
            f"{package_name} is not valid for the current environment, skipping: 'extra' does not exist in evaluation environment.",
        )
    ]


def test_python_files_for_dist_files_with_python_suffix():
    file_names = ["main.py", "package/__init__.py", "main.pyi", "package/__main__.pyi"]
    dist = InMemoryDistribution({name: [] for name in file_names})

    assert [str(f) for f in (python_files_for_dist(dist))] == file_names


def test_python_files_for_dist_pth_file(tmpdir):
    pkg_dir = tmpdir.join("pkg").ensure_dir()
    files = [
        pkg_dir.join(filename).ensure()
        for filename in ("__init__.py", "__init__.pyi", "__main__.py", "module.py")
    ]
    # non-module entry (expect to ignore)
    tmpdir.join("setup.py").ensure()
    # non-python file (expect to ignore)
    pkg_dir.join("data.txt").ensure()

    pkg_pth = tmpdir.join("pkg.pth").ensure()
    pkg_pth.write(tmpdir)
    dist = InMemoryDistribution({"pkg.pth": [str(tmpdir)]})

    with tmpdir.as_cwd():
        got = tuple(python_files_for_dist(dist))

    assert sorted(got) == sorted(files)
