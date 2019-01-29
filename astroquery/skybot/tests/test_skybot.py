# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os
import warnings

from astroquery.utils.testing_tools import MockResponse
import astropy.units as u
from astropy.time import Time
from astropy.table import Table
from astropy.coordinates import SkyCoord, Angle
from astropy.tests.helper import assert_quantity_allclose
from .. import Skybot, SkybotClass

# files in data/
DATA_FILE = 'general_query.dat'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, url, **kwargs):

    with open(data_path(DATA_FILE), 'rb') as f:
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

def test_input():
    """test the different input arguments"""

    # test coo input
    a = Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = Skybot.cone_search(SkyCoord(ra=100, dec=20, unit=(u.deg, u.deg),
                                    frame='icrs'),
                           1, 2451200, get_query_payload=True)
    assert(a['-ra'] == b['-ra'])
    assert(a['-dec'] == b['-dec'])

    # test rad input
    a = Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = Skybot.cone_search((100, 20), Angle(60*u.arcmin),
                           2451200, get_query_payload=True)
    assert(a['-rd'] == b['-rd'])

    with warnings.catch_warnings(record=True) as w:
        a = Skybot.cone_search((100, 20), 100, 2451200,
                               get_query_payload=True)
        assert(a['-rd'] == 10)
        assert('search cone radius' in str(w[-1].message))

    # test epoch input
    a = Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = Skybot.cone_search((100, 20), 1, Time(2451200, format='jd'),
                           get_query_payload=True)
    c = Skybot.cone_search((100, 20), 1, Time('1999-01-21 12:00',
                                              format='iso'),
                           get_query_payload=True)
    assert(a['-ep'] == b['-ep'] == c['-ep'])

    # test position_error input
    a = Skybot.cone_search((100, 20), 1, 2451200, position_error=10,
                           get_query_payload=True)
    b = Skybot.cone_search((100, 20), 1, 2451200,
                           position_error=Angle(10*u.arcsec),
                           get_query_payload=True)
    assert(a['-filter'] == b['-filter'])

    with warnings.catch_warnings(record=True) as w:
        a = Skybot.cone_search((100, 20), 1, 2451200, position_error=1000,
                               get_query_payload=True)
        assert(a['-filter'] == 120)
        assert('positional error' in str(w[-1].message))

    # test target filters
    a = Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    assert(a['-objFilter'] == '111')
    a = Skybot.cone_search((100, 20), 1, 2451200, find_planets=False,
                           get_query_payload=True)
    assert(a['-objFilter'] == '101')
    a = Skybot.cone_search((100, 20), 1, 2451200, find_asteroids=False,
                           get_query_payload=True)
    assert(a['-objFilter'] == '011')
    a = Skybot.cone_search((100, 20), 1, 2451200, find_comets=False,
                           get_query_payload=True)
    assert(a['-objFilter'] == '110')

    # test coordinate reference system
    a = Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    assert(a['-refsys'] == 'EQJ2000')


def general_query(patch_request):
    """test a mock query"""

    a = Skybot.cone_search((0, 0), 0.5, 2451200, get_raw_response=True)

    assert(len(a) == 141)
    assert(type(a['Number'][0]) == int)
    assert(a['RA'][0] == 359.94077541666667*u.deg)
    assert(a['DEC'][0] == -0.013904166666666667*u.deg)
