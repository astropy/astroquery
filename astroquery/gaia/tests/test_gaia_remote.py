import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from .. import GaiaClass
from ...utils.tap.model.filter import Filter


@pytest.mark.remote_data
def test_query_object_columns_with_radius():
    # Regression test: `columns` were ignored if `radius` was provided [#2025]
    gaia = GaiaClass()
    sc = SkyCoord(ra=0 * u.deg, dec=0 * u.deg)
    table = gaia.query_object_async(sc, radius=10 * u.arcsec, columns=['ra'])
    assert table.colnames == ['ra', 'dist']


@pytest.mark.remote_data
def test_query_object_row_limit():
    gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    width = u.Quantity(0.1, u.deg)
    height = u.Quantity(0.1, u.deg)
    r = gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == gaia.ROW_LIMIT

    gaia.ROW_LIMIT = 10
    r = gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == 10 == gaia.ROW_LIMIT

    gaia.ROW_LIMIT = -1
    r = gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == 184


@pytest.mark.remote_data
def test_cone_search_row_limit():
    gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    radius = u.Quantity(0.1, u.deg)
    j = gaia.cone_search_async(coord, radius=radius)
    r = j.get_results()

    assert len(r) == gaia.ROW_LIMIT

    gaia.ROW_LIMIT = 10
    j = gaia.cone_search_async(coord, radius=radius)
    r = j.get_results()

    assert len(r) == 10 == gaia.ROW_LIMIT

    gaia.ROW_LIMIT = -1
    j = gaia.cone_search_async(coord, radius=radius)
    r = j.get_results()

    assert len(r) == 1218


@pytest.mark.remote_data
def test_search_async_jobs():
    # Regression test: `columns` were ignored if `radius` was provided [#2025]
    gaia = GaiaClass()
    jobfilter = Filter()
    jobfilter.limit = 10
    jobs = gaia.search_async_jobs(jobfilter=jobfilter, verbose=True)
    assert len(jobs) == 10
