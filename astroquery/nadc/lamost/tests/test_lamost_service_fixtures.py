# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from pathlib import Path

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
import pytest

from ..core import LamostClass
from .helpers import create_mock_response


DATA_DIR = Path(__file__).parent / "data"


def service_response(filename):
    manifest = json.loads((DATA_DIR / "manifest.json").read_text())
    metadata = manifest["files"][filename]
    return create_mock_response(
        content=(DATA_DIR / filename).read_bytes(),
        status_code=metadata["status_code"],
        content_type=metadata["content_type"],
    )


@pytest.fixture
def lamost_service(monkeypatch):
    seen = set()

    def fixture(filename):
        seen.add(filename)
        return service_response(filename)

    def nonremote_request(self, request_type, url, params=None, json=None, **kwargs):
        if url.endswith("/openapi/dr_versions"):
            return fixture("dr_versions_response.json")
        if url.endswith("/lrs/voservice/conesearch"):
            return fixture("conesearch_response.xml")
        if url.endswith("/lrs/voservice/ssap"):
            return fixture("ssap_response.xml")
        if url.endswith("/sql"):
            output_format = params["output.fmt"]
            suffix = "xml" if output_format == "votable" else output_format
            return fixture(f"sql_response_{output_format}.{suffix}")
        if url.endswith("/query/combined"):
            return fixture("catalog_query_response.json")
        if url.endswith("/lrs/spectrum/info"):
            return fixture("metadata_response.json")
        if url.endswith("/tables"):
            return fixture("tables_metadata_response.json")
        if url.endswith("/voservice/tap_url"):
            return fixture("tap_url_response.json")
        if url.endswith("/lrs/footprint"):
            return fixture("footprint_image.png")
        if url.endswith("/get_unique_id_and_related_obsids"):
            return fixture("unique_id_response.json")
        if url.endswith("/get_query_result_count"):
            return fixture("query_result_count.json")
        if url.endswith("/get_query_result"):
            return fixture(f"query_result_page{params['page']}.json")
        raise AssertionError(f"Unhandled request: {request_type} {url} params={params} json={json}")

    monkeypatch.setattr(LamostClass, "_request", nonremote_request)
    return LamostClass(), seen


def test_service_fixtures_drive_lamost_discovery_api(lamost_service):
    lamost, seen = lamost_service

    assert lamost.get_dr_versions()
    assert len(lamost.get_metadata("686112127")) == 1
    assert "combined" in lamost.get_tables_metadata()["tables"]
    assert lamost.get_tap_url()["url"].endswith("/voservice/tap")
    assert lamost.get_footprint().startswith(b"\x89PNG\r\n\x1a\n")
    assert lamost.get_unique_id_and_related_obsids(obsid="686112127")["unique_id"]

    assert seen == {
        "dr_versions_response.json",
        "footprint_image.png",
        "metadata_response.json",
        "tables_metadata_response.json",
        "tap_url_response.json",
        "unique_id_response.json",
    }


def test_service_fixtures_drive_lamost_table_apis(lamost_service):
    lamost, seen = lamost_service

    assert isinstance(
        lamost.query_region(SkyCoord(10.0004738, 40.9952444, unit="deg"), 0.2 * u.deg),
        Table,
    )
    assert isinstance(lamost.query_ssap(SkyCoord(10.0, 40.0, unit="deg"), 0.2 * u.deg), Table)

    assert len(lamost.query_sql("SELECT * FROM combined LIMIT 3", output_format="json")) == 3
    assert len(lamost.query_sql("SELECT * FROM combined LIMIT 3", output_format="csv")) == 3
    assert len(lamost.query_sql("SELECT * FROM combined LIMIT 3", output_format="votable")) == 3

    assert len(lamost.query_catalog("combined", columns=["obsid", "ra", "dec"], max_rows=3)) == 3

    assert seen == {
        "catalog_query_response.json",
        "conesearch_response.xml",
        "sql_response_csv.csv",
        "sql_response_json.json",
        "sql_response_votable.xml",
        "ssap_response.xml",
    }


def test_service_fixtures_drive_lamost_query_result_pages(lamost_service):
    lamost, seen = lamost_service

    assert lamost.get_query_result_count(12345) == 10

    rows = lamost.get_query_result(12345, page_size=5)
    assert len(rows) == 10
    assert rows[0]["obsid"] == "10001"
    assert rows[-1]["obsid"] == "10010"

    assert seen == {
        "query_result_count.json",
        "query_result_page1.json",
        "query_result_page2.json",
    }
