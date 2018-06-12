# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest
from astropy.tests.helper import remote_data


@remote_data
class TestTemplateClass:
    # now write tests for each method here
    def test_this(self):
        pass
