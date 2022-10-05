from __future__ import annotations

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
