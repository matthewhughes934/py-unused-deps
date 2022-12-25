from __future__ import annotations

import argparse
import logging
import os.path
from collections.abc import Mapping
from itertools import chain
from typing import Dict, NamedTuple, cast

from unused_deps.compat import toml
from unused_deps.errors import InternalError

logger = logging.getLogger("unused-deps")

_CONFIG_LOCATIONS = (
    ".py-unused-deps.toml",
    "pyproject.toml",
)


class Config(NamedTuple):
    filepaths: list[str]
    distribution: str | None = None
    ignore: list[str] | None = None
    extras: list[str] | None = None
    requirements: list[str] | None = None
    include: list[str] | None = None
    exclude: list[str] | None = None
    verbose: int = 0
    config_file: str | None = None


def build_config(
    args: argparse.Namespace, config_from_file: Mapping[str, object] | None
) -> Config:
    if config_from_file is None:
        return Config(**vars(args))

    invalid_keys = tuple(key for key in config_from_file if key not in Config._fields)
    if invalid_keys:
        raise InternalError("Unknown configuration values: " + "\n".join(invalid_keys))

    return Config(
        **{
            k: v
            for (k, v) in chain(config_from_file.items(), vars(args).items())
            if v is not None
        }
    )


def load_config_from_file(path: str | None) -> dict[str, object] | None:
    if path is not None:
        config = _read_config(path)
        if config is None:
            raise InternalError(f"Could not read config from {path}")
        else:
            return config
    else:
        for location in _CONFIG_LOCATIONS:
            if os.path.exists(location):
                config = _read_config(location)
                if config is not None:
                    logger.debug("Detected config in: %s", path)
                    return config
    return None


def _read_config(path: str) -> dict[str, object] | None:
    with open(path, "rb") as f:
        try:
            toml_data = toml.load(f)
        except toml.TOMLDecodeError as e:
            raise InternalError(f"Failed to read TOML file: {path}: {e}")

    if os.path.basename(path) == "pyproject.toml":
        return cast(Dict[str, object], toml_data.get("tool", {}).get("py-unused-deps"))
    else:
        return toml_data.get("py-unused-deps")
