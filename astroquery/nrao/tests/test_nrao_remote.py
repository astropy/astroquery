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
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"),
            retry=5)
        assert response is not None
        assert response.content

    def test_query_region(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"),
            retry=5)
        assert isinstance(result, Table)
        # I don't know why this is byte-typed
        assert b'0430+052' in result['Source']

    def test_query_region_archive(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("05h35.8m 35d43m"), querytype='ARCHIVE',
            retry=5, radius='1d')
        assert len(result) >= 230
        assert 'VLA_XH78003_file15.dat' in result['Archive File']
