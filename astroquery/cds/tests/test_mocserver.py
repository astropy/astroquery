# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import pytest
import os
import requests

from astropy import coordinates
from astropy.table import Table

try:
    from mocpy import MOC
    HAS_MOCPY = True
except ImportError:
    HAS_MOCPY = False

try:
    from regions import CircleSkyRegion, PolygonSkyRegion
    HAS_REGIONS = True
except ImportError:
    HAS_REGIONS = False

from ..core import cds
from ...utils.testing_tools import MockResponse


DATA_FILES = {
    'PROPERTIES_SEARCH': 'properties.json',
    'HIPS_FROM_SAADA_AND_ALASKY': 'hips_from_saada_alasky.json',
}


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def get_mockreturn(self, method, url, data=None, timeout=10,
                   files=None, params=None, headers=None, **kwargs):
    filename = data_path(DATA_FILES[data])
    content = open(filename, 'rb').read()
    return MockResponse(content)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


"""List of all the constrain we want to test"""
# SPATIAL CONSTRAINTS DEFINITIONS
polygon1 = coordinates.SkyCoord([57.376, 56.391, 56.025, 56.616], [24.053, 24.622, 24.049, 24.291],
                                frame="icrs",
                                unit="deg")
polygon2 = coordinates.SkyCoord([58.376, 53.391, 56.025, 54.616], [24.053, 25.622, 22.049, 27.291],
                                frame="icrs",
                                unit="deg")

# PROPERTY CONSTRAINTS DEFINITIONS
meta_data_ex = 'ID = *SDSS* && moc_sky_fraction<=0.01'
meta_data_hips_from_saada_alasky = '(hips_service_url*=http://saada*) && (hips_service_url*=http://alasky.*)'
"""
Combination of one spatial with a property constrain

Each tuple(spatial, property) characterizes a specific query and is tested
with regards to the true results stored in a file located in the data directory

"""


@pytest.mark.skipif('not HAS_REGIONS')
@pytest.mark.skipif('not HAS_MOCPY')
@pytest.mark.parametrize('datafile',
                         ['PROPERTIES_SEARCH', 'HIPS_FROM_SAADA_AND_ALASKY'])
def test_request_results(patch_get, datafile):
    """
    Compare the request result obtained with the astroquery.Mocserver API

    with the one obtained on the http://alasky.unistra.fr/MocServer/query
    """
    results = cds.query_region(get_query_payload=False,
                               verbose=True,
                               data=datafile)
    assert type(results) == Table


"""
Spatial Constrains requests

We test a polygon/cone/moc search and ensure the
request param 'intersect' is correct

"""


@pytest.mark.skipif('not HAS_REGIONS')
@pytest.mark.skipif('not HAS_MOCPY')
@pytest.mark.parametrize('RA, DEC, RADIUS',
                         [(10.8, 6.5, 0.5),
                          (25.6, -23.2, 1.1),
                          (150.6, 45.1, 1.5)])
def test_cone_search_spatial_request(RA, DEC, RADIUS):
    center = coordinates.SkyCoord(ra=RA, dec=DEC, unit="deg")
    radius = coordinates.Angle(RADIUS, unit="deg")
    cone_region = CircleSkyRegion(center=center, radius=radius)

    request_payload = cds.query_region(region=cone_region,
                                       get_query_payload=True,
                                       intersect='overlaps')

    assert (request_payload['DEC'] == str(DEC)) and \
           (request_payload['RA'] == str(RA)) and \
           (request_payload['SR'] == str(RADIUS))


@pytest.mark.skipif('not HAS_REGIONS')
@pytest.mark.skipif('not HAS_MOCPY')
@pytest.mark.parametrize('poly, poly_payload',
                         [(polygon1, 'Polygon 57.376 24.053 56.391 24.622 56.025 24.049 56.616 24.291'),
                          (polygon2, 'Polygon 58.376 24.053 53.391 25.622 56.025 22.049 54.616 27.291')])
def test_polygon_spatial_request(poly, poly_payload):
    polygon_region = PolygonSkyRegion(vertices=poly)

    request_payload = cds.query_region(region=polygon_region,
                                       intersect='overlaps',
                                       get_query_payload=True)

    assert request_payload['stc'] == poly_payload


@pytest.mark.skipif('not HAS_REGIONS')
@pytest.mark.skipif('not HAS_MOCPY')
@pytest.mark.parametrize('intersect',
                         ['encloses', 'overlaps', 'covers'])
def test_intersect_param(intersect):
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")

    cone_region = CircleSkyRegion(center, radius)
    request_payload = cds.query_region(region=cone_region,
                                       intersect=intersect,
                                       get_query_payload=True)
    if intersect == 'encloses':
        assert request_payload['intersect'] == 'enclosed'
    else:
        assert request_payload['intersect'] == intersect
