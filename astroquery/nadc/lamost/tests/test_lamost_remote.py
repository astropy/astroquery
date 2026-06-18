# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from ..core import Lamost


pytestmark = pytest.mark.remote_data


def test_query_region_remote():
    coord = SkyCoord(10.0004738, 40.9952444, unit="deg", frame="icrs")
    result = Lamost.query_region(coord, radius=0.2 * u.deg, resolution="low")

    assert isinstance(result, Table)
    assert len(result.colnames) > 0


def test_query_sql_remote():
    result = Lamost.query_sql("SELECT * FROM combined LIMIT 1")

    assert isinstance(result, Table)
    assert len(result) <= 1


def test_query_ssap_remote():
    coord = SkyCoord(10.0, 40.0, unit="deg", frame="icrs")
    result = Lamost.query_ssap(coord, radius=0.2 * u.deg, resolution="low")

    assert isinstance(result, Table)
    assert len(result.colnames) > 0


def test_query_catalog_remote():
    result = Lamost.query_catalog(
        "combined",
        columns=["obsid", "ra", "dec"],
        max_rows=1,
    )

    assert isinstance(result, Table)
    assert len(result) <= 1


def test_get_dr_versions_remote():
    result = Lamost.get_dr_versions()

    assert isinstance(result, list)
    assert len(result) > 0
    assert {"dr_version", "sub_version", "public_status"}.issubset(result[0])
