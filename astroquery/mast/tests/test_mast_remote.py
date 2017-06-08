# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from astropy.table import Table

from ... import mast


@remote_data
class TestMast(object):

    # MastClass tests
    def test_mast_service_request_async(self):
        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.2}

        responses = mast.Mast.service_request_async(service, params)

        assert isinstance(responses, list)

    def test_mast_service_request(self):
        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.2}

        result = mast.Mast.service_request(service, params)

        assert isinstance(result, Table)

    # ObservationsClass tests
    def test_observations_query_region_async(self):
        responses = mast.Observations.query_region_async("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(responses, list)

    def test_observations_query_region(self):
        result = mast.Observations.query_region("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, Table)

    def test_observations_query_object_async(self):
        responses = mast.Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):
        result = mast.Observations.query_object("M8", radius=".02 deg")
        assert isinstance(result, Table)
