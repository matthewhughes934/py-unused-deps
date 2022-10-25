from __future__ import annotations

import logging

import pytest

from tests.utils import InMemoryDistribution
from unused_deps.dist_info import (
    distribution_packages,
    parse_requirement,
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

    got = list(required_dists(root_dist, None))

    assert [dist.name for dist in got] == expected_dist_names


def test_required_dist_non_importable_package(caplog):
    package_name = "missing-pacakge"
    file_lines_map = {"requires.txt": [package_name]}

    with caplog.at_level(logging.INFO):
        got = list(required_dists(InMemoryDistribution(file_lines_map), None))

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
        got = list(required_dists(root_dist, None))

    assert got == []
    assert caplog.record_tuples == [
        (
            "unused-deps",
            logging.INFO,
            # asserting on an error message from another package is maybe a bad idea
            f"{package_name} is not valid for the current environment, skipping",
        )
    ]


def test_required_dist_invalid_selects_with_supported_extra(caplog):
    package_name = "foo-only-dep"
    file_lines_map = {"requires.txt": [f"{package_name}; extra == 'foo'"]}
    root_dist = InMemoryDistribution(file_lines_map)
    root_dist.add_package(package_name)

    with caplog.at_level(logging.INFO):
        got = list(required_dists(root_dist, ["foo"]))

    assert [dist.name for dist in got] == [package_name]


def test_python_files_for_dist_files_with_python_suffix():
    file_names = ["main.py", "package/__init__.py", "main.pyi", "package/__main__.pyi"]
    dist = InMemoryDistribution({name: [] for name in file_names})

    assert [str(f) for f in (python_files_for_dist(dist, None))] == file_names


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
        got = tuple(python_files_for_dist(dist, None))

    assert sorted(got) == sorted(files)


def test_python_files_for_dist_pth_file_nested_structed(tmpdir):
    pkg_dir = tmpdir.join("pkg").ensure_dir()
    nested_dir = pkg_dir.join("nested").ensure_dir()
    files = [
        pkg_dir.join("__init__.py").ensure(),
        nested_dir.join("__init__.py").ensure(),
    ]

    pkg_pth = tmpdir.join("pkg.pth").ensure()
    pkg_pth.write(tmpdir)
    dist = InMemoryDistribution({"pkg.pth": [str(tmpdir)]})

    with tmpdir.as_cwd():
        got = tuple(python_files_for_dist(dist, None))

    assert sorted(got) == sorted(files)


def test_python_files_for_dist_scans_extra_sources_if_provided(tmpdir):
    run_dir = tmpdir.join("run_dir").ensure_dir()
    test_dir = run_dir.join("tests").ensure_dir()
    script_dir = run_dir.join("scripts").ensure_dir()

    files = [
        test_dir.join("__init__.py").ensure(),
        test_dir.join("foo_test.py").ensure(),
        test_dir.join("some_pkg").ensure_dir().join("__init__.py").ensure(),
        script_dir.join("script.py").ensure(),
    ]

    with run_dir.as_cwd():
        got = list(
            python_files_for_dist(InMemoryDistribution({}), [test_dir, script_dir])
        )

    assert sorted(got) == sorted(files)


@pytest.mark.parametrize(
    "raw_requirement", ("# this is a comment", "   # indented comment")
)
def test_parse_requirements_returns_none_on_comments(raw_requirement):
    dist = InMemoryDistribution({})

    assert parse_requirement(dist, raw_requirement, []) is None


@pytest.mark.parametrize(
    "raw_requirement",
    (
        "--verbose",
        "-r other-requirements.txt",
        "-c constraints.txt",
        "/path/to/local/distribution.whl",
    ),
)
def test_parse_requirements_returns_none_on_invalid_requirement(
    raw_requirement, caplog
):
    dist = InMemoryDistribution({})

    with caplog.at_level(logging.DEBUG):
        got = parse_requirement(dist, raw_requirement, [])

    (record,) = caplog.records
    assert got is None
    assert record.levelno == logging.DEBUG
    assert record.name == "unused-deps"
    assert record.message.startswith(f"Skipping requirement {raw_requirement}:")


def test_parse_requirements_returns_dist_on_valid_requirement():
    raw_requirement = "parse-requirements-requirement"
    dist = InMemoryDistribution({})
    dist.add_package(raw_requirement)

    got = parse_requirement(dist, raw_requirement, [])

    assert got is not None
    assert got.name == raw_requirement
