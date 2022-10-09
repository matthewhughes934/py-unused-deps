from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

from unused_deps.compat import importlib_metadata


class InMemoryDistribution(importlib_metadata.Distribution):
    dist_map: dict[str, dict[str, list[str]]] = {}

    def __init__(self, file_lines_map: Mapping[str, Iterable[str]]) -> None:
        self.file_map = {
            filename: StringIO("\n".join(lines))
            for filename, lines in file_lines_map.items()
        }
        self.names_to_clear: list[str] = []

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
            return InMemoryDistribution(cls.dist_map[name])
        except KeyError:
            raise importlib_metadata.PackageNotFoundError(name)

    def add_package(self, name: str) -> None:
        self.dist_map[name] = {"METADATA": [f"name: {name}"]}
        self.names_to_clear.append(name)

    def __del__(self) -> None:
        # Naive attempt to keep things clean
        for name in self.names_to_clear:
            del self.dist_map[name]
