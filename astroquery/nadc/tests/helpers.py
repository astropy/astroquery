# Licensed under a 3-clause BSD style license - see LICENSE.rst

from __future__ import annotations

import json
from pathlib import Path

from astroquery.utils.mocks import MockResponse


def assert_task_query_payload(payload, *, submit_url_suffix, result_format):
    assert payload["submit"]["url"].endswith(submit_url_suffix)
    assert payload["results"]["url"].endswith(
        f"/query/openapi/sqlid/<sqlid>/results.{result_format}"
    )


def assert_task_constraints(payload, expected):
    assert payload["submit"]["json"]["column_constraints"] == expected


def assert_task_columns(payload, expected):
    assert payload["submit"]["json"]["showcol"] == expected


def assert_task_cone(payload, *, radius_arcsec, nearest_only=False):
    cone = payload["submit"]["json"]["pos"]["cone"]
    assert payload["submit"]["json"]["pos"]["type"] == "cone"
    assert cone["radius"] == radius_arcsec
    assert cone["cone_nearestonly"] is nearest_only


def query_data_fixture_dir(module_name):
    return Path(__file__).parents[1] / module_name / "tests" / "data"


def query_data_manifest(module_name):
    return json.loads((query_data_fixture_dir(module_name) / "manifest.json").read_text())


def query_data_response(module_name, filename, *, url):
    data_dir = query_data_fixture_dir(module_name)
    manifest = query_data_manifest(module_name)
    metadata = manifest["files"][filename]
    return MockResponse(
        (data_dir / filename).read_bytes(),
        url=url,
        content_type=metadata["content_type"],
    )
