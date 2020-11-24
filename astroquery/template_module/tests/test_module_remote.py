# Licensed under a 3-clause BSD style license - see LICENSE.rst


# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest


@pytest.mark.remote_data
class TestTemplateClass:
    # now write tests for each method here
    def test_this(self):
        pass
