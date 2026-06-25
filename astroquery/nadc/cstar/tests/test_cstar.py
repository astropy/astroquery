# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json

import pytest

import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table
from requests import HTTPError

import astroquery.nadc._query_data as query_data_module
from ....exceptions import InvalidQueryError, TableParseError
from astroquery.nadc import conf as nadc_conf
from astroquery.nadc._query_data import _drop_none, _table_from_list_of_dicts
from astroquery.nadc.tests.helpers import (
    assert_task_columns,
    assert_task_cone,
    assert_task_constraints,
    assert_task_query_payload,
)
from astroquery.utils.mocks import MockResponse

from .. import conf
from ..core import CstarClass, _configured_token_from_env


SUBMIT_SQLID = {"sqlid": 123}


CATALOGS_PAYLOAD = {
    "total": 3,
    "rows": [
        {
            "id": 1,
            "catname": "cstar",
            "shortname": "CSTAR",
            "showname_en": "CSTAR",
            "showname_zh": "CSTAR",
            "datatype": "catalog",
            "cattype": "domestic",
            "dbname": "cstar",
            "priority": 0,
        },
        {
            "id": 2,
            "catname": "legacyplate",
            "shortname": "LEGACYPLATE",
            "showname_en": "Legacy Plate",
            "showname_zh": "Legacy Plate",
            "datatype": "catalog",
            "cattype": "domestic",
            "dbname": "legacyplate",
            "priority": 1,
        },
        {
            "id": 3,
            "catname": "legacyplate_scans",
            "shortname": "LEGACYPLATE SCANS",
            "showname_en": "Legacy Plate Scans",
            "showname_zh": "Legacy Plate Scans",
            "datatype": "catalog",
            "cattype": "domestic",
            "dbname": "legacyplate_scans",
            "priority": 2,
        },
    ],
}


RESULTS_VOTABLE = b"""<?xml version="1.0" encoding="utf-8"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE>
    <TABLE>
      <FIELD name="ra" datatype="double" unit="deg" />
      <FIELD name="dec" datatype="double" unit="deg" />
      <FIELD name="id" datatype="char" arraysize="*" />
      <DATA>
        <TABLEDATA>
          <TR>
            <TD>1.0</TD>
            <TD>2.0</TD>
            <TD>src1</TD>
          </TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>
"""


MALFORMED_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.4">
  <RESOURCE type="results">
    <TABLE>
      <FIELD ID="COLID_-4" name="dist_arcsec" arraysize=""></FIELD>
      <FIELD ID="COLID_1" name="id" datatype="int"></FIELD>
      <DATA>
        <TABLEDATA>
          <TR><TD>0.0</TD><TD>1</TD></TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>
"""


ZERO_ARRAYSIZE_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.4">
    <RESOURCE type="results">
        <TABLE>
            <FIELD ID="COLID_1" name="source_id" datatype="long" arraysize="0"></FIELD>
            <FIELD ID="COLID_2" name="year" datatype="int" arraysize="0"></FIELD>
            <DATA>
                <TABLEDATA>
                    <TR><TD>123</TD><TD>1901</TD></TR>
                </TABLEDATA>
            </DATA>
        </TABLE>
    </RESOURCE>
</VOTABLE>
"""


INVALID_DATE_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.4">
    <RESOURCE type="results">
        <TABLE>
            <FIELD ID="COLID_1" name="id" datatype="long"></FIELD>
            <FIELD ID="COLID_2" name="dateobs" datatype="date"></FIELD>
            <DATA>
                <TABLEDATA>
                    <TR><TD>123</TD><TD>2010-10-03T06:23:06.879000</TD></TR>
                </TABLEDATA>
            </DATA>
        </TABLE>
    </RESOURCE>
</VOTABLE>
"""


BROKEN_MALFORMED_VOTABLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3" version="1.4">
  <RESOURCE type="results">
    <TABLE>
      <FIELD ID="COLID_-4" name="dist_arcsec" arraysize=""></FIELD>
"""


def json_response(data, *, url="http://dummy.example/query/openapi/json"):
    return MockResponse(
        json.dumps(data).encode("utf-8"),
        url=url,
        content_type="application/json",
    )


def nonremote_request(self, request_type, url, **kwargs):
    self._nreq = getattr(self, "_nreq", 0) + 1
    if url.endswith("/query/openapi/vo/cstar/conesearch"):
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/catalogs/cstar/tables/catalog/query"):
        return json_response(SUBMIT_SQLID, url=url)
    if url.endswith("/query/openapi/catalogs/cstar/query"):
        return json_response(SUBMIT_SQLID, url=url)
    if "/query/openapi/sqlid/" in url and "results.votable" in url:
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/get_catalogs"):
        return json_response(CATALOGS_PAYLOAD, url=url)
    if url.endswith("/query/openapi/catalogs/cstar"):
        return json_response(
            {
                "catname": "cstar",
                "file_download": {
                    "supported": True,
                    "single_file_endpoint": "/query/openapi/catalogs/cstar/file",
                    "batch_download_endpoint": "/query/openapi/catalogs/cstar/download",
                    "categories": [
                        "fig",
                        "fits",
                        "ghost-fig",
                        "ghost-fits",
                        "diurnal-fig",
                        "diurnal-fits",
                    ],
                    "single_file_query_by_category": {
                        "fig": {"category": "fig"},
                        "fits": {"category": "fits"},
                    },
                },
            },
            url=url,
        )
    raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")


@pytest.fixture
def cstar(monkeypatch):
    monkeypatch.setattr(CstarClass, "_request", nonremote_request)
    client = CstarClass(catalog="cstar", token=None)
    client.URL = "http://dummy.example/"
    client._nreq = 0
    return client


