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

OBJ_LIST = ["00h42m44.330s +41d16m07.50s",
            commons.GalacticCoordGenerator(l=121.1743, b=-21.5733,
                                           unit=(u.deg, u.deg))]

DATA_FILES = {'JSON':'response.json'}

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(lco.core.Lco, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=True, **kwargs):
    filename = data_path(DATA_FILES[params['JSON']])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


@pytest.mark.parametrize(("coordinates"), OBJ_LIST)
def test_query_region_async(coordinates, patch_get):
    response = lco.core.Lco.query_region_async(
        coordinates, get_query_payload=True)
    assert response is not None

@pytest.mark.parametrize(("object_name"), "M15")
def test_query_object_async(object_name, patch_get):
    response = lco.core.Lco.query_object_async(
        object_name, get_query_payload=True)
    assert response is not None
