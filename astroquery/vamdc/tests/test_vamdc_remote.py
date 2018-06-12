# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest

from astropy.tests.helper import remote_data

try:
    from ... import vamdc
    import vamdclib
    HAS_VAMDCLIB = True
except ImportError:
    HAS_VAMDCLIB = False


@pytest.mark.skipif('not HAS_VAMDCLIB')
@remote_data
class TestVamdcClass:
    # now write tests for each method here
    def test_query_molecule(self):
        ch3oh = vamdc.core.VamdcClass().query_molecule('CH3OH')
        assert 'SCDMS-2369983' in ch3oh.data['States']
