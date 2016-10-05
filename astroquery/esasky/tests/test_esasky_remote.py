# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.table import Table
from astropy.tests.helper import remote_data

from ... import esasky

@remote_data
class TestESASky:
        
    def test_esasky_query_region_maps(self):
        result = esasky.core.ESASkyClass().query_region_maps("M51", "5 arcmin")
        assert isinstance(result, Table)

    def test_esasky_query_object_maps(self):
        result = esasky.core.ESASkyClass().query_object_maps("M51")
        assert isinstance(result, Table)
        
    def test_esasky_query_region_catalogs(self):
        result = esasky.core.ESASkyClass().query_region_catalogs("M51", "5 arcmin")
        assert isinstance(result, Table)
        
    def test_esasky_query_object_catalogs(self):
        result = esasky.core.ESASkyClass().query_object_maps("M51")
        assert isinstance(result, Table)
        
