# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import numpy as np

from astropy.tests.helper import remote_data
from astropy.table import Table
import astropy.units as u

from ... import nist


@remote_data
class TestNist:

    def test_query_async(self):
        response = nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm)
        assert response is not None

    def test_query(self):
        result = nist.core.Nist.query(4000 * u.nm, 7000 * u.nm)
        assert isinstance(result, Table)

        # check that no javascript was left in the table
        # (regression test for 1355)
        assert np.all(result['TP'] == 'T8637')
