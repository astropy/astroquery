# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import pytest, remote_data
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

import requests
import imp

from ... import lco

imp.reload(requests)

@remote_data
class TestLco:

    def test_query_region_async(self):
        response = lco.core.Lco.query_region_async(
            "00h42m44.330s +41d16m07.50s")
        assert response is not None
        assert isinstance(response, Table)
