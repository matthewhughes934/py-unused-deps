from textwrap import dedent

import pytest

from unused_deps.dist_detector import detect_dist


class TestDetectPackage:
    def test_detects_package_from_setupcfg_metadata(self, tmpdir):
        package_name = "my-package"
        setup_cfg_content = dedent(
            f"""\
            [metadata]
            name = {package_name}
        """
        )
        setup_cfg = tmpdir.join("setup.cfg")
        setup_cfg.write(setup_cfg_content)

        assert detect_dist(tmpdir) == package_name

    @pytest.mark.parametrize(
        "setup_cfg_contents",
        (
            dedent(
                """\
                [metadata]
                version = 1.0.0
            """
            ),
            (""),
        ),
    )
    def test_does_not_detect_dist_from_setup_cfg_if_missing(
        self, tmpdir, setup_cfg_contents
    ):
        setup_cfg = tmpdir.join("setup.cfg")
        setup_cfg.write(setup_cfg_contents)

        assert detect_dist(tmpdir) is None

    @pytest.mark.parametrize(
        "setup_py_contents",
        (
            dedent(
                """\
                from setuptools import setup
                setup(name="{}")
            """
            ),
            dedent(
                """\
                import setuptools
                setuptools.setup(name="{}")
            """
            ),
            dedent(
                """\
                import setuptools
                some_other_function(name="hello")
                setuptools.setup(name="{}")
            """
            ),
            dedent(
                """\
                import setuptools

                def setup():
                    pass

                # note: not handling the case where there's a custom 'setup' function
                # taking 'name' as a string
                setup(name=12)
                setuptools.setup(name="{}")
            """
            ),
        ),
    )
    def test_detects_package_from_setup_py_setup_call(self, tmpdir, setup_py_contents):
        package_name = "my-package"
        setup_py = tmpdir.join("setup.py")
        setup_py.write(setup_py_contents.format(package_name))

        assert detect_dist(tmpdir) == package_name

    @pytest.mark.parametrize(
        "setup_py_contents",
        (
            pytest.param(
                dedent(
                    """\
                import setuptools
                package_name = "{package_name}"
                setuptools.setup(name=package_name)
            """
                ),
                id="Package name stored in variable",
            ),
            pytest.param(
                dedent(
                    """\
                import setuptools
                metadata = {{"name": "{package_name}"}}
                setuptools.setup(**metadata)
            """
                ),
                id="Setup params stored in variable",
            ),
        ),
    )
    def test_unhandled_setup_py_constructs(self, tmpdir, setup_py_contents):
        package_name = "my-package"
        setup_py = tmpdir.join("setup.py")
        setup_py.write(setup_py_contents.format(package_name=package_name))

        assert detect_dist(tmpdir) is None

    @pytest.mark.parametrize(
        "pyproject_toml_contents",
        (
            dedent(
                """\
            [tool.poetry]
            name = "{package_name}"
        """
            ),
            dedent(
                """\
            [project]
            name = "{package_name}"
        """
            ),
        ),
    )
    def test_detects_package_name_from_pyproject_toml(
        self, tmpdir, pyproject_toml_contents
    ):
        package_name = "my-package"
        pyproject_toml = tmpdir.join("pyproject.toml")
        pyproject_toml.write(pyproject_toml_contents.format(package_name=package_name))

        assert detect_dist(tmpdir) == package_name

    @pytest.mark.parametrize(
        ("pyproject_toml_contents", "expected_error_location"),
        (
            (
                dedent(
                    """\
            [tool.poetry]
            name = 12
        """
                ),
                "[tool][poetry][name]",
            ),
            (
                dedent(
                    """\
            [project]
            name = 12
        """
                ),
                "[project][name]",
            ),
        ),
    )
    def test_raises_valueerror_on_non_str_name_in_pyproject_toml(
        self, tmpdir, pyproject_toml_contents, expected_error_location
    ):
        pyproject_toml = tmpdir.join("pyproject.toml")
        pyproject_toml.write(pyproject_toml_contents)

        with pytest.raises(ValueError) as exc:
            detect_dist(tmpdir)

        assert (
            str(exc.value)
            == "Expected a name at "
            + expected_error_location
            + " but found non-string: 12"
        )

    def test_does_not_detect_dist_from_pyproject_toml_if_missing(self, tmpdir):
        pyproject_toml = tmpdir.join("pyproject.toml")
        pyproject_toml.write("[too.black]\nline-length = 100\n")

        assert detect_dist(tmpdir) is None