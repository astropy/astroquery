import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from .. import GaiaClass


@pytest.mark.remote_data
def test_query_object_row_limit():
    Gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    width = u.Quantity(0.1, u.deg)
    height = u.Quantity(0.1, u.deg)
    r = Gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == Gaia.ROW_LIMIT

    Gaia.ROW_LIMIT = 10
    r = Gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == 10 == Gaia.ROW_LIMIT

    Gaia.ROW_LIMIT = -1
    r = Gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == 176


@pytest.mark.remote_data
def test_cone_search_row_limit():
    Gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    radius = u.Quantity(0.1, u.deg)
    j = Gaia.cone_search_async(coord, radius)
    r = j.get_results()

    assert len(r) == Gaia.ROW_LIMIT

    Gaia.ROW_LIMIT = 10
    j = Gaia.cone_search_async(coord, radius)
    r = j.get_results()

    assert len(r) == 10 == Gaia.ROW_LIMIT

    Gaia.ROW_LIMIT = -1
    j = Gaia.cone_search_async(coord, radius)
    r = j.get_results()

    assert len(r) == 1188
