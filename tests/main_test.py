from __future__ import annotations

import logging
from pathlib import Path
from unittest import mock

import pytest

from tests.utils import InMemoryDistribution
from unused_deps.main import main


class TestMain:
    @pytest.mark.parametrize(
        ("args", "expected_logging_level"),
        (
            (["--verbose"], logging.INFO),
            (["--verbose", "--verbose"], logging.DEBUG),
            (["--verbose", "--verbose", "--verbose"], logging.DEBUG),
        ),
    )
    def test_logging_level_set_from_args(self, tmpdir, args, expected_logging_level):
        with tmpdir.as_cwd():
            main(args)

        logger = logging.getLogger("unused-deps")
        assert logger.getEffectiveLevel() == expected_logging_level

    @pytest.mark.parametrize("with_argv", (True, False))
    def test_failure_when_no_package_given_and_no_package_in_dir(
        self, tmpdir, capsys, with_argv
    ):
        with tmpdir.as_cwd():
            if with_argv:
                with mock.patch("unused_deps.main.sys.argv", ["prog-name"]):
                    return_value = main()
            else:
                return_value = main([])

        captured = capsys.readouterr()
        assert return_value == 1
        assert captured.out == ""
        assert (
            captured.err
            == "Error: Could not detect package in current directory. Consider specifying it with the `--package` flag\n"
        )

    def test_failure_when_no_package_not_installable(self, tmpdir, capsys):
        package_name = "?invalid-package-name"
        argv = ["--package", package_name]

        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert (
            captured.err
            == "Error: Could not find metadata for package `"
            + package_name
            + "` is it installed?\n"
        )

    @pytest.mark.parametrize("filenames", ([], ["not_python.c"]))
    def test_logs_on_package_with_no_source_files(self, filenames, caplog):
        root_package = "my-package"
        root_dist = InMemoryDistribution({filename: [] for filename in filenames})
        mock_dist = mock.Mock(**{"from_name.return_value": root_dist})
        argv = ["--package", root_package, "--verbose"]

        with caplog.at_level(logging.INFO), mock.patch(
            "unused_deps.main.importlib_metadata.Distribution", mock_dist
        ):
            returncode = main(argv)

        assert returncode == 0
        assert caplog.record_tuples == [
            (
                "unused-deps",
                logging.INFO,
                f"Could not find any source files for: {root_package}",
            )
        ]

    def test_falls_back_to_package_detection(self, caplog, tmpdir):
        root_package = "some-package"
        mock_dist = mock.Mock(
            **{"from_name.return_value": InMemoryDistribution({"__init__.py": []})}
        )
        tmpdir.join("__init__.py").ensure()

        with mock.patch(
            "unused_deps.main.detect_package", return_value=root_package
        ) as detect_package_mock, mock.patch(
            "unused_deps.main.importlib_metadata.Distribution", mock_dist
        ), caplog.at_level(
            logging.INFO
        ), tmpdir.as_cwd():
            returncode = main(["--verbose"])

        assert returncode == 0
        assert caplog.record_tuples[0] == (
            "unused-deps",
            logging.INFO,
            f"Detected package: {root_package}",
        )
        assert detect_package_mock.call_args_list == [mock.call(Path("."))]

    def test_dist_with_all_used_deps(self, tmpdir):
        py_lines = ["import some_dep"]
        py_file = tmpdir.join("__init__.py").ensure()
        py_file.write("\n".join(py_lines))
        root_package = "uses-all-deps"
        root_dist = InMemoryDistribution(
            {"requires.txt": ["some-dep"], "__init__.py": py_lines}
        )
        root_dist.add_package("some-dep", {"top_level.txt": ["some_dep"]})
        mock_dist = mock.Mock(**{"from_name.return_value": root_dist})
        argv = ["--package", root_package]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution", mock_dist
        ), tmpdir.as_cwd():
            returncode = main(argv)

        assert returncode == 0

    def test_dist_with_all_used_deps_multiple_top_level(self, tmpdir):
        py_lines = ["import big_dep"]
        py_file = tmpdir.join("__init__.py").ensure()
        py_file.write("\n".join(py_lines))
        root_package = "uses-all-deps"
        root_dist = InMemoryDistribution(
            {"requires.txt": ["big-dep"], "__init__.py": py_lines}
        )
        root_dist.add_package("big-dep", {"top_level.txt": ["big_dep", "_big_dep"]})
        mock_dist = mock.Mock(**{"from_name.return_value": root_dist})
        argv = ["--package", root_package]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution", mock_dist
        ), tmpdir.as_cwd():
            returncode = main(argv)

        assert returncode == 0

    def test_dist_with_unused_deps(self, capsys):
        package_name = "has-unused-deps"
        dep_name = "unused-dep"
        root_dist = InMemoryDistribution({"requires.txt": [dep_name]})
        root_dist.add_package(dep_name, {"top_level.txt": ["some_dep"]})
        mock_dist = mock.Mock(**{"from_name.return_value": root_dist})
        argv = ["--package", package_name]

        with mock.patch("unused_deps.main.importlib_metadata.Distribution", mock_dist):
            returncode = main(argv)

        captured = capsys.readouterr()
        assert returncode == 1
        assert captured.out == ""
        assert captured.err == f"No usage found for: {dep_name}\n"
