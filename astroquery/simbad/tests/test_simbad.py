# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path
import re

from astropy.coordinates import SkyCoord
from astropy.io.votable import parse_single_table
from astropy.table import Table
import astropy.units as u
from pyvo.dal.tap import TAPService

import pytest

from ... import simbad
from .test_simbad_remote import multicoords
from astroquery.exceptions import LargeQueryWarning


GALACTIC_COORDS = SkyCoord(l=-67.02084 * u.deg, b=-29.75447 * u.deg, frame="galactic")
ICRS_COORDS = SkyCoord("05h35m17.3s -05h23m28s", frame="icrs")
FK4_COORDS = SkyCoord(ra=84.90759 * u.deg, dec=-80.89403 * u.deg, frame="fk4")
FK5_COORDS = SkyCoord(ra=83.82207 * u.deg, dec=-80.86667 * u.deg, frame="fk5")


@pytest.fixture()
def _mock_simbad_class(monkeypatch):
    """Avoid a TAP request for properties in the tests."""

    with open(Path(__file__).parent / "data" / "simbad_output_options.xml", "rb") as f:
        table = parse_single_table(f).to_table()
    # This should not change too often, to regenerate this file, do:
    # >>> from astroquery.simbad import Simbad
    # >>> options = Simbad.list_output_options()
    # >>> options.write("simbad_output_options.xml", format="votable")
    monkeypatch.setattr(simbad.SimbadClass, "hardlimit", 2000000)
    monkeypatch.setattr(simbad.SimbadClass, "list_output_options", lambda self: table)


@pytest.fixture()
def _mock_basic_columns(monkeypatch):
    """Avoid a request to get the columns of basic."""
    with open(Path(__file__).parent / "data" / "simbad_basic_columns.xml", "rb") as f:
        table = parse_single_table(f).to_table()
    # This should not change too often, to regenerate this file, do:
    # >>> from astroquery.simbad import Simbad
    # >>> columns = Simbad.list_columns("basic")
    # >>> columns.write("simbad_basic_columns.xml", format="votable")

    def _mock_list_columns(self, table_name=None):
        """Patch a call with basic as an argument only."""
        if table_name == "basic":
            return table
        # to test in add_output_columns
        if table_name == "mesdistance":
            return Table(
                [["bibcode"]], names=["column_name"]
            )
        return simbad.SimbadClass().list_columns(table_name)

    monkeypatch.setattr(simbad.SimbadClass, "list_columns", _mock_list_columns)


@pytest.fixture()
def _mock_linked_to_basic(monkeypatch):
    """Avoid a request to get the columns of basic."""
    with open(Path(__file__).parent / "data" / "simbad_linked_to_basic.xml", "rb") as f:
        table = parse_single_table(f).to_table()
    # This should not change too often, to regenerate this file, do:
    # >>> from astroquery.simbad import Simbad
    # >>> linked = Simbad.list_linked_tables("basic")
    # >>> linked.write("simbad_linked_to_basic.xml", format="votable")

    def _mock_linked_to_basic(self, table_name=None):
        """Patch a call with basic as an argument only."""
        if table_name == "basic":
            return table
        return simbad.SimbadClass().list_linked_tables(table_name)

    monkeypatch.setattr(simbad.SimbadClass, "list_linked_tables", _mock_linked_to_basic)


def test_adql_parameter():
    # escape single quotes
    assert simbad.core._adql_parameter("Barnard's galaxy") == "Barnard''s galaxy"


# ------------------
# Testing properties
# ------------------


def test_simbad_mirror():
    simbad_instance = simbad.SimbadClass()
    # default value should be set at instantiation
    assert simbad_instance.server == "simbad.cds.unistra.fr"
    # it can be switched to harvard mirror
    simbad_instance.server = "simbad.harvard.edu"
    assert simbad_instance.server == "simbad.harvard.edu"
    # but not to an invalid mirror
    with pytest.raises(ValueError,
                       match="'test' does not correspond to a SIMBAD server, *"):
        simbad_instance.server = "test"


