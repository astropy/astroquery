# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import simbad
from astropy.tests.helper import remote_data
import astropy.coordinates as coord
import astropy.units as u
from astropy.table import Table
import sys
from ...utils.testing_tools import MockResponse
is_python3 = (sys.version_info >= (3,))

# double-check super-undo monkeypatching...
import requests
reload(requests)


ICRS_COORDS = coord.ICRSCoordinates("05h35m17.3s -05h23m28s")


@remote_data
class TestSimbad(object):

    @classmethod
    def setup_class(cls):
        simbad.core.Simbad.ROW_LIMIT = 5

    def test_query_criteria1(self):
        result = simbad.core.Simbad.query_criteria("region(box, GAL, 49.89 -0.3, 0.5d 0.5d)", otype='HII')
        assert isinstance(result, Table)

    def test_query_criteria2(self):
        result = simbad.core.Simbad.query_criteria(otype='SNR')
        assert isinstance(result, Table)

    def test_query_bibcode_async(self):
        response = simbad.core.Simbad.query_bibcode_async('2006ApJ*', wildcard=True)
        assert response is not None
        response.raise_for_status()
        # make sure requests has *NOT* been monkeypatched
        assert hasattr(response,'connection')
        assert hasattr(response,'close')
        assert hasattr(response,'status_code')
        assert hasattr(response,'request')
        assert not isinstance(response,MockResponse)
        assert not issubclass(response.__class__,MockResponse)

    def test_query_bibcode(self):
        result = simbad.core.Simbad.query_bibcode('2006ApJ*', wildcard=True)
        assert isinstance(result, Table)

    def test_query_bibobj_async(self):
        response = simbad.core.Simbad.query_bibobj_async('2005A&A.430.165F')
        assert response is not None

    def test_query_bibobj(self):
        result = simbad.core.Simbad.query_bibobj('2005A&A.430.165F')
        assert isinstance(result, Table)

    def test_query_catalog_async(self):
        response = simbad.core.Simbad.query_catalog_async('m')
        assert response is not None

    def test_query_catalog(self):
        result = simbad.core.Simbad.query_catalog('m')
        assert isinstance(result, Table)

    def test_query_region_async(self):
        response = simbad.core.Simbad.query_region_async(ICRS_COORDS, radius=5*u.deg,
                                                        equinox=2000.0, epoch='J2000')
        assert response is not None

    def test_query_region(self):
        result = simbad.core.Simbad.query_region(ICRS_COORDS, radius=5*u.deg,
                                                equinox=2000.0, epoch='J2000')
        assert isinstance(result, Table)

    def test_query_object_async(self):
        response = simbad.core.Simbad.query_object_async("m [0-9]",
                                                        wildcard=True)
        assert response is not None

    def test_query_object(self):
        result = simbad.core.Simbad.query_object("m [0-9]", wildcard=True)
        assert isinstance(result, Table)

    def test_query_multi_object(self):
        result = simbad.core.Simbad.query_objects(['M32', 'M81'])
        assert len(result) == 2
        assert len(result.errors) == 0

        result = simbad.core.Simbad.query_objects(['M32', 'M81', 'gHer'])
        #'gHer' is not a valid Simbad identifier - it should be 'g Her' to get the star
        assert len(result) == 2
        assert len(result.errors) == 1

        #test async
        s = simbad.core.Simbad()
        response = s.query_objects_async(['M32', 'M81'])

        result = s._parse_result(response)
        assert len(result) == 1

