# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import numpy as np

import astropy.units as u
from astropy.coordinates import EarthLocation
from astropy.time import Time

from ... import mpc
from ...utils.testing_tools import MockResponse
from ...utils import commons


DEFAULT_EPHEMERIS_ARGS = {
    'target': 'Ceres',
    'ut_offset': 0,
    'suppress_daytime': False,
    'suppress_set': False,
    'perturbed': True,
    'location': '500',
    'start': '2001-01-01',
    'step': u.Quantity('1d'),
    'number': 1,
    'eph_type': 'equatorial',
    'proper_motion': 'total'
}


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(mpc.MPCClass, '_request', post_mockreturn)
    return mp


def post_mockreturn(self, httpverb, url, params, auth):
    tr = str.maketrans(' /()')
    if url == mpc.core.MPC.MPES_URL:
        prefix = params['TextArea'].translate(tr)
        suffix = '-'.join((params['raty'], params['s']))
        filename = data_path('{}_ephemeris_{}.html'.format(prefix, suffix))
        content = open(filename, 'r').read()
        return MockResponse(content)
    else:
        return MockResponse()


def test_query_object_get_query_payload(patch_post):
    request_payload = mpc.core.MPC.query_object_async(
        get_query_payload=True, target_type='asteroid', name='ceres')
    assert request_payload == {"name": "ceres", "json": 1, "limit": 1}


def test_args_to_object_payload():
    test_args = mpc.core.MPC._args_to_object_payload(name="eros", number=433)
    assert test_args == {"name": "eros", "number": 433, "json": 1}


@pytest.mark.parametrize('type, url', [
    ('comet',
        'https://minorplanetcenter.net/web_service/search_comet_orbits'),
    ('asteroid',
        'https://minorplanetcenter.net/web_service/search_orbits')])
def test_get_mpc_object_endpoint(type, url):
    query_url = mpc.core.MPC.get_mpc_object_endpoint(target_type=type)
    assert query_url == url


def test_args_to_ephemeris_payload():
    payload = mpc.core.MPC._args_to_ephemeris_payload(
        **DEFAULT_EPHEMERIS_ARGS)
    assert payload == {
        'ty': 'e', 'TextArea': 'Ceres', 'uto': '0', 'igd': 'n', 'ibh': 'n',
        'fp': 'y', 'adir': 'N', 'tit': '', 'bu': '', 'c': '500',
        'd': '2001-01-01', 'i': '1', 'u': 'd', 'l': 1, 'raty': 'a',
        's': 't', 'm': 'h'
    }


def test_get_ephemeris_by_location_str():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location='000', get_query_payload=True)
    assert payload['c'] == '000'


def test_get_ephemeris_by_location_int():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location=0, get_query_payload=True)
    assert payload['c'] == '000'


@pytest.mark.parametrize('location', (
    (0 * u.deg, '51d28m31.6s', 65.8 * u.m),
    EarthLocation(0 * u.deg, '51d28m31.6s', 65.8 * u.m)
))
def test_get_ephemeris_by_location_latlonalt(location):
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location=location, get_query_payload=True)
    assert np.isclose(payload['long'], 0.0)
    assert np.isclose(payload['lat'], 51.47544444444445)
    assert np.isclose(payload['alt'], 65.8)


def test_get_ephemeris_by_start_str():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', start='2001-1-1', get_query_payload=True)
    assert payload['d'] == '2001-1-1'


def test_get_ephemeris_by_start_time():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', start=Time('2001-1-1'), get_query_payload=True)
    assert payload['d'] == '2001-01-01 000000'


def test_get_ephemeris_by_start_now():
    payload = mpc.core.MPC.get_ephemeris('(1)', get_query_payload=True)
    assert len(payload['d']) == 17


@pytest.mark.parametrize('step,interval,unit', (
    ('1d', '1', 'd'),
    ('2h', '2', 'h'),
    ('3min', '3', 'm'),
    ('10s', '10', 's')
))
def test_get_ephemeris_by_step(step, interval, unit):
    payload = mpc.core.MPC.get_ephemeris(
        '10P', step=step, get_query_payload=True)
    assert payload['i'] == interval
    assert payload['u'] == unit


def test_get_ephemeris_by_step_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', step='1m')  # units of meters


@pytest.mark.parametrize('number,step,val', (
    (1, '1d', 1),
    (None, '1d', '21'),
    (None, '2h', '49'),
    (None, '3min', '121'),
    (None, '10s', '301')
))
def test_get_ephemeris_by_number(number, step, val):
    payload = mpc.core.MPC.get_ephemeris('10P', number=number, step=step,
                                         get_query_payload=True)
    assert payload['l'] == val


def test_get_ephemeris_by_number_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', number=1500)


@pytest.mark.parametrize('eph_type,cols', (
    ('equatorial', ('RA', 'Dec')),
    ('heliocentric', ('X', 'Y', 'Z', "X'", "Y'", "Z'")),
    ('geocentric', ('X', 'Y', 'Z'))
))
def test_get_ephemeris_by_eph_type(eph_type, cols):
    result = mpc.core.MPC.get_ephemeris('2P', eph_type=eph_type)
    for col in cols:
        assert col in result.colnames


def test_get_ephemeris_by_eph_type_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', eph_type='something else')


@pytest.mark.parametrize('mu,columns', (
    ('total', ('Proper motion', 'Direction')),
    ('coordinate', ('dRA', 'dDec')),
    ('sky', ('dRA cos(Dec)', 'dDec'))
))
def test_get_ephemeris_by_proper_motion(mu, columns):
    result = mpc.core.MPC.get_ephemeris('2P', proper_motion=mu)
    for col in columns:
        assert col in result.colnames


def test_get_ephemeris_by_proper_motion_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', proper_motion='something else')


@pytest.mark.parametrize('mu,unit,columns,units', (
    ('total', 'arcsec/h', ('Proper motion', 'Direction'), ('arcsec/h', 'deg')),
    ('coordinate', 'arcmin/h', ('dRA', 'dDec'), ('arcmin/h', 'arcmin/h')),
    ('sky', 'arcsec/d', ('dRA cos(Dec)', 'dDec'), ('arcsec/d', 'arcsec/d'))
))
def test_get_ephemeris_by_proper_motion_unit(mu, unit, columns, units):
    result = mpc.core.MPC.get_ephemeris(
        '2P', proper_motion=mu, proper_motion_unit=unit)
    for col, unit in zip(columns, units):
        assert result[col].unit == u.Unit(unit)


def test_get_ephemeris_by_proper_motion_unit_fail():
    with pytest.raises(ValueError):
        result = mpc.core.MPC.get_ephemeris('2P', proper_motion_unit='km/s')
