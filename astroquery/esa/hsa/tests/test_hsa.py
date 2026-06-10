# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import pytest

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyDeprecationWarning
from ..core import HSAClass
from ..tests.dummy_tap_handler import DummyHSATapHandler


class TestHSA:
    def get_dummy_tap_handler(self):
        parameterst = {'query': "select top 10 * from hsa.v_active_observation",
                       'output_file': "test.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHSATapHandler("launch_job", parameterst)
        return dummyTapHandler
        os.remove("test.vot")

    def test_query_hsa_tap(self):
        parameters = {'query': "select top 10 * from hsa.v_active_observation",
                      'output_file': "test.vot",
                      'output_format': "votable",
                      'verbose': False}
        hsa = HSAClass(self.get_dummy_tap_handler())
        hsa.query_hsa_tap(**parameters)
        self.get_dummy_tap_handler().check_call("launch_job", parameters)
        self.get_dummy_tap_handler().check_parameters(parameters, "launch_job")
        self.get_dummy_tap_handler().check_method("launch_job")
        self.get_dummy_tap_handler().get_tables()
        self.get_dummy_tap_handler().get_columns()
        self.get_dummy_tap_handler().load_tables()

    def test_get_tables(self):
        parameters = {'only_names': True,
                      'verbose': True}
        dummyTapHandler = DummyHSATapHandler("get_tables", parameters)
        hsa = HSAClass(self.get_dummy_tap_handler())
        hsa.get_tables(**parameters)
        dummyTapHandler.check_call("get_tables", parameters)

    def test_get_columns(self):
        parameters = {'table_name': "table",
                      'only_names': True,
                      'verbose': True}
        dummyTapHandler = DummyHSATapHandler("get_columns", parameters)
        hsa = HSAClass(self.get_dummy_tap_handler())
        hsa.get_columns(**parameters)
        dummyTapHandler.check_call("get_columns", parameters)

    def test_query_observations(self):
        c = SkyCoord(ra=100.2417*u.degree, dec=9.895*u.degree, frame='icrs')
        parameters = {'coordinates': c,
                      'radius': 0.5}
        dummyTapHandler = DummyHSATapHandler("query_observations", parameters)
        hsa = HSAClass(self.get_dummy_tap_handler())
        hsa.query_observations(**parameters)
        dummyTapHandler.check_call("query_observations", parameters)

    def test_query_region(self):
        c = SkyCoord(ra=100.2417*u.degree, dec=9.895*u.degree, frame='icrs')
        parameters = {'coordinates': c,
                      'radius': 0.5}
        dummyTapHandler = DummyHSATapHandler("query_region", parameters)
        hsa = HSAClass(self.get_dummy_tap_handler())
        hsa.query_region(**parameters)
        dummyTapHandler.check_call("query_region", parameters)

    def test_query_region_multiple_coordinates(self):
        coords = SkyCoord(ra=[100.2417, 101.2417]*u.degree,
                          dec=[9.895, 10.895]*u.degree, frame='icrs')
        hsa = HSAClass(self.get_dummy_tap_handler())
        result = hsa.query_region(coordinates=coords, radius=0.5)
        # The dummy TAP handler's launch_job returns a Job with no results
        # and no output file, so each per-position query returns None and
        # the combined result is a plain list with one entry per position.
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(entry is None for entry in result)

    def test_query_region_deprecated_coordinate(self):
        c = SkyCoord(ra=100.2417*u.degree, dec=9.895*u.degree, frame='icrs')
        hsa = HSAClass(self.get_dummy_tap_handler())
        with pytest.warns(AstropyDeprecationWarning, match="coordinate"):
            hsa.query_region(coordinate=c, radius=0.5)
        with pytest.warns(AstropyDeprecationWarning, match="coordinate"):
            hsa.query_observations(coordinate=c, radius=0.5)
