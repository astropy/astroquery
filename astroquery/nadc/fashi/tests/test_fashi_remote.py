# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.table import Table

from .. import conf
from ..core import FashiClass


pytestmark = pytest.mark.remote_data


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
    client = FashiClass(token=None)
    if _is_private_server(conf.server) and not client.token:
        pytest.skip(
            "Default `conf.server` points to a private network address and no token is configured; "
            "set `conf.server`/token to run this remote test."
        )
    return client


def test_list_catalogs_remote():
    client = _skip_if_remote_unconfigured()
    result = client.list_catalogs(cache=False)

    assert isinstance(result, Table)
    assert "catname" in result.colnames
    if len(result) > 0:
        assert "FASHI" in {_as_text(value) for value in result["catname"]}


def test_query_hi_sources_remote():
    client = _skip_if_remote_unconfigured()
    result = client.query_hi_sources(
        output_format="json",
        max_rows=1,
        page_size=1,
        cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) <= 1
