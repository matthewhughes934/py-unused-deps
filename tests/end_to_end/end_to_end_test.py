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
    ("package_name", "filepath"),
    (
        ("setuptools-dist-all-deps", "setuptools_all_deps.py"),
        ("poetry-dist-all-deps", "poetry_all_deps"),
    ),
)
def test_setuptools_with_all_deps(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_with_all_deps"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, filepath])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-dist-missing-a-dep", "setuptools_missing_dep.py"),
        ("poetry-dist-missing-a-dep", "poetry_missing_dep"),
    ),
)
def test_simple_package_missing_dep(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_dep"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, filepath])

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-dist-missing-a-dep", "setuptools_missing_dep.py"),
        ("poetry-dist-missing-a-dep", "poetry_missing_dep"),
    ),
)
def test_simple_package_missing_dep_ignored(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_dep"

    with as_cwd(package_dir):
        returncode = main(
            [
                "--distribution",
                package_name,
                "--ignore",
                "py-unused-deps-testing-bar",
                filepath,
            ]
        )

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-nested-dist-all-deps", "setuptools_src"),
        ("poetry-nested-dist-all-deps", "poetry_src"),
    ),
)
def test_setuptools_nested_with_all_deps(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_nested_with_all_deps"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, filepath])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-nested-dist-all-deps", "setuptools_src"),
        ("poetry-nested-dist-all-deps", "poetry_src"),
    ),
)
def test_setuptools_nested_with_all_deps_with_exclude(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_nested_with_all_deps"

    with as_cwd(package_dir):
        returncode = main(
            [
                "--distribution",
                package_name,
                "--exclude",
                "nested",
                filepath,
            ]
        )

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


def test_package_with_deps_in_tests_without_extra_source(capsys):
    package_name = "setuptools-dist-dep-in-tests"
    package_dir = Path(__file__).parent / "data" / "test_pkg_with_dep_in_tests"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, "setuptools_deps_in_tests"])

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


def test_package_with_deps_in_tests_with_extra_source(capsys):
    package_name = "setuptools-dist-dep-in-tests"
    package_dir = Path(__file__).parent / "data" / "test_pkg_with_dep_in_tests"

    with as_cwd(package_dir):
        returncode = main(
            ["--distribution", package_name, "setuptools_deps_in_tests", "tests"]
        )

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-dist-missing-extra-dep", "setuptools_missing_extra_dep.py"),
        ("poetry-dist-missing-extra-dep", "poetry_missing_extra_dep"),
    ),
)
def test_package_missing_extra_dep_fails_with_extra_specified(
    capsys, package_name, filepath
):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_extra_dep"

    with as_cwd(package_dir):
        returncode = main(
            ["--distribution", package_name, "--extra", "tests", filepath]
        )

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        ("setuptools-dist-missing-extra-dep", "setuptools_missing_extra_dep.py"),
        ("poetry-dist-missing-extra-dep", "poetry_missing_extra_dep"),
    ),
)
@pytest.mark.parametrize("extra_args", ([], ["--extra", "something-else"]))
def test_package_missing_extra_dep_passes_without_extra_specificed(
    capsys, package_name, filepath, extra_args
):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_extra_dep"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name] + extra_args + [filepath])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        (
            "setuptools-dist-missing-a-dep-in-requirements",
            "setuptools_missing_dep_in_requirements.py",
        ),
        (
            "poetry-dist-missing-a-dep-in-requirements",
            "poetry_missing_dep_in_requirements",
        ),
    ),
)
def test_package_missing_dep_in_requirements_no_error_without_requirements_specified(
    capsys, package_name, filepath
):
    package_dir = (
        Path(__file__).parent / "data" / "test_pkg_missing_dep_in_requirements"
    )

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, filepath])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        (
            "setuptools-dist-missing-a-dep-in-requirements",
            "setuptools_missing_dep_in_requirements.py",
        ),
        (
            "poetry-dist-missing-a-dep-in-requirements",
            "poetry_missing_dep_in_requirements",
        ),
    ),
)
def test_package_missing_dep_in_requirements_reports_missing_when_pass_requirements(
    capsys, package_name, filepath
):
    package_dir = (
        Path(__file__).parent / "data" / "test_pkg_missing_dep_in_requirements"
    )

    with as_cwd(package_dir):
        returncode = main(
            [
                "--distribution",
                package_name,
                "--requirement",
                "requirements.txt",
                filepath,
            ]
        )

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        (
            "setuptools-dist-missing-a-dep-with-config",
            "setuptools_missing_dep_with_config.py",
        ),
        ("poetry-dist-missing-a-dep-with-config", "poetry_missing_dep_with_config"),
    ),
)
def test_package_missing_dep_follows_configured_ignore(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_dep_with_config"

    with as_cwd(package_dir):
        returncode = main(["--distribution", package_name, filepath])

    captured = capsys.readouterr()
    assert returncode == 0
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("package_name", "filepath"),
    (
        (
            "setuptools-dist-missing-a-dep-with-config",
            "setuptools_missing_dep_with_config.py",
        ),
        ("poetry-dist-missing-a-dep-with-config", "poetry_missing_dep_with_config"),
    ),
)
def test_package_missing_dep_with_separate_config(capsys, package_name, filepath):
    package_dir = Path(__file__).parent / "data" / "test_pkg_missing_dep_with_config"

    with as_cwd(package_dir):
        returncode = main(
            [
                "--distribution",
                package_name,
                "--config",
                "config-with-no-ignore.toml",
                filepath,
            ]
        )

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"


def test_script_without_package_missing_dep(capsys):
    script_dir = Path(__file__).parent / "data" / "test_without_pkg"

    with as_cwd(script_dir):
        returncode = main(
            [
                "--no-distribution",
                "--requirement",
                "requirements.txt",
                "script.py",
            ]
        )

    captured = capsys.readouterr()
    assert returncode == 1
    assert captured.out == ""
    assert captured.err == "No usage found for: py-unused-deps-testing-bar\n"
