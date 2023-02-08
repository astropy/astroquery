# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import re
import numpy as np

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.utils.mocks import MockResponse
from astroquery.ipac.most import Most, conf

DATA_FILES = "MOST_regular_outputs.html"


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(Most, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=False, **kwargs):
    filename = data_path(DATA_FILES)
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def test_get_regular():
    response = Most.query()
    breakpoint()

    a = 1
