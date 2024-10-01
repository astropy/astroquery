# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
test_mpc

Generate offline ephemeris files for testing with the following commands.

  * The first object can be any target with successful queries.

  * The second object must be one that returns ephemeris uncertainties.

  * The third object must be one that does not exist in the MPC database.  The
    string 'test fail' is sufficient.

  * The fourth object must be one that fails an orbit lookup.  Today (2022
    July), that is 2008 JG, which has a permanent number 613986. The ephemeris
    service is not resolving the temporary designation to the permanent number,
    and therefore fails the orbit lookup.

Any changes to these queries (such as target name) must be reflected in the
appropriate tests below.

```
from astroquery.mpc import MPC
parameters = {
  '2P_ephemeris_G37-a-t': ('2P', {'location': 'G37'}),
  '2P_ephemeris_500-s-t': ('2P', {'eph_type': 'heliocentric'}),
  '2P_ephemeris_500-G-t': ('2P', {'eph_type': 'geocentric'}),
  '2P_ephemeris_500-a-t': ('2P', {'proper_motion': 'total'}),
  '2P_ephemeris_500-a-c': ('2P', {'proper_motion': 'coordinate'}),
  '2P_ephemeris_500-a-s': ('2P', {'proper_motion': 'sky'}),
  '2024AA_ephemeris_500-a-t': ('2024 AA', {}),
  '2024AA_ephemeris_G37-a-t': ('2024 AA', {'location': 'G37'}),
  'testfail_ephemeris_500-a-t': ('test fail', {}),
  '2008JG_ephemeris_500-a-t': ('2008 JG', {}),
}
for prefix, (name, kwargs) in parameters.items():
    with open(prefix + '.html', 'w') as outf:
        response = MPC.get_ephemeris_async(name, unc_links=True, **kwargs)
        outf.write(response.text)
```

For mock testing the object query:

```
from astroquery.mpc import MPC
result = MPC.query_object_async('comet', designation='C/2012 S1')
with open('comet_object_C2012S1.json', 'w') as outf:
    outf.write(result.text)
```

For ObsCodes.html:

    wget https://minorplanetcenter.net/iau/lists/ObsCodes.html

Then edit and remove all but the first 10 lines of observatories.
This is sufficient for offline testing.

