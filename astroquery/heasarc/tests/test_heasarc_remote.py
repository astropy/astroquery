# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
import requests

from ...heasarc import Heasarc
from ...utils import commons


@pytest.mark.remote_data
class TestHeasarc:

    def test_basic_example(self):
        mission = 'rosmaster'
        object_name = '3c273'

        heasarc = Heasarc()
        table = heasarc.query_object(object_name, mission=mission)

        assert len(table) == 63

    def test_mission_list(self):
        heasarc = Heasarc()
        missions = heasarc.query_mission_list()

        # Assert that there are indeed a large number of tables
        # Number of tables could change, but should be > 900 (currently 956)
        assert len(missions) > 900

    def test_mission_cols(self):
        heasarc = Heasarc()
        mission = 'rosmaster'
        cols = heasarc.query_mission_cols(mission=mission)

        assert len(cols) == 29

        # Test that the cols list contains known names
        assert 'EXPOSURE' in cols
        assert 'RA' in cols
        assert 'DEC' in cols
        assert 'SEARCH_OFFSET_' in cols

    def test_query_object_async(self):
        mission = 'rosmaster'
        object_name = '3c273'

        heasarc = Heasarc()
        response = heasarc.query_object_async(object_name, mission=mission)
        assert response is not None
        assert type(response) is requests.models.Response

    def test_query_region_async(self):
        heasarc = Heasarc()
        mission = 'rosmaster'
        c = commons.coord.SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
        response = heasarc.query_region_async(c, mission=mission,
                                              radius='1 degree')
        assert response is not None
        assert type(response) is requests.models.Response

    def test_query_region(self):
        heasarc = Heasarc()
        mission = 'rosmaster'

        # Define coordinates for '3c273' object
        c = commons.coord.SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
        table = heasarc.query_region(c, mission=mission, radius='1 degree')

        assert len(table) == 63
