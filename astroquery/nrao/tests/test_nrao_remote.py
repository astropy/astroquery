# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from astropy.table import Table
import astropy.coordinates as coord
import requests
import imp
imp.reload(requests)

from ... import nrao


@remote_data
class TestNrao:

    def test_query_region_async(self):
        response = nrao.core.Nrao.query_region_async(coord.ICRS("04h33m11.1s 05d21m15.5s"))
        assert response is not None

    def test_query_region(self):
        result = nrao.core.Nrao.query_region(coord.ICRS("04h33m11.1s 05d21m15.5s"))
        assert isinstance(result, Table)
