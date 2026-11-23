# Licensed under a 3-clause BSD style license - see LICENSE.rst
import builtins
import pytest
from astroquery.exceptions import TimeoutError, EmptyResponseError


def test_timeout_error_subclasses_builtin():
    assert issubclass(TimeoutError, builtins.TimeoutError)
    assert issubclass(TimeoutError, Exception)

    with pytest.raises(builtins.TimeoutError):
        raise TimeoutError("Connection timed out")

    with pytest.raises(TimeoutError):
        raise TimeoutError("Connection timed out")


def test_empty_response_error_subclasses_builtin():
    assert issubclass(EmptyResponseError, ValueError)
