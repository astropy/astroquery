# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json

import astropy.coordinates as coord
import astropy.units as u
from astropy.table import Table
import pytest

from astroquery.nadc import conf as nadc_conf
from astroquery.nadc import ColumnConstraint
from astroquery.nadc.tests.helpers import (
    assert_task_columns,
    assert_task_cone,
    assert_task_constraints,
    assert_task_query_payload,
)
from astroquery.exceptions import InvalidQueryError
from astroquery.utils.mocks import MockResponse

from .. import conf
from ..core import LegacyplateClass, _configured_token_from_env


RESULTS_VOTABLE = b"""<?xml version='1.0' encoding='utf-8'?>
<VOTABLE version='1.4' xmlns='http://www.ivoa.net/xml/VOTable/v1.3'>
  <RESOURCE>
    <TABLE>
      <FIELD name='id' datatype='int'/>
      <FIELD name='ra' datatype='double'/>
      <FIELD name='dec' datatype='double'/>
      <DATA>
        <TABLEDATA>
          <TR><TD>1</TD><TD>12.3</TD><TD>-45.6</TD></TR>
        </TABLEDATA>
      </DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>
"""


def json_response(data, *, url="http://dummy.example/query/openapi/json"):
    return MockResponse(
        json.dumps(data).encode("utf-8"),
        url=url,
        content_type="application/json",
    )


