# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os

import astropy.units as u
from astroquery.utils.mocks import MockResponse

from .. import Miriade, MiriadeClass

# files in data/ for different query types


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, request_type, url, **kwargs):

    filename = '3552_coordtype{}.dat'.format(
        kwargs['params']['-tcoor'])
    with open(data_path(filename), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)

    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(MiriadeClass, '_request', nonremote_request)
    return mp


# --------------------------------- actual test functions


def test_spherical_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=1)
    cols = ('epoch', 'RA', 'DEC', 'delta', 'V', 'alpha', 'elong', 'RAcosD_rate',
            'DEC_rate', 'delta_rate', 'rvc', 'berv', 'rvs')
    units = (u.d, u.deg, u.deg, u.au, u.mag, u.deg, u.deg,
             u.arcsec / u.minute, u.arcsec / u.minute, u.km / u.s,
             u.km / u.s, u.km / u.s, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_rectangular_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=2)
    cols = ('epoch', 'px', 'py', 'pz', 'delta', 'heldist', 'alpha', 'elong', 'V',
            'vx', 'vy', 'vz', 'delta_rate', 'rvc', 'berv', 'rvs')
    units = (u.d, u.au, u.au, u.au, u.au, u.au, u.deg, u.deg, u.mag,
             u.au / u.day, u.au / u.day, u.au / u.day,
             u.km / u.s, u.km / u.s, u.km / u.s, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_local_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=3)
    cols = ('epoch', 'siderealtime', 'AZ', 'EL', 'delta', 'V',
            'alpha', 'elong', 'refrac', 'delta_rate', 'rvc', 'berv', 'rvs')
    units = (u.d, 'h min s', u.deg, u.deg, u.au, u.mag,
             u.deg, u.deg, u.arcsec, u.km / u.s, u.km / u.s,
             u.km / u.s, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_hourangle_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=4)
    cols = ['epoch', 'siderealtime', 'hourangle', 'dec', 'delta', 'V',
            'alpha', 'elong', 'airmass', 'delta_rate', 'rvc', 'berv', 'rvs']
    units = (u.d, 'h min s', u.deg, u.deg, u.au, u.mag,
             u.deg, u.deg, None, u.km / u.s, u.km / u.s,
             u.km / u.s, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_observation_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=5)
    cols = ['epoch', 'siderealtime', 'RA', 'DEC', 'hourangle', 'AZ', 'EL',
            'delta', 'heldist', 'V', 'alpha', 'elong', 'airmass',
            'RAcosD_rate', 'DEC_rate', 'delta_rate', 'rvc', 'berv', 'rvs']
    units = (u.d, "h min s", u.deg, u.deg, u.deg, u.deg, u.deg,
             u.au, u.au, u.mag, u.deg, u.deg, None,
             u.arcsec / u.min, u.arcsec / u.min, u.km / u.s, u.km / u.s,
             u.km / u.s, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_get_raw_response(patch_request):
    raw_eph = Miriade.get_ephemerides(
        '3552', coordtype=1, get_raw_response=True)
    assert '<?xml version="1.0" encoding="UTF-8"?>' in raw_eph
