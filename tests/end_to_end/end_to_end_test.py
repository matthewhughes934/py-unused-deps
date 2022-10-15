from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import pytest

from unused_deps.main import main


@contextmanager
def as_cwd(path: Path) -> Generator[None, None, None]:
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


@pytest.mark.parametrize(
    "package_name", ("setuptools-dist-all-deps", "poetry-dist-all-deps")
)
def test_setuptools_with_all_deps(capsys, package_name):
    package_dir = Path(__file__).parent / "data" / "test_pkg_with_all_deps"

    with as_cwd(package_dir):
        returncode = main(["--package", package_name])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    "package_name", ("setuptools-dist-missing-a-dep", "poetry-dist-missing-a-dep")
)
def test_simple_package_missing_dep(capsys, package_name):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_dep"

    with as_cwd(package_dir):
        returncode = main(["--package", package_name])

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    "package_name", ("setuptools-nested-dist-all-deps", "poetry-nested-dist-all-deps")
)
def test_setuptools_nested_with_all_deps(capsys, package_name):
    package_dir = Path(__file__).parent / "data" / "test_pkg_nested_with_all_deps"

    with as_cwd(package_dir):
        returncode = main(["--package", package_name])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""
