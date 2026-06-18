# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json

from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u
import pytest
from astroquery.nadc import conf as nadc_conf
from astroquery.nadc.tests.helpers import (
    assert_task_columns,
    assert_task_cone,
    assert_task_constraints,
    assert_task_query_payload,
)
from astroquery.utils.mocks import MockResponse

from .. import conf
from ..core import SageClass, _configured_token_from_env


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
                "total": 4,
                "rows": [
                    {"catname": "cstar", "priority": 0},
                    {"catname": "SAGES-DR1", "priority": 1, "datatype": "catalog"},
                    {"catname": "SAGES-StellarParameters", "priority": 2, "datatype": "catalog"},
                    {"catname": "legacyplate", "priority": 3},
                ],
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/SAGES-DR1/tables"):
        return json_response(
            {"tables": [{"tblname": "catalog", "records": 100, "tbltype": "BASE TABLE"}]},
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/SAGES-StellarParameters/tables"):
        return json_response(
            {"tables": [{"tblname": "sages_param", "records": 50, "tbltype": "BASE TABLE"}]},
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/SAGES-DR1/tables/catalog/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "source_id", "datatype": "long", "description": "source id"},
                    {"colname": "ra", "datatype": "double", "description": "right ascension"},
                    {"colname": "dec", "datatype": "double", "description": "declination"},
                ],
            },
            url=url,
        )

    if url.endswith("/query/openapi/catalogs/SAGES-StellarParameters/tables/sages_param/columns"):
        return json_response(
            {
                "columns": [
                    {"colname": "source_id", "datatype": "long", "description": "source id"},
                    {"colname": "teff", "datatype": "float", "description": "effective temperature"},
                    {"colname": "logg", "datatype": "float", "description": "surface gravity"},
                ],
            },
            url=url,
        )

    raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")


@pytest.fixture
def sage(monkeypatch):
    monkeypatch.setattr(SageClass, "_request", nonremote_request)
    client = SageClass(catalog="SAGES-DR1", token=None)
    client.URL = "http://dummy.example/"
    return client


def test_default_catalog_and_supported_catalogs(sage):
    assert sage.catalog == "SAGES-DR1"
    assert sage._supported_catalogs() == ["SAGES-DR1", "SAGES-StellarParameters"]


def test_list_catalogs_filters_supported_catalogs(sage):
    table = sage.list_catalogs()
    assert isinstance(table, Table)
    assert list(table["catname"]) == ["SAGES-DR1", "SAGES-StellarParameters"]


def test_supported_catalogs_can_be_configured(monkeypatch):
    monkeypatch.setattr(SageClass, "_request", nonremote_request)
    with conf.set_temp("supported_catalogs", "SAGES-StellarParameters"):
        client = SageClass(catalog="SAGES-DR1", token=None)
        client.URL = "http://dummy.example/"
        table = client.list_catalogs()

    assert list(table["catname"]) == ["SAGES-StellarParameters"]


def test_list_columns_auto_detects_single_table(sage):
    columns = sage.list_columns(catalog="SAGES-StellarParameters")

    assert isinstance(columns, Table)
    assert list(columns["colname"]) == ["source_id", "teff", "logg"]


def test_init_reads_shared_token_from_environment(monkeypatch):
    for env_name in (
        "ASTROQUERY_SAGE_TOKEN",
        "ASTROQUERY_NADC_SAGE_TOKEN",
        "NADC_SAGE_TOKEN",
        "CHINAVO_SAGE_TOKEN",
        "ASTROQUERY_SAGE_ACCESS_TOKEN",
        "ASTROQUERY_NADC_SAGE_ACCESS_TOKEN",
        "NADC_SAGE_ACCESS_TOKEN",
        "CHINAVO_SAGE_ACCESS_TOKEN",
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

        client = SageClass(catalog="SAGES-DR1", token=None)
        assert client.token == "shared-secret"


def test_module_specific_token_precedes_shared_token(monkeypatch):
    for env_name in (
        "ASTROQUERY_SAGE_TOKEN",
        "ASTROQUERY_NADC_SAGE_TOKEN",
        "NADC_SAGE_TOKEN",
        "CHINAVO_SAGE_TOKEN",
        "ASTROQUERY_SAGE_ACCESS_TOKEN",
        "ASTROQUERY_NADC_SAGE_ACCESS_TOKEN",
        "NADC_SAGE_ACCESS_TOKEN",
        "CHINAVO_SAGE_ACCESS_TOKEN",
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
        monkeypatch.setenv("ASTROQUERY_SAGE_TOKEN", "module-secret")

        assert _configured_token_from_env() == "module-secret"

        client = SageClass(catalog="SAGES-DR1", token=None)
        assert client.token == "module-secret"


def test_query_uv_sources_builds_photometry_payload(sage):
    center = SkyCoord(ra=180 * u.deg, dec=30 * u.deg)
    payload = sage.query_uv_sources(
        center,
        2 * u.arcsec,
        mag_u_range=(14, 21),
        err_u_max=0.1,
        flag_u=0,
        columns=["sage_id", "ra", "dec", "mag_u", "err_u"],
        nearest_only=True,
        output_format="json",
        max_rows=15,
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/SAGES-DR1/tables/dr1_uv/query",
        result_format="json",
    )
    assert_task_cone(payload, radius_arcsec=2.0, nearest_only=True)
    assert_task_columns(payload, ["sage_id", "ra", "dec", "mag_u", "err_u"])
    assert_task_constraints(
        payload,
        [
            {"column_name": "mag_u", "operation": "between", "min": 14, "max": 21},
            {"column_name": "err_u", "operation": "lessequal", "constraint": "0.1"},
            {"column_name": "flag_u", "operation": "equal", "constraint": "0"},
        ],
    )


def test_query_gri_sources_builds_photometry_payload(sage):
    payload = sage.query_gri_sources(
        mag_g_range=(14, 21),
        err_g_max=0.1,
        flag_g=0,
        columns=["sage_id", "mag_g", "err_g"],
        output_format="json",
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/SAGES-DR1/tables/dr1s_gri/query",
        result_format="json",
    )
    assert_task_columns(payload, ["sage_id", "mag_g", "err_g"])
    assert_task_constraints(
        payload,
        [
            {"column_name": "mag_g", "operation": "between", "min": 14, "max": 21},
            {"column_name": "err_g", "operation": "lessequal", "constraint": "0.1"},
            {"column_name": "flag_g", "operation": "equal", "constraint": "0"},
        ],
    )


def test_query_stellar_parameters_builds_quality_payload(sage):
    payload = sage.query_stellar_parameters(
        teff_range=(4500, 6500),
        feh_range=(-1.0, 0.5),
        err_teff_max=150,
        err_feh_max=0.2,
        ruwe_max=1.4,
        columns=["sourceid", "teff", "feh", "ruwe"],
        output_format="json",
        get_query_payload=True,
    )

    assert_task_query_payload(
        payload,
        submit_url_suffix="/query/openapi/catalogs/SAGES-StellarParameters/tables/sages_param/query",
        result_format="json",
    )
    assert_task_columns(payload, ["sourceid", "teff", "feh", "ruwe"])
    assert_task_constraints(
        payload,
        [
            {"column_name": "teff", "operation": "between", "min": 4500, "max": 6500},
            {"column_name": "feh", "operation": "between", "min": -1.0, "max": 0.5},
            {"column_name": "err_teff", "operation": "lessequal", "constraint": "150"},
            {"column_name": "err_feh", "operation": "lessequal", "constraint": "0.2"},
            {"column_name": "ruwe", "operation": "lessequal", "constraint": "1.4"},
        ],
    )
