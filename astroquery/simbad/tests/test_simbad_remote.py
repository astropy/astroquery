# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import shutil
import tempfile

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table
from astroquery.utils.mocks import MockResponse
from astroquery.simbad import Simbad
# Maybe we need to expose SimbadVOTableResult to be in the public API?
from astroquery.simbad.core import SimbadVOTableResult
from astroquery.exceptions import BlankResponseWarning
from packaging import version
from pyvo import __version__ as pyvo_version
try:
    # This requires pyvo 1.4
    from pyvo.dal.exceptions import DALOverflowWarning
except ImportError:
    pass


# M42 coordinates
ICRS_COORDS_M42 = SkyCoord("05h35m17.3s -05d23m28s", frame='icrs')
ICRS_COORDS_SgrB2 = SkyCoord(266.835*u.deg, -28.38528*u.deg, frame='icrs')
multicoords = SkyCoord([ICRS_COORDS_M42, ICRS_COORDS_SgrB2])


@pytest.mark.remote_data
class TestSimbad:

    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()

        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_query_criteria1(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_criteria(
            "region(box, GAL, 49.89 -0.3, 0.5d 0.5d)", otype='HII')
        assert isinstance(result, Table)

    def test_query_criteria2(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_criteria(otype='SNR')
        assert isinstance(result, Table)

    def test_query_bibcode_async(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        response = simbad.query_bibcode_async(
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

    def test_query_bibcode(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_bibcode('2006ApJ*', wildcard=True)
        assert isinstance(result, Table)

    def test_non_ascii_bibcode(self, temp_dir):
        # regression test for #1775
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_bibcode('2019PASJ...71...55K')
        assert len(result) > 0

    def test_query_bibobj_async(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        response = simbad.query_bibobj_async('2006AJ....131.1163S')
        assert response is not None

    def test_query_bibobj(self, temp_dir):
        simbad = Simbad()
        simbad.ROW_LIMIT = 5
        simbad.cache_location = temp_dir
        result = simbad.query_bibobj('2005A&A.430.165F')
        assert isinstance(result, Table)
        assert len(result) == 5

    def test_query_catalog_async(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        response = simbad.query_catalog_async('m')
        assert response is not None

    def test_query_catalog(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_catalog('m')
        assert isinstance(result, Table)

    def test_query_region_async(self, temp_dir):
        simbad = Simbad()
        simbad.ROW_LIMIT = 100
        simbad.cache_location = temp_dir
        response = simbad.query_region_async(
            ICRS_COORDS_M42, radius=5 * u.arcsec, equinox=2000.0, epoch='J2000')
        # A correct response code
        assert response.status_code == 200
        # Check that Orion was found
        assert "NAME Ori Region" in response.text

    @pytest.mark.parametrize("radius", (0.5 * u.arcsec, "0.5s"))
    def test_query_region_async_vector(self, temp_dir, radius):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        response1 = simbad.query_region_async(multicoords, radius=radius)
        assert response1.request.body == 'script=votable+%7Bmain_id%2Ccoordinates%7D%0Avotable+open%0Aquery+coo+5%3A35%3A17.3+-5%3A23%3A28+radius%3D0.5s+frame%3DICRS+equi%3D2000.0%0Aquery+coo+17%3A47%3A20.4+-28%3A23%3A07.008+radius%3D0.5s+frame%3DICRS+equi%3D2000.0%0Avotable+close'   # noqa

    def test_query_region(self, temp_dir):
        simbad = Simbad()
        simbad.TIMEOUT = 100
        simbad.ROW_LIMIT = 100
        simbad.cache_location = temp_dir
        result = simbad.query_region(ICRS_COORDS_M42, radius=2 * u.deg,
                                     equinox=2000.0, epoch='J2000')
        assert isinstance(result, Table)

    def test_query_regions(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_region(multicoords, radius=1 * u.arcmin,
                                     equinox=2000.0, epoch='J2000')
        assert isinstance(result, Table)

    def test_query_object_async(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        response = simbad.query_object_async("m [0-9]", wildcard=True)
        assert response is not None

    def test_query_object(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_object("m [0-9]", wildcard=True)
        assert isinstance(result, Table)

    def test_query_multi_object(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_objects(['M32', 'M81'])
        assert len(result) == 2
        assert len(result.errors) == 0

        with pytest.warns(BlankResponseWarning):
            result = simbad.query_objects(['M32', 'M81', 'gHer'])
        # 'gHer' is not a valid Simbad identifier - it should be 'g Her' to
        # get the star
        assert len(result) == 2
        assert len(result.errors) == 1

        # test async
        s = Simbad()
        response = s.query_objects_async(['M32', 'M81'])

        result = s._parse_result(response, SimbadVOTableResult)
        assert len(result) == 2

    def test_query_object_ids(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_objectids("Polaris")

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
    def test_null_response(self, temp_dir, function):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        with pytest.warns(BlankResponseWarning):
            assert (simbad.__getattribute__(function)('idonotexist')
                    is None)

    # Special case of null test: list of nonexistent parameters
    def test_query_objects_null(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        with pytest.warns(BlankResponseWarning):
            assert simbad.query_objects(['idonotexist', 'idonotexisteither']) is None

    # Special case of null test: zero-size and very small region
    @pytest.mark.parametrize('radius', ["0d", 1.0*u.marcsec])
    def test_query_region_null(self, temp_dir, radius):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        with pytest.warns(BlankResponseWarning):
            result = simbad.query_region(SkyCoord("00h01m0.0s 00h00m0.0s"), radius=1.0 * u.marcsec,
                                         equinox=2000.0, epoch='J2000')
        assert result is None

    # Special case : zero-sized region with one object
    def test_query_zero_sized_region(self, temp_dir):
        simbad = Simbad()
        simbad.cache_location = temp_dir
        result = simbad.query_region(SkyCoord("20h54m05.6889s 37d01m17.380s"), radius="1s",
                                     equinox=2000.0, epoch='J2000')
        # This should find a single star, BD+36 4308
        assert len(result) == 1

    def test_simbad_flux_qual(self):
        '''Regression test for issue 680'''
        request = Simbad()
        request.add_votable_fields("flux_qual(V)")
        response = request.query_object('algol')
        assert ("FLUX_QUAL_V" in response.keys())

    def test_multi_vo_fields(self):
        '''Regression test for issue 820'''
        request = Simbad()

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
        assert ("FLUX_QUAL_V" in response.keys())
        assert ("FLUX_QUAL_R" in response.keys())
        assert ("RA_d" in response.keys())
        assert ("RA_s" in response.keys())
        assert ("RA___A_ICRS_J2000" in response.keys())
        assert ("RA___A_fk5_J2000" in response.keys())
        assert ("OTYPE_S" in response.keys())
        assert ("OTYPE_3" in response.keys())
        assert ("ID_1" in response.keys())
        assert ("ID_2mass" in response.keys())
        assert ("ID_s" in response.keys())

    def test_query_tap(self):
        # a robust query about something that should not change in Simbad
        filtername = Simbad.query_tap("select filtername from filter where filtername='B'")
        assert 'B' == filtername["filtername"][0]
        # test uploads by joining two local tables
        table_letters = Table([["a", "b", "c"]], names=["letters"])
        table_numbers = Table([[1, 2, 3], ["a", "b", "c"]], names=["numbers", "letters"])
        result = Simbad.query_tap("SELECT * FROM TAP_UPLOAD.numbers "
                                  "JOIN TAP_UPLOAD.letters USING(letters)",
                                  numbers=table_numbers, letters=table_letters)
        expect = "letters numbers\n------- -------\n      a       1\n      b       2\n      c       3"
        assert expect == str(result)
        # Test query_tap raised errors
        # DALOverflowWarning exists since pyvo 1.4
        if version.parse(pyvo_version) > version.parse('1.4'):
            with pytest.raises(DALOverflowWarning, match="Partial result set *"):
                truncated_result = Simbad.query_tap("SELECT * from basic", maxrec=2)
                assert len(truncated_result) == 2
        with pytest.raises(ValueError, match="The maximum number of records cannot exceed 2000000."):
            Simbad.query_tap("select top 5 * from basic", maxrec=10e10)
        with pytest.raises(ValueError, match="Query string contains an odd number of single quotes.*"):
            Simbad.query_tap("'''")

    def test_simbad_list_tables(self):
        tables = Simbad.list_tables()
        # check the content
        assert "basic" in str(tables)
        # there might be new tables, we have 30 now.
        assert len(tables) >= 30

    def test_simbad_list_columns(self):
        columns = Simbad.list_columns("ident", "biblio")
        assert len(columns) == 4
        assert "oidref" in str(columns)
        columns = Simbad.list_columns(keyword="herschel")
        assert {"mesHerschel"} == set(columns["table_name"])

    def test_list_linked_tables(self):
        links = Simbad.list_linked_tables("h_link")
        assert {"basic"} == set(links["target_table"])
