# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import math
import pytest
import requests
import os

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table

from astroquery.casda import Casda

DATA_FILES = {'CIRCLE': 'cone.xml', 'RANGE': 'box.xml'}


class MockResponse(object):

    def __init__(self, content):
        self.content = content


def get_mockreturn(self, method, url, data=None, timeout=10,
                   files=None, params=None, headers=None, **kwargs):
    print("get_mockreturn", url, params)
    key = params['POS'].split()[0] if params['POS'] else None
    filename = data_path(DATA_FILES[key])
    content = open(filename, 'rb').read()
    return MockResponse(content)


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def isclose(value1, value2, abs_tol=1e-09):
    return abs(value1 - value2) < abs_tol


def test_query_region_text_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    query_payload = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=radius * u.deg, cache=False,
                                       get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 3


def test_query_region_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region(centre, radius=radius * u.deg, cache=False, get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region(centre, radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 3


def test_query_region_async_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region_async(centre, radius=radius * u.deg, cache=False, get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region_async(centre, radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, MockResponse)


def test_query_region_box(patch_get):
    ra = 333.9092
    dec = -45.8418
    width = 0.5
    height = 0.2
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region(centre, width=width * u.deg, height=height * u.deg, cache=False,
                                       get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('RANGE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'RANGE'
    assert isclose(float(pos_parts[1]), ra - width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), ra + width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), dec - height / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[4]), dec + height / 2, abs_tol=1e-5)
    assert len(pos_parts) == 5

    responses = Casda.query_region(centre, width=width * u.deg, height=height * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 2


def test_query_region_async_box(patch_get):
    ra = 333.9092
    dec = -45.8418
    width = 0.5
    height = 0.2
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region_async(centre, width=width * u.deg, height=height * u.deg, cache=False,
                                             get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('RANGE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'RANGE'
    assert isclose(float(pos_parts[1]), ra - width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), ra + width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), dec - height / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[4]), dec + height / 2, abs_tol=1e-5)
    assert len(pos_parts) == 5

    responses = Casda.query_region_async(centre, width=width * u.deg, height=height * u.deg, cache=False)
    assert isinstance(responses, MockResponse)