"""
import os
import pytest
import numpy as np

import astropy.units as u
from astropy.coordinates import EarthLocation, Angle
from astropy.time import Time

from ...exceptions import EmptyResponseError, InvalidQueryError
from ... import mpc
from astroquery.utils.mocks import MockResponse
from requests import Request


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


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(mpc.MPCClass, '_request', post_mockreturn)
    return mp


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(mpc.MPCClass, '_request', get_mockreturn)
    return mp


def get_mockreturn(self, httpverb, url, params={}, auth=None, **kwargs):
    filename = None

    if mpc.core.MPC.MPC_URL in url:
        filename = 'comet_object_C2012S1.json'
    elif url == mpc.core.MPC.OBSERVATORY_CODES_URL:
        filename = 'ObsCodes.html'
    elif mpc.core.MPC.MPCOBS_URL in url:
        filename = 'mpc_obs.dat'
    else:
        content = None
    if filename:
        with open(data_path(filename), 'rb') as infile:
            content = infile.read()
    return MockResponse(content, url=url, auth=auth)


def post_mockreturn(self, httpverb, url, data={}, **kwargs):
    if url == mpc.core.MPC.MPES_URL:
        prefix = data['TextArea'].replace(' ', '')
        suffix = '-'.join((data['c'], data['raty'], data['s']))
        filename = data_path('{}_ephemeris_{}.html'.format(prefix, suffix))
        with open(filename, 'rb') as infile:
            content = infile.read()
    else:
        content = None

    response = MockResponse(content, url=url)
    response.request = Request('POST', url, data=data).prepare()

    return response


def test_query_object_get_query_payload(patch_get):
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
    query_url = mpc.core.MPC._get_mpc_object_endpoint(target_type=type)
    assert query_url == url


def test_args_to_ephemeris_payload():
    payload = mpc.core.MPC._args_to_ephemeris_payload(
        **DEFAULT_EPHEMERIS_ARGS)
    assert payload == {
        'ty': 'e', 'TextArea': 'Ceres', 'uto': '0', 'igd': 'n', 'ibh': 'n',
        'fp': 'y', 'adir': 'N', 'tit': '', 'bu': '', 'c': '500',
        'd': '2001-01-01 000000', 'i': '1', 'u': 'd', 'l': 1, 'raty': 'a',
        's': 't', 'm': 'h'
    }


def test_get_ephemeris_Moon_phase(patch_post):
    result = mpc.core.MPC.get_ephemeris('2P', location='G37')
    assert result['Moon phase'][0] >= 0


def test_get_ephemeris_Uncertainty(patch_post):
    # this test requires an object with uncertainties != N/A
    result = mpc.core.MPC.get_ephemeris('2024 AA')
    assert result['Uncertainty 3sig'].quantity[0] > 0 * u.arcsec


def test_get_ephemeris_Moon_phase_and_Uncertainty(patch_post):
    # this test requires an object with uncertainties != N/A
    result = mpc.core.MPC.get_ephemeris('2024 AA', location='G37')
    assert result['Moon phase'][0] >= 0
    assert result['Uncertainty 3sig'].quantity[0] > 0 * u.arcsec


def test_get_ephemeris_by_name_empty(patch_post):
    with pytest.raises(EmptyResponseError):
        mpc.core.MPC.get_ephemeris('340P', location='G37')


def test_get_ephemeris_by_name_fail(patch_post):
    with pytest.raises(InvalidQueryError):
        mpc.core.MPC.get_ephemeris('test fail')


def test_get_ephemeris_object_without_orbit(patch_post):
    with pytest.raises(InvalidQueryError):
        mpc.core.MPC.get_ephemeris('2008 JG')


def test_get_ephemeris_location_str():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location='000', get_query_payload=True)
    assert payload['c'] == '000'


def test_get_ephemeris_location_int():
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location=0, get_query_payload=True)
    assert payload['c'] == '000'


@pytest.mark.parametrize('patch_post,location', (
    (patch_post, (0 * u.deg, '51d28m31.6s', 65.8 * u.m)),
    (patch_post, EarthLocation(0 * u.deg, '51d28m31.6s', 65.8 * u.m))
))
def test_get_ephemeris_location_latlonalt(patch_post, location):
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', location=location, get_query_payload=True)
    assert np.isclose(payload['long'], 0.0)
    assert np.isclose(payload['lat'], 51.47544444444445)
    assert np.isclose(payload['alt'], 65.8)


def test_get_ephemeris_location_array_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', location=(1, 2, 3, 4))


def test_get_ephemeris_location_type_fail():
    with pytest.raises(TypeError):
        mpc.core.MPC.get_ephemeris('2P', location=1.0)


@pytest.mark.parametrize('start', ('2001-1-1', Time('2001-1-1')))
def test_get_ephemeris_start(start):
    payload = mpc.core.MPC.get_ephemeris(
        '(1)', start=start, get_query_payload=True)
    assert payload['d'] == '2001-01-01 000000'


def test_get_ephemeris_start_now():
    payload = mpc.core.MPC.get_ephemeris('(1)', get_query_payload=True)
    assert len(payload['d']) == 17


def test_get_ephemeris_start_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', start=2000)


@pytest.mark.parametrize('step,interval,unit', (
    ('1d', '1', 'd'),
    ('2h', '2', 'h'),
    ('3min', '3', 'm'),
    ('10s', '10', 's')
))
def test_get_ephemeris_step(step, interval, unit):
    payload = mpc.core.MPC.get_ephemeris(
        '10P', step=step, get_query_payload=True)
    assert payload['i'] == interval
    assert payload['u'] == unit


def test_get_ephemeris_step_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', step='1m')  # units of meters


@pytest.mark.parametrize('number,step,val', (
    (1, '1d', 1),
    (None, '1d', '21'),
    (None, '2h', '49'),
    (None, '3min', '121'),
    (None, '10s', '301')
))
def test_get_ephemeris_number(number, step, val):
    payload = mpc.core.MPC.get_ephemeris('10P', number=number, step=step,
                                         get_query_payload=True)
    assert payload['l'] == val


def test_get_ephemeris_number_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', number=1500)


def test_get_ephemeris_ra_format(patch_post):
    result = mpc.core.MPC.get_ephemeris('2P')
    ra0 = Angle(result['RA'])
    result = mpc.core.MPC.get_ephemeris('2P', ra_format={'unit': 'hourangle'})
    ra1 = Angle(result['RA'])
    assert np.allclose(ra0.deg, ra1.deg)


def test_get_ephemeris_dec_format(patch_post):
    result = mpc.core.MPC.get_ephemeris('2P')
    dec0 = Angle(result['Dec'])
    result = mpc.core.MPC.get_ephemeris('2P', dec_format={'unit': 'deg'})
    dec1 = Angle(result['Dec'])
    assert np.allclose(dec0.deg, dec1.deg)


@pytest.mark.parametrize('eph_type,cols', (
    ('equatorial', ('RA', 'Dec')),
    ('heliocentric', ('X', 'Y', 'Z', "X'", "Y'", "Z'")),
    ('geocentric', ('X', 'Y', 'Z'))
))
def test_get_ephemeris_eph_type(eph_type, cols, patch_post):
    result = mpc.core.MPC.get_ephemeris('2P', eph_type=eph_type)
    for col in cols:
        assert col in result.colnames


def test_get_ephemeris_eph_type_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', eph_type='something else')


@pytest.mark.parametrize('mu,columns', (
    ('total', ('Proper motion', 'Direction')),
    ('coordinate', ('dRA', 'dDec')),
    ('sky', ('dRA cos(Dec)', 'dDec'))
))
def test_get_ephemeris_proper_motion(mu, columns, patch_post):
    result = mpc.core.MPC.get_ephemeris('2P', proper_motion=mu)
    for col in columns:
        assert col in result.colnames


def test_get_ephemeris_proper_motion_fail():
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', proper_motion='something else')


@pytest.mark.parametrize('mu,unit,columns,units', (
    ('total', 'arcsec/h',
     ('Proper motion', 'Direction'), ('arcsec/h', 'deg')),
    ('coordinate', 'arcmin/h',
     ('dRA', 'dDec'), ('arcmin/h', 'arcmin/h')),
    ('sky', 'arcsec/d',
     ('dRA cos(Dec)', 'dDec'), ('arcsec/d', 'arcsec/d'))
))
def test_get_ephemeris_proper_motion_unit(mu, unit, columns, units,
                                          patch_post):
    result = mpc.core.MPC.get_ephemeris(
        '2P', proper_motion=mu, proper_motion_unit=unit)
    for col, unit in zip(columns, units):
        assert result[col].unit == u.Unit(unit)


def test_get_ephemeris_proper_motion_unit_fail(patch_post):
    with pytest.raises(ValueError):
        mpc.core.MPC.get_ephemeris('2P', proper_motion_unit='km/s')


@pytest.mark.parametrize('suppress_daytime,val', ((True, 'y'), (False, 'n')))
def test_get_ephemeris_suppress_daytime(suppress_daytime, val):
    payload = mpc.core.MPC.get_ephemeris('2P', suppress_daytime=suppress_daytime,
                                         get_query_payload=True)
    assert payload['igd'] == val


@pytest.mark.parametrize('suppress_set,val', ((True, 'y'), (False, 'n')))
def test_get_ephemeris_suppress_set(suppress_set, val):
    payload = mpc.core.MPC.get_ephemeris('2P', suppress_set=suppress_set,
                                         get_query_payload=True)
    assert payload['ibh'] == val


@pytest.mark.parametrize('perturbed,val', ((True, 'y'), (False, 'n')))
def test_get_ephemeris_perturbed(perturbed, val):
    payload = mpc.core.MPC.get_ephemeris('2P', perturbed=perturbed,
                                         get_query_payload=True)
    assert payload['fp'] == val


@pytest.mark.parametrize('unc_links', (True, False))
def test_get_ephemeris_unc_links(unc_links, patch_post):
    result = mpc.core.MPC.get_ephemeris('2024 AA', unc_links=unc_links)
    assert np.all(result['Uncertainty 3sig'].quantity > 0 * u.arcsec)
    assert ('Unc. map' in result.colnames) == unc_links
    assert ('Unc. offsets' in result.colnames) == unc_links


def test_get_observatory_codes(patch_get):
    result = mpc.core.MPC.get_observatory_codes()
    greenwich = ['000', 0.0, 0.62411, 0.77873, 'Greenwich']
    assert all([r == g for r, g in zip(result[0], greenwich)])


def test_get_observatory_location(patch_get):
    result = mpc.core.MPC.get_observatory_location('000')
    greenwich = [Angle(0.0, 'deg'), 0.62411, 0.77873, 'Greenwich']
    assert all([r == g for r, g in zip(result, greenwich)])


def test_get_observatory_location_fail():
    with pytest.raises(TypeError):
        mpc.core.MPC.get_observatory_location(0)
    with pytest.raises(ValueError):
        mpc.core.MPC.get_observatory_location('00')


def test_get_observations(patch_get):
    result = mpc.core.MPC.get_observations(12893)
    assert result['desig'][0] == '1998 QS55'
    assert result['mag'].unit == u.mag
    assert result['RA'].unit == u.deg
    assert result['DEC'].unit == u.deg
    assert result['epoch'].unit == u.d

    result = mpc.core.MPC.get_observations_async('12893')
    assert result.json()[0]['designation'] == "1998 QS55"

    result = mpc.core.MPC.get_observations('12893',
                                           get_mpcformat=True)
    assert "12893J93S07X*4 1993 09 17.25833" in str(result)


def test_get_observations_target_parsing(patch_get):
    result = mpc.core.MPC.get_observations(12893, get_query_payload=True)
    assert result['object_type'] == 'M' and result['number'] == '12893'

    result = mpc.core.MPC.get_observations(1, get_query_payload=True)
    assert result['object_type'] == 'M' and result['number'] == '1'

    result = mpc.core.MPC.get_observations(345678, get_query_payload=True)
    assert result['object_type'] == 'M' and result['number'] == '345678'

    result = mpc.core.MPC.get_observations('1998 QS55', get_query_payload=True)
    assert result['object_type'] == 'M' and result['designation'] == '1998 QS55'

    result = mpc.core.MPC.get_observations('P/2010 WK', get_query_payload=True)
    assert result['object_type'] == 'P' and result['designation'] == 'P/2010 WK'

    result = mpc.core.MPC.get_observations('C/2013 US10', get_query_payload=True)
    assert result['object_type'] == 'C' and result['designation'] == 'C/2013 US10'

    result = mpc.core.MPC.get_observations('C/2008 FK75', get_query_payload=True)
    assert result['object_type'] == 'C' and result['designation'] == 'C/2008 FK75'

    result = mpc.core.MPC.get_observations('1P', get_query_payload=True)
    assert result['object_type'] == 'P' and result['number'] == '1'

    # test `id_type`

    result = mpc.core.MPC.get_observations('C/2008 FK75',
                                           id_type='comet designation',
                                           get_query_payload=True)
    assert result['object_type'] == 'C' and result['designation'] == 'C/2008 FK75'

    result = mpc.core.MPC.get_observations('P/2010 WK',
                                           id_type='comet designation',
                                           get_query_payload=True)
    assert result['object_type'] == 'P' and result['designation'] == 'P/2010 WK'

    result = mpc.core.MPC.get_observations('1P',
                                           id_type='comet number',
                                           get_query_payload=True)
    assert (result['object_type'] == 'P' and result['number'] == '1')

    result = mpc.core.MPC.get_observations(345678,
                                           id_type='asteroid number',
                                           get_query_payload=True)
    assert result['object_type'] == 'M' and result['number'] == '345678'

    result = mpc.core.MPC.get_observations('1998 QS55',
                                           id_type='asteroid designation',
                                           get_query_payload=True)
    assert result['object_type'] == 'M' and result['designation'] == '1998 QS55'

    with pytest.raises(ValueError):
        result = mpc.core.MPC.get_observations(
            '1998 QS55', id_type='comet designation', get_query_payload=True)

    with pytest.raises(ValueError):
        result = mpc.core.MPC.get_observations(
            '1998 QS55', id_type='comet number', get_query_payload=True)

    # this should technically not work, but the server allows it
    result = mpc.core.MPC.get_observations(
        '1998 QS55', id_type='asteroid number', get_query_payload=True)
    assert result['object_type'] == 'M' and result['number'] == '1998 QS55'

    result = mpc.core.MPC.get_observations(
        '1P', id_type='comet designation', get_query_payload=True)
    assert result['object_type'] == 'P' and result['designation'] == '1P'
