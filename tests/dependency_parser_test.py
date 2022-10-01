import pytest

from unused_deps.dependency_parser import PackageInfo, get_name_from_spec


class TestGetNameFromSpec:
    @pytest.mark.parametrize(
        "invalid_spec",
        (
            "-bad-package-name",
            "!also-not-package",
            "-bad-package-name valid_package_name",
        ),
    )
    def test_returns_none_for_invalid_specifications(self, invalid_spec):
        assert get_name_from_spec(invalid_spec) is None

    @pytest.mark.parametrize(
        ("spec", "expected_package_info"),
        (
            ('argparse;python_version<"2.7"', PackageInfo("argparse", None)),
            ('tomli; python_version <= "3.10"', PackageInfo("tomli", None)),
            ("pytest", PackageInfo("pytest", None)),
            ("\tpytest", PackageInfo("pytest", None)),
            ("  pytest", PackageInfo("pytest", None)),
            ("  \t \tpytest", PackageInfo("pytest", None)),
            (
                "pip @ https://github.com/pypa/pip/archive/1.3.1.zip#sha1=da9234ee9982d4bbb3c72346a6de940a148ea686",
                PackageInfo("pip", None),
            ),
            (
                "requests[security,tests]",
                PackageInfo("requests", None),
            ),
            (
                'requests [security,tests] >= 2.8.1, == 2.8.* ; python_version < "2.7"',
                PackageInfo("requests", None),
            ),
            ('flake8; extra == "testing"', PackageInfo("flake8", "testing")),
            ('flake8;extra == "testing"', PackageInfo("flake8", "testing")),
            ('flake8;\textra== "testing"', PackageInfo("flake8", "testing")),
            ('flake8;\textra=="testing"', PackageInfo("flake8", "testing")),
            ('flake8;\textra==\t "testing"', PackageInfo("flake8", "testing")),
        ),
    )
    def test_valid_specs(self, spec, expected_package_info):
        assert get_name_from_spec(spec) == expected_package_info
