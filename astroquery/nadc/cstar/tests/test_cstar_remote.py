# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from .. import conf
from ..core import CstarClass


pytestmark = pytest.mark.remote_data


DEFAULT_RA_DEG = 19.07925000
DEFAULT_DEC_DEG = -87.35715556
DEFAULT_RADIUS_ARCSEC = 2.0


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


def _skip_if_remote_unconfigured():
    client = CstarClass(token=None)
    if _is_private_server(conf.server) and not client.token:
        pytest.skip(
            "Default `conf.server` points to a private network address and no token is configured; "
            "set `conf.server`/token to run this remote test."
        )
    return client


def test_list_catalogs_remote():
    client = _skip_if_remote_unconfigured()
    result = client.list_catalogs()

    assert isinstance(result, Table)
    assert len(result.colnames) > 0
    if "catname" in result.colnames and len(result) > 0:
        assert {str(value).strip().lower() for value in result["catname"]} <= {"cstar"}


def test_query_sources_remote():
    client = _skip_if_remote_unconfigured()
    result = client.query_sources(
        SkyCoord(DEFAULT_RA_DEG * u.deg, DEFAULT_DEC_DEG * u.deg, frame="icrs"),
        DEFAULT_RADIUS_ARCSEC * u.arcsec,
        output_format="json",
        max_rows=1,
        page_size=1,
        cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) <= 1
