# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import pytest

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.utils.exceptions import AstropyDeprecationWarning
from astropy.table import Table

from astroquery.exceptions import NoResultsWarning
from astroquery.simbad import Simbad
from astroquery.simbad.core import _cached_query_tap, _Column, _Join

from pyvo.dal.exceptions import DALOverflowWarning

# this is for the very slow tests
SKIP_SLOW = True

# M42 coordinates
ICRS_COORDS_M42 = SkyCoord("05h35m17.3s -05d23m28s", frame='icrs')
ICRS_COORDS_SgrB2 = SkyCoord(266.835*u.deg, -28.38528*u.deg, frame='icrs')
multicoords = SkyCoord([ICRS_COORDS_SgrB2, ICRS_COORDS_SgrB2])


@pytest.mark.remote_data()
class TestSimbad:

    simbad = Simbad()

    def test_query_bibcode(self):
        self.simbad.ROW_LIMIT = 20
        # wildcard option
        refs = self.simbad.query_bibcode('2006ApJ*', wildcard=True)
        assert set(refs["journal"]).issubset({"ApJ", "ApJS"})
        assert "abstract" not in refs.colnames
        assert len(refs) == 20  # we applied the ROW_LIMIT

    def test_non_ascii_bibcode(self):
        # regression test for #1775
        ref = self.simbad.query_bibcode('2019PASJ...71...55K', abstract=True)
        assert ref["title"][0].startswith("The dominant origin of diffuse Lyα halos")
        # we also check the abstract option here
        assert "abstract" in ref.colnames

    def test_query_bibobj(self):
        self.simbad.ROW_LIMIT = 5
        self.simbad.add_votable_fields("otype")
        bibcode = '2005A&A...430..165F'
        result = self.simbad.query_bibobj(bibcode, criteria="otype='*..'")
        assert all((bibcode == code) for code in result["bibcode"].data.data)
        assert all(('*' in otype) for otype in result["otype"].data.data)
        self.simbad.reset_votable_fields()

    def test_query_catalog(self):
        self.simbad.ROW_LIMIT = -1
        result = self.simbad.query_catalog('M')
        assert len(result) == 110

    def test_query_hierarchy(self):
        self.simbad.ROW_LIMIT = -1
        obj = "NGC 4038"
        parents = self.simbad.query_hierarchy(obj, hierarchy="parents")
        assert len(parents) == 4
        children = self.simbad.query_hierarchy(obj, hierarchy="children")
        assert len(children) >= 45  # as of 2025, but more could be added
        siblings = self.simbad.query_hierarchy(obj, hierarchy="siblings",
                                               criteria="otype='G..'")
        assert len(siblings) >= 29

    def test_query_region(self):
        self.simbad.ROW_LIMIT = 10
        result = self.simbad.query_region(ICRS_COORDS_M42, radius="1d")
        assert all(ra > 83 and ra < 85 for ra in result["ra"].data.data)

    def test_query_regions(self):
        self.simbad.ROW_LIMIT = 10
        result = self.simbad.query_region(SkyCoord([SkyCoord.from_name('m81'),
                                                    SkyCoord.from_name('m10')]),
                                          radius=1 * u.arcmin, criteria="main_id LIKE 'M %'")
        # filtering on main_id to retrieve the two cone centers
        assert {"M  81", "M  10"} == set(result["main_id"].data.data)

    def test_query_regions_long_list(self):
        self.simbad.ROW_LIMIT = -1
        # we create a list of centers longer than 300 to trigger the TAP upload case
        centers = SkyCoord(np.arange(0, 360, 1), np.arange(0, 180, 0.5) - 90, unit="deg")
        result = self.simbad.query_region(centers, radius="1m")
        assert len(result) > 90

    def test_query_object_ids(self):
        self.simbad.ROW_LIMIT = -1
        result = self.simbad.query_objectids("Polaris")
        # Today, there are 42 names.  There could be more in the future
        assert len(result) >= 42

    def test_query_multi_object(self):
        result = self.simbad.query_objects(['M32', 'M81'])
        assert len(result) == 2
        # check that adding fields preserves the left join
        self.simbad.add_votable_fields("mesdistance", "otype")
        result = self.simbad.query_objects(['M32', 'M81', 'gHer'])
        # 'gHer' is not a valid Simbad identifier - it should be 'g Her' to
        # get the star. This appears as an empty line corresponding to
        # 'object_number_id' = 3
        assert max(result["object_number_id"]) == 3
        self.simbad.reset_votable_fields()

    @pytest.mark.skipif("SKIP_SLOW")  # ~300 seconds (has to regexp all the database twice!)
    def test_query_multi_object_wildcard(self):
        # with wildcards
        result = self.simbad.query_objects(['*Crab*', '*Bubble*'], wildcard=True)
        assert len(result) >= 23

    def test_simbad_flux_qual(self):
        '''Regression test for issue 680'''
        simbad_instance = Simbad()
        simbad_instance.add_votable_fields("flux")
        response = simbad_instance.query_object('algol', criteria="filter='V'")
        assert "flux.qual" in response.colnames
        assert response["flux.filter"][0] == "V"

    def test_query_object(self):
        self.simbad.ROW_LIMIT = 5
        result = self.simbad.query_object("NGC [0-9]*", wildcard=True)
        assert all(matched_id.startswith("NGC") for matched_id in result["matched_id"].data.data)

    def test_query_object_with_measurement_table(self):
        # regression for #3197
        self.simbad.reset_votable_fields()
        self.simbad.add_votable_fields("mesdistance")
        vega = self.simbad.query_object("vega")
        # there is one response line
        assert len(vega) == 1
        # even if the measurement table is empty
        assert bool(vega["mesdistance.dist"][0].mask)

    def test_query_criteria(self):
        simbad_instance = Simbad()
        simbad_instance.add_votable_fields("otype")
        with pytest.warns(AstropyDeprecationWarning, match="'query_criteria' is deprecated*"):
            result = simbad_instance.query_criteria("region(Galactic Center, 10s)", maintype="X")
            assert all(result["otype"].data.data == "X")
            assert len(result) >= 16  # there could be more measurements, there are 16 sources in 2024

    def test_query_tap(self):
        # a robust query about something that should not change in Simbad
        filtername = self.simbad.query_tap("select filtername from filter where filtername='B'")
        assert filtername["filtername"][0] == 'B'
        # test uploads by joining two local tables
        table_letters = Table([["a", "b", "c"]], names=["letters"])
        table_numbers = Table([[1, 2, 3], ["a", "b", "c"]], names=["numbers", "letters"])
        result = self.simbad.query_tap("SELECT * FROM TAP_UPLOAD.numbers "
                                       "JOIN TAP_UPLOAD.letters USING(letters)",
                                       numbers=table_numbers, letters=table_letters)
        expect = ("letters numbers\n------- -------\n      a       1\n      b       2\n"
                  "      c       3")
        assert expect == str(result)
        # Test query_tap raised errors
        with pytest.warns(DALOverflowWarning, match="Partial result set *"):
            truncated_result = Simbad.query_tap("SELECT * from basic", maxrec=2)
            assert len(truncated_result) == 2
        with pytest.raises(ValueError, match="The maximum number of records cannot exceed 2000000."):
            Simbad.query_tap("select top 5 * from basic", maxrec=10e10)
        with pytest.raises(ValueError, match="Query string contains an odd number of single quotes.*"):
            Simbad.query_tap("'''")
        # test the cache
        assert _cached_query_tap.cache_info().currsize != 0
        Simbad.clear_cache()
        assert _cached_query_tap.cache_info().currsize == 0

    def test_empty_response_warns(self):
        with pytest.warns(NoResultsWarning, match="The request executed correctly, but *"):
            # a catalog that does not exists should return an empty response
            Simbad.query_catalog("unknown_catalog")

    # ----------------------------------

    def test_simbad_list_tables(self):
        tables = Simbad.list_tables()
        # check the content
        assert "basic" in str(tables)
        # there might be new tables, we have 30 now.
        assert len(tables) >= 30

    def test_simbad_list_columns(self):
        columns = Simbad.list_columns("ident", "bibliO")  # this should be case insensitive
        assert len(columns) == 4
        assert "oidref" in str(columns)
        columns = Simbad.list_columns(keyword="herschel")
        assert {"mesHerschel"} == set(columns["table_name"])

    def test_list_linked_tables(self):
        links = Simbad.list_linked_tables("h_link")
        assert {"basic"} == set(links["target_table"])

    # ----------------------------------

    def test_add_bundle_to_output(self):
        simbad_instance = Simbad()
        # empty before the test
        simbad_instance.columns_in_output = []
        # add a bundle
        simbad_instance.add_votable_fields("dim")
        # check the length
        assert len(simbad_instance.columns_in_output) == 8
        assert _Column("basic", "galdim_majaxis") in simbad_instance.columns_in_output

    def test_add_votable_fields(self):
        simbad_instance = Simbad()
        # empty before the test
        simbad_instance.columns_in_output = []
        simbad_instance.add_votable_fields("otypes")
        assert _Column("otypes", "otype", 'otypes.otype') in simbad_instance.columns_in_output
        # tables also require a join
        assert _Join("otypes",
                     _Column("basic", "oid"),
                     _Column("otypes", "oidref"),
                     "LEFT JOIN") == simbad_instance.joins[0]
        # tables that have been renamed should warn
        with pytest.warns(DeprecationWarning, match="'iue' has been renamed 'mesiue'.*"):
            simbad_instance.add_votable_fields("IUE")
        # empty before the test
        simbad_instance.columns_in_output = []
        # mixed columns bundles and tables
        simbad_instance.add_votable_fields("flux", "velocity", "update_date")
        assert len(simbad_instance.columns_in_output) == 19

        # add fluxes by their filter names
        simbad_instance = Simbad()
        simbad_instance.add_votable_fields("U", "V")
        simbad_instance.add_votable_fields("u")
        result = simbad_instance.query_object("HD 147933")
        assert all(filtername in result.colnames for filtername in {"u", "U", "V"})

    def test_double_ident_in_query_objects(self):
        simbad = Simbad()
        simbad.add_votable_fields("ident")
        result = simbad.query_objects(['HD 1'])
        assert len(result) > 1
        assert all(result["main_id"] == "HD      1")
