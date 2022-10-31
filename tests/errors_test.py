from io import StringIO

import pytest

from unused_deps.errors import InternalError, log_error


@pytest.mark.parametrize(
    ("exception", "expected_out", "expected_return_value"),
    (
        (InternalError("It broke!"), "Error: It broke!", 1),
        (KeyboardInterrupt(), "Interrupted (^C)", 130),
        (ValueError("Bad value"), "Fatal: unexpected error: 'Bad value'", 2),
    ),
)
def test_log_error(exception, expected_out, expected_return_value):
    assert log_error(exception) == (expected_return_value, expected_out)
