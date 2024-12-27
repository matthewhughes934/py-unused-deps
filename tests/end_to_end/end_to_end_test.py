from __future__ import annotations

import os
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path

import pytest
import tomli_w

from unused_deps.main import main


@contextmanager
def as_cwd(path: Path) -> Generator[None]:
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def write_config(config: Mapping[str, object], tmpdir: str) -> Path:
    path = Path(tmpdir) / "config.toml"
    with open(path, "w") as f:
        f.write(tomli_w.dumps({"py-unused-deps": config}))
    return path


def run_with_args(
    capsys: pytest.CaptureFixture,
    tmpdir: str,
    package_name: str | None,
    package_dir: str,
    filepaths: list[str],
    cmd_args: list[str] | None = None,
    config: dict[str, object] | None = None,
) -> tuple[int, str, str]:
    package_path = Path(__file__).parent / "data" / package_dir

    if config is not None:
        if package_name is not None:
            config["distribution"] = package_name
        config_path = write_config(config, tmpdir)
        args = ["--config", str(config_path)]

    if cmd_args is not None:
        if package_name is not None:
            args = cmd_args + ["--distribution", package_name]
        else:
            args = cmd_args

    with as_cwd(package_path):
        returncode = main(args + [*filepaths])

    captured = capsys.readouterr()
    return returncode, captured.out, captured.err


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_with_all_deps(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "dist-all-deps"
    filepath = "all_deps.py"

    package_dir = "test_pkg_with_all_deps"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_simple_package_missing_dep(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "dist-missing-a-dep"
    filepath = "missing_dep.py"

    package_dir = "test_pkg_missing_dep"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    (
        (["--ignore", "py-unused-deps-testing-bar"], None),
        (None, {"ignore": "py-unused-deps-testing-bar"}),
    ),
)
def test_simple_package_missing_dep_ignored(capsys, tmp_path, cmd_args, config):
    package_name = "dist-missing-a-dep"
    filepath = "missing_dep.py"

    package_dir = "test_pkg_missing_dep"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_nested_with_all_deps(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "nested-dist-all-deps"
    filepath = "src"

    package_dir = "test_pkg_nested_with_all_deps"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    ((["--exclude", "nested"], None), (None, {"exclude": ["nested"]})),
)
def test_nested_with_all_deps_with_exclude(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "nested-dist-all-deps"
    filepath = "src"

    package_dir = "test_pkg_nested_with_all_deps"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_package_with_deps_in_tests_without_extra_source(
    capsys, tmp_path, cmd_args, config
):
    package_dir = "test_pkg_with_dep_in_tests"
    package_name = "dist-dep-in-tests"
    filepath = "deps_in_tests"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_package_with_deps_in_tests_with_extra_source(
    capsys, tmp_path, cmd_args, config
):
    package_dir = "test_pkg_with_dep_in_tests"
    package_name = "dist-dep-in-tests"
    filepaths = ["deps_in_tests", "tests"]

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        filepaths,
        cmd_args,
        config,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    ((["--extra", "tests"], None), (None, {"extras": ["tests"]})),
)
def test_package_missing_extra_dep_fails_with_extra_specified(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "dist-missing-extra-dep"
    filepath = "missing_extra_dep.py"
    package_dir = "test_pkg_missing_extra_dep"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    (
        (["--extra", "something-else"], None),
        ([], None),
        (None, {"extras": ["something-else"]}),
        (None, {}),
    ),
)
def test_package_missing_extra_dep_passes_without_extra_specificed(
    capsys, tmp_path, cmd_args, config
):
    package_name = "dist-missing-extra-dep"
    filepath = "missing_extra_dep.py"
    package_dir = "test_pkg_missing_extra_dep"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(("cmd_args", "config"), (([], None), (None, {})))
def test_package_missing_dep_in_requirements_no_error_without_requirements_specified(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "dist-missing-a-dep-in-requirements"
    filepath = "missing_dep_in_requirements"
    package_dir = "test_pkg_missing_dep_in_requirements"
    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 0, err
    assert out == ""
    assert err == ""


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    (
        (["--requirement", "requirements.txt"], None),
        (None, {"requirements": ["requirements.txt"]}),
    ),
)
def test_package_missing_dep_in_requirements_reports_missing_when_pass_requirements(
    capsys,
    tmp_path,
    cmd_args,
    config,
):
    package_name = "dist-missing-a-dep-in-requirements"
    filepath = "missing_dep_in_requirements"
    package_dir = "test_pkg_missing_dep_in_requirements"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


def test_package_missing_dep_follows_configured_ignore(capsys, tmp_path):
    package_name = "dist-missing-a-dep-with-config"
    filepath = "missing_dep_with_config.py"
    package_dir = "test_pkg_missing_dep_with_config"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        [],
        None,
    )

    assert returncode == 0
    assert out == ""
    assert err == ""


def test_package_missing_dep_with_separate_config(
    capsys,
    tmp_path,
):
    package_name = "dist-missing-a-dep-with-config"
    filepath = "missing_dep_with_config.py"
    package_dir = "test_pkg_missing_dep_with_config"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        package_name,
        package_dir,
        [filepath],
        ["--config", "config-with-no-ignore.toml"],
        None,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"


@pytest.mark.parametrize(
    ("cmd_args", "config"),
    (
        (["--no-distribution", "--requirement", "requirements.txt"], None),
        (None, {"requirements": ["requirements.txt"], "no_distribution": True}),
    ),
)
def test_script_without_package_missing_dep(capsys, tmp_path, cmd_args, config):
    package_dir = "test_without_pkg"
    filepath = "script.py"

    returncode, out, err = run_with_args(
        capsys,
        tmp_path,
        None,
        package_dir,
        [filepath],
        cmd_args,
        config,
    )

    assert returncode == 1
    assert out == ""
    assert err == "No usage found for: py-unused-deps-testing-bar\n"
