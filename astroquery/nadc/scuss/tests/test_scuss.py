# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json

from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u
import pytest

from astroquery.exceptions import InvalidQueryError
from astroquery.nadc import conf as nadc_conf
from astroquery.utils.mocks import MockResponse

from .. import conf
from ..core import ScussClass, _configured_token_from_env


def json_response(data, *, url="http://dummy.example/query/openapi/json"):
    return MockResponse(
        json.dumps(data).encode("utf-8"),
        url=url,
        content_type="application/json",
    )


def nonremote_request(self, request_type, url, **kwargs):
    if url.endswith("/query/openapi/get_catalogs"):
        return json_response(
            {
                "total": 5,
                "rows": [
                    {"catname": "cstar", "priority": 0},
                    {"catname": "scuss", "priority": 1, "datatype": "catalog,image"},
                    {"catname": "scuss-cat", "priority": 2, "datatype": "catalog"},
                    {"catname": "scuss-image", "priority": 3, "datatype": "catalog,image"},
                    {"catname": "scuss-proper-motion", "priority": 4, "datatype": "catalog"},
                ],
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-image"):
        return json_response(
            {
                "catname": "scuss-image",
                "file_download": {
                    "supported": True,
                    "single_file_endpoint": "/query/openapi/catalogs/scuss-image/file",
                    "batch_download_endpoint": "/query/openapi/catalogs/scuss-image/download",
                    "categories": ["png", "fits"],
                    "single_file_query_by_category": {
                        "png": {"path": "png", "ext": "png"},
                        "fits": {"path": "fits", "ext": "fits"},
                    },
                },
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-image/file"):
        params = kwargs.get("params") or {}
        if params.get("path") != "png" or params.get("ext") != "png":
            raise AssertionError(f"Unexpected SCUSS file params: {params}")
        return MockResponse(
            b"png-bytes",
            url=url,
            headers={"Content-Disposition": 'attachment; filename="scuss.png"'},
            content_type="image/png",
        )

    if url.endswith("/query/openapi/catalogs/scuss/tables"):
        return json_response(
            {
                "tables": [
                    {"tblname": "catalogue", "records": 100, "tbltype": "BASE TABLE"},
                    {"tblname": "sdss10", "records": 50, "tbltype": "BASE TABLE"},
                ]
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-cat/tables"):
        return json_response({"tables": []}, url=url)

    if url.endswith("/query/openapi/catalogs/scuss-image/tables"):
        return json_response(
            {"tables": [{"tblname": "image", "records": 20, "tbltype": "BASE TABLE"}]},
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-proper-motion/tables"):
        return json_response(
            {"tables": [{"tblname": "proper_motion", "records": 20, "tbltype": "BASE TABLE"}]},
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss/tables/catalogue/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "id", "datatype": "long", "description": "row id"},
                    {"colname": "ra", "datatype": "double", "description": "right ascension"},
                    {"colname": "dec", "datatype": "double", "description": "declination"},
                ]
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss/tables/sdss10/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "sdssobjid", "datatype": "long", "description": "SDSS object id"},
                    {"colname": "psfmag_u", "datatype": "float", "description": "u-band psf magnitude"},
                ]
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-image/tables/image/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "id", "datatype": "long", "description": "row id"},
                    {"colname": "filename", "datatype": "char", "description": "image filename"},
                    {"colname": "cra", "datatype": "double", "description": "center ra"},
                ]
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/scuss-proper-motion/tables/proper_motion/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "id", "datatype": "long", "description": "row id"},
                    {"colname": "pmra", "datatype": "float", "description": "proper motion ra"},
                    {"colname": "pmdec", "datatype": "float", "description": "proper motion dec"},
                ]
            },
            url=url,
        )

    raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")


@pytest.fixture
def scuss(monkeypatch):
    monkeypatch.setattr(ScussClass, "_request", nonremote_request)
    client = ScussClass(catalog="scuss", token=None)
    client.URL = "http://dummy.example/"
    return client


def test_default_catalog_and_supported_catalogs(scuss):
    assert scuss.catalog == "scuss"
    assert scuss._supported_catalogs() == ["scuss", "scuss-cat", "scuss-image", "scuss-proper-motion"]


def test_list_catalogs_filters_supported_catalogs(scuss):
    table = scuss.list_catalogs()
    assert isinstance(table, Table)
    assert list(table["catname"]) == ["scuss", "scuss-cat", "scuss-image", "scuss-proper-motion"]


def test_supported_catalogs_can_be_configured(monkeypatch):
    monkeypatch.setattr(ScussClass, "_request", nonremote_request)
    with conf.set_temp("supported_catalogs", "scuss-image,scuss-proper-motion"):
        client = ScussClass(catalog="scuss", token=None)
        client.URL = "http://dummy.example/"
        table = client.list_catalogs()

    assert list(table["catname"]) == ["scuss-image", "scuss-proper-motion"]


def test_list_tables_returns_multi_table_root_catalog(scuss):
    tables = scuss.list_tables(catalog="scuss")

    assert isinstance(tables, Table)
    assert list(tables["tblname"]) == ["catalogue", "sdss10"]


def test_list_columns_auto_detects_single_table(scuss):
    columns = scuss.list_columns(catalog="scuss-image")

    assert isinstance(columns, Table)
    assert list(columns["colname"]) == ["id", "filename", "cra"]


