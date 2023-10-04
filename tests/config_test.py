from argparse import ArgumentParser

import pytest

from unused_deps.config import Config, build_config, load_config_from_file
from unused_deps.errors import InternalError

default_exclude = [
    ".svn",
    "CVS",
    ".bzr",
    ".hg",
    ".git",
    "__pycache__",
    ".tox",
    ".nox",
    ".eggs",
    "*.egg",
    ".venv",
    "venv",
]
default_include = ["*.py", "*.pyi"]


class TestLoadConfig:
    def test_raises_error_when_path_given_but_no_config(self, tmpdir):
        config_file = tmpdir.join("config.toml").ensure()
        config_file.write("[some-other-config-section]")

        with pytest.raises(InternalError) as exc:
            load_config_from_file(str(config_file))

        assert str(exc.value) == f"Could not read config from {config_file}"

    def test_raises_error_when_path_contains_invalid_toml(self, tmpdir):
        config_file = tmpdir.join("config.toml").ensure()
        config_file.write("]] bad toml [[")

        with pytest.raises(InternalError) as exc:
            load_config_from_file(config_file)

        assert str(exc.value).startswith(f"Failed to read TOML file: {config_file}:")

    def test_raises_error_when_path_is_missing_config(self, tmpdir):
        config_file = tmpdir.join("config.toml").ensure()
        config_file.write("[tool.some-other-tool]\nverbose = 1\n")

        with pytest.raises(InternalError) as exc:
            load_config_from_file(config_file)

        assert str(exc.value) == f"Could not read config from {config_file}"

    def test_returns_none_when_no_config(self, tmpdir):
        with tmpdir.as_cwd():
            assert load_config_from_file(None) is None

    def test_returns_config_loaded_from_valid_path(self, tmpdir):
        verbosity = 1
        config_file = tmpdir.join("config.toml").ensure()
        config_file.write(f"[py-unused-deps]\nverbose = {verbosity}\n")
        expected = {"verbose": verbosity}

        assert load_config_from_file(config_file) == expected

    def test_reads_from_configs_in_order_if_none_given(self, tmpdir):
        unused_deps_config_verbosity = 1
        pyproject_toml_config_verbosity = 2
        tmpdir.join(".py-unused-deps.toml").ensure().write(
            f"[py-unused-deps]\nverbose = {unused_deps_config_verbosity}\n"
        )
        tmpdir.join("pyproject.toml").ensure().write(
            f"[tool.py-unused-deps]\nverbose = {pyproject_toml_config_verbosity}\n"
        )

        with tmpdir.as_cwd():
            config = load_config_from_file(None)

        assert config is not None
        assert config["verbose"] == unused_deps_config_verbosity

    def test_skips_unreadable_configs_if_none_given(self, tmpdir):
        verbosity = 1
        tmpdir.join(".py-unused-deps.toml").ensure().write("[some-other-config]")
        tmpdir.join("pyproject.toml").ensure().write(
            f"[tool.py-unused-deps]\nverbose = {verbosity}\n"
        )

        with tmpdir.as_cwd():
            config = load_config_from_file(None)

        assert config is not None
        assert config["verbose"] == verbosity

    def test_returns_none_when_no_path_given_and_no_config(self, tmpdir):
        tmpdir.join(".py-unused-deps.toml").ensure().write("[some-other-config]")
        tmpdir.join("pyproject.toml").ensure().write("[some-other-config]")

        with tmpdir.as_cwd():
            assert load_config_from_file(None) is None


class TestBuildConfig:
    @staticmethod
    def _build_arg_parser():
        parser = ArgumentParser()
        parser.add_argument("--distribution", required=False)
        parser.add_argument("--no-distribution", required=False, default=False)
        parser.add_argument("filepaths", nargs="*")

        return parser

    @pytest.mark.parametrize(
        ("args", "config_from_file", "expected_config"),
        (
            pytest.param(
                [],
                {"verbose": 2, "distribution": None},
                Config(
                    verbose=2,
                    filepaths=["."],
                    include=default_include,
                    exclude=default_exclude,
                ),
                id="Skips None values",
            ),
            pytest.param(
                ["--distribution", "foo"],
                {"verbose": 2},
                Config(
                    verbose=2,
                    distribution="foo",
                    filepaths=["."],
                    include=default_include,
                    exclude=default_exclude,
                ),
                id="Merges values",
            ),
            pytest.param(
                ["--distribution", "foo"],
                {"distribution": "bar"},
                Config(
                    distribution="foo",
                    filepaths=["."],
                    include=default_include,
                    exclude=default_exclude,
                ),
                id="Prioritizes args when merging",
            ),
            pytest.param(
                ["--distribution", "foo"],
                None,
                Config(
                    distribution="foo",
                    filepaths=["."],
                    include=default_include,
                    exclude=default_exclude,
                ),
                id="Handles no config from file",
            ),
        ),
    )
    def test_handles_valid_configs(self, args, config_from_file, expected_config):
        parsed_args = self._build_arg_parser().parse_args(args)

        assert build_config(parsed_args, config_from_file) == expected_config

    def test_raises_error_on_invalid_config_key(self):
        invalid_key = "invalid-key"
        args = self._build_arg_parser().parse_args([])
        config_from_file = {invalid_key: "bar"}

        with pytest.raises(InternalError) as exc:
            build_config(args, config_from_file)

        assert str(exc.value) == f"Unknown configuration values: {invalid_key}"
