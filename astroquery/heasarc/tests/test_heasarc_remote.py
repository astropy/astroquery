# Licensed under a 3-clause BSD style license - see LICENSE.rst

from time import time
import pytest
import requests

from astropy.coordinates import SkyCoord
import astropy.units as u

from ...heasarc import Heasarc
from ...utils import commons

from .parametrization import parametrization_local_save_remote, patch_get, MockResponse


@parametrization_local_save_remote
class TestHeasarc:
    def test_custom_args(self):
        object_name = 'Crab'
        mission = 'intscw'

        heasarc = Heasarc()

        table = heasarc.query_object(object_name,
                                     mission=mission,
                                     radius='1 degree',
                                     time="2020-09-01 .. 2020-12-01",
                                     resultmax=10,
                                     good_isgri=">1000",
                                     cache=False
                                     )

    def test_filter_custom_args(self):
        object_name = 'Crab'
        mission = 'intscw'

        heasarc = Heasarc()

        with pytest.raises(ValueError):
            table = heasarc.query_object(object_name,
                                         mission=mission,
                                         radius='1 degree',
                                         time="2020-09-01 .. 2020-12-01",
                                         resultmax=10,
                                         very_good_isgri=">1000",
                                         )

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

        assert len(cols) >= 29

        print(cols)

        # Test that the cols list contains known names
        assert 'exposure' in cols
        assert 'ra' in cols
        assert 'dec' in cols
        assert 'Search_Offset' in cols

    def test_query_object_async(self):
        mission = 'rosmaster'
        object_name = '3c273'

        heasarc = Heasarc()
        response = heasarc.query_object_async(object_name, mission=mission)
        assert response is not None
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region_async(self):
        heasarc = Heasarc()
        mission = 'rosmaster'
        c = commons.coord.SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
        response = heasarc.query_region_async(c, mission=mission,
                                              radius='1 degree')
        assert response is not None
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region(self):
        heasarc = Heasarc()
        mission = 'rosmaster'

        # Define coordinates for '3c273' object
        c = commons.coord.SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
        table = heasarc.query_region(c, mission=mission, radius='1 degree')

        assert len(table) == 63

    def test_strange_units(self):
        coords = SkyCoord('150.01d 2.2d', frame='icrs')  #COSMOS center acording to Simbad
        #first get an X-ray catalog from Heasarc
        heasarc = Heasarc()
        table = heasarc.query_mission_list()
        mask = (table['Mission'] =="CHANDRA")
        chandratable = table[mask]  


        #want ccosmoscat
        mission = 'ccosmoscat'
        ccosmoscat_rad = 1 #radius of chandra cosmos catalog
        ccosmoscat = heasarc.query_region(coords, mission=mission, radius='1 degree', resultmax = 5000, fields = "ALL")

        #need to make the chandra catalog into a fits table 
        ccosmoscat.write('COSMOS_chandra.fits', overwrite = "True")