def test_get_catalog_metadata_returns_file_download_mapping(scuss):
    metadata = scuss.get_catalog_metadata(catalog="scuss-image")

    assert metadata["catname"] == "scuss-image"
    assert metadata["capabilities_summary"]["file_download_supported"] is True
    assert metadata["file_download"]["single_file_query_by_category"]["png"] == {
        "path": "png",
        "ext": "png",
    }


def test_download_file_uses_metadata_query_params(tmp_path, scuss):
    destination = tmp_path / "scuss.png"

    saved = scuss.download_file(
        "1",
        catalog="scuss-image",
        category="png",
        out_path=destination,
    )

    assert saved == str(destination.resolve())
    assert destination.read_bytes() == b"png-bytes"


def test_list_tables_allows_no_table_catalog(scuss):
    tables = scuss.list_tables(catalog="scuss-cat")

    assert isinstance(tables, Table)
    assert len(tables) == 0


def test_init_reads_shared_token_from_environment(monkeypatch):
    for env_name in (
        "ASTROQUERY_SCUSS_TOKEN",
        "ASTROQUERY_NADC_SCUSS_TOKEN",
        "NADC_SCUSS_TOKEN",
        "CHINAVO_SCUSS_TOKEN",
        "ASTROQUERY_SCUSS_ACCESS_TOKEN",
        "ASTROQUERY_NADC_SCUSS_ACCESS_TOKEN",
        "NADC_SCUSS_ACCESS_TOKEN",
        "CHINAVO_SCUSS_ACCESS_TOKEN",
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
        monkeypatch.setenv("ASTROQUERY_CHINAVO_TOKEN", "shared-secret")
        assert _configured_token_from_env() == "shared-secret"

        client = ScussClass(catalog="scuss", token=None)
        assert client.token == "shared-secret"


def test_module_specific_token_precedes_shared_token(monkeypatch):
    for env_name in (
        "ASTROQUERY_SCUSS_TOKEN",
        "ASTROQUERY_NADC_SCUSS_TOKEN",
        "NADC_SCUSS_TOKEN",
        "CHINAVO_SCUSS_TOKEN",
        "ASTROQUERY_SCUSS_ACCESS_TOKEN",
        "ASTROQUERY_NADC_SCUSS_ACCESS_TOKEN",
        "NADC_SCUSS_ACCESS_TOKEN",
        "CHINAVO_SCUSS_ACCESS_TOKEN",
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
        monkeypatch.setenv("ASTROQUERY_CHINAVO_TOKEN", "shared-secret")
        monkeypatch.setenv("ASTROQUERY_SCUSS_TOKEN", "module-secret")

        assert _configured_token_from_env() == "module-secret"

        client = ScussClass(catalog="scuss", token=None)
        assert client.token == "module-secret"


def test_query_sources_builds_science_payload(scuss):
    center = SkyCoord(180 * u.deg, 30 * u.deg)

    payload = scuss.query_sources(
        center,
        5 * u.arcmin,
        mag_range=(14, 22),
        magerr_max=0.1,
        columns=["id", "psfmag"],
        nearest_only=True,
        output_format="json",
        max_rows=20,
        page_size=5,
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/scuss/tables/catalogue/query")
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.json")
    assert payload["max_rows"] == 20
    assert payload["page_size"] == 5

    submit_json = payload["submit"]["json"]
    assert submit_json["showcol"] == ["id", "psfmag"]
    assert submit_json["pos"]["type"] == "cone"
    assert submit_json["pos"]["cone"]["radius"] == 300.0
    assert submit_json["pos"]["cone"]["cone_nearestonly"] is True
    assert submit_json["column_constraints"] == [
        {"column_name": "psfmag", "operation": "between", "min": 14, "max": 22},
        {"column_name": "psferr", "operation": "lessequal", "constraint": "0.1"},
    ]


def test_query_images_builds_science_payload_with_json_default(scuss):
    payload = scuss.query_images(
        seeing_max=2.0,
        columns=["filename", "seeing"],
        max_rows=3,
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/scuss-image/tables/image/query")
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.json")
    assert payload["submit"]["json"]["showcol"] == ["filename", "seeing"]
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "seeing", "operation": "lessequal", "constraint": "2.0"},
    ]


def test_query_proper_motions_builds_science_payload(scuss):
    payload = scuss.query_proper_motions(
        pmra_range=(-50, 50),
        pmdec_range=(-25, 25),
        mag_range=(14, 20),
        obsused_min=3,
        columns=["id", "pmra", "pmdec"],
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/scuss-proper-motion/tables/proper_motion/query"
    )
    assert payload["submit"]["json"]["showcol"] == ["id", "pmra", "pmdec"]
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "pmra", "operation": "between", "min": -50, "max": 50},
        {"column_name": "pmdec", "operation": "between", "min": -25, "max": 25},
        {"column_name": "mag", "operation": "between", "min": 14, "max": 20},
        {"column_name": "obsused", "operation": "greaterequal", "constraint": "3"},
    ]


def test_query_sdss_matches_builds_science_payload(scuss):
    payload = scuss.query_sdss_matches(
        match_error_max=1.5,
        columns=["sdssobjid", "match_err"],
        output_format="json",
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith("/query/openapi/catalogs/scuss/tables/sdss10/query")
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.json")
    assert payload["submit"]["json"]["showcol"] == ["sdssobjid", "match_err"]
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "match_err", "operation": "lessequal", "constraint": "1.5"},
    ]


def test_science_query_rejects_bad_range(scuss):
    with pytest.raises(InvalidQueryError, match="psfmag range"):
        scuss.query_sources(mag_range=(14,), get_query_payload=True)