def test_simbad_row_limit():
    simbad_instance = simbad.SimbadClass()
    # default value is -1
    assert simbad_instance.ROW_LIMIT == -1
    # we can assign afterward
    simbad_instance.ROW_LIMIT = 5
    assert simbad_instance.ROW_LIMIT == 5
    # or from the beginning
    simbad_instance = simbad.SimbadClass(ROW_LIMIT=10)
    assert simbad_instance.ROW_LIMIT == 10
    # non-valid values trigger an error
    with pytest.raises(ValueError, match="ROW_LIMIT can be either -1 to set the limit "
                       "to SIMBAD's maximum capability, 0 to retrieve an empty table, "
                       "or a positive integer."):
        simbad_instance = simbad.SimbadClass(ROW_LIMIT='test')


def test_simbad_create_tap_service():
    simbad_instance = simbad.Simbad()
    # newly created should have no tap service
    assert simbad_instance._tap is None
    # then we create it
    simbadtap = simbad_instance.tap
    assert 'simbad/sim-tap' in simbadtap.baseurl


def test_simbad_hardlimit(monkeypatch):
    simbad_instance = simbad.Simbad()
    monkeypatch.setattr(TAPService, "hardlimit", 2)
    assert simbad_instance.hardlimit == 2


def test_init_columns_in_output():
    simbad_instance = simbad.Simbad()
    default_columns = simbad_instance.columns_in_output
    # main_id from basic should be there
    assert simbad.SimbadClass.Column("basic", "main_id") in default_columns
    # there are 8 default columns
    assert len(default_columns) == 8


@pytest.mark.usefixtures("_mock_simbad_class")
def test_mocked_simbad():
    simbad_instance = simbad.Simbad()
    # this mocks the list_output_options
    options = simbad_instance.list_output_options()
    assert len(options) > 90
    # this mocks the hardlimit
    assert simbad_instance.hardlimit == 2000000

# ----------------------------
# Test output options settings
# ----------------------------


@pytest.mark.usefixtures("_mock_basic_columns")
def test_list_output_options(monkeypatch):
    monkeypatch.setattr(simbad.SimbadClass, "query_tap",
                        lambda self, _: Table([["biblio"], ["biblio description"]],
                                              names=["name", "description"],
                                              dtype=["object", "object"]))
    options = simbad.SimbadClass().list_output_options()
    assert set(options.group_by("type").groups.keys["type"]) == {"table",
                                                                 "column of basic",
                                                                 "bundle of basic columns"}


@pytest.mark.usefixtures("_mock_basic_columns")
@pytest.mark.parametrize(("bundle_name", "column"),
                         [("coordinates", simbad.SimbadClass.Column("basic", "ra")),
                          ("coordinates", simbad.SimbadClass.Column("basic", "coo_bibcode")),
                          ("dim", simbad.SimbadClass.Column("basic", "galdim_wavelength"))])
def test_get_bundle_columns(bundle_name, column):
    assert column in simbad.SimbadClass()._get_bundle_columns(bundle_name)


@pytest.mark.usefixtures("_mock_linked_to_basic")
def test_add_table_to_output(monkeypatch):
    # if table = basic, no need to add a join
    simbad_instance = simbad.Simbad()
    simbad_instance._add_table_to_output("basic")
    assert simbad.SimbadClass.Column("basic", "*") in simbad_instance.columns_in_output
    # cannot add h_link (two ways to join it, it's not a simple link)
    with pytest.raises(ValueError, match="'h_link' has no explicit link to 'basic'.*"):
        simbad_instance._add_table_to_output("h_link")
    # add a table with a link and an alias needed
    monkeypatch.setattr(simbad.SimbadClass, "list_columns", lambda self, _: Table([["oidref", "bibcode"]],
                                                                                  names=["column_name"]))
    simbad_instance._add_table_to_output("mesDiameter")
    assert simbad.SimbadClass.Join("mesdiameter",
                                   simbad.SimbadClass.Column("basic", "oid"),
                                   simbad.SimbadClass.Column("mesdiameter", "oidref")
                                   ) in simbad_instance.joins
    assert simbad.SimbadClass.Column("mesdiameter", "bibcode", '"mesdiameter.bibcode"'
                                     ) in simbad_instance.columns_in_output
    assert simbad.SimbadClass.Column("mesdiameter", "oidref", '"mesdiameter.oidref"'
                                     ) not in simbad_instance.columns_in_output


