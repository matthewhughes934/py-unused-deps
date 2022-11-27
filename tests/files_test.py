import os

import pytest

from unused_deps.files import find_files


def _normalize_path(path):
    return path.replace("/", os.path.sep)


def _normalize_paths(*paths):
    return tuple(_normalize_path(path) for path in paths)


def test_find_files_includes_bare_filename(tmpdir):
    path = tmpdir.join(_normalize_path("some/file.py")).ensure()
    expected = (path,)

    got = tuple(find_files(path, exclude=(), include=(path,)))

    assert len(got) == len(expected)
    assert set(got) == set(expected)


@pytest.mark.parametrize(
    ("paths", "include", "exclude", "expected"),
    (
        pytest.param(
            ("file.py",), ("*.py",), (), ("file.py",), id="Simple prefix include"
        ),
        pytest.param(
            ("file.sh",),
            ("*.py",),
            (),
            (),
            id="Include with no match",
        ),
        pytest.param(("file.py",), (), ("*.py",), (), id="Simple prefix exclude"),
        pytest.param(
            ("file.py", "other.py"),
            ("*.py",),
            ("other.py",),
            ("file.py",),
            id="Mixed include/exclude",
        ),
        pytest.param(
            _normalize_paths("dir/file.py"),
            ("*.py",),
            (),
            _normalize_paths("dir/file.py"),
            id="Simple prefix include subdir",
        ),
        pytest.param(
            _normalize_paths("dir/file.py"),
            (),
            ("*.py",),
            (),
            id="Simple prefix exclude subdir",
        ),
        pytest.param(
            _normalize_paths("dir/file1.py", "dir/file2.py", "dir/foo/file3.py"),
            ("*.py",),
            ("dir",),
            (),
            id="Exclude directory",
        ),
        pytest.param(
            _normalize_paths("dir/file1.py", "dir/file2.py", "dir2/bar.py"),
            ("*.py",),
            ("dir",),
            _normalize_paths("dir2/bar.py"),
            id="Mixed include/exclude dir",
        ),
    ),
)
def test_find_files(tmpdir, paths, include, exclude, expected):
    for path in paths:
        tmpdir.join(path).ensure()

    got = tuple(find_files(tmpdir, exclude=exclude, include=include))

    assert len(got) == len(expected)
    assert set(got) == set(tmpdir.join(path) for path in expected)
