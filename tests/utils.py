from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from io import StringIO

from unused_deps.compat import importlib_metadata


class InMemoryDistribution(importlib_metadata.Distribution):  # type: ignore[misc] # for py<3.8
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