@pytest.mark.usefixtures("_mock_simbad_class")
@pytest.mark.usefixtures("_mock_basic_columns")
@pytest.mark.usefixtures("_mock_linked_to_basic")
def test_add_output_columns():
    simbad_instance = simbad.Simbad()
    # add columns from basic (one value)
    simbad_instance.add_output_columns("pmra")
    assert simbad.SimbadClass.Column("basic", "pmra") in simbad_instance.columns_in_output
    # add two columns from basic
    simbad_instance.add_output_columns("pmdec", "pm_bibcodE")  # also test case insensitive
    expected = [simbad.SimbadClass.Column("basic", "pmdec"),
                simbad.SimbadClass.Column("basic", "pm_bibcode")]
    assert all(column in simbad_instance.columns_in_output for column in expected)
    # add a table
    simbad_instance.columns_in_output = []
    simbad_instance.add_output_columns("basic")
    assert [simbad.SimbadClass.Column("basic", "*")] == simbad_instance.columns_in_output
    # add a bundle
    simbad_instance.add_output_columns("dimensions")
    assert simbad.SimbadClass.Column("basic", "galdim_majaxis") in simbad_instance.columns_in_output
    # a column which name has changed should raise a warning but still
    # be added under its new name
    simbad_instance.columns_in_output = []
    with pytest.warns(DeprecationWarning, match=r"'id\(1\)' has been renamed 'main_id'. You'll see it "
                      "appearing with its new name in the output table"):
        simbad_instance.add_output_columns("id(1)")
    assert simbad.SimbadClass.Column("basic", "main_id") in simbad_instance.columns_in_output
    # a table which name has changed should raise a warning too
    with pytest.warns(DeprecationWarning, match="'distance' has been renamed 'mesdistance'*"):
        simbad_instance.add_output_columns("distance")
    # errors are raised for the deprecated fields with options
    with pytest.raises(ValueError, match="Criteria on filters are deprecated when defining Simbad's output.*"):
        simbad_instance.add_to_output("fluxdata(V)")
    with pytest.raises(ValueError, match="Coordinates conversion and formatting is no longer supported.*"):
        simbad_instance.add_to_output("coo(s)", "dec(d)")
    with pytest.raises(ValueError, match="Catalog Ids are no longer supported as an output option.*"):
        simbad_instance.add_output_columns("ID(Gaia)")
    with pytest.raises(ValueError, match="Selecting a range of years for bibcode is removed.*"):
        simbad_instance.add_output_columns("bibcodelist(2042-2050)")
    # historical measurements
    with pytest.raises(ValueError, match="'einstein' is no longer a part of SIMBAD.*"):
        simbad_instance.add_output_columns("einstein")
    # typos should have suggestions
    with pytest.raises(ValueError, match="'alltype' is not one of the accepted options which can be "
                       "listed with 'list_output_options'. Did you mean 'alltypes' or 'otype' or 'otypes'?"):
        simbad_instance.add_output_columns("ALLTYPE")
    # bundles and tables require a connection to the tap_schema and are thus tested in test_simbad_remote


# ------------------------------------------
# Test query_*** methods that call query_tap
# ------------------------------------------

