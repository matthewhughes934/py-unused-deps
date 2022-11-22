from __future__ import annotations

import os
from collections.abc import Generator, Sequence
from fnmatch import fnmatch


# TODO: default includes: *.py, *.pyi
# TODO: default excludes: .svn,CVS,.bzr,.hg,.git,__pycache__,.tox,.nox,.eggs,*.egg,.venv,venv
def find_files(
    path: str, *, exclude: Sequence[str], include: Sequence[str]
) -> Generator[str, None, None]:
    return (
        filename
        for filename in _walk_path(path, exclude)
        if _include(filename, include)
    )


def _walk_path(path: str, exclude: Sequence[str]) -> Generator[str, None, None]:
    if os.path.isdir(path):
        for root, sub_directories, files in os.walk(path):
            for directory in tuple(sub_directories):
                joined = os.path.join(root, directory)
                if _exclude(joined, exclude):
                    sub_directories.remove(directory)

            for filename in files:
                joined = os.path.join(root, filename)
                if not _exclude(joined, exclude):
                    yield joined
    else:
        yield path


def _include(path: str, globs: Sequence[str]) -> bool:
    return any(path == glob or fnmatch(path, glob) for glob in globs)


def _exclude(path: str, exclude: Sequence[str]) -> bool:
    basename = os.path.basename(path)
    abs_path = os.path.abspath(path)

    return any(
        fnmatch(basename, pattern) or fnmatch(abs_path, pattern) for pattern in exclude
    )