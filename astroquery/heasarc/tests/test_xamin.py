# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.heasarc import Xamin
from astroquery.exceptions import InvalidQueryError

OBJ_LIST = ["NGC 4151", "182d38m08.64s 39d24m21.06s",
            SkyCoord(l=155.0771, b=75.0631, unit=(u.deg, u.deg), frame='galactic')]

SIZE_LIST = [2 * u.arcmin, '0d2m0s']


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("radius", SIZE_LIST)
def test_query_region_cone(coordinates, radius):
    query = Xamin.query_region(coordinates, table='suzamaster', spatial='cone', radius=radius,
                               get_query_payload=True)

    # We don't fully float compare in this string, there are slight differences due to the name-coordinate
    # resolution and conversions
    assert "SELECT * FROM suzamaster WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',182.63" in query
    assert ",39.40" in query
    assert ",0.0333" in query


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("width", SIZE_LIST)
def test_query_region_box(coordinates, width):
    query = Xamin.query_region(coordinates, table='suzamaster', spatial='box', width=2 * u.arcmin,
                               get_query_payload=True)

    assert "SELECT * FROM suzamaster WHERE CONTAINS(POINT('ICRS',ra,dec),BOX('ICRS',182.63" in query
    assert ",39.40" in query
    assert ",0.0333" in query


poly1 = [SkyCoord(ra=10.1 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.0 * u.deg)]
poly2 = [(10.1 * u.deg, 10.1 * u.deg), (10.0 * u.deg, 10.1 * u.deg),
         (10.0 * u.deg, 10.0 * u.deg)]


@pytest.mark.parametrize("polygon", [poly1, poly2])
def test_query_region_polygon(polygon):
    # position is not used for polygon
    query1 = Xamin.query_region(table="suzamaster", spatial="polygon", polygon=polygon,
                                get_query_payload=True)
    query2 = Xamin.query_region("ngc4151", table="suzamaster", spatial="polygon", polygon=polygon,
                                get_query_payload=True)

    assert query1 == query2
    assert query1 == ("SELECT * FROM suzamaster "
                      "WHERE CONTAINS(POINT('ICRS',ra,dec),POLYGON('ICRS',10.1,10.1,10.0,10.1,10.0,10.0))=1")


def test_query_allsky():
    query1 = Xamin.query_region(table="suzamaster", spatial="all-sky", get_query_payload=True)
    query2 = Xamin.query_region("m31", table="suzamaster", spatial="all-sky", get_query_payload=True)

    assert query1 == query2 == "SELECT * FROM suzamaster"


@pytest.mark.parametrize('spatial', ['space', 'invalid'])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Xamin.query_region(OBJ_LIST[0], table='invalid_spatial', spatial=spatial)


def test_no_table():
    with pytest.raises(InvalidQueryError):
        Xamin.query_region("m31", spatial='cone')


def test_data_links():
    with pytest.raises(ValueError, match='query_result is None'):
        Xamin.get_links()

    with pytest.raises(TypeError, match='query_result need to be an astropy.table.Table'):
        Xamin.get_links([1,2])

    with pytest.raises(ValueError, match='Unknown table name:'):
        Xamin.get_links(Table({'__row':[1,2,3.]}), tablename=1)

    with pytest.raises(ValueError, match='No __row column found'):
        Xamin.get_links(Table({'id':[1,2,3.]}), tablename='xray')