@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_bibcode_class():
    simbad_instance = simbad.Simbad()
    # wildcard
    adql = simbad_instance.query_bibcode("????LASP.*", wildcard=True, get_adql=True)
    assert "WHERE regexp(lowercase(bibcode), '^....lasp\\\\..*$') = 1" in adql
    # with row limit and abstract
    simbad_instance.ROW_LIMIT = 5
    adql = simbad_instance.query_bibcode("1968ZA.....68..366D", abstract=True, get_adql=True)
    assert adql == ('SELECT TOP 5 "bibcode", "doi", "journal", "nbobject", "page", "last_page",'
                    ' "title", "volume", "year", "abstract" FROM ref WHERE bibcode ='
                    ' \'1968ZA.....68..366D\' ORDER BY bibcode')
    # with a criteria
    adql = simbad_instance.query_bibcode("200*", wildcard=True,
                                         criteria="abstract LIKE '%exoplanet%'", get_adql=True)
    assert adql == ('SELECT TOP 5 "bibcode", "doi", "journal", "nbobject", "page", "last_page", '
                    '"title", "volume", "year" FROM ref '
                    'WHERE regexp(lowercase(bibcode), \'^200.*$\') = 1 '
                    'AND abstract LIKE \'%exoplanet%\' ORDER BY bibcode')


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_objectids():
    adql = simbad.core.Simbad.query_objectids('Polaris',
                                              criteria="ident.id LIKE 'HD%'",
                                              get_adql=True)
    expected = ("SELECT ident.id FROM ident AS id_typed JOIN ident USING(oidref)"
                "WHERE id_typed.id = 'Polaris' AND ident.id LIKE 'HD%'")
    assert adql == expected


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_bibobj():
    bibcode = '2005A&A.430.165F'
    adql = simbad.core.Simbad.query_bibobj(bibcode, get_adql=True,
                                           criteria="dec < 5")
    # test condition
    assert f"WHERE bibcode = '{bibcode}' AND (dec < 5)" in adql
    # test join
    assert 'basic JOIN has_ref ON basic."oid" = has_ref."oidref"' in adql


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_catalog():
    simbad_instance = simbad.Simbad()
    adql = simbad_instance.query_catalog('Gaia DR2', get_adql=True,
                                         criteria="update_date < '2010-01-01'")
    where_clause = "WHERE id LIKE 'Gaia DR2 %' AND (update_date < '2010-01-01')"
    assert adql.endswith(where_clause)


@pytest.mark.parametrize(('coordinates', 'radius', 'where'),
                         [(ICRS_COORDS, 2*u.arcmin,
                           r"WHERE CONTAINS\(POINT\('ICRS', basic\.ra, basic\.dec\), "
                           r"CIRCLE\('ICRS', 83\.\d*, -80\.\d*, 0\.\d*\)\) = 1"),
                          (GALACTIC_COORDS, 5 * u.deg,
                           r"WHERE CONTAINS\(POINT\(\'ICRS\', basic\.ra, basic\.dec\), "
                           r"CIRCLE\(\'ICRS\', 83\.\d*, -80\.\d*, 5\.0\)\) = 1"),
                          (FK4_COORDS, '5d0m0s',
                           r"WHERE CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 83.\d*, -80.\d*, 5.0\)\) = 1"),
                          (FK5_COORDS, 2*u.arcmin,
                           r"WHERE CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 83.\d*, -80.\d*, 0.\d*\)\) = 1"),
                          (multicoords, 0.5*u.arcsec,
                           r"WHERE  \(CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 266.835, -28.38528, 0.\d*\)\) "
                           r"= 1 OR CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 266.835, -28.38528, 0.\d*\)\) = 1 \)"),
                          (multicoords, ["0.5s", "0.2s"],
                           r"WHERE  \(CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 266.835, -28.38528, 0.\d*\)\) "
                           r"= 1 OR CONTAINS\(POINT\(\'ICRS\', basic.ra, basic.dec\), "
                           r"CIRCLE\(\'ICRS\', 266.835, -28.38528, 5.\d*e-05\)\) = 1 \)"),
                          ])
