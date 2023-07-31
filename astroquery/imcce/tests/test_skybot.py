# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

from astroquery.utils.mocks import MockResponse
import astropy.units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, Angle
from astropy.table import MaskedColumn

from .. import core, SkybotClass

# files in data/
DATA_FILE = 'skybot_query.dat'


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
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(SkybotClass, '_request', nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_input():
    """test the different input arguments"""

    # test coo input
    a = core.Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = core.Skybot.cone_search(SkyCoord(ra=100, dec=20, unit=(u.deg, u.deg),
                                         frame='icrs'),
                                1, 2451200, get_query_payload=True)
    assert (a['-ra'] == b['-ra'])
    assert (a['-dec'] == b['-dec'])

    # test rad input
    a = core.Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = core.Skybot.cone_search((100, 20), Angle(60*u.arcmin),
                                2451200, get_query_payload=True)
    assert (a['-rd'] == b['-rd'])

    with pytest.warns(UserWarning, match='search cone radius'):
        a = core.Skybot.cone_search((100, 20), 100, 2451200,
                                    get_query_payload=True)
        assert (a['-rd'] == 10)

    # test epoch input
    a = core.Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    b = core.Skybot.cone_search((100, 20), 1, Time(2451200, format='jd'),
                                get_query_payload=True)
    c = core.Skybot.cone_search((100, 20), 1, Time('1999-01-21 12:00',
                                                   format='iso'),
                                get_query_payload=True)
    assert (a['-ep'] == b['-ep'] == c['-ep'])

    # test position_error input
    a = core.Skybot.cone_search((100, 20), 1, 2451200, position_error=10,
                                get_query_payload=True)
    b = core.Skybot.cone_search((100, 20), 1, 2451200,
                                position_error=Angle(10*u.arcsec),
                                get_query_payload=True)
    assert (a['-filter'] == b['-filter'])

    with pytest.warns(UserWarning, match='positional error'):
        a = core.Skybot.cone_search((100, 20), 1, 2451200, position_error=1000,
                                    get_query_payload=True)
        assert (a['-filter'] == 120)

    # test target filters
    a = core.Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    assert (a['-objFilter'] == '111')
    a = core.Skybot.cone_search((100, 20), 1, 2451200, find_planets=False,
                                get_query_payload=True)
    assert (a['-objFilter'] == '101')
    a = core.Skybot.cone_search((100, 20), 1, 2451200, find_asteroids=False,
                                get_query_payload=True)
    assert (a['-objFilter'] == '011')
    a = core.Skybot.cone_search((100, 20), 1, 2451200, find_comets=False,
                                get_query_payload=True)
    assert (a['-objFilter'] == '110')

    # test coordinate reference system
    a = core.Skybot.cone_search((100, 20), 1, 2451200, get_query_payload=True)
    assert (a['-refsys'] == 'EQJ2000')


def general_query(patch_request):
    """test a mock query"""

    a = core.Skybot.cone_search((0, 0), 0.5, 2451200)

    assert (len(a) == 141)
    assert isinstance(a['Number'][0], int)
    assert (a['RA'][0] == 359.94077541666667*u.deg)
    assert (a['DEC'][0] == -0.013904166666666667*u.deg)


def test_get_raw_response(patch_request):
    raw = core.Skybot.cone_search(
        (0, 0), 0.5, 2451200, get_raw_response=True)
    assert " 299383 | 2005 VC73 | 23 59 45.7861 |" in raw


def test_parsing_unnumbered_asteroids(patch_request):
    """
    test a query that returns at least one unnumbered asteroid.
    Checking that the Numbers column is indeed masked.
    """
    coord = SkyCoord(ra=271.74541667, dec=-19.94805556, unit=(u.deg, u.deg), frame='icrs')
    a = core.Skybot.cone_search(coord,
                                rad=1.7*u.deg,
                                epoch=Time(56734.74982639, format='mjd'),
                                location=260,
                                position_error=15*u.arcsec)

    assert (isinstance(a['Number'], MaskedColumn))

    assert (a['Number'].mask.sum() > 0)