def nonremote_request(self, request_type, url, **kwargs):
    self._nreq = getattr(self, "_nreq", 0) + 1
    if url.endswith("/query/openapi/vo/legacyplate/conesearch"):
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/vo/legacyplate-image/siap"):
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/catalogs/legacyplate/query"):
        return json_response({"sqlid": 7}, url=url)
    if url.endswith("/query/openapi/catalogs/legacyplate/docs"):
        return json_response(
            {
                "total": 1,
                "rows": [
                    {"id": "intro", "title": "Introduction", "catname": "legacyplate"},
                ],
            },
            url=url,
        )
    if url.endswith("/query/openapi/catalogs/legacyplate/docs/intro"):
        return json_response(
            {
                "id": "intro",
                "title": "Introduction",
                "content": "Legacy plate catalog docs",
                "catname": "legacyplate",
            },
            url=url,
        )
    if url.endswith("/query/openapi/catalogs/legacyplate"):
        return json_response(
            {
                "catname": "legacyplate",
                "capabilities": {
                    "queryable": False,
                    "catalog_query": False,
                    "table_query": False,
                    "table_metadata_available": False,
                    "docs": True,
                    "file_download": False,
                },
                "query_status": {
                    "code": "no_tables",
                    "reason": "No table metadata is configured for this catalog.",
                },
                "file_download": {"supported": False, "categories": []},
            },
            url=url,
        )
    if url.endswith("/query/openapi/catalogs/legacyplate-image"):
        return json_response(
            {
                "catname": "legacyplate-image",
                "capabilities": {
                    "queryable": True,
                    "catalog_query": True,
                    "table_query": True,
                    "table_metadata_available": True,
                    "conesearch": True,
                    "siap": True,
                    "ssap": False,
                    "docs": True,
                    "file_download": True,
                },
                "query_status": {
                    "code": "ok",
                    "reason": "Catalog table metadata is configured and query endpoints are available.",
                },
                "file_download": {
                    "supported": True,
                    "single_file_endpoint": "/query/openapi/catalogs/legacyplate-image/file",
                    "batch_download_endpoint": "/query/openapi/catalogs/legacyplate-image/download",
                    "categories": ["fits", "out"],
                    "id_source": {
                        "column": "filename",
                        "result_field": "image_filename",
                        "parameter": "id",
                    },
                    "single_file_query_by_category": {
                        "fits": {"category": "fits"},
                        "out": {"category": "out"},
                    },
                },
            },
            url=url,
        )
    if url.endswith("/query/openapi/catalogs/legacyplate-image/file"):
        return MockResponse(
            b"plate-bytes",
            url=url,
            headers={"Content-Disposition": 'attachment; filename="plate.fits"'},
            content_type="application/octet-stream",
        )
    if url.endswith("/query/openapi/catalogs/legacyplate-image/download"):
        if kwargs.get("json", {}).get("fmt") == "samba":
            return json_response({"status": "submitted", "target": "samba"}, url=url)
        return MockResponse(
            b"http://example.com/file1\nhttp://example.com/file2\n",
            url=url,
            headers={"Content-Disposition": 'attachment; filename="urls.txt"'},
            content_type="text/plain",
        )
    if url.endswith("/query/openapi/catalogs/legacyplateedr/tables/images/vo/conesearch"):
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/catalogs/legacyplateedr/tables/images/coordinate_groups"):
        return json_response(
            {
                "default_group_id": "ra,dec",
                "groups": [
                    {
                        "id": "ra,dec",
                        "label": "Main coordinates",
                        "ra_column": "ra",
                        "dec_column": "dec",
                        "queryable": True,
                        "is_default": True,
                        "source": "ucd",
                        "selectors": {"role": "main"},
                        "warnings": [],
                    }
                ],
                "metadata_quality": "ok",
                "requires_selection": False,
                "spatial_query_supported": True,
                "status": "resolved",
                "warnings": [],
            },
            url=url,
        )
    if "/query/openapi/sqlid/" in url and "results.votable" in url:
        return MockResponse(RESULTS_VOTABLE, url=url, content_type="application/x-votable+xml")
    if url.endswith("/query/openapi/get_catalogs"):
        return json_response(
            {
                "total": 6,
                "rows": [
                    {
                        "catname": "cstar",
                        "priority": 0,
                        "queryable": True,
                        "catalog_query_supported": True,
                        "table_query_supported": True,
                        "file_download_supported": True,
                    },
                    {
                        "catname": "legacyplate",
                        "priority": 1,
                        "queryable": False,
                        "catalog_query_supported": False,
                        "table_query_supported": False,
                        "file_download_supported": False,
                    },
                    {
                        "catname": "legacyplateedr",
                        "priority": 2,
                        "queryable": True,
                        "catalog_query_supported": True,
                        "table_query_supported": True,
                        "file_download_supported": True,
                    },
                    {
                        "catname": "legacyplate-cat",
                        "priority": 3,
                        "queryable": True,
                        "catalog_query_supported": True,
                        "table_query_supported": True,
                        "file_download_supported": False,
                    },
                    {
                        "catname": "legacyplate-image",
                        "priority": 4,
                        "queryable": True,
                        "catalog_query_supported": True,
                        "table_query_supported": True,
                        "file_download_supported": True,
                    },
                    {
                        "catname": "legacyplate_scans",
                        "priority": 5,
                        "queryable": False,
                        "catalog_query_supported": False,
                        "table_query_supported": False,
                        "file_download_supported": False,
                    },
                ],
            },
            url=url,
        )
    if "/tables" in url and "/columns" in url:
        # e.g. /catalogs/legacyplateedr/tables/images/columns
        return json_response(
            {
                "total": 3,
                "rows": [
                    {"colname": "id", "datatype": "long", "description": ""},
                    {"colname": "observat", "datatype": "char", "description": "observatory"},
                    {"colname": "year", "datatype": "int", "description": "year"},
                ],
            },
            url=url,
        )
    if "/tables" in url:
        # e.g. /catalogs/legacyplateedr/tables
        return json_response(
            {
                "total": 1,
                "rows": [
                    {"tblname": "images", "records": 100, "tbltype": "BASE TABLE"},
                ],
            },
            url=url,
        )
    raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")


@pytest.fixture
def legacyplate(monkeypatch):
    monkeypatch.setattr(LegacyplateClass, "_request", nonremote_request)
    client = LegacyplateClass(catalog="legacyplate", token=None)
    client.URL = "http://dummy.example/"
    client._nreq = 0
    return client


