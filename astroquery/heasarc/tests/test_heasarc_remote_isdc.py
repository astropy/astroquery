# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import requests
from astropy.time import Time, TimeDelta
import astropy.units as u

from ...heasarc import Heasarc, Conf
from .conftest import MockResponse, parametrization_local_save_remote, skycoord_3C_273


@parametrization_local_save_remote
class TestHeasarcISDC:

    @pytest.fixture(autouse=True)
    def _patch_get(self, patch_get):
        return patch_get

    @property
    def isdc_context(self):
        return Conf.server.set_temp(
            'https://www.isdc.unige.ch/browse/w3query.pl'
        )

    def test_custom_args(self):
        object_name = 'Crab'
        mission = 'integral_rev3_scw'

        heasarc = Heasarc()

        with self.isdc_context:
            table = heasarc.query_object(
                object_name,
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
        mission = 'integral_rev3_scw'

        heasarc = Heasarc()

        with self.isdc_context:
            with pytest.raises(ValueError):
                heasarc.query_object(
                    object_name,
                    mission=mission,
                    radius='1 degree',
                    time="2020-09-01 .. 2020-12-01",
                    resultmax=10,
                    very_good_isgri=">1000",
                )

    def test_basic_time(self):
        object_name = 'Crab'

        heasarc = Heasarc()

        def Q(mission):
            return heasarc.query_object(
                object_name,
                mission=mission,
                radius='1 degree',
                time="2020-09-01 .. 2020-12-01",
                resultmax=10000
            )

        with self.isdc_context:
            table_isdc = Q('integral_rev3_scw')

        table_heasarc = Q('intscw')

        assert len(table_isdc) == 11
        assert len(table_isdc) == len(table_heasarc)

    def test_compare_time(self, patch_get):
        patch_get.assume_fileid_for_request(
            lambda url, params: f"last-month-{params['tablehead'].split()[-1]}")

        object_name = 'Crab'

        heasarc = Heasarc()

        month_ago = (Time.now() - TimeDelta(30 * u.day)).isot[:10]
        today = Time.now().isot[:10]
        T = month_ago + " .. " + today

        def Q(mission):
            return heasarc.query_object(
                object_name,
                mission=mission,
                time=T,
                resultmax=10000,
                radius='1000 deg'
            )

        with self.isdc_context:
            table_isdc = Q('integral_rev3_scw')

        table_heasarc = Q('intscw')

        # heasarc synchronizes twice a month, and it might or might not be the same at the request time
        assert len(table_isdc) >= len(table_heasarc)

    def test_ra_validity(self):
        object_name = 'Crab'

        heasarc = Heasarc()

        T = "2020-01-01 03:56:30 .. 2020-01-01 04:55:10"

        with self.isdc_context:
            table_isdc = heasarc.query_object(
                object_name,
                mission='integral_rev3_scw',
                time=T,
                resultmax=10000,
                radius='1000 deg'
            )

        table_heasarc = heasarc.query_object(
            object_name,
            mission='intscw',
            time=T,
            resultmax=10000,
            radius='1000 deg'
        )

        assert len(table_isdc) == len(table_heasarc) == 1

        assert table_isdc['SCW_ID'] == table_heasarc['SCW_ID']

        assert 'RA' in table_heasarc.columns
        assert 'RA_X' in table_isdc.columns

        assert abs(float(table_isdc['RA_X'][0]) - float(table_heasarc['RA'][0])) < 0.0001

    def test_basic_example(self):
        mission = 'integral_rev3_scw'
        object_name = '3c273'

        heasarc = Heasarc()

        with self.isdc_context:
            table = heasarc.query_object(
                object_name,
                mission=mission,
                radius='1 degree'
            )

        assert len(table) >= 274

    def test_mission_list(self):
        heasarc = Heasarc()

        with self.isdc_context:
            missions = heasarc.query_mission_list()

        # Assert that there are indeed a large number of tables
        # Number of tables could change, but should be > 900 (currently 956)
        assert len(missions) == 5

    def test_mission_cols(self):
        heasarc = Heasarc()
        mission = 'integral_rev3_scw'

        with self.isdc_context:
            cols = heasarc.query_mission_cols(mission=mission)

        assert len(cols) == 35

        # Test that the cols list contains known names
        assert 'SCW_ID' in cols
        assert 'GOOD_ISGRI' in cols
        assert 'RA_X' in cols
        assert 'DEC_X' in cols
        assert 'SEARCH_OFFSET_' in cols

    def test_query_object_async(self):
        mission = 'integral_rev3_scw'
        object_name = '3c273'

        heasarc = Heasarc()
        response = heasarc.query_object_async(object_name, mission=mission)
        assert response is not None
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region_async(self):
        heasarc = Heasarc()
        mission = 'integral_rev3_scw'

        with self.isdc_context:
            response = heasarc.query_region_async(
                skycoord_3C_273, mission=mission, radius="1 degree")
        assert response is not None
        assert isinstance(response, (requests.models.Response, MockResponse))

    def test_query_region(self):
        heasarc = Heasarc()
        mission = 'integral_rev3_scw'

        with self.isdc_context:
            table = heasarc.query_region(
                skycoord_3C_273, mission=mission, radius="1 degree")

        assert len(table) >= 274
