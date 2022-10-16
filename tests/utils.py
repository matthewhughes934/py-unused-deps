from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from io import StringIO
from pathlib import Path

from unused_deps.compat import importlib_metadata


class InMemoryDistribution(importlib_metadata.Distribution):  # type: ignore[misc] # for py<3.8
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
        def _build_path(name):
            path = importlib_metadata.PackagePath(name)
            path.dist = self
            return path

        dist_files = [_build_path(filename) for filename in self.file_map.keys()]
        if dist_files:
            return dist_files
        else:
            return None

    def locate_file(self, path: str | os.PathLike[str]) -> os.PathLike[str]:
        raise NotImplementedError("Unimplemented unused abstractmethod")

    @classmethod
    def from_name(cls, name: str) -> InMemoryDistribution:
        try:
            return InMemoryDistribution(cls.dist_map[name])
        except KeyError:
            raise importlib_metadata.PackageNotFoundError(name)

    def add_package(
        self, name: str, file_map: Mapping[str, list[str]] | None = None
    ) -> None:
        self.dist_map[name] = {"METADATA": [f"name: {name}"]}
        if file_map:
            self.dist_map[name].update(file_map)
        self.names_to_clear.append(name)

    def __del__(self) -> None:
        # Naive attempt to keep things clean
        for name in self.names_to_clear:
            del self.dist_map[name]
