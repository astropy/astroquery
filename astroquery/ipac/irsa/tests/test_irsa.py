# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u

from astroquery.ipac.irsa import Irsa
from astroquery.exceptions import InvalidQueryError

OBJ_LIST = ["00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743 * u.deg, b=-21.5733 * u.deg, frame="galactic")]

SIZE_LIST = [2 * u.arcmin, '0d2m0s']


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("radius", SIZE_LIST)
def test_query_region_cone(coordinates, radius):
    query = Irsa.query_region(coordinates, catalog='fp_psc', spatial='Cone', radius=radius,
                              get_query_payload=True)

    # We don't fully float compare in this string, there are slight differences due to the name-coordinate
    # resolution and conversions
    assert "SELECT * FROM fp_psc WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',10.68" in query
    assert ",41.26" in query
    assert ",0.0333" in query


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("width", SIZE_LIST)
def test_query_region_box(coordinates, width):
    query = Irsa.query_region(coordinates, catalog='fp_psc', spatial='Box', width=2 * u.arcmin,
                              get_query_payload=True)

    assert "SELECT * FROM fp_psc WHERE CONTAINS(POINT('ICRS',ra,dec),BOX('ICRS',10.68" in query
    assert ",41.26" in query
    assert ",0.0333" in query


poly1 = [SkyCoord(ra=10.1 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.0 * u.deg)]
poly2 = [(10.1 * u.deg, 10.1 * u.deg), (10.0 * u.deg, 10.1 * u.deg),
         (10.0 * u.deg, 10.0 * u.deg)]


@pytest.mark.parametrize("polygon", [poly1, poly2])
def test_query_region_polygon(polygon):
    query1 = Irsa.query_region(catalog="fp_psc", spatial="Polygon", polygon=polygon,
                               get_query_payload=True)
    query2 = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon", polygon=polygon,
                               get_query_payload=True)

    assert query1 == query2
    assert query1 == ("SELECT * FROM fp_psc "
                      "WHERE CONTAINS(POINT('ICRS',ra,dec),POLYGON('ICRS',10.1,10.1,10.0,10.1,10.0,10.0))=1")


def test_query_allsky():
    query1 = Irsa.query_region(catalog="fp_psc", spatial="All-Sky", get_query_payload=True)
    query2 = Irsa.query_region("m31", catalog="fp_psc", spatial="All-Sky", get_query_payload=True)

    assert query1 == query2 == "SELECT * FROM fp_psc"


@pytest.mark.parametrize('spatial', ['cone', 'box', 'polygon', 'all-Sky', 'All-sky', 'invalid'])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Irsa.query_region(OBJ_LIST[0], catalog='invalid_spatial', spatial=spatial)


def test_no_catalog():
    with pytest.raises(InvalidQueryError):
        Irsa.query_region("m31", spatial='Cone')


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.irsa  # noqa: F401
