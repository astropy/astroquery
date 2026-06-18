# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.table import Table

from .. import conf
from ..core import LegacyplateClass


pytestmark = pytest.mark.remote_data


DEFAULT_IMAGE_CATALOG = "legacyplate-image"


def _is_private_server(url: str) -> bool:
    url = (url or "").lower()
    return any(
        host in url
        for host in (
            "http://10.",
            "http://192.168.",
            "http://172.16.",
            "http://172.17.",
            "http://172.18.",
            "http://172.19.",
            "http://172.2",
            "http://172.3",
        )
    )


def _as_text(value):
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    return str(value).strip()


def _skip_if_remote_unconfigured():
    client = LegacyplateClass(token=None)
    if _is_private_server(conf.server) and not client.token:
        pytest.skip(
            "Default `conf.server` points to a private network address and no token is configured; "
            "set `conf.server`/token to run this remote test."
        )
    return client


def test_list_catalogs_remote():
    client = _skip_if_remote_unconfigured()
    result = client.list_catalogs()
    if len(result) == 0:
        pytest.skip("No configured legacyplate catalogs were exposed by the remote service.")

    assert isinstance(result, Table)
    assert len(result.colnames) > 0
    if "catname" in result.colnames:
        assert all(_as_text(value).lower().startswith("legacyplate") for value in result["catname"])


def test_query_catalog_remote():
    client = _skip_if_remote_unconfigured()
    result = client.query_catalog(
        catalog=DEFAULT_IMAGE_CATALOG,
        showcol=["id", "filename", "ra", "dec"],
        max_rows=1,
        page_size=1,
        cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) <= 1
