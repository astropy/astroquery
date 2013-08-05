# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests

import numpy.testing as npt
from astropy.tests.helper import pytest
from astropy.table import Table
import astropy.units as u

from ... import nist

DATA_FILES = {'lines': 'nist_out.html'}

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES['lines'])
    content = open(filename, 'r').read()
    return MockResponse(content)

class MockResponse(object):
    def __init__(self, content):
        self.content = content

def test_parse_wavelength():
    minwav, maxwav, unit = nist.core._parse_wavelength(4000 * u.AA, 7000 * u.AA)
    npt.assert_approx_equal(minwav, 4000, significant=4)
    npt.assert_approx_equal(maxwav, 7000, significant=4)
    assert unit == ist.core.Nist.unit_code['Angstrom']

def test_query_async(patch_get):
    response = nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm, "H I")
    assert response is not None

def test_query(patch_get):
    result =  nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm, "H I", get_query_payload=True)
    assert result['spectra'] == "H I"
    assert result['unit'] == nist.core.Nist.unit_code['nm']
    result =  nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm, "H I")
    assert isinstance(result, Table)
