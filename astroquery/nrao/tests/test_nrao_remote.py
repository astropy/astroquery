# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from astropy.table import Table
import astropy.coordinates as coord
import requests
import imp

from ... import nrao

imp.reload(requests)


@remote_data
class TestNrao:

    def test_query_region_async(self):
        response = nrao.core.Nrao.query_region_async(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"))
        assert response is not None

    def test_query_region(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"))
        assert isinstance(result, Table)
