# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os
import re
import numpy as np

import pytest
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

from ...utils.testing_tools import MockResponse
from ...utils import commons
from ... import lco
from ...lco import conf

OBJ_LIST = ["M15", "00h42m44.330s +41d16m07.50s",
            commons.GalacticCoordGenerator(l=121.1743, b=-21.5733,
                                           unit=(u.deg, u.deg))]


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(lco.core.Lco, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=True, **kwargs):
    filename = data_path(DATA_FILES[params['spatial']])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


@pytest.mark.parametrize(('dim'),
                         ['5d0m0s', 0.3 * u.rad, '5h0m0s', 2 * u.arcmin])
def test_parse_dimension(dim):
    # check that the returned dimension is always in units of 'arcsec',
    # 'arcmin' or 'deg'
    new_dim = lco.core._parse_dimension(dim)
    assert new_dim.unit in ['arcsec', 'arcmin', 'deg']


@pytest.mark.parametrize(('ra', 'dec', 'expected'),
                         [(10, 10, '10 +10'),
                          (10.0, -11, '10.0 -11')
                          ])
def test_format_decimal_coords(ra, dec, expected):
    out = lco.core._format_decimal_coords(ra, dec)
    assert out == expected


@pytest.mark.parametrize(('coordinates', 'expected'),
                         [("5h0m0s 0d0m0s", "75.0 +0.0")
                          ])
def test_parse_coordinates(coordinates, expected):
    out = lco.core._parse_coordinates(coordinates)
    for a, b in zip(out.split(), expected.split()):
        try:
            a = float(a)
            b = float(b)
            np.testing.assert_almost_equal(a, b)
        except ValueError:
            assert a == b


def test_args_to_payload():
    out = lco.core.Lco._args_to_payload("lco_img")
    assert out == dict(catalog='lco_img', outfmt=3,
                       outrows=conf.row_limit, spatial=None)


@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_cone_async(coordinates, patch_get):
    response = lco.core.Lco.query_region_async(
        coordinates, catalog='lco_img', spatial='Cone',
        radius=2 * u.arcmin, get_query_payload=True)
    assert response['radius'] == 2
    assert response['radunits'] == 'arcmin'
    response = lco.core.Lco.query_region_async(
        coordinates, catalog='lco_img', spatial='Cone', radius=2 * u.arcmin)
    assert response is not None


@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_cone(coordinates, patch_get):
    result = lco.core.Lco.query_region(coordinates, catalog='lco_img',
                                           spatial='Cone', radius=2 * u.arcmin)

    assert isinstance(result, Table)


@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_box_async(coordinates, patch_get):
    response = lco.core.Lco.query_region_async(
        coordinates, catalog='lco_img', spatial='Box',
        width=2 * u.arcmin, get_query_payload=True)
    assert response['size'] == 120
    response = lco.core.Lco.query_region_async(
        coordinates, catalog='lco_img', spatial='Box', width=2 * u.arcmin)
    assert response is not None
