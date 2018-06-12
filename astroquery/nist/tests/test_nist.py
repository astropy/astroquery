# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import numpy.testing as npt
import pytest
from astropy.table import Table
import astropy.units as u

from ...utils.testing_tools import MockResponse
from ... import nist

DATA_FILES = {'lines': 'nist_out.html'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(nist.Nist, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, **kwargs):
    filename = data_path(DATA_FILES['lines'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def test_parse_wavelength():
    minwav, maxwav, unit = nist.core._parse_wavelength(4000 * u.AA,
                                                       7000 * u.AA)
    npt.assert_approx_equal(minwav, 4000, significant=4)
    npt.assert_approx_equal(maxwav, 7000, significant=4)
    assert unit == nist.core.Nist.unit_code['Angstrom']


def test_query_async(patch_get):
    response = nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm,
                                          "H I", get_query_payload=True)
    assert response['spectra'] == "H I"
    assert response['unit'] == nist.core.Nist.unit_code['nm']
    response = nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm, "H I")
    assert response is not None


def test_query(patch_get):
    result = nist.core.Nist.query(4000 * u.nm, 7000 * u.nm, "H I")
    assert isinstance(result, Table)
