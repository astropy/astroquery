# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
import os

import astropy.units as u
from ...utils.testing_tools import MockResponse

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
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(MiriadeClass, '_request',
               nonremote_request)
    return mp


# --------------------------------- actual test functions


def test_spherical_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=1)
    cols = ('target', 'epoch', 'RA', 'DEC', 'delta', 'V', 'alpha', 'elong',
            'RAcosD_rate', 'DEC_rate', 'delta_rate')
    units = (None, u.d, u.deg, u.deg, u.au, u.mag, u.deg, u.deg,
             u.arcsec / u.minute, u.arcsec / u.minute, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_rectangular_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=2)
    cols = ('target', 'epoch', 'x', 'y', 'z',
            'vx', 'vy', 'vz', 'delta', 'V',
            'alpha', 'elong', 'rv', 'heldist',
            'x_h', 'y_h', 'z_h',
            'vx_h', 'vy_h', 'vz_h')
    units = (None, u.d, u.au, u.au, u.au, u.au/u.day, u.au/u.day,
             u.au/u.day, u.au, u.mag, u.deg, u.deg, u.km/u.s,
             u.au, u.au, u.au, u.au, u.au/u.day, u.au/u.day, u.au/u.day)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_local_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=3)
    cols = ('target', 'epoch', 'AZ', 'EL', 'V', 'delta', 'alpha', 'elong')
    units = (None, u.day, u.deg, u.deg, u.mag, u.au, u.deg, u.deg)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_hourangle_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=4)
    cols = ('target', 'epoch', 'hourangle',
            'DEC', 'V', 'delta', 'alpha', 'elong')
    units = (None, u.d, u.deg, u.deg, u.mag, u.au, u.deg, u.deg)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_observation_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=5)
    cols = ('target', 'epoch', 'siderealtime', 'RAJ2000', 'DECJ2000',
            'hourangle', 'DEC', 'AZ', 'EL', 'refraction',
            'airmass', 'V', 'delta', 'heldist', 'alpha', 'elong', 'posunc',
            'RAcosD_rate', 'DEC_rate', 'delta_rate')
    units = (None, u.d, u.h, u.deg, u.deg, u.deg, u.deg, u.deg, u.deg,
             u.arcsec, '-', u.mag, u.au, u.au, u.deg, u.deg, u.arcsec,
             u.arcsec / u.minute, u.arcsec / u.minute, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_aoobservation_coordinates(patch_request):
    eph = Miriade.get_ephemerides('3552', coordtype=6)
    cols = ('target', 'epoch', 'siderealtime', 'RAJ2000', 'DECJ2000',
            'refraction', 'airmass', 'V', 'delta', 'heldist', 'alpha',
            'elong', 'posunc', 'RAcosD_rate', 'DEC_rate', 'delta_rate')
    units = (None, u.d, u.h, u.deg, u.deg, u.arcsec, '-', u.mag,
             u.au, u.au, u.deg, u.deg, u.arcsec, u.arcsec / u.minute,
             u.arcsec / u.minute, u.km / u.s)
    for i in range(len(cols)):
        assert cols[i] in eph.columns
        assert eph[cols[i]].unit == units[i]


def test_get_raw_response(patch_request):
    raw_eph = Miriade.get_ephemerides(
        '3552', coordtype=1, get_raw_response=True)
    assert "<?xml version='1.0' encoding='UTF-8'?>" in raw_eph
