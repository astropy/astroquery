# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

from astropy.tests.helper import remote_data, pytest
from ... import esasky



@remote_data
def test_esasky_list_catalogs():
    result = esasky.core.ESASkyClass().list_catalogs()
    assert(len(result) == 13)
