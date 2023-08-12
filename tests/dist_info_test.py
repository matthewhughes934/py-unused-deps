from __future__ import annotations

import logging
from unittest import mock

import pytest

from tests.utils import InMemoryDistribution
from unused_deps.dist_info import (
    distribution_packages,
    parse_requirement,
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
    root_dist = InMemoryDistribution({"requires.txt": [package_name]})
    requirement_dist = InMemoryDistribution({"METADATA": [f"name: {package_name}"]})
    expected = [requirement_dist]

    with mock.patch(
        "unused_deps.dist_info.importlib.metadata.Distribution.from_name",
        return_value=requirement_dist,
    ):
        got = list(required_dists(root_dist, None))

    assert got == expected


def test_required_dist_non_importable_package(caplog):
    package_name = "missing-package"
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
    requirement_dist = InMemoryDistribution({"METADATA": [f"name: {package_name}"]})

    with caplog.at_level(logging.INFO), mock.patch(
        "unused_deps.dist_info.importlib.metadata.Distribution.from_name",
        return_value=requirement_dist,
    ):
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
    requirement_dist = InMemoryDistribution({"METADATA": [f"name: {package_name}"]})
    expected = [requirement_dist]

    with caplog.at_level(logging.INFO), mock.patch(
        "unused_deps.dist_info.importlib.metadata.Distribution.from_name",
        return_value=requirement_dist,
    ):
        got = list(required_dists(root_dist, ["foo"]))

    assert got == expected


@pytest.mark.parametrize(
    "raw_requirement", ("# this is a comment", "   # indented comment")
)
def test_parse_requirements_returns_none_on_comments(raw_requirement):
    assert parse_requirement(raw_requirement, []) is None


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
    with caplog.at_level(logging.DEBUG):
        got = parse_requirement(raw_requirement, [])

    (record,) = caplog.records
    assert got is None
    assert record.levelno == logging.DEBUG
    assert record.name == "unused-deps"
    assert record.message.startswith(f"Skipping requirement {raw_requirement}:")


def test_parse_requirements_returns_dist_on_valid_requirement():
    raw_requirement = "parse-requirements-requirement"
    requirement_dist = InMemoryDistribution({"METADATA": [f"name: {raw_requirement}"]})

    with mock.patch(
        "unused_deps.dist_info.importlib.metadata.Distribution.from_name",
        return_value=requirement_dist,
    ):
        got = parse_requirement(raw_requirement, [])

    assert got == requirement_dist