def test_default_catalog_and_supported_catalogs(legacyplate):
    assert legacyplate.catalog == "legacyplate"
    assert legacyplate._supported_catalogs() == [
        "legacyplate",
        "legacyplateedr",
        "legacyplate-cat",
        "legacyplate-image",
    ]


def test_list_catalogs_filters_supported_queryable_catalogs(legacyplate):
    table = legacyplate.list_catalogs()
    assert isinstance(table, Table)
    assert list(table["catname"]) == [
        "legacyplateedr",
        "legacyplate-cat",
        "legacyplate-image",
    ]


def test_list_catalogs_can_include_unqueryable_supported_catalogs(legacyplate):
    table = legacyplate.list_catalogs(queryable_only=False)

    assert isinstance(table, Table)
    assert list(table["catname"]) == [
        "legacyplate",
        "legacyplateedr",
        "legacyplate-cat",
        "legacyplate-image",
    ]


def test_supported_catalogs_can_be_configured(monkeypatch):
    monkeypatch.setattr(LegacyplateClass, "_request", nonremote_request)
    with conf.set_temp("supported_catalogs", "legacyplate, legacyplate_scans"):
        client = LegacyplateClass(catalog="legacyplate", token=None)
        client.URL = "http://dummy.example/"
        table = client.list_catalogs(queryable_only=False)

    assert set(table["catname"]) == {"legacyplate", "legacyplate_scans"}


