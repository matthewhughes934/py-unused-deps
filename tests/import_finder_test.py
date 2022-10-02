from textwrap import dedent

import pytest

from unused_deps.import_finder import get_import_bases


class TestGetImportBases:
    @pytest.mark.parametrize(
        ("code", "expected_base"),
        (
            ("import foo", "foo"),
            ("import foo.bar", "foo"),
            ("import foo as bar", "foo"),
            ("import foo.bar as buz", "foo"),
            ("from foo import bar", "foo"),
            ("from foo import bar, buz", "foo"),
            ("from foo.bar import buz", "foo"),
            ("from foo import bar as buz", "foo"),
            ("from foo.bar import buz as bux", "foo"),
        ),
    )
    def test_get_import_bases_valid_single_lines(self, code, expected_base):
        assert list(get_import_bases(code, "filename")) == [expected_base]

    def test_multiple_valid_lines(self):
        code = dedent(
            """\
            import foo
            import bar

            from foo.something import function
            from something_else import foo
            """
        )
        expected_bases = ["foo", "bar", "foo", "something_else"]

        assert list(get_import_bases(code, "filename")) == expected_bases
