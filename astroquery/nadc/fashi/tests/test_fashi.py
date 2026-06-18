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
from ..core import FashiClass, _configured_token_from_env


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
                "total": 6,
                "rows": [
                    {"catname": "cstar", "priority": 0},
                    {"catname": "FASHI", "priority": 1, "showname_en": "FASHI"},
                    {"catname": "alfalfa_crossmatch", "parent_catname": "FASHI", "priority": 2},
                    {"catname": "optical_counterparts_sdss_phot", "parent_catname": "FASHI", "priority": 3},
                    {"catname": "optical_counterparts_sdss_spec", "parent_catname": "FASHI", "priority": 4},
                    {"catname": "optical_counterparts_sga", "parent_catname": "FASHI", "priority": 5},
                ],
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/FASHI/tables"):
        return json_response(
            {
                "tables": [
                    {"tblname": "extragalactic_hi_source_catalog", "records": 41741},
                ]
            },
            url=url,
        )

    for catalog_name, table_name, records in [
        ("alfalfa_crossmatch", "alfalfa_crossmatch", 3620),
        ("optical_counterparts_sdss_phot", "optical_counterparts_sdss_phot", 10975),
        ("optical_counterparts_sdss_spec", "optical_counterparts_sdss_spec", 2900),
        ("optical_counterparts_sga", "optical_counterparts_sga", 14072),
    ]:
        if url.endswith(f"/query/openapi/catalogs/{catalog_name}/tables"):
            return json_response(
                {"tables": [{"tblname": table_name, "records": records}]},
                url=url,
            )

    if url.endswith("/query/openapi/catalogs/FASHI/table_links"):
        return json_response(
            {
                "is_single_table": True,
                "links": [
                    {
                        "tblname": "extragalactic_hi_source_catalog",
                        "is_main_table": True,
                        "join_mode": "main",
                    },
                ],
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/FASHI/tables/extragalactic_hi_source_catalog/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "id_fashi", "datatype": "int"},
                    {"colname": "ra", "datatype": "double"},
                    {"colname": "dec", "datatype": "double"},
                    {"colname": "cz", "datatype": "double"},
                    {"colname": "snr", "datatype": "double"},
                ]
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/alfalfa_crossmatch/tables/alfalfa_crossmatch/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "id_fashi", "datatype": "int"},
                    {"colname": "agcnr_alfalfa", "datatype": "int"},
                    {"colname": "ra_alfalfa", "datatype": "double"},
                ]
            },
            url=url,
        )

    raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")


@pytest.fixture
def fashi(monkeypatch):
    monkeypatch.setattr(FashiClass, "_request", nonremote_request)
    client = FashiClass(catalog="FASHI", token=None)
    client.URL = "http://dummy.example/"
    return client


def _clear_token_env(monkeypatch):
    for env_name in (
        "ASTROQUERY_FASHI_TOKEN",
        "ASTROQUERY_NADC_FASHI_TOKEN",
        "NADC_FASHI_TOKEN",
        "CHINAVO_FASHI_TOKEN",
        "ASTROQUERY_FASHI_ACCESS_TOKEN",
        "ASTROQUERY_NADC_FASHI_ACCESS_TOKEN",
        "NADC_FASHI_ACCESS_TOKEN",
        "CHINAVO_FASHI_ACCESS_TOKEN",
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


def test_default_catalog_and_supported_catalogs(fashi):
    assert fashi.catalog == "FASHI"
    assert fashi._supported_catalogs() == [
        "FASHI",
        "alfalfa_crossmatch",
        "optical_counterparts_sdss_phot",
        "optical_counterparts_sdss_spec",
        "optical_counterparts_sga",
    ]


def test_list_catalogs_filters_fashi(fashi):
    table = fashi.list_catalogs()

    assert isinstance(table, Table)
    assert list(table["catname"]) == [
        "FASHI",
        "alfalfa_crossmatch",
        "optical_counterparts_sdss_phot",
        "optical_counterparts_sdss_spec",
        "optical_counterparts_sga",
    ]


def test_list_tables_returns_parent_fashi_table(fashi):
    table = fashi.list_tables(catalog="FASHI")

    assert list(table["tblname"]) == ["extragalactic_hi_source_catalog"]


def test_list_tables_returns_child_catalog_table(fashi):
    table = fashi.list_tables(catalog="alfalfa_crossmatch")

    assert list(table["tblname"]) == ["alfalfa_crossmatch"]


def test_list_table_links_exposes_main_table(fashi):
    links = fashi.list_table_links(catalog="FASHI")

    assert links.meta["is_single_table"] is True
    assert list(links["join_mode"]) == ["main"]


def test_list_columns_requires_explicit_table_for_fashi(fashi):
    columns = fashi.list_columns("extragalactic_hi_source_catalog", catalog="FASHI")

    assert list(columns["colname"])[:3] == ["id_fashi", "ra", "dec"]


def test_init_reads_shared_token_from_environment(monkeypatch):
    _clear_token_env(monkeypatch)

    with conf.set_temp("token", ""), nadc_conf.set_temp("token", ""):
        monkeypatch.setenv("ASTROQUERY_CHINAVO_TOKEN", "shared-secret")
        assert _configured_token_from_env() == "shared-secret"

        client = FashiClass(catalog="FASHI", token=None)
        assert client.token == "shared-secret"


def test_module_specific_token_precedes_shared_token(monkeypatch):
    _clear_token_env(monkeypatch)

    with conf.set_temp("token", ""), nadc_conf.set_temp("token", ""):
        monkeypatch.setenv("ASTROQUERY_CHINAVO_TOKEN", "shared-secret")
        monkeypatch.setenv("ASTROQUERY_FASHI_TOKEN", "module-secret")

        assert _configured_token_from_env() == "module-secret"

        client = FashiClass(catalog="FASHI", token=None)
        assert client.token == "module-secret"


def test_query_hi_sources_builds_science_payload(fashi):
    center = SkyCoord(125 * u.deg, -6 * u.deg)

    payload = fashi.query_hi_sources(
        center,
        5 * u.arcmin,
        cz_range=(1000, 8000),
        snr_min=8,
        log10mass_range=(8.5, 10.5),
        columns=["id_fashi", "ra", "dec", "cz", "snr"],
        output_format="json",
        max_rows=20,
        page_size=5,
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/FASHI/tables/extragalactic_hi_source_catalog/query"
    )
    assert payload["results"]["url"].endswith("/query/openapi/sqlid/<sqlid>/results.json")
    assert payload["submit"]["json"]["pos_group"] == "ra,dec"
    assert payload["submit"]["json"]["showcol"] == ["id_fashi", "ra", "dec", "cz", "snr"]
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "cz", "operation": "between", "min": 1000, "max": 8000},
        {"column_name": "snr", "operation": "greaterequal", "constraint": "8"},
        {"column_name": "log10mass", "operation": "between", "min": 8.5, "max": 10.5},
    ]


