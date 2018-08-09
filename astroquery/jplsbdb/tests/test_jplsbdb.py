# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

from astroquery.utils.testing_tools import MockResponse

from .. import SBDB, SBDBClass

# files in data/ for different query types
DATA_FILES = {'1': 'ceres.dat',
              'Apophis': 'apophis.dat',
              '3200': 'phaethon.dat',
              '67P': '67P.dat',
              }

SCHEMATICS = {'1': ('| +-- equinox: J2000\n'
                    '| +-- data_arc: 24437\n'
                    '| +-- not_valid_after: None\n'
                    '| +-- n_del_obs_used: 405\n'
                    '| +-- sb_used: SB431-N16\n'),
              'Apophis': ('| +-- albedo: 0.23\n'
                          '| +-- albedo_sig: None\n'
                          '| +-- albedo_ref: T. Mueller (2013)\n'
                          '| +-- albedo_note: http://www.esa.int/Our_'
                          'Activities/Space_Science/Herschel_intercepts_'
                          'asteroid_Apophis'),
              '3200': ('| +-+ model_pars: \n'
                       '| | +-- A2: -4.86111e-15 AU / d2\n'
                       '| | +-- A2_sig: 1.386e-15 AU / d2\n'
                       '| | +-- A2_kind: EST\n'
                       '| | +-- ALN: 1.\n'
                       '| | +-- ALN_sig: None\n'),
              '67P': ('| +-+ des_alt: \n'
                      '| | +-- yl: [\'1988i\', \'1982f\', \'1975i\', '
                      '\'1969h\']\n'
                      '| | +-- rn: [\'1989 VI\', \'1982 VIII\', '
                      '\'1976 VII\', \'1969 IV\']\n'
                      '| +-+ orbit_class: \n'
                      '| | +-- name: Jupiter-family Comet\n'
                      '| | +-- code: JFc\n')
              }


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

def test_objects_against_schema(patch_request):
    for targetname in DATA_FILES.keys():

        sbdb = SBDB.query(targetname, id_type='search', phys=True,
                          alternate_id=True, full_precision=True,
                          covariance='mat', validity=True,
                          alternate_orbit=True, close_approach=True,
                          virtual_impactor=True,
                          discovery=True, radar=True)

        assert SCHEMATICS[targetname] in SBDB.schematic(sbdb)