@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_region(coordinates, radius, where):
    adql = simbad.core.Simbad.query_region(coordinates, radius=radius, get_adql=True)
    adql_2 = simbad.core.Simbad().query_region(coordinates, radius=radius, get_adql=True)
    assert adql == adql_2
    assert re.search(where, adql) is not None


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_region_with_criteria():
    adql = simbad.core.Simbad.query_region(ICRS_COORDS, radius="0.1s",
                                           criteria="galdim_majaxis>0.2", get_adql=True)
    assert adql.endswith("AND (galdim_majaxis>0.2)")


# transform large query warning into error to save execution time
@pytest.mark.filterwarnings("error:For very large queries")
@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_region_errors():
    with pytest.raises(u.UnitsError):
        simbad.core.Simbad().query_region(ICRS_COORDS, radius=0)
    with pytest.raises(TypeError, match="The cone radius must be specified as an angle-equivalent quantity"):
        simbad.SimbadClass().query_region(ICRS_COORDS, radius=None)
    with pytest.raises(ValueError, match="Mismatch between radii of length 3 "
                       "and center coordinates of length 2."):
        simbad.SimbadClass().query_region(multicoords, radius=[1, 2, 3] * u.deg)
    centers = SkyCoord([0] * 10001, [0] * 10001, unit="deg", frame="icrs")
    with pytest.raises(LargeQueryWarning, match="For very large queries, you may receive a timeout error.*"):
        simbad.core.Simbad.query_region(centers, radius="2m", get_adql=True)


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_objects():
    # no wildcard and additional criteria
    adql = simbad.core.Simbad.query_objects(("m1", "m2"), criteria="otype = 'Galaxy..'", get_adql=True)
    expected = ('FROM basic JOIN ident ON basic."oid" = ident."oidref" RIGHT JOIN TAP_UPLOAD.script_infos'
                ' ON ident."id" = TAP_UPLOAD.script_infos."typed_id" WHERE (id IN (\'m1\', \'m2\') OR '
                'typed_id IS NOT NULL) AND (otype = \'Galaxy..\')')
    assert adql.endswith(expected)
    # with wildcard
    adql = simbad.core.Simbad.query_objects(("M *", "NGC *"), wildcard=True, get_adql=True)
    expected = (r'SELECT .* TAP_UPLOAD\.script_infos\.\* FROM basic JOIN ident '
                r'ON basic\."oid" = ident\."oidref" RIGHT JOIN TAP_UPLOAD\.script_infos ON'
                r' ident\."id" = TAP_UPLOAD\.script_infos\."typed_id" WHERE \(\(regexp\(id, \'\^M \+\.\*\$\'\)'
                r' = 1 OR regexp\(id, \'\^NGC \+\.\*\$\'\) = 1\) OR typed_id IS NOT NULL\)')
    assert re.match(expected, adql) is not None


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_object():
    # no wildcard
    adql = simbad.core.Simbad.query_object("m1", wildcard=False, get_adql=True)
    expected = r'SELECT .* FROM basic JOIN ident ON basic\."oid" = ident\."oidref" WHERE id = \'m1\''
    assert re.match(expected, adql) is not None
    # with wildcard
    adql = simbad.core.Simbad.query_object("m [0-9]", wildcard=True, get_adql=True)
    end = "WHERE  regexp(id, '^m +[0-9]$') = 1"
    assert adql.endswith(end)
    # with criteria
    adql = simbad.core.Simbad.query_object("NGC*", wildcard=True, criteria="otype = 'G..'", get_adql=True)
    end = "AND (otype = 'G..')"
    assert adql.endswith(end)

# -------------------------
# Test query_tap exceptions
# -------------------------


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_tap_errors():
    # test the hardlimit
    with pytest.raises(ValueError, match="The maximum number of records cannot exceed 2000000."):
        simbad.Simbad.query_tap("select top 5 * from basic", maxrec=10e10)
    # test the escape of single quotes
    with pytest.raises(ValueError, match="Query string contains an odd number of single quotes.*"):
        simbad.Simbad.query_tap("'''")


@pytest.mark.usefixtures("_mock_simbad_class")
def test_query_tap_cache_call(monkeypatch):
    msg = "called_cached_query_tap"
    monkeypatch.setattr(simbad.core, "_cached_query_tap", lambda tap, query, maxrec: msg)
    assert simbad.Simbad.query_tap("select top 1 * from basic") == msg


