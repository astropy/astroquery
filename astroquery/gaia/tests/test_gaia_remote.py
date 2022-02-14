import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from astroquery.exceptions import MaxResultsWarning
from astroquery.gaia import conf
from .. import GaiaClass


@pytest.mark.remote_data
def test_query_object_columns_with_radius():
    # Regression test: `columns` were ignored if `radius` was provided [#2025]
    Gaia = GaiaClass()
    sc = SkyCoord(ra=0*u.deg, dec=0*u.deg)
    table = Gaia.query_object_async(sc, radius=10*u.arcsec, columns=['ra'])
    assert table.colnames == ['ra', 'dist']


@pytest.mark.remote_data
def test_query_object_row_limit():
    Gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    width = u.Quantity(0.1, u.deg)
    height = u.Quantity(0.1, u.deg)
    r = Gaia.query_object_async(coordinate=coord, width=width, height=height)

    assert len(r) == conf.ROW_LIMIT

    Gaia.ROW_LIMIT = 10
    msg = ('The number of rows in the result matches the current row limit of '
           '10. You might wish to specify a different "row_limit" value.')
    with pytest.warns(MaxResultsWarning, match=msg):
        r = Gaia.query_object_async(coordinate=coord, width=width, height=height, verbose=True)

    assert len(r) == 10 == Gaia.ROW_LIMIT

    r = Gaia.query_object_async(coordinate=coord, width=width, height=height, row_limit=-1)

    assert len(r) == 176


@pytest.mark.remote_data
def test_cone_search_row_limit():
    Gaia = GaiaClass()
    coord = SkyCoord(ra=280, dec=-60, unit=(u.degree, u.degree), frame='icrs')
    radius = u.Quantity(0.1, u.deg)
    j = Gaia.cone_search_async(coord, radius)
    r = j.get_results()

    assert len(r) == conf.ROW_LIMIT

    Gaia.ROW_LIMIT = 10
    msg = ('The number of rows in the result matches the current row limit of 10. You might wish '
           'to specify a different "row_limit" value.')
    with pytest.warns(MaxResultsWarning, match=msg):
        j = Gaia.cone_search_async(coord, radius, verbose=True)
    r = j.get_results()

    assert len(r) == 10 == Gaia.ROW_LIMIT

    j = Gaia.cone_search_async(coord, radius, row_limit=-1)
    r = j.get_results()

    assert len(r) == 1188