def test_query_alfalfa_matches_uses_fashi_coordinates_by_default(fashi):
    payload = fashi.query_alfalfa_matches(
        SkyCoord(125 * u.deg, -6 * u.deg),
        5 * u.arcmin,
        agcnr_alfalfa=5951,
        cz_fashi_range=(1000, 9000),
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/alfalfa_crossmatch/tables/alfalfa_crossmatch/query"
    )
    assert payload["submit"]["json"]["pos_group"] == "ra_fashi,dec_fashi"
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "agcnr_alfalfa", "operation": "equal", "constraint": "5951"},
        {"column_name": "cz_fashi", "operation": "between", "min": 1000, "max": 9000},
    ]


def test_query_alfalfa_matches_allows_external_coordinate_group(fashi):
    payload = fashi.query_alfalfa_matches(
        SkyCoord(125 * u.deg, -6 * u.deg),
        5 * u.arcmin,
        pos_group="ra_alfalfa,dec_alfalfa",
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["json"]["pos_group"] == "ra_alfalfa,dec_alfalfa"


def test_query_table_supports_child_catalog(fashi):
    payload = fashi.query_table(
        catalog="alfalfa_crossmatch",
        table="alfalfa_crossmatch",
        showcol=["id_fashi", "agcnr_alfalfa"],
        max_rows=5,
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/alfalfa_crossmatch/tables/alfalfa_crossmatch/query"
    )
    assert payload["submit"]["json"]["showcol"] == ["id_fashi", "agcnr_alfalfa"]


def test_query_sdss_phot_counterparts_builds_payload_without_spatial_group(fashi):
    payload = fashi.query_sdss_phot_counterparts(
        probability_min=0.8,
        objid_sdss=123,
        columns=["id_fashi", "objid_sdss", "probability_sdss"],
        output_format="json",
        get_query_payload=True,
        cache=False,
    )

    submit_json = payload["submit"]["json"]
    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/optical_counterparts_sdss_phot/tables/optical_counterparts_sdss_phot/query"
    )
    assert "pos_group" not in submit_json
    assert submit_json["column_constraints"] == [
        {"column_name": "objid_sdss", "operation": "equal", "constraint": "123"},
        {"column_name": "probability_sdss", "operation": "greaterequal", "constraint": "0.8"},
    ]


def test_query_sdss_spec_counterparts_builds_payload(fashi):
    payload = fashi.query_sdss_spec_counterparts(
        z_fashi_range=(0.01, 0.05),
        z_sdss_range=(0.01, 0.05),
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/optical_counterparts_sdss_spec/tables/optical_counterparts_sdss_spec/query"
    )
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "z_fashi", "operation": "between", "min": 0.01, "max": 0.05},
        {"column_name": "z_sdss", "operation": "between", "min": 0.01, "max": 0.05},
    ]


def test_query_sga_counterparts_builds_payload(fashi):
    payload = fashi.query_sga_counterparts(
        name_sga="PGC1035830",
        z_sga_range=(0.01, 0.04),
        get_query_payload=True,
        cache=False,
    )

    assert payload["submit"]["url"].endswith(
        "/query/openapi/catalogs/optical_counterparts_sga/tables/optical_counterparts_sga/query"
    )
    assert payload["submit"]["json"]["column_constraints"] == [
        {"column_name": "name_sga", "operation": "equal", "constraint": "PGC1035830"},
        {"column_name": "z_sga", "operation": "between", "min": 0.01, "max": 0.04},
    ]


def test_science_query_rejects_bad_range(fashi):
    with pytest.raises(InvalidQueryError, match="cz range"):
        fashi.query_hi_sources(cz_range=(1000,), get_query_payload=True)