def test_query_region_payload(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar.query_region(c, 5 * u.arcsec, get_query_payload=True)
    assert payload["method"] == "GET"
    assert payload["url"].endswith("/query/openapi/vo/cstar/conesearch")
    assert payload["params"]["output.fmt"] == "votable"
    assert payload["params"]["RA"] == 1.0
    assert payload["params"]["DEC"] == 2.0


def test_query_region_parses_votable(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    table = cstar.query_region(c, 5 * u.arcsec)
    assert isinstance(table, Table)
    assert {"ra", "dec", "id"}.issubset(set(table.colnames))


def test_query_region_object_name_uses_parse_coordinates(cstar, monkeypatch):
    resolved = coord.SkyCoord(ra=11 * u.deg, dec=-3 * u.deg, frame="icrs")
    calls = {}

    def fake_parse_coordinates(value):
        calls["value"] = value
        return resolved

    monkeypatch.setattr(cstar, "_parse_coordinates", fake_parse_coordinates)

    payload = cstar.query_region("M31", 5 * u.arcsec, get_query_payload=True)

    assert calls["value"] == "M31"
    assert payload["params"]["RA"] == 11.0
    assert payload["params"]["DEC"] == -3.0


def test_query_catalog_payload(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar.query_catalog(
        coordinates=c,
        radius=5 * u.arcsec,
        output_format="votable",
        max_rows=10,
        page_size=10,
        get_query_payload=True,
    )
    assert payload["submit"]["method"] == "POST"
    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/cstar/query")
    assert payload["submit"]["json"]["output.fmt"] == "html"
    assert payload["submit"]["json"]["pos"]["type"] == "cone"
    assert payload["submit"]["json"]["pos_group"] == "ra,dec"
    assert payload["results"]["method"] == "GET"
    assert payload["max_rows"] == 10
    assert payload["page_size"] == 10
    assert "results.votable" in payload["results"]["url"]


def test_query_catalog_cone_helper_payload(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar.query_catalog_cone(
        c,
        5 * u.arcsec,
        output_format="json",
        max_rows=50,
        page_size=25,
        get_query_payload=True,
    )
    assert payload["submit"]["json"]["pos"]["type"] == "cone"
    assert payload["submit"]["json"]["pos"]["cone"]["radius"] == 5.0
    assert payload["submit"]["json"]["pos_group"] == "ra,dec"
    assert payload["results"]["params"]["page"] == 1
    assert payload["results"]["params"]["rows"] == 25
    assert payload["max_rows"] == 50
    assert payload["page_size"] == 25
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.json")


def test_query_catalog_rectangle_payload(cstar):
    payload = cstar.query_catalog_rectangle(
        10 * u.deg,
        12.5,
        -2.5,
        3 * u.deg,
        output_format="csv",
        get_query_payload=True,
    )
    rect = payload["submit"]["json"]["pos"]["rect"]
    assert payload["submit"]["json"]["pos"]["type"] == "rect"
    assert payload["submit"]["json"]["pos_group"] == "ra,dec"
    assert rect["ramin"] == 10.0
    assert rect["ramax"] == 12.5
    assert rect["decmin"] == -2.5
    assert rect["decmax"] == 3.0
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.csv")


def test_query_catalog_proximity_payload(cstar):
    payload = cstar.query_catalog_proximity(
        [
            (1 * u.deg, 2 * u.deg),
            (3, 4, 5 * u.arcsec),
        ],
        default_radius=2 * u.arcsec,
        nearest_only=True,
        get_query_payload=True,
    )
    proximity = payload["submit"]["json"]["pos"]["proximity"]
    assert payload["submit"]["json"]["pos"]["type"] == "proximity"
    assert payload["submit"]["json"]["pos_group"] == "ra,dec"
    assert proximity["radecTextarea"] == "1.0,2.0\n3.0,4.0,5.0"
    assert proximity["defaultRadius"] == 2.0
    assert proximity["proximity_nearestonly"] is True


def test_query_sources_builds_science_payload(cstar):
    center = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar.query_sources(
        center,
        5 * u.arcsec,
        mag_range=(10, 13.5),
        magerr_max=0.05,
        columns=["id", "ra", "dec", "mag", "magerr"],
        nearest_only=True,
        output_format="json",
        max_rows=12,
        page_size=6,
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/cstar/query",
        result_format="json",
    )
    assert payload["max_rows"] == 12
    assert payload["page_size"] == 6
    assert_task_cone(payload, radius_arcsec=5.0, nearest_only=True)
    assert_task_columns(payload, ["id", "ra", "dec", "mag", "magerr"])
    assert_task_constraints(
        payload,
        [
            {"column_name": "mag", "operation": "between", "min": 10, "max": 13.5},
            {"column_name": "magerr", "operation": "lessequal", "constraint": "0.05"},
        ],
    )


def test_query_sources_rejects_bad_magnitude_range(cstar):
    with pytest.raises(InvalidQueryError, match="mag range"):
        cstar.query_sources(mag_range=(10,), get_query_payload=True)


def test_query_table_payload_uses_table_endpoint(cstar):
    payload = cstar.query_table(
        catalog="cstar",
        table="catalog",
        showcol=["id", "mag"],
        output_format="csv",
        get_query_payload=True,
    )

    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/cstar/tables/catalog/query")
    assert payload["submit"]["json"]["showcol"] == ["id", "mag"]
    assert payload["submit"]["json"]["output.fmt"] == "html"
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.csv")


def test_query_table_rectangle_payload_uses_table_endpoint(cstar):
    payload = cstar.query_table_rectangle(
        10 * u.deg,
        12.5,
        -2.5,
        3 * u.deg,
        catalog="cstar",
        table="catalog",
        output_format="json",
        get_query_payload=True,
    )

    rect = payload["submit"]["json"]["pos"]["rect"]
    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/cstar/tables/catalog/query")
    assert payload["submit"]["json"]["pos"]["type"] == "rect"
    assert rect == {"ramin": 10.0, "ramax": 12.5, "decmin": -2.5, "decmax": 3.0}


def test_query_table_proximity_payload_uses_table_endpoint(cstar):
    payload = cstar.query_table_proximity(
        [(1 * u.deg, 2 * u.deg), (3, 4, 5 * u.arcsec)],
        catalog="cstar",
        table="catalog",
        default_radius=2 * u.arcsec,
        nearest_only=True,
        get_query_payload=True,
    )

    proximity = payload["submit"]["json"]["pos"]["proximity"]
    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/cstar/tables/catalog/query")
    assert payload["submit"]["json"]["pos"]["type"] == "proximity"
    assert proximity["radecTextarea"] == "1.0,2.0\n3.0,4.0,5.0"
    assert proximity["defaultRadius"] == 2.0
    assert proximity["proximity_nearestonly"] is True


def test_table_payload_requires_explicit_table_without_request(cstar):
    def fail_request(*args, **kwargs):
        raise AssertionError("get_query_payload=True must not issue service requests")

    cstar._request = fail_request

    with pytest.raises(InvalidQueryError, match="`table` is required"):
        cstar.query_table(catalog="cstar", get_query_payload=True)

    with pytest.raises(InvalidQueryError, match="`table` is required"):
        cstar.list_columns(catalog="cstar", get_query_payload=True)

    with pytest.raises(InvalidQueryError, match="`table` is required"):
        cstar.submit_table_query({"output.fmt": "html"}, catalog="cstar", get_query_payload=True)

    with pytest.raises(InvalidQueryError, match="`table` is required"):
        cstar.query_table_cone(
            coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
            5 * u.arcsec,
            catalog="cstar",
            get_query_payload=True,
        )


def test_query_catalog_allows_overriding_pos_group(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar.query_catalog_cone(
        c,
        5 * u.arcsec,
        pos_group="ra_obs,dec_obs",
        get_query_payload=True,
    )
    assert payload["submit"]["json"]["pos_group"] == "ra_obs,dec_obs"


def test_query_catalog_max_rows(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    table = cstar.query_catalog(
        coordinates=c,
        radius=5 * u.arcsec,
        max_rows=2,
        page_size=1,
        output_format="votable",
    )
    assert isinstance(table, Table)
    assert len(table) == 2
    # submit + 2 pages
    assert cstar._nreq == 3


def test_query_catalog_cone_max_rows(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    table = cstar.query_catalog_cone(
        c,
        5 * u.arcsec,
        max_rows=2,
        page_size=1,
        output_format="votable",
    )
    assert isinstance(table, Table)
    assert len(table) == 2
    assert cstar._nreq == 3


def test_query_catalog_rectangle_sync_payload(cstar):
    payload = cstar.query_catalog_rectangle(
        0,
        1,
        -1,
        1,
        max_rows=5,
        page_size=2,
        get_query_payload=True,
    )
    assert payload["max_rows"] == 5
    assert payload["page_size"] == 2
    assert payload["submit"]["json"]["pos"]["type"] == "rect"
    assert payload["results"]["params"]["rows"] == 2


def test_list_catalogs_parses_json(cstar):
    table = cstar.list_catalogs()
    assert isinstance(table, Table)
    assert "catname" in table.colnames
    assert len(table) == 1
    assert table["catname"][0] == "cstar"


def test_get_catalog_metadata_parses_json(cstar):
    metadata = cstar.get_catalog_metadata()

    assert metadata["catname"] == "cstar"
    assert metadata["file_download"]["supported"] is True
    assert "fits" in metadata["file_download"]["categories"]
    assert metadata["capabilities_summary"]["file_download_supported"] is True


def test_list_tables_and_columns_parse_json(cstar, monkeypatch):
    def fake_request(request_type, url, **kwargs):
        if url.endswith("/query/openapi/catalogs/cstar/tables"):
            return json_response([{"table_name": "sources", "description": "demo"}], url=url)
        if url.endswith("/query/openapi/catalogs/cstar/tables/sources/columns"):
            return json_response([{"name": "ra", "datatype": "float"}], url=url)
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    monkeypatch.setattr(cstar, "_request", fake_request)

    tables = cstar.list_tables()
    columns = cstar.list_columns("sources")

    assert tables["table_name"][0] == "sources"
    assert columns["name"][0] == "ra"


def test_list_schema_flattens_catalog_tables(cstar, monkeypatch):
    def fake_request(request_type, url, **kwargs):
        if url.endswith("/query/openapi/catalogs/cstar/tables"):
            return json_response(
                [
                    {
                        "table_name": "sources",
                        "description": "source photometry",
                        "records": 10,
                    },
                    {
                        "table_name": "quality",
                        "description": "quality flags",
                        "records": 5,
                    },
                ],
                url=url,
            )
        if url.endswith("/query/openapi/catalogs/cstar/tables/sources/columns"):
            return json_response(
                [
                    {
                        "name": "ra",
                        "datatype": "float",
                        "unit": "deg",
                        "description": "right ascension",
                    },
                    {
                        "name": "mag",
                        "datatype": "float",
                        "unit": "mag",
                        "description": "magnitude",
                    },
                ],
                url=url,
            )
        if url.endswith("/query/openapi/catalogs/cstar/tables/quality/columns"):
            return json_response(
                [
                    {
                        "colname": "flag",
                        "type": "int",
                        "description": "quality flag",
                    }
                ],
                url=url,
            )
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    monkeypatch.setattr(cstar, "_request", fake_request)

    schema = cstar.list_schema()

    assert isinstance(schema, Table)
    assert schema.meta["catalog"] == "cstar"
    assert schema.meta["tables"] == ["sources", "quality"]
    assert len(schema) == 3
    assert set(schema["table"]) == {"sources", "quality"}
    assert list(schema["column"]) == ["ra", "mag", "flag"]
    assert schema["datatype"][0] == "float"
    assert schema["datatype"][2] == "int"
    assert schema["table_description"][0] == "source photometry"
    assert schema["table_records"][0] == 10


def test_list_table_links_parse_json(cstar, monkeypatch):
    def fake_request(request_type, url, **kwargs):
        if url.endswith("/query/openapi/catalogs/cstar/table_links"):
            return json_response(
                {
                    "is_single_table": True,
                    "links": [
                        {
                            "tblname": "catalog",
                            "is_main_table": True,
                            "join_mode": "main",
                            "join_summary": "main table",
                            "order": 0,
                        }
                    ],
                },
                url=url,
            )
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    monkeypatch.setattr(cstar, "_request", fake_request)

    table_links = cstar.list_table_links()

    assert table_links["tblname"][0] == "catalog"
    assert table_links["join_mode"][0] == "main"
    assert table_links.meta["is_single_table"] is True


def test_parse_result_repairs_malformed_votable(cstar):
    response = MockResponse(
        MALFORMED_VOTABLE,
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="application/x-votable+xml",
    )
    table = cstar._parse_result(response)
    assert len(table) == 1
    assert table["dist_arcsec"][0] == "0.0"
    assert table["id"][0] == 1


def test_parse_result_repairs_zero_arraysize_votable(cstar):
    response = MockResponse(
        ZERO_ARRAYSIZE_VOTABLE,
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="application/x-votable+xml",
    )
    table = cstar._parse_result(response)
    assert len(table) == 1
    assert table["source_id"][0] == 123
    assert table["year"][0] == 1901


def test_parse_result_repairs_invalid_date_votable(cstar):
    response = MockResponse(
        INVALID_DATE_VOTABLE,
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="application/x-votable+xml",
    )
    table = cstar._parse_result(response)
    assert len(table) == 1
    assert table["id"][0] == 123
    assert table["dateobs"][0] == "2010-10-03T06:23:06.879000"


def test_parse_result_falls_back_to_general_votable_parser(cstar, monkeypatch):
    response = MockResponse(
        b"<?xml version='1.0' encoding='utf-8'?><VOTABLE></VOTABLE>",
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="application/x-votable+xml",
    )

    class FakeVOTableTable:
        fields = []

        def to_table(self, use_names_over_ids=False):
            return Table({"catalog": ["legacyplate-cat"], "rows": [5]})

    class FakeVOTableDocument:
        def iter_tables(self):
            return iter([FakeVOTableTable()])

    def fail_single_table(*args, **kwargs):
        raise IndexError("index 0 is out of bounds for size 0")

    monkeypatch.setattr(query_data_module, "parse_single_table", fail_single_table)
    monkeypatch.setattr(query_data_module, "parse_votable", lambda *args, **kwargs: FakeVOTableDocument())

    table = cstar._parse_result(response)
    assert table["catalog"][0] == "legacyplate-cat"
    assert table["rows"][0] == 5


def test_parse_result_rejects_html_error_page(cstar):
    response = MockResponse(
        b"<!DOCTYPE html><html><head><title>Login</title></head><body>login</body></html>",
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="text/html; charset=utf-8",
    )
    with pytest.raises(TableParseError, match="Server returned HTML instead of a table response"):
        cstar._parse_result(response)


def test_parse_result_includes_debug_summary_when_enabled():
    client = CstarClass(debug=True)
    response = MockResponse(
        b"<!DOCTYPE html><html><head><title>Login</title></head><body>login</body></html>",
        url="http://dummy.example/query/openapi/sqlid/1/results.votable",
        content_type="text/html; charset=utf-8",
    )
    with pytest.raises(TableParseError, match="content_type='text/html; charset=utf-8'"):
        client._parse_result(response)


def test_drop_none():
    assert _drop_none({"a": 1, "b": None}) == {"a": 1}


def test_table_from_list_of_dicts_empty():
    empty = _table_from_list_of_dicts([])
    assert isinstance(empty, Table)
    assert len(empty.colnames) == 0


def test_table_from_list_of_dicts_fills_missing_keys():
    table = _table_from_list_of_dicts([{"b": 2}, {"a": 1, "b": 3}])
    assert table.colnames == ["a", "b"]
    assert list(table["a"]) == [None, 1]
    assert list(table["b"]) == [2, 3]


def test_init_rejects_invalid_auth_method():
    with pytest.raises(ValueError, match='auth_method must be "query" or "bearer"'):
        CstarClass(auth_method="invalid")


def test_init_reads_token_from_environment(monkeypatch):
    for env_name in (
        "ASTROQUERY_CSTAR_TOKEN",
        "ASTROQUERY_NADC_CSTAR_TOKEN",
        "NADC_CSTAR_TOKEN",
        "CHINAVO_CSTAR_TOKEN",
        "ASTROQUERY_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_CSTAR_ACCESS_TOKEN",
        "NADC_CSTAR_ACCESS_TOKEN",
        "CHINAVO_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_TOKEN",
        "NADC_QUERYDATA_TOKEN",
        "ASTROQUERY_NADC_ACCESS_TOKEN",
        "NADC_QUERYDATA_ACCESS_TOKEN",
        "ASTROQUERY_CHINAVO_TOKEN",
        "CHINAVO_QUERYDATA_TOKEN",
        "ASTROQUERY_CHINAVO_ACCESS_TOKEN",
        "CHINAVO_QUERYDATA_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(env_name, raising=False)

    with conf.set_temp("token", ""), nadc_conf.set_temp("token", ""):
        monkeypatch.setenv("ASTROQUERY_CSTAR_ACCESS_TOKEN", "'env-secret'")
        assert _configured_token_from_env() == "env-secret"

        client = CstarClass(token=None)
        assert client.token == "env-secret"


def test_init_reads_shared_token_from_environment(monkeypatch):
    for env_name in (
        "ASTROQUERY_CSTAR_TOKEN",
        "ASTROQUERY_NADC_CSTAR_TOKEN",
        "NADC_CSTAR_TOKEN",
        "CHINAVO_CSTAR_TOKEN",
        "ASTROQUERY_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_CSTAR_ACCESS_TOKEN",
        "NADC_CSTAR_ACCESS_TOKEN",
        "CHINAVO_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_TOKEN",
        "NADC_QUERYDATA_TOKEN",
        "ASTROQUERY_NADC_ACCESS_TOKEN",
        "NADC_QUERYDATA_ACCESS_TOKEN",
        "ASTROQUERY_CHINAVO_TOKEN",
        "CHINAVO_QUERYDATA_TOKEN",
        "ASTROQUERY_CHINAVO_ACCESS_TOKEN",
        "CHINAVO_QUERYDATA_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(env_name, raising=False)

    with conf.set_temp("token", ""), nadc_conf.set_temp("token", ""):
        monkeypatch.setenv("ASTROQUERY_CHINAVO_TOKEN", '"shared-secret"')
        assert _configured_token_from_env() == "shared-secret"

        client = CstarClass(token=None)
        assert client.token == "shared-secret"


def test_init_prefers_explicit_and_conf_tokens_over_environment(monkeypatch):
    monkeypatch.setenv("ASTROQUERY_CSTAR_TOKEN", "env-secret")

    with conf.set_temp("token", "conf-secret"), nadc_conf.set_temp("token", "shared-secret"):
        assert CstarClass(token=None).token == "conf-secret"
        assert CstarClass(token="direct-secret").token == "direct-secret"
        assert CstarClass(token="").token is None


def test_init_uses_shared_conf_token_when_module_token_missing(monkeypatch):
    for env_name in (
        "ASTROQUERY_CSTAR_TOKEN",
        "ASTROQUERY_NADC_CSTAR_TOKEN",
        "NADC_CSTAR_TOKEN",
        "CHINAVO_CSTAR_TOKEN",
        "ASTROQUERY_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_CSTAR_ACCESS_TOKEN",
        "NADC_CSTAR_ACCESS_TOKEN",
        "CHINAVO_CSTAR_ACCESS_TOKEN",
        "ASTROQUERY_NADC_TOKEN",
        "NADC_QUERYDATA_TOKEN",
        "ASTROQUERY_NADC_ACCESS_TOKEN",
        "NADC_QUERYDATA_ACCESS_TOKEN",
        "ASTROQUERY_CHINAVO_TOKEN",
        "CHINAVO_QUERYDATA_TOKEN",
        "ASTROQUERY_CHINAVO_ACCESS_TOKEN",
        "CHINAVO_QUERYDATA_ACCESS_TOKEN",
    ):
        monkeypatch.delenv(env_name, raising=False)

    with conf.set_temp("token", ""), nadc_conf.set_temp("token", "shared-secret"):
        assert CstarClass(token=None).token == "shared-secret"


def test_safe_cache_without_token():
    plain = CstarClass(token="", auth_method="query")
    assert plain._safe_cache(True) is True
    assert plain._safe_cache(True, stream=True) is False
    assert plain._service_url("/query/openapi/ping").endswith("/query/openapi/ping")


def test_auth_bearer_mode():
    bearer = CstarClass(token="secret", auth_method="bearer")
    params, headers = bearer._auth_params_headers(params={"a": 1}, headers={"X-Test": "ok"})
    assert params == {"a": 1}
    assert headers["Authorization"] == "Bearer secret"
    assert headers["X-Test"] == "ok"
    assert bearer._safe_cache(True) is False


def test_auth_query_mode():
    query = CstarClass(token="secret", auth_method="query")
    params, headers = query._auth_params_headers(params={"a": 1})
    assert params["token"] == "secret"
    assert headers == {}


def test_request_raise_wraps_request(monkeypatch):
    client = CstarClass(token="token", auth_method="query")
    captured = {}

    class Response(MockResponse):
        def __init__(self):
            super().__init__(b"{}", url="http://dummy.example", content_type="application/json")
            self.raise_called = False

        def raise_for_status(self):
            self.raise_called = True

    response = Response()

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["kwargs"] = kwargs
        return response

    monkeypatch.setattr(client, "_request", fake_request)
    result = client._request_raise(
        "POST",
        "http://dummy.example/query",
        params={"x": 1},
        headers={"X-Test": "yes"},
        json={"payload": True},
        timeout=17,
        cache=True,
        stream=True,
    )

    assert result is response
    assert response.raise_called is True
    assert captured["method"] == "POST"
    assert captured["kwargs"]["params"]["token"] == "token"
    assert captured["kwargs"]["headers"]["X-Test"] == "yes"
    assert captured["kwargs"]["timeout"] == 17
    assert captured["kwargs"]["cache"] is False
    assert captured["kwargs"]["stream"] is True


def test_request_raise_surfaces_structured_api_errors(monkeypatch):
    client = CstarClass(token="token", auth_method="query")

    response = MockResponse(
        json.dumps(
            {
                "error": "not_found",
                "message": "Table 'missing' not found in catalog 'cstar'",
                "method": "GET",
                "path": "/query/openapi/catalogs/cstar/tables/missing/columns",
                "status_code": 404,
            }
        ).encode("utf-8"),
        url="http://dummy.example/query/openapi/catalogs/cstar/tables/missing/columns",
        content_type="application/json",
        status_code=404,
    )

    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: response)

    with pytest.raises(
        HTTPError,
        match=r"CSTAR API error \(404\): not_found: Table 'missing' not found in catalog 'cstar'",
    ):
        client._request_raise("GET", response.url)


def test_request_raise_includes_debug_context(monkeypatch):
    client = CstarClass(token="token", auth_method="query", debug=True)

    response = MockResponse(
        json.dumps(
            {
                "error": "not_found",
                "message": "Table 'missing' not found in catalog 'cstar'",
                "method": "GET",
                "path": "/query/openapi/catalogs/cstar/tables/missing/columns",
                "status_code": 404,
            }
        ).encode("utf-8"),
        url="http://dummy.example/query/openapi/catalogs/cstar/tables/missing/columns",
        content_type="application/json",
        status_code=404,
    )

    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: response)

    with pytest.raises(HTTPError, match=r"\[GET /query/openapi/catalogs/cstar/tables/missing/columns status=404\]"):
        client._request_raise("GET", response.url)


def test_request_raise_falls_back_to_response_body_preview(monkeypatch):
    client = CstarClass(token=None)

    response = MockResponse(
        b"Gateway timeout while contacting upstream service",
        url="http://dummy.example/query/openapi/catalogs/cstar/query",
        content_type="text/plain",
        status_code=504,
    )

    monkeypatch.setattr(client, "_request", lambda *args, **kwargs: response)

    with pytest.raises(HTTPError, match=r"CSTAR API error \(504\): Gateway timeout while contacting upstream service"):
        client._request_raise("POST", response.url)


def test_ping_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    ping = client.ping(get_query_payload=True)
    assert ping == {"method": "GET", "url": client._service_url("/query/openapi/ping")}


def test_list_catalogs_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    catalogs = client.list_catalogs(get_query_payload=True)
    assert catalogs["params"]["token"] == "secret"


def test_get_catalog_metadata_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    metadata = client.get_catalog_metadata(get_query_payload=True)
    assert metadata["url"].endswith("/query/openapi/catalogs/demo")
    assert metadata["params"]["token"] == "secret"


def test_list_tables_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    tables = client.list_tables(get_query_payload=True)
    assert tables["url"].endswith("/query/openapi/catalogs/demo/tables")
    assert tables["params"]["token"] == "secret"


def test_list_columns_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    columns = client.list_columns("sources", get_query_payload=True)
    assert columns["url"].endswith("/query/openapi/catalogs/demo/tables/sources/columns")
    assert columns["params"]["token"] == "secret"


def test_list_table_links_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    table_links = client.list_table_links(get_query_payload=True)
    assert table_links["url"].endswith("/query/openapi/catalogs/demo/table_links")
    assert table_links["params"]["token"] == "secret"


def test_submit_query_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    submit = client.submit_query({"output.fmt": "html"}, get_query_payload=True)
    assert submit["method"] == "POST"
    assert submit["json"]["output.fmt"] == "html"
    assert submit["params"]["token"] == "secret"


def test_submit_query_returns_job_metadata(cstar):
    submit = cstar.submit_query({"output.fmt": "html"})
    assert submit == {"sqlid": 123}


def test_submit_table_query_returns_job_metadata(cstar):
    submit = cstar.submit_table_query({"output.fmt": "html"}, table="catalog")
    assert submit == {"sqlid": 123}


def test_submit_query_sqlid_can_fetch_results(cstar):
    submit = cstar.submit_query({"output.fmt": "html"})
    results = cstar.get_results(submit["sqlid"])
    assert isinstance(results, Table)
    assert {"ra", "dec", "id"}.issubset(set(results.colnames))


def test_get_results_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    results = client.get_results(42, fmt=".csv", page=2, rows=3, sort="id", order="desc", get_query_payload=True)
    assert results["url"].endswith("/query/openapi/sqlid/42/results.csv")
    assert results["params"] == {"page": 2, "rows": 3, "sort": "id", "order": "desc", "token": "secret"}


def test_get_results_max_rows_alias():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    results_alias = client.get_results(42, max_rows=4, get_query_payload=True)
    assert results_alias["params"] == {"page": 1, "rows": 4, "token": "secret"}


def test_get_results_rejects_rows_and_max_rows():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    with pytest.raises(InvalidQueryError, match="Provide either `rows` or `max_rows`"):
        client.get_results(42, rows=3, max_rows=4, get_query_payload=True)


def test_get_count_payload():
    client = CstarClass(catalog="demo", token="secret", auth_method="query")
    count = client.get_count(42, get_query_payload=True)
    assert count["url"].endswith("/query/openapi/sqlid/42/count")
    assert count["params"]["token"] == "secret"


def test_metadata_request_methods(monkeypatch):
    client = CstarClass(catalog="demo", token=None)
    calls = []

    def fake_request_raise(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return {"method": method, "url": url, "kwargs": kwargs}

    monkeypatch.setattr(client, "_request_raise", fake_request_raise)

    assert client._request_ping(cache=False)["url"].endswith("/query/openapi/ping")
    assert client._request_catalog_metadata(cache=False)["url"].endswith("/query/openapi/catalogs/demo")
    assert client._request_list_tables(cache=False)["url"].endswith("/query/openapi/catalogs/demo/tables")
    assert client._request_list_columns("sources", cache=False)["url"].endswith(
        "/query/openapi/catalogs/demo/tables/sources/columns"
    )
    assert client._get_count_response(42, cache=False)["url"].endswith("/query/openapi/sqlid/42/count")
    assert [call[2]["cache"] for call in calls] == [False, False, False, False, False]


def test_conesearch_numeric_and_format_helpers(cstar):
    payload = cstar.conesearch(
        1.5,
        -2.5,
        3.0,
        verb=3,
        output_format="csv",
        get_query_payload=True,
    )
    assert payload["params"]["RA"] == 1.5
    assert payload["params"]["DEC"] == -2.5
    assert payload["params"]["VERB"] == 3
    assert payload["params"]["SR"] == pytest.approx(3.0 * u.arcsec.to(u.deg))

    assert cstar._normalize_output_format("html", allow_html=True) == "html"
    with pytest.raises(InvalidQueryError, match="conesearch output_format"):
        cstar.conesearch(1, 2, 3, output_format="fits", get_query_payload=True)
    with pytest.raises(InvalidQueryError, match="output_format must be one of"):
        cstar._normalize_output_format("fits")


@pytest.mark.parametrize(
    ("method_name", "value", "name"),
    [
        ("_to_degree", object(), "ra"),
        ("_to_arcsec", object(), "radius"),
    ],
)
def test_angle_conversion_validation(cstar, method_name, value, name):
    method = getattr(cstar, method_name)
    with pytest.raises(InvalidQueryError, match=f"{name} must be a float or angular quantity"):
        method(value, name=name)


def test_proximity_helpers(cstar):
    coord_obj = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    assert cstar._format_proximity_line(" 1,2,3 ") == "1,2,3"
    assert cstar._format_proximity_line(coord_obj) == "1.0,2.0"
    assert cstar._format_proximity_line((1 * u.deg, 2 * u.deg)) == "1.0,2.0"
    assert cstar._format_proximity_line((1, 2, 3 * u.arcsec)) == "1.0,2.0,3.0"

    built = cstar._build_proximity_pos(" 1,2 \n 3,4 ", nearest_only=True)
    assert built["type"] == "proximity"
    assert built["proximity"]["radecTextarea"] == "1,2 \n 3,4"
    assert built["proximity"]["proximity_nearestonly"] is True

    with pytest.raises(InvalidQueryError, match="must not be empty"):
        cstar._format_proximity_line("   ")
    with pytest.raises(InvalidQueryError, match="2/3-item iterable"):
        cstar._format_proximity_line((1, 2, 3, 4))
    with pytest.raises(InvalidQueryError, match="At least one proximity position is required"):
        cstar._build_proximity_pos("   ")


def test_query_catalog_validation_errors(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    pos = {"type": "cone", "cone": {"racenter": 1.0, "deccenter": 2.0, "radius": 3.0}}

    with pytest.raises(InvalidQueryError, match="Provide either `pos` or"):
        cstar.query_catalog(coordinates=c, radius=5 * u.arcsec, pos=pos)
    with pytest.raises(InvalidQueryError, match="both `coordinates` and `radius` are required"):
        cstar.query_catalog(coordinates=c)
    with pytest.raises(InvalidQueryError, match="both `coordinates` and `radius` are required"):
        cstar.query_catalog(radius=5 * u.arcsec)


def test_execute_catalog_query_response_chain(cstar):
    c = coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs")
    payload = cstar._build_catalog_query_payload(
        pos=cstar._build_cone_pos(c, 5 * u.arcsec),
    )
    response = cstar._execute_catalog_query_response(
        payload,
        output_format="votable",
        page=1,
        rows=2,
    )
    assert isinstance(response, MockResponse)
    assert response.headers["Content-Type"] == "application/x-votable+xml"
    assert cstar._nreq == 2


def test_execute_catalog_query_table_edge_cases(cstar, monkeypatch):
    empty = cstar._execute_catalog_query_table({"output.fmt": "html"}, max_rows=0)
    assert isinstance(empty, Table)
    assert len(empty) == 0

    with pytest.raises(InvalidQueryError, match="max_rows must be -1, 0, or a positive integer"):
        cstar._execute_catalog_query_table({"output.fmt": "html"}, max_rows=-2)

    with pytest.raises(InvalidQueryError, match="page_size must be a positive integer"):
        cstar._execute_catalog_query_table({"output.fmt": "html"}, max_rows=1, page_size=0)

    monkeypatch.setattr(cstar, "_submit_catalog_job", lambda *args, **kwargs: 7)
    monkeypatch.setattr(cstar, "_get_results_response", lambda *args, **kwargs: MockResponse(b"", url="http://dummy"))
    monkeypatch.setattr(cstar, "_parse_result", lambda *args, **kwargs: Table())
    result = cstar._execute_catalog_query_table({"output.fmt": "html"}, max_rows=5, page_size=5)
    assert isinstance(result, Table)
    assert len(result) == 0


def test_execute_catalog_query_table_uses_default_row_limit():
    client = CstarClass(catalog="cstar", token="secret", auth_method="query")

    with conf.set_temp("row_limit", 7):
        payload = client._execute_catalog_query_table({"output.fmt": "html"}, get_query_payload=True)

    assert payload["max_rows"] == 7
    assert payload["page_size"] == 7
    assert payload["results"]["params"]["rows"] == 7
    assert payload["submit"]["params"]["token"] == "secret"


def test_execute_catalog_query_table_single_page(monkeypatch):
    client = CstarClass(catalog="cstar", token=None)
    pages = iter([Table({"value": [1, 2]})])

    monkeypatch.setattr(client, "_submit_catalog_job", lambda *args, **kwargs: 9)
    monkeypatch.setattr(client, "_get_results_response", lambda *args, **kwargs: MockResponse(b"", url="http://dummy"))
    monkeypatch.setattr(client, "_parse_result", lambda *args, **kwargs: next(pages))

    result = client._execute_catalog_query_table({"output.fmt": "html"}, max_rows=10, page_size=5)
    assert len(result) == 2
    assert client.table is result


def test_execute_catalog_query_table_multiple_pages(monkeypatch):
    client = CstarClass(catalog="cstar", token=None)
    requested_pages = []
    payloads = {
        1: [{"value": 1}, {"value": 2}],
        2: [{"value": 3}, {"value": 4}],
        3: [],
    }

    monkeypatch.setattr(client, "_submit_catalog_job", lambda *args, **kwargs: 9)

    def fake_get_results_response(sqlid, **kwargs):
        page = kwargs["page"]
        requested_pages.append(page)
        return json_response(payloads[page], url=f"http://dummy/sqlid/{sqlid}/results.json")

    monkeypatch.setattr(client, "_get_results_response", fake_get_results_response)

    result = client._execute_catalog_query_table(
        {"output.fmt": "html"},
        output_format="json",
        max_rows=-1,
        page_size=2,
    )

    assert list(result["value"]) == [1, 2, 3, 4]
    assert requested_pages == [1, 2, 3]
    assert client.table is result


def test_execute_catalog_query_table_truncates_oversized_page(monkeypatch):
    client = CstarClass(catalog="cstar", token=None)
    page = Table({"value": [1, 2, 3]})

    monkeypatch.setattr(client, "_submit_catalog_job", lambda *args, **kwargs: 9)
    monkeypatch.setattr(client, "_get_results_response", lambda *args, **kwargs: MockResponse(b"", url="http://dummy"))
    monkeypatch.setattr(client, "_parse_result", lambda *args, **kwargs: page)

    result = client._execute_catalog_query_table({"output.fmt": "html"}, max_rows=2, page_size=5)
    assert list(result["value"]) == [1, 2]
    assert client.table is result


def test_query_catalog_proximity_sync_and_query_object(cstar, monkeypatch):
    table = cstar.query_catalog_proximity(
        [(1 * u.deg, 2 * u.deg), (3, 4, 5 * u.arcsec)],
        default_radius=2 * u.arcsec,
        max_rows=1,
        page_size=5,
    )
    assert isinstance(table, Table)
    assert len(table) == 1

    calls = {}

    def fake_query_region(object_name, radius, **kwargs):
        calls["object_name"] = object_name
        calls["radius"] = radius
        calls["kwargs"] = kwargs
        return {"ok": True}

    monkeypatch.setattr(cstar, "query_region", fake_query_region)
    payload = cstar.query_object("M31", 5 * u.arcsec, output_format="json")
    assert payload == {"ok": True}
    assert calls["object_name"] == "M31"
    assert calls["kwargs"]["output_format"] == "json"


def test_extract_sqlid_branches(cstar):
    assert cstar._extract_sqlid(json_response(42)) == 42
    assert cstar._extract_sqlid(json_response("123")) == 123
    assert cstar._extract_sqlid(json_response({"sqlid": 7})) == 7

    with pytest.raises(TableParseError, match="Could not parse sqlid from key"):
        cstar._extract_sqlid(json_response({"sqlid": "abc"}))
    with pytest.raises(TableParseError, match="did not return JSON"):
        cstar._extract_sqlid(MockResponse(b"not-json", url="http://dummy", content_type="text/plain"))
    with pytest.raises(TableParseError, match="Could not extract sqlid"):
        cstar._extract_sqlid(json_response({"other": 1}))


def test_extract_sqlid_includes_debug_summary_when_enabled():
    client = CstarClass(debug=True)
    response = MockResponse(b"not-json", url="http://dummy/sqlid", content_type="text/plain")
    with pytest.raises(TableParseError, match="content_type='text/plain'"):
        client._extract_sqlid(response)


def test_parse_result_csv_plain_and_json_variants(cstar):
    csv_table = cstar._parse_result(
        MockResponse(b"a,b\n1,2\n", url="http://dummy", content_type="text/csv")
    )
    assert csv_table.colnames == ["a", "b"]

    txt_table = cstar._parse_result(
        MockResponse(b"a b\n1 2\n", url="http://dummy", content_type="text/plain")
    )
    assert txt_table.colnames == ["a", "b"]

    json_list = cstar._parse_result(json_response([{"a": 1}, {"a": 2}]))
    assert list(json_list["a"]) == [1, 2]

    rows_table = cstar._parse_result(json_response({"rows": [{"x": 1}]}))
    assert rows_table["x"][0] == 1

    tables_table = cstar._parse_result(json_response({"tables": [{"name": "t"}]}))
    assert tables_table["name"][0] == "t"

    columns_table = cstar._parse_result(json_response({"columns": [{"name": "col"}]}))
    assert columns_table["name"][0] == "col"

    total_table = cstar._parse_result(json_response({"total": 5}))
    assert total_table["total"][0] == 5

    mapping_table = cstar._parse_result(json_response({"status": "ok", "version": 1}))
    assert mapping_table["status"][0] == "ok"
    assert mapping_table["version"][0] == 1


@pytest.mark.parametrize(
    ("response", "exception_type", "match"),
    [
        (
            MockResponse(b"", url="http://dummy", content_type="text/plain"),
            TableParseError,
            "Failed to parse ASCII table response",
        ),
        (
            json_response([1, 2, 3]),
            TableParseError,
            "JSON response is a list but not a list of objects",
        ),
        (
            json_response({"rows": [1]}),
            TableParseError,
            "Response 'rows' is not a list of objects",
        ),
        (
            json_response({"tables": [1]}),
            TableParseError,
            "Response 'tables' is not a list of objects",
        ),
        (
            json_response({"columns": [1]}),
            TableParseError,
            "Response 'columns' is not a list of objects",
        ),
        (
            json_response({"nested": {"a": 1}}),
            InvalidQueryError,
            "Unrecognized JSON response structure",
        ),
        (
            MockResponse(b"not-json", url="http://dummy", content_type="application/json"),
            TableParseError,
            "Failed to decode JSON response",
        ),
        (
            MockResponse(b"binary", url="http://dummy", content_type="application/octet-stream"),
            TableParseError,
            "Unrecognized response content-type",
        ),
        (
            MockResponse(
                BROKEN_MALFORMED_VOTABLE,
                url="http://dummy.example/query/openapi/sqlid/1/results.votable",
                content_type="application/x-votable+xml",
            ),
            TableParseError,
            "Failed to parse VOTable response",
        ),
    ],
)
def test_parse_result_error_paths(cstar, response, exception_type, match):
    with pytest.raises(exception_type, match=match):
        cstar._parse_result(response)
