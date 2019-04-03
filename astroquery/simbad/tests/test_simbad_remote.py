# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.tests.helper import remote_data
import astropy.coordinates as coord
import astropy.units as u
from astropy.table import Table
from ...utils.testing_tools import MockResponse
from ... import simbad

# double-check super-undo monkeypatching...
import requests
import imp
imp.reload(requests)

# M42 coordinates
ICRS_COORDS_M42 = coord.SkyCoord("05h35m17.3s -05h23m28s", frame='icrs')
ICRS_COORDS_SgrB2 = coord.SkyCoord(266.835*u.deg, -28.38528*u.deg, frame='icrs')
multicoords = coord.SkyCoord([ICRS_COORDS_M42, ICRS_COORDS_SgrB2])


@remote_data
class TestSimbad(object):

    @classmethod
    def setup_class(cls):
        simbad.core.Simbad.ROW_LIMIT = 5

    def test_query_criteria1(self):
        result = simbad.core.Simbad.query_criteria(
            "region(box, GAL, 49.89 -0.3, 0.5d 0.5d)", otype='HII')
        assert isinstance(result, Table)

    def test_query_criteria2(self):
        result = simbad.core.Simbad.query_criteria(otype='SNR')
        assert isinstance(result, Table)

    def test_query_bibcode_async(self):
        response = simbad.core.Simbad.query_bibcode_async(
            '2006ApJ*', wildcard=True)
        assert response is not None
        response.raise_for_status()
        # make sure requests has *NOT* been monkeypatched
        assert hasattr(response, 'connection')
        assert hasattr(response, 'close')
        assert hasattr(response, 'status_code')
        assert hasattr(response, 'request')
        assert not isinstance(response, MockResponse)
        assert not issubclass(response.__class__, MockResponse)

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
        response = simbad.core.Simbad.query_region_async(
            ICRS_COORDS_M42, radius=5 * u.deg, equinox=2000.0, epoch='J2000')

        assert response is not None

    def test_query_region_async_vector(self):
        response1 = simbad.core.Simbad.query_region_async(multicoords,
                                                          radius=0.5*u.arcsec)
        assert response1.request.body == 'script=votable+%7Bmain_id%2Ccoordinates%7D%0Avotable+open%0Aquery+coo+5%3A35%3A17.3+-80%3A52%3A00+radius%3D0.5s+frame%3DICRS+equi%3D2000.0%0Aquery+coo+17%3A47%3A20.4+-28%3A23%3A07.008+radius%3D0.5s+frame%3DICRS+equi%3D2000.0%0Avotable+close'   # noqa

    def test_query_region(self):
        result = simbad.core.Simbad.query_region(ICRS_COORDS_M42, radius=5 * u.deg,
                                                 equinox=2000.0, epoch='J2000')
        assert isinstance(result, Table)

    def test_query_regions(self):
        result = simbad.core.Simbad.query_region(multicoords, radius=1 * u.arcmin,
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
        # 'gHer' is not a valid Simbad identifier - it should be 'g Her' to
        # get the star
        assert len(result) == 2
        assert len(result.errors) == 1

        # test async
        s = simbad.core.Simbad()
        response = s.query_objects_async(['M32', 'M81'])

        result = s._parse_result(response, simbad.core.SimbadVOTableResult)
        assert len(result) == 2

    def test_query_object_ids(self):
        result = simbad.core.Simbad.query_objectids("Polaris")

        # Today, there are 42 names.  There could be more in the future
        assert len(result) >= 42

    # Test multiple functions correctly return "None" when SIMBAD has no
    # data for the query
    @pytest.mark.parametrize('function', [
        ('query_criteria'),
        ('query_object'),
        ('query_catalog'),
        ('query_bibobj'),
        ('query_bibcode'),
        ('query_objectids')])
    def test_null_response(self, function):
        assert (simbad.core.Simbad.__getattribute__(function)('idonotexist')
                is None)

    # Special case of null test: list of nonexistent parameters
    def test_query_objects_null(self):
        assert simbad.core.Simbad.query_objects(['idonotexist',
                                                 'idonotexisteither']) is None

    # Special case of null test: zero-sized region
    def test_query_region_null(self):
        result = simbad.core.Simbad.query_region(
            coord.SkyCoord("00h01m0.0s 00h00m0.0s"), radius="0d",
            equinox=2000.0, epoch='J2000')
        assert result is None

    # Special case of null test: very small region
    def test_query_small_region_null(self):
        result = simbad.core.Simbad.query_region(
            coord.SkyCoord("00h01m0.0s 00h00m0.0s"), radius=1.0 * u.marcsec,
            equinox=2000.0, epoch='J2000')
        assert result is None

    # Special case : zero-sized region with one object
    def test_query_zero_sized_region(self):
        result = simbad.core.Simbad.query_region(
            coord.SkyCoord("20h54m05.6889s 37d01m17.380s"), radius="1s",
            equinox=2000.0, epoch='J2000')
        # This should find a single star, BD+36 4308
        assert len(result) == 1

    def test_simbad_flux_qual(self):
        '''Regression test for issue 680'''
        request = simbad.core.Simbad()
        request.add_votable_fields("flux_qual(V)")
        response = request.query_object('algol')
        assert("FLUX_QUAL_V" in response.keys())

    def test_multi_vo_fields(self):
        '''Regression test for issue 820'''
        request = simbad.core.Simbad()

        request.add_votable_fields("flux_qual(V)")
        request.add_votable_fields("flux_qual(R)")
        request.add_votable_fields("coo(s)")  # sexagesimal coordinates
        request.add_votable_fields("coo(d)")  # degree coordinates
        request.add_votable_fields("ra(:;A;ICRS;J2000)")
        request.add_votable_fields("ra(:;A;fk5;J2000)")
        request.add_votable_fields("bibcodelist(2000-2006)")
        request.add_votable_fields("bibcodelist(1990-2000)")
        request.add_votable_fields("otype(S)")
        request.add_votable_fields("otype(3)")
        request.add_votable_fields("id(1)")
        request.add_votable_fields("id(2mass)")
        request.add_votable_fields("id(s)")

        response = request.query_object('algol')
        assert("FLUX_QUAL_V" in response.keys())
        assert("FLUX_QUAL_R" in response.keys())
        assert("RA_d" in response.keys())
        assert("RA_s" in response.keys())
        assert("RA___A_ICRS_J2000" in response.keys())
        assert("RA___A_fk5_J2000" in response.keys())
        assert("OTYPE_S" in response.keys())
        assert("OTYPE_3" in response.keys())
        assert("ID_1" in response.keys())
        assert("ID_2mass" in response.keys())
        assert("ID_s" in response.keys())
