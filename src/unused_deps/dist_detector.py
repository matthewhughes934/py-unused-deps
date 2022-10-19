"""
Module to naively detect the distribution at a given path. It probably works fine for
distributions which declare the distributions name in a static method (e.g. in ``setup.cfg`` or
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

from unused_deps.compat import toml


def detect_dist(path: Path) -> str | None:
    detectors = {
        "setup.cfg": _read_package_from_setup_cfg,
        "setup.py": _read_package_from_setup_py,
        "pyproject.toml": _read_package_from_pyproject_toml,
    }

    for filename, detector in detectors.items():
        file = path / filename
        if file.exists():
            package_from_file = detector(file)
            if package_from_file is not None:
                return package_from_file
    return None


def _read_package_from_setup_cfg(setup_cfg: Path) -> str | None:
    config = ConfigParser()
    config.read(setup_cfg)

    try:
        return config["metadata"]["name"]
    except KeyError:
        return None


def _read_package_from_setup_py(setup_py: Path) -> str | None:
    with open(setup_py) as f:
        contents = f.read()

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
                    if keyword.arg == "name":
                        if isinstance(keyword.value, ast.Constant) and isinstance(
                            keyword.value.value, str
                        ):  # pragma: >=3.8 cover
                            return keyword.value.value
                        elif isinstance(keyword.value, ast.Str):  # pragma: <3.8 cover
                            return keyword.value.s
    return None


def _read_package_from_pyproject_toml(pyproject_toml: Path) -> str | None:
    with open(pyproject_toml) as f:
        contents = f.read()

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