# ---------------------------------------------------
# Test the adql string for query_tap helper functions
# ---------------------------------------------------


def test_simbad_list_tables():
    tables_adql = "SELECT table_name, description FROM TAP_SCHEMA.tables WHERE schema_name = 'public'"
    assert simbad.Simbad.list_tables(get_adql=True) == tables_adql


def test_simbad_list_columns():
    # with three table names
    columns_adql = ("SELECT table_name, column_name, datatype, description, unit, ucd"
                    " FROM TAP_SCHEMA.columns "
                    "WHERE table_name NOT LIKE 'TAP_SCHEMA.%'"
                    " AND LOWERCASE(table_name) IN ('mespm', 'otypedef', 'journals')"
                    " ORDER BY table_name, principal DESC, column_name")
    assert simbad.Simbad.list_columns("mesPM", "otypedef", "journals", get_adql=True) == columns_adql
    # with only one
    columns_adql = ("SELECT table_name, column_name, datatype, description, unit, ucd "
                    "FROM TAP_SCHEMA.columns WHERE table_name NOT LIKE 'TAP_SCHEMA.%' "
                    "AND LOWERCASE(table_name) = 'basic' ORDER BY table_name, principal DESC, column_name")
    assert simbad.Simbad.list_columns("basic", get_adql=True) == columns_adql
    # with only a keyword
    list_columns_adql = ("SELECT table_name, column_name, datatype, description, unit, ucd "
                         "FROM TAP_SCHEMA.columns WHERE table_name NOT LIKE 'TAP_SCHEMA.%' "
                         "AND ( (LOWERCASE(column_name) "
                         "LIKE LOWERCASE('%stellar%')) OR (LOWERCASE(description) "
                         "LIKE LOWERCASE('%stellar%')) OR (LOWERCASE(table_name) "
                         "LIKE LOWERCASE('%stellar%'))) ORDER BY table_name, principal DESC, column_name")
    assert simbad.Simbad.list_columns(keyword="stellar", get_adql=True) == list_columns_adql


def test_list_linked_tables():
    list_linked_tables_adql = ("SELECT from_table, from_column, target_table, target_column "
                               "FROM TAP_SCHEMA.key_columns JOIN TAP_SCHEMA.keys USING (key_id) "
                               "WHERE (from_table = 'basic') OR (target_table = 'basic')")
    assert simbad.Simbad.list_linked_tables("basic", get_adql=True) == list_linked_tables_adql


@pytest.mark.usefixtures("_mock_simbad_class")
def test_construct_query():
    column = simbad.Simbad.Column("basic", "*")
    # bare minimum with an alias
    expected = 'SELECT basic."main_id" AS my_id FROM basic'
    assert simbad.Simbad._construct_query(-1,
                                          [simbad.Simbad.Column("basic", "main_id", "my_id")],
                                          [],
                                          [], get_adql=True) == expected
    # with top
    # and duplicated columns are dropped
    expected = "SELECT TOP 1 basic.* FROM basic"
    assert simbad.Simbad._construct_query(1,
                                          [column, column],
                                          [],
                                          [], get_adql=True) == expected
    # with a join
    expected = 'SELECT basic.*, ids."ids" FROM basic JOIN ids ON basic."oid" = ids."oidref"'
    assert simbad.Simbad._construct_query(-1,
                                          [column, simbad.Simbad.Column("ids", "ids")],
                                          [simbad.Simbad.Join("ids",
                                                              simbad.Simbad.Column("basic", "oid"),
                                                              simbad.Simbad.Column("ids", "oidref"))],
                                          [], get_adql=True) == expected
    # with a condition
    expected = "SELECT basic.* FROM basic WHERE ra < 6 AND ra > 5"
    assert simbad.Simbad._construct_query(-1,
                                          [column],
                                          [],
                                          ["ra < 6", "ra > 5"], get_adql=True) == expected
