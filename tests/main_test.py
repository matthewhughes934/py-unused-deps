from __future__ import annotations

import logging
from unittest import mock

import pytest

from tests.utils import InMemoryDistribution
from unused_deps.main import main


class TestMain:
    def test_failure_when_no_package_given_and_no_package_in_dir(self, tmpdir, capsys):
        with tmpdir.as_cwd():
            return_value = main([])

        captured = capsys.readouterr()
        assert return_value == 1
        assert captured.out == ""
        assert (
            captured.err
            == "Could not detect package in current directory. Consider specifying it with the `--package` flag\n"
        )

    def test_failure_when_no_package_not_installable(self, tmpdir, capsys):
        package_name = "?invalid-package-name"
        argv = ["--package", package_name]

        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert (
            captured.err
            == "Could not find metadata for package `"
            + package_name
            + "` is it installed?\n"
        )

    @mock.patch("unused_deps.main.importlib_metadata.Distribution")
    @pytest.mark.parametrize("filenames", ([], ["not_python.c"]))
    def test_logs_on_package_with_no_source_files(self, mock_dist, filenames, caplog):
        root_package = "my-package"
        root_dist = InMemoryDistribution({filename: [] for filename in filenames})
        mock_dist.from_name.return_value = root_dist
        argv = ["--package", root_package, "--verbose"]

        with caplog.at_level(logging.INFO):
            returncode = main(argv)

        assert returncode == 0
        assert caplog.record_tuples == [
            (
                "unused-deps",
                logging.INFO,
                f"Could not find any source files for: {root_package}",
            )
        ]
