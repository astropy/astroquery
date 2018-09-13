# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

from astroquery.utils.testing_tools import MockResponse
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from .. import SBDB, SBDBClass

# files in data/ for different query types
DATA_FILES = {'1': 'ceres.dat',
              'Apophis': 'apophis.dat',
              '3200': 'phaethon.dat',
              '67P': '67P.dat',
              }

SCHEMATICS = {'1': '| +-- n_del_obs_used: 405',
              'Apophis': '| +-- albedo_note: http://www.esa.int/Our_',
              '3200': '| | +-- A2_kind: EST',
              '67P': '| | +-- name: Jupiter-family Comet'
              }

SEMI_MAJOR = {'1': 2.767046248500289,
              'Apophis': .9224383019077086,
              '3200': 1.271196435728355,
              '67P': 3.46473701803964}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, url, **kwargs):

    targetname = kwargs['params']['sstr']

    with open(data_path(DATA_FILES[targetname]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(SBDBClass, '_request',
               nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_objects_numerically(patch_request):
    for targetname in DATA_FILES.keys():

        sbdb = SBDB.query(targetname, id_type='search', phys=True,
                          alternate_id=True, full_precision=True,
                          covariance='mat', validity=True,
                          alternate_orbit=True, close_approach=True,
                          virtual_impactor=True,
                          discovery=True, radar=True)

        assert_quantity_allclose(sbdb['orbit']['elements']['a'].scale,
                                 SEMI_MAJOR[targetname])


# def test_objects_against_schema(patch_request):
#     for targetname in DATA_FILES.keys():

#         sbdb = SBDB.query(targetname, id_type='search', phys=True,
#                           alternate_id=True, full_precision=True,
#                           covariance='mat', validity=True,
#                           alternate_orbit=True, close_approach=True,
#                           virtual_impactor=True,
#                           discovery=True, radar=True)

#         assert SCHEMATICS[targetname] in SBDB.schematic(sbdb)
