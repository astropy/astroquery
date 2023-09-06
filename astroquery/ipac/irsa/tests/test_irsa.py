# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import re
import numpy as np

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.utils.mocks import MockResponse
from astroquery.ipac.irsa import Irsa, conf
from astroquery.ipac import irsa

DATA_FILES = {'Cone': 'Cone.xml',
              'Box': 'Box.xml',
              'Polygon': 'Polygon.xml'}

OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743 * u.deg, b=-21.5733 * u.deg, frame="galactic")]


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(Irsa, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=False, **kwargs):
    filename = data_path(DATA_FILES[params['spatial']])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


#def test_args_to_payload():
#    out = Irsa._args_to_payload("fp_psc")
#    assert out == dict(catalog='fp_psc', outfmt=3, outrows=conf.row_limit,
#                       selcols='')


@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_cone(coordinates, patch_get):
    result = Irsa.query_region(
        coordinates, catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin)

    assert isinstance(result, Table)


@pytest.mark.skip("Upstream TAP doesn't support Box geometry yet")
@pytest.mark.parametrize("coordinates", OBJ_LIST)
def test_query_region_box(coordinates, patch_get):
    result = Irsa.query_region(
        coordinates, catalog='fp_psc', spatial='Box', width=2 * u.arcmin)

    assert isinstance(result, Table)


poly1 = [SkyCoord(ra=10.1 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.0 * u.deg)]
poly2 = [(10.1 * u.deg, 10.1 * u.deg), (10.0 * u.deg, 10.1 * u.deg),
         (10.0 * u.deg, 10.0 * u.deg)]


@pytest.mark.parametrize("polygon", [poly1, poly2])
def test_query_region_polygon(polygon, patch_get):
    result = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon", polygon=polygon)

    assert isinstance(result, Table)


@pytest.mark.parametrize('spatial', ['cone', 'box', 'polygon', 'all-Sky', 'All-sky', 'invalid'])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Irsa.query_region("m31", catalog='invalid_spatial', spatial=spatial)


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.irsa  # noqa: F401
