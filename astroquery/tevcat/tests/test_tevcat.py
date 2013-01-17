# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
from ... import tevcat


@remote_data
def test_tevcat():
    table = tevcat.get_tevcat()
    assert len(table) > 100
