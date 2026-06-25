# Licensed under a 3-clause BSD style license - see LICENSE.rst

import importlib

import pytest

from astropy.table import Table

from astroquery.nadc.tests.helpers import query_data_manifest, query_data_response


QUERY_DATA_CASES = [
    ("cstar", "CstarClass"),
    ("fashi", "FashiClass"),
    ("sage", "SageClass"),
    ("scuss", "ScussClass"),
    ("legacyplate", "LegacyplateClass"),
]


@pytest.mark.parametrize("module_name,class_name", QUERY_DATA_CASES)
def test_service_fixtures_drive_query_data_api(monkeypatch, module_name, class_name):
    manifest = query_data_manifest(module_name)
    catalog = manifest["representative_catalog"]
    table = manifest["representative_table"]
    submit_url = manifest["query_payload"]["submit"]["url"]
    expected_submit_json = manifest["query_payload"]["submit"]["json"]
    expected_results_params = manifest["query_payload"]["results"]["params"]
    table_query = f"/tables/{table}/query" in submit_url
    seen = set()

    def fixture(filename, url):
        seen.add(filename)
        return query_data_response(module_name, filename, url=url)

    def nonremote_request(self, request_type, url, **kwargs):
        if url.endswith("/query/openapi/get_catalogs"):
            return fixture("catalogs.json", url)
        if url.endswith(f"/query/openapi/catalogs/{catalog}"):
            return fixture("catalog_metadata.json", url)
        if url.endswith(f"/query/openapi/catalogs/{catalog}/tables"):
            return fixture("tables.json", url)
        if url.endswith(f"/query/openapi/catalogs/{catalog}/tables/{table}/columns"):
            return fixture("columns.json", url)
        if url.endswith(f"/query/openapi/catalogs/{catalog}/tables/{table}/query"):
            assert kwargs.get("json") == expected_submit_json
            return fixture("query_submit.json", url)
        if url.endswith(f"/query/openapi/catalogs/{catalog}/query"):
            assert kwargs.get("json") == expected_submit_json
            return fixture("query_submit.json", url)
        if "/query/openapi/sqlid/" in url and url.endswith("/results.json"):
            assert kwargs.get("params") == expected_results_params
            return fixture("query_results.json", url)
        raise AssertionError(f"Unhandled request: {request_type} {url} kwargs={kwargs}")

    core = importlib.import_module(f"astroquery.nadc.{module_name}.core")
    klass = getattr(core, class_name)
    monkeypatch.setattr(klass, "_request", nonremote_request)

    client = klass(catalog=catalog, token=None)
    client.URL = "http://dummy.example/"

    catalogs = client.list_catalogs()
    assert catalog in set(catalogs["catname"])

    metadata = client.get_catalog_metadata(catalog=catalog)
    assert metadata["catname"] == catalog
    assert metadata["capabilities_summary"]["queryable"] is True

    tables = client.list_tables(catalog=catalog)
    assert table in set(tables["tblname"])

    columns = client.list_columns(table, catalog=catalog)
    assert len(columns) > 0
    query_kwargs = {
        "catalog": catalog,
        "output_format": "json",
        "max_rows": 1,
        "page_size": 1,
    }
    if "showcol" in expected_submit_json:
        query_kwargs["showcol"] = expected_submit_json["showcol"]

    if table_query:
        payload = client.query_table(
            table=table,
            **query_kwargs,
            get_query_payload=True,
        )
        result = client.query_table(
            table=table,
            **query_kwargs,
        )
    else:
        payload = client.query_catalog(
            **query_kwargs,
            get_query_payload=True,
        )
        result = client.query_catalog(
            **query_kwargs,
        )

    submit_path = submit_url.removeprefix(manifest["server"].rstrip("/"))
    assert payload["submit"]["url"].endswith(submit_path)
    assert payload["submit"]["json"] == expected_submit_json
    assert payload["results"]["params"] == expected_results_params
    assert isinstance(result, Table)
    assert len(result) == 1
    assert seen == {
        "catalogs.json",
        "catalog_metadata.json",
        "tables.json",
        "columns.json",
        "query_submit.json",
        "query_results.json",
    }
