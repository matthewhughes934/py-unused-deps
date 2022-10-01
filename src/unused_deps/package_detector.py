"""
Module to naively detect the package at a given path. It probably works fine for
packages which declare the package name in a static method (e.g. in ``setup.cfg`` or
``pyproject.toml``) but quickly gets worse for any dynamic naming in e.g. ``setup.py``.
"""
from __future__ import annotations

import ast
import sys
from collections.abc import Iterable
from configparser import ConfigParser
from functools import reduce
from operator import getitem
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    import tomllib as toml
else:
    import tomli as toml


def detect_package(path: Path, encoding: str | None = None) -> str | None:
    detectors = {
        "setup.cfg": _read_package_from_setup_cfg,
        "setup.py": _read_package_from_setup_py,
        "pyproject.toml": _read_package_from_pyproject_toml,
    }

    for filename, detector in detectors.items():
        file = path / filename
        if file.exists():
            package_from_file = detector(file, encoding)
            if package_from_file is not None:
                return package_from_file
    return None


def _read_package_from_setup_cfg(
    setup_cfg: Path, encoding: str | None = None
) -> str | None:
    config = ConfigParser()
    config.read(setup_cfg, encoding=encoding)

    try:
        return config["metadata"]["name"]
    except KeyError:
        return None


def _read_package_from_setup_py(
    setup_py: Path, encoding: str | None = None
) -> str | None:
    with open(setup_py, "rb") as f:
        raw_contents = f.read()
    if encoding is not None:
        contents = raw_contents.decode(encoding=encoding)
    else:
        contents = raw_contents.decode()

    parsed = ast.parse(contents)

    for node in ast.walk(parsed):
        if isinstance(node, ast.Call):
            func = node.func
            if (isinstance(func, ast.Name) and func.id == "setup") or (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "setuptools"
                and func.attr == "setup"
            ):
                for keyword in node.keywords:
                    if (
                        keyword.arg == "name"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    ):
                        return keyword.value.value
    return None


def _read_package_from_pyproject_toml(
    pyproject_toml: Path, encoding: str | None = None
) -> str | None:
    with open(pyproject_toml, "rb") as f:
        raw_contents = f.read()

    try:
        contents = raw_contents.decode()
    except UnicodeDecodeError:
        raise ValueError(
            f"{pyproject_toml} is not UTF-8 encoded. TOML files must be UTF-8 Encoded"
        )

    toml_data = toml.loads(contents)

    locations = (
        # PEP 621
        ("project", "name"),
        # poetry
        ("tool", "poetry", "name"),
    )
    for location in locations:
        name = _get_name_from_pyproject_toml(toml_data, location)
        if name is not None:
            return name
    return None


def _get_name_from_pyproject_toml(
    toml_data: dict[str, Any], location: Iterable[str]
) -> str | None:
    try:
        name_from_toml = reduce(getitem, location, toml_data)
    except KeyError:
        return None

    if not isinstance(name_from_toml, str):
        raise ValueError(
            f"Expected a name at {''.join(f'[{key}]' for key in location)} but found non-string: {name_from_toml}"
        )
    else:
        return name_from_toml
