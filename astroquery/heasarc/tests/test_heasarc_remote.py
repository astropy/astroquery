# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import requests

from ...heasarc import Heasarc

from .conftest import MockResponse, parametrization_local_save_remote, skycoord_3C_273

from astroquery.exceptions import NoResultsWarning

from astropy.coordinates import SkyCoord
from astropy import units as u


@parametrization_local_save_remote
class TestHeasarc:

    @pytest.fixture(autouse=True)
    def _patch_get(self, patch_get):
        return patch_get

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
        assert len(table) > 0

    def test_filter_custom_args(self):
        object_name = 'Crab'
        mission = 'intscw'

        heasarc = Heasarc()

        with pytest.raises(ValueError):
            heasarc.query_object(object_name,
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
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region_async(self):
        heasarc = Heasarc()
        mission = 'rosmaster'
        response = heasarc.query_region_async(
            skycoord_3C_273, mission=mission, radius="1 degree")
        assert response is not None
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region(self):
        heasarc = Heasarc()
        mission = 'rosmaster'

        table = heasarc.query_region(
            skycoord_3C_273, mission=mission, radius="1 degree")

        assert len(table) == 63

    def test_query_region_nohits(self):
        """
        Regression test for #2560: HEASARC returns a FITS file as a null result
        """
        heasarc = Heasarc()

        with pytest.warns(NoResultsWarning, match='No matching rows were found in the query.'):
            # This was an example coordinate that returned nothing
            # Since Fermi is still active, it is possible that sometime in the
            # future an event will occur here.
            table = heasarc.query_region(SkyCoord(0.28136*u.deg, -0.09789*u.deg, frame='fk5'),
                                         mission='fermilpsc', radius=0.1*u.deg)

        assert len(table) == 0
        # this is to check that the header comments got parsed correctly
        # I'm not certain that they will always be returned in the same order,
        # so it may be necessary in the future to change this part of the test
        assert 'heasarc_fermilpsc' in table.meta['COMMENT'][0]