def test_init_reads_shared_token_from_environment(monkeypatch):
    for env_name in (
        "ASTROQUERY_LEGACYPLATE_TOKEN",
        "ASTROQUERY_NADC_LEGACYPLATE_TOKEN",
        "NADC_LEGACYPLATE_TOKEN",
        "CHINAVO_LEGACYPLATE_TOKEN",
        "ASTROQUERY_LEGACYPLATE_ACCESS_TOKEN",
        "ASTROQUERY_NADC_LEGACYPLATE_ACCESS_TOKEN",
        "NADC_LEGACYPLATE_ACCESS_TOKEN",
        "CHINAVO_LEGACYPLATE_ACCESS_TOKEN",
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
        monkeypatch.setenv("CHINAVO_QUERYDATA_TOKEN", "shared-secret")
        assert _configured_token_from_env() == "shared-secret"

        client = LegacyplateClass(catalog="legacyplate", token=None)
        assert client.token == "shared-secret"


def test_init_uses_shared_conf_token_when_module_token_missing(monkeypatch):
    for env_name in (
        "ASTROQUERY_LEGACYPLATE_TOKEN",
        "ASTROQUERY_NADC_LEGACYPLATE_TOKEN",
        "NADC_LEGACYPLATE_TOKEN",
        "CHINAVO_LEGACYPLATE_TOKEN",
        "ASTROQUERY_LEGACYPLATE_ACCESS_TOKEN",
        "ASTROQUERY_NADC_LEGACYPLATE_ACCESS_TOKEN",
        "NADC_LEGACYPLATE_ACCESS_TOKEN",
        "CHINAVO_LEGACYPLATE_ACCESS_TOKEN",
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
        client = LegacyplateClass(catalog="legacyplate", token=None)
        assert client.token == "shared-secret"


def test_query_catalog_cone_payload_includes_constraints_and_sorting(legacyplate):
    payload = legacyplate.query_catalog_cone(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        column_constraints=[
            {"column_name": "year", "operation": "greaterequal", "constraint": "1900"},
            {"column_name": "observat", "operation": "equal", "constraint": "Naoc"},
        ],
        sort="year",
        order="desc",
        get_query_payload=True,
    )

    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/legacyplate/query")
    assert payload["submit"]["json"]["column_constraints"][0]["column_name"] == "year"
    assert payload["submit"]["json"]["column_constraints"][0]["operation"] == "greaterequal"
    assert payload["submit"]["json"]["column_constraints"][1]["column_name"] == "observat"
    assert payload["submit"]["json"]["column_constraints"][1]["constraint"] == "Naoc"
    assert payload["results"]["params"]["sort"] == "year"
    assert payload["results"]["params"]["order"] == "desc"


def test_query_region_uses_default_catalog(legacyplate):
    payload = legacyplate.query_region(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        get_query_payload=True,
    )
    assert payload["url"].endswith("/query/openapi/vo/legacyplate/conesearch")


def test_list_catalogs_payload_is_raw_service_request():
    client = LegacyplateClass(catalog="legacyplate", token="secret", auth_method="query")
    module_payload = client.list_catalogs(get_query_payload=True)
    assert module_payload["params"]["token"] == "secret"


# ---------------------------------------------------------------------------
# ColumnConstraint dataclass tests
# ---------------------------------------------------------------------------


class TestColumnConstraint:

    @pytest.mark.parametrize(
        ("factory_name", "args", "expected"),
        [
            (
                "equal",
                ("observat", "Naoc"),
                {"column_name": "observat", "operation": "equal", "constraint": "Naoc"},
            ),
            (
                "notequal",
                ("observat", "Pmo"),
                {"column_name": "observat", "operation": "notequal", "constraint": "Pmo"},
            ),
            (
                "less",
                ("year", "1960"),
                {"column_name": "year", "operation": "less", "constraint": "1960"},
            ),
            (
                "lessequal",
                ("year", "1960"),
                {"column_name": "year", "operation": "lessequal", "constraint": "1960"},
            ),
            (
                "greater",
                ("year", "1960"),
                {"column_name": "year", "operation": "greater", "constraint": "1960"},
            ),
            (
                "greaterequal",
                ("year", "1950"),
                {"column_name": "year", "operation": "greaterequal", "constraint": "1950"},
            ),
            (
                "between",
                ("year", 1950, 1970),
                {"column_name": "year", "operation": "between", "min": 1950, "max": 1970},
            ),
            (
                "contains",
                ("object", "M31"),
                {"column_name": "object", "operation": "contains", "constraint": "M31"},
            ),
            (
                "in_",
                ("observat", ["Naoc", "Shao", "Ynao"]),
                {"column_name": "observat", "operation": "in", "textarea": "Naoc\nShao\nYnao"},
            ),
        ],
    )
    def test_factory_to_dict(self, factory_name, args, expected):
        cc = getattr(ColumnConstraint, factory_name)(*args)

        assert cc.column_name == expected["column_name"]
        assert cc.operation == expected["operation"]
        assert cc.to_dict() == expected

    def test_frozen(self):
        cc = ColumnConstraint.equal("year", "1950")
        with pytest.raises(AttributeError):
            cc.column_name = "other"

    def test_to_dict_omits_none_fields(self):
        cc = ColumnConstraint.equal("year", "1950")
        d = cc.to_dict()
        assert "min" not in d
        assert "max" not in d
        assert "textarea" not in d


# ---------------------------------------------------------------------------
# ColumnConstraint in payload tests
# ---------------------------------------------------------------------------


def test_query_catalog_cone_payload_with_column_constraint_objects(legacyplate):
    payload = legacyplate.query_catalog_cone(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        column_constraints=[
            ColumnConstraint.greaterequal("year", "1900"),
            ColumnConstraint.equal("observat", "Naoc"),
        ],
        sort="year",
        order="desc",
        get_query_payload=True,
    )

    constraints = payload["submit"]["json"]["column_constraints"]
    assert constraints[0] == {"column_name": "year", "operation": "greaterequal", "constraint": "1900"}
    assert constraints[1] == {"column_name": "observat", "operation": "equal", "constraint": "Naoc"}


def test_query_catalog_cone_payload_with_mixed_constraints(legacyplate):
    """ColumnConstraint objects and raw dicts can be mixed."""
    payload = legacyplate.query_catalog_cone(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        column_constraints=[
            ColumnConstraint.equal("observat", "Naoc"),
            {"column_name": "year", "operation": "greaterequal", "constraint": "1950"},
        ],
        get_query_payload=True,
    )

    constraints = payload["submit"]["json"]["column_constraints"]
    assert constraints[0]["column_name"] == "observat"
    assert constraints[1]["column_name"] == "year"


def test_query_plates_builds_archive_payload(legacyplate):
    payload = legacyplate.query_plates(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        year_range=(1950, 1970),
        observatory="Shao",
        telescope="40/60",
        object_name="M31",
        columns=["id", "year", "observat", "object"],
        nearest_only=True,
        output_format="json",
        max_rows=20,
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/legacyplateedr/query",
        result_format="json",
    )
    assert_task_cone(payload, radius_arcsec=5.0, nearest_only=True)
    assert_task_columns(payload, ["id", "year", "observat", "object"])
    assert_task_constraints(
        payload,
        [
            {"column_name": "year", "operation": "between", "min": 1950, "max": 1970},
            {"column_name": "observat", "operation": "equal", "constraint": "Shao"},
            {"column_name": "telescop", "operation": "equal", "constraint": "40/60"},
            {"column_name": "object", "operation": "contains", "constraint": "M31"},
        ],
    )


def test_query_plate_images_targets_image_catalog(legacyplate):
    payload = legacyplate.query_plate_images(
        observatory="Naoc",
        columns=["filename", "year", "observat"],
        output_format="json",
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/legacyplate-image/query",
        result_format="json",
    )
    assert_task_columns(payload, ["filename", "year", "observat"])
    assert_task_constraints(
        payload,
        [{"column_name": "observat", "operation": "equal", "constraint": "Naoc"}],
    )


# ---------------------------------------------------------------------------
# list_columns optional table tests
# ---------------------------------------------------------------------------


def test_list_columns_with_explicit_table(legacyplate):
    table = legacyplate.list_columns("images", catalog="legacyplateedr")
    assert isinstance(table, Table)
    assert "colname" in table.colnames


def test_list_columns_auto_detect_single_table(legacyplate):
    table = legacyplate.list_columns(catalog="legacyplateedr")
    assert isinstance(table, Table)
    assert "colname" in table.colnames
    assert "year" in list(table["colname"])


def test_query_table_cone_payload_uses_explicit_table(legacyplate):
    payload = legacyplate.query_table_cone(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        catalog="legacyplateedr",
        table="images",
        coordinate_group="ra,dec",
        get_query_payload=True,
    )

    assert payload["url"].endswith("/query/openapi/catalogs/legacyplateedr/tables/images/vo/conesearch")
    assert payload["params"]["RA"] == 1.0
    assert payload["params"]["DEC"] == 2.0
    assert payload["params"]["coordinate_group"] == "ra,dec"


def test_query_table_cone_parses_votable(legacyplate):
    table = legacyplate.query_table_cone(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        5 * u.arcsec,
        catalog="legacyplateedr",
    )

    assert isinstance(table, Table)
    assert list(table["id"]) == [1]


def test_list_coordinate_groups_auto_detects_single_table(legacyplate):
    table = legacyplate.list_coordinate_groups(catalog="legacyplateedr")

    assert isinstance(table, Table)
    assert list(table["id"]) == ["ra,dec"]
    assert table.meta["default_group_id"] == "ra,dec"
    assert table.meta["status"] == "resolved"
    assert table.meta["spatial_query_supported"] is True


def test_query_siap_payload_uses_degree_size(legacyplate):
    payload = legacyplate.query_siap(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        0.5,
        catalog="legacyplate-image",
        get_query_payload=True,
    )

    assert payload["url"].endswith("/query/openapi/vo/legacyplate-image/siap")
    assert payload["params"]["POS"] == "1.0,2.0"
    assert payload["params"]["SIZE"] == 0.5
    assert payload["params"]["format"] == "votable"


def test_query_siap_parses_votable(legacyplate):
    table = legacyplate.query_siap(
        coord.SkyCoord(ra=1 * u.deg, dec=2 * u.deg, frame="icrs"),
        0.5 * u.deg,
        catalog="legacyplate-image",
    )

    assert isinstance(table, Table)
    assert list(table["id"]) == [1]


def test_list_docs_parses_table(legacyplate):
    table = legacyplate.list_docs(catalog="legacyplate")

    assert isinstance(table, Table)
    assert list(table["id"]) == ["intro"]
    assert table.meta["total"] == 1


def test_get_doc_returns_mapping(legacyplate):
    document = legacyplate.get_doc("intro", catalog="legacyplate")

    assert document["id"] == "intro"
    assert document["content"] == "Legacy plate catalog docs"


def test_get_catalog_metadata_returns_mapping(legacyplate):
    metadata = legacyplate.get_catalog_metadata(catalog="legacyplate-image")

    assert metadata["catname"] == "legacyplate-image"
    assert metadata["file_download"]["supported"] is True
    assert metadata["file_download"]["categories"] == ["fits", "out"]
    assert metadata["capabilities_summary"]["queryable"] is True


def test_get_catalog_metadata_normalizes_detail_response(legacyplate):
    metadata = legacyplate.get_catalog_metadata(catalog="legacyplate-image")
    capabilities = metadata["capabilities_summary"]

    assert capabilities == {
        "catname": "legacyplate-image",
        "queryable": True,
        "catalog_query_supported": True,
        "table_query_supported": True,
        "table_metadata_available": True,
        "conesearch_supported": True,
        "siap_supported": True,
        "ssap_supported": False,
        "docs_supported": True,
        "file_download_supported": True,
        "file_download_categories": ["fits", "out"],
        "query_status_code": "ok",
        "query_status_reason": "Catalog table metadata is configured and query endpoints are available.",
    }


def test_get_catalog_metadata_reports_non_queryable_catalog(legacyplate):
    metadata = legacyplate.get_catalog_metadata(catalog="legacyplate")
    capabilities = metadata["capabilities_summary"]

    assert capabilities["queryable"] is False
    assert capabilities["catalog_query_supported"] is False
    assert capabilities["table_query_supported"] is False
    assert capabilities["query_status_code"] == "no_tables"


def test_download_file_writes_to_requested_path(tmp_path, legacyplate):
    destination = tmp_path / "custom-plate.fits"

    saved = legacyplate.download_file(
        "plate-1",
        catalog="legacyplate-image",
        category="fits",
        out_path=destination,
    )

    assert saved == str(destination.resolve())
    assert destination.read_bytes() == b"plate-bytes"


def test_download_file_payload_marks_streaming(legacyplate):
    payload = legacyplate.download_file(
        "plate-1",
        catalog="legacyplate-image",
        category="fits",
        file_params={"category": "fits"},
        get_query_payload=True,
    )

    assert payload["url"].endswith("/query/openapi/catalogs/legacyplate-image/file")
    assert payload["params"]["id"] == "plate-1"
    assert payload["params"]["category"] == "fits"
    assert payload["stream"] is True


def test_download_file_payload_requires_explicit_file_params(legacyplate):
    with pytest.raises(InvalidQueryError, match="`file_params` is required"):
        legacyplate.download_file(
            "plate-1",
            catalog="legacyplate-image",
            category="fits",
            get_query_payload=True,
        )


def test_batch_download_writes_url_list(tmp_path, legacyplate):
    destination = tmp_path / "batch-links.txt"

    saved = legacyplate.batch_download(
        catalog="legacyplate-image",
        fmt="urllist",
        id_list=["1", "2"],
        categories=["fits"],
        out_path=destination,
    )

    assert saved == str(destination.resolve())
    assert "http://example.com/file1" in destination.read_text(encoding="utf-8")


def test_batch_download_without_categories_omits_filter(tmp_path, monkeypatch):
    client = LegacyplateClass(catalog="legacyplate", token=None)
    client.URL = "http://dummy.example/"
    destination = tmp_path / "batch-links.txt"

    def fake_request(request_type, url, **kwargs):
        if url.endswith("/query/openapi/catalogs/legacyplate-image"):
            return json_response(
                {
                    "catname": "legacyplate-image",
                    "file_download": {
                        "supported": True,
                        "single_file_endpoint": "/query/openapi/catalogs/legacyplate-image/file",
                        "batch_download_endpoint": "/query/openapi/catalogs/legacyplate-image/download",
                        "categories": ["fits", "out"],
                        "id_source": {
                            "column": "filename",
                            "result_field": "image_filename",
                            "parameter": "id",
                        },
                        "single_file_query_by_category": {
                            "fits": {"category": "fits"},
                            "out": {"category": "out"},
                        },
                    },
                },
                url=url,
            )
        if url.endswith("/query/openapi/catalogs/legacyplate-image/download"):
            assert "categories" not in kwargs["json"]
            return MockResponse(
                b"http://example.com/file1\n",
                url=url,
                headers={"Content-Disposition": 'attachment; filename="urls.txt"'},
                content_type="text/plain",
            )
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    monkeypatch.setattr(client, "_request", fake_request)

    saved = client.batch_download(
        catalog="legacyplate-image",
        fmt="urllist",
        id_list=["1"],
        out_path=destination,
    )

    assert saved == str(destination.resolve())


def test_batch_download_samba_returns_json(legacyplate):
    response = legacyplate.batch_download(
        catalog="legacyplate-image",
        fmt="samba",
        sqlid=7,
        categories=["out"],
    )

    assert response == {"status": "submitted", "target": "samba"}


def test_download_products_extracts_ids_from_query_table(tmp_path, legacyplate):
    products = Table({"image_filename": ["plate-a", "plate-b"], "ra": [10.0, 11.0]})
    destination = tmp_path / "products.txt"

    saved = legacyplate.download_products(
        products,
        catalog="legacyplate-image",
        fmt="urllist",
        categories=["fits"],
        out_path=destination,
    )

    assert saved == str(destination.resolve())
    assert "http://example.com/file1" in destination.read_text(encoding="utf-8")


def test_download_products_uses_metadata_result_field(tmp_path, monkeypatch):
    client = LegacyplateClass(catalog="legacyplate", token=None)
    client.URL = "http://dummy.example/"
    destination = tmp_path / "products.txt"

    def fake_request(request_type, url, **kwargs):
        if url.endswith("/query/openapi/catalogs/legacyplate-image"):
            return json_response(
                {
                    "catname": "legacyplate-image",
                    "file_download": {
                        "supported": True,
                        "single_file_endpoint": "/query/openapi/catalogs/legacyplate-image/file",
                        "batch_download_endpoint": "/query/openapi/catalogs/legacyplate-image/download",
                        "categories": ["fits", "out"],
                        "id_source": {
                            "column": "filename",
                            "result_field": "image_filename",
                            "parameter": "id",
                        },
                        "single_file_query_by_category": {
                            "fits": {"category": "fits"},
                            "out": {"category": "out"},
                        },
                    },
                },
                url=url,
            )
        if url.endswith("/query/openapi/catalogs/legacyplate-image/download"):
            assert kwargs["json"]["id_list"] == ["SH9701CL97006001"]
            return MockResponse(
                b"http://example.com/plate.fits\n",
                url=url,
                headers={"Content-Disposition": 'attachment; filename="urls.txt"'},
                content_type="text/plain",
            )
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    monkeypatch.setattr(client, "_request", fake_request)

    saved = client.download_products(
        Table({"image_filename": ["SH9701CL97006001"]}),
        catalog="legacyplate-image",
        fmt="urllist",
        categories=["fits"],
        out_path=destination,
    )

    assert saved == str(destination.resolve())


def test_download_products_allows_explicit_id_column(tmp_path, legacyplate):
    products = Table({"custom_file_id": ["plate-a"]})
    destination = tmp_path / "explicit-id-column.txt"

    saved = legacyplate.download_products(
        products,
        catalog="legacyplate-image",
        fmt="urllist",
        categories=["fits"],
        id_column="custom_file_id",
        out_path=destination,
    )

    assert saved == str(destination.resolve())
