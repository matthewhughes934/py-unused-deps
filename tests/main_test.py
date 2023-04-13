from __future__ import annotations

import logging
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
    def test_logging_level_set_from_args(self, args, expected_logging_level):
        main(args + ["--no-distribution"])

        logger = logging.getLogger("unused-deps")
        assert logger.getEffectiveLevel() == expected_logging_level

    @pytest.mark.parametrize(
        "args", ([], ["--distribution", "some-dist", "--no-distribution"])
    )
    def test_failure_when_no_distribution_mode_given(self, capsys, args):
        assert main(args) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert (
            captured.err
            == "Error: You must specify exactly one of '--distribution' or '--no-distribution'\n"
        )

    def test_failure_when_no_package_not_installable(self, tmpdir, capsys):
        package_name = "?invalid-package-name"
        argv = ["--distribution", package_name]

        assert main(argv) == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert (
            captured.err
            == "Error: Could not find metadata for distribution `"
            + package_name
            + "` is it installed?\n"
        )

    @pytest.mark.parametrize("filenames", ([], ["not_python.c"]))
    def test_logs_on_package_with_no_source_files(self, filenames, caplog, tmpdir):
        root_package = "my-package"
        root_dist = InMemoryDistribution({filename: [] for filename in filenames})
        mock_dist = mock.Mock(**{"from_name.return_value": root_dist})
        argv = ["--distribution", root_package, "--verbose"]

        with caplog.at_level(logging.INFO), mock.patch(
            "unused_deps.main.importlib_metadata.Distribution", mock_dist
        ), tmpdir.as_cwd():
            returncode = main(argv)

        assert returncode == 0
        assert (
            "unused-deps",
            logging.INFO,
            "Could not find any source files",
        ) in caplog.record_tuples

    def test_dist_with_all_used_deps(self, tmpdir):
        py_lines = ["import some_dep"]
        py_file = tmpdir.join("__init__.py").ensure()
        py_file.write("\n".join(py_lines))
        root_package = "uses-all-deps"
        root_dist = InMemoryDistribution(
            {"requires.txt": ["some-dep"], "__init__.py": py_lines}
        )
        requirement_dist = InMemoryDistribution(
            {"top_level.txt": ["some_dep"], "METADATA": ["name: some-dep"]}
        )
        argv = ["--distribution", root_package]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution",
            new=mock.Mock(**{"from_name.return_value": root_dist}),
        ), mock.patch(
            "unused_deps.main.required_dists", return_value=[requirement_dist]
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
        requirement_dist = InMemoryDistribution(
            {"top_level.txt": ["big_dep", "_big_dep"], "METADATA": ["name: big-dep"]}
        )
        argv = ["--distribution", root_package]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution",
            new=mock.Mock(**{"from_name.return_value": root_dist}),
        ), mock.patch(
            "unused_deps.main.required_dists", return_value=[requirement_dist]
        ), tmpdir.as_cwd():
            returncode = main(argv)

        assert returncode == 0

    def test_dist_with_unused_deps(self, capsys):
        package_name = "has-unused-deps"
        dep_name = "unused-dep"
        root_dist = InMemoryDistribution({"requires.txt": [dep_name]})
        requirement_dist = InMemoryDistribution(
            {"top_level.txt": ["some_dep"], "METADATA": [f"name: {dep_name}"]}
        )
        argv = ["--distribution", package_name]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution",
            new=mock.Mock(**{"from_name.return_value": root_dist}),
        ), mock.patch(
            "unused_deps.main.required_dists", return_value=[requirement_dist]
        ):
            returncode = main(argv)

        captured = capsys.readouterr()
        assert returncode == 1
        assert captured.out == ""
        assert captured.err == f"No usage found for: {dep_name}\n"

    def test_skips_ignore_dependencies(self, capsys, tmpdir, caplog):
        unused_dep_name = "not-used"
        py_lines = ["import first_dep"]
        py_file = tmpdir.join("__init__.py").ensure()
        py_file.write("\n".join(py_lines))
        root_package = "ignores-unused-dep"
        root_dist = InMemoryDistribution(
            {"requires.txt": ["first-dep", unused_dep_name], "__init__.py": py_lines}
        )
        used_dist = InMemoryDistribution(
            {"top_level.txt": ["first_dep"], "METADATA": ["name: first-dep"]}
        )
        unused_dist = InMemoryDistribution(
            {"top_level.txt": ["use_this"], "METADATA": [f"name: {unused_dep_name}"]}
        )
        argv = ["--distribution", root_package, "--ignore", unused_dep_name]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution",
            new=mock.Mock(**{"from_name.return_value": root_dist}),
        ), mock.patch(
            "unused_deps.main.required_dists", return_value=[used_dist, unused_dist]
        ), tmpdir.as_cwd(), caplog.at_level(
            logging.INFO
        ):
            returncode = main(argv)

        captured = capsys.readouterr()
        assert returncode == 0
        assert caplog.record_tuples == [
            ("unused-deps", logging.INFO, f"Ignoring: {unused_dep_name}")
        ]
        assert captured.err == ""
        assert captured.out == ""

    def test_dist_with_unused_dep_from_requirement(self, capsys, tmpdir):
        requirements_txt = tmpdir.join("requirements.txt").ensure()
        package_name = "has-unused-deps"
        dep_name = "main-test-unused-requirement"
        requirements_txt.write(f"{dep_name}\n")
        root_dist = InMemoryDistribution({})
        requirement_dist = InMemoryDistribution(
            {"top_level.txt": ["some_dep"], "METADATA": [f"name: {dep_name}"]}
        )
        argv = ["--distribution", package_name, "--requirement", str(requirements_txt)]

        with mock.patch(
            "unused_deps.main.importlib_metadata.Distribution",
            new=mock.Mock(**{"from_name.return_value": root_dist}),
        ), mock.patch(
            "unused_deps.main.parse_requirement", return_value=requirement_dist
        ):
            returncode = main(argv)

        captured = capsys.readouterr()
        assert returncode == 1
        assert captured.out == ""
        assert captured.err == f"No usage found for: {dep_name}\n"
