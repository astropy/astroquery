# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os
from collections import OrderedDict

from numpy.ma import is_masked
from astropy.tests.helper import assert_quantity_allclose
from astropy.utils.exceptions import AstropyDeprecationWarning
from astropy import units as u

from astroquery.utils.mocks import MockResponse
from ...query import AstroQuery
from ... import jplhorizons

# files in data/ for different query types
DATA_FILES = {'ephemerides-single': 'ceres_ephemerides_single.txt',
              'elements-single': 'ceres_elements_single.txt',
              'vectors-single': 'ceres_vectors_single.txt',
              'ephemerides-range': 'ceres_ephemerides_range.txt',
              'elements-range': 'ceres_elements_range.txt',
              'vectors-range': 'ceres_vectors_range.txt',
              '"1935 UZ"': 'no_H.txt',
              '"tlist_error"': 'tlist_error.txt'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, request_type, url, **kwargs):
    if kwargs['params']['COMMAND'] == '"Ceres"':
        # pick DATA_FILE based on query type and time request
        query_type = {'OBSERVER': 'ephemerides',
                      'ELEMENTS': 'elements',
                      'VECTORS': 'vectors'}[kwargs['params']['EPHEM_TYPE']]

        if 'TLIST' in kwargs['params']:
            query_type += '-single'
        elif ('START_TIME' in kwargs['params']
              and 'STOP_TIME' in kwargs['params']
              and 'STEP_SIZE' in kwargs['params']):
            query_type += '-range'

        with open(data_path(DATA_FILES[query_type]), 'rb') as f:
            response = MockResponse(content=f.read(), url=url)
    else:
        with open(data_path(DATA_FILES[kwargs['params']['COMMAND']]),
                  'rb') as f:
            response = MockResponse(content=f.read(), url=url)

    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(jplhorizons.core.HorizonsClass, '_request',
               nonremote_request)
    return mp


# --------------------------------- actual test functions

def test_parse_result(patch_request):
    q = jplhorizons.Horizons(id='tlist_error')
    # need _last_query to be defined
    q._last_query = AstroQuery('GET', 'http://dummy')
    with pytest.raises(ValueError):
        q.ephemerides()


def test_ephemerides_query(patch_request):
    # check values of Ceres for a given epoch
    # orbital uncertainty of Ceres is basically zero
    res = jplhorizons.Horizons(id='Ceres', location='500',
                               epochs=2451544.5).ephemerides()[0]

    assert res['targetname'] == "1 Ceres (A801 AA)"
    assert res['datetime_str'] == "2000-Jan-01 00:00:00.000"
    assert res['solar_presence'] == ""
    assert res['lunar_presence'] == ""
    assert res['elongFlag'] == '/L'
    assert res['airmass'] == 999

    assert is_masked(res['AZ'])
    assert is_masked(res['EL'])
    assert is_masked(res['magextinct'])

    assert_quantity_allclose(
        [2451544.5, 188.70280, 9.09829, 34.40955, -2.68359, 8.459, 6.999,
         96.17083, 161.3828, 10.4528, 2.551099027865, 0.1744491, 2.26315121010004,
         -21.9390512, 18.82205467, 95.3996, 22.5698, 292.551, 296.850,
         184.3426241, 11.7996517, 289.864335, 71.545654, 0.0, 0.0],
        [res['datetime_jd'],
         res['RA'], res['DEC'], res['RA_rate'], res['DEC_rate'],
         res['V'], res['surfbright'], res['illumination'],
         res['EclLon'], res['EclLat'], res['r'], res['r_rate'],
         res['delta'], res['delta_rate'], res['lighttime'],
         res['elong'], res['alpha'], res['sunTargetPA'], res['velocityPA'],
         res['ObsEclLon'], res['ObsEclLat'], res['GlxLon'], res['GlxLat'],
         res['RA_3sigma'], res['DEC_3sigma']], rtol=1e-3)


def test_elements_query(patch_request):
    # check values of Ceres for a given epoch
    # orbital uncertainty of Ceres is basically zero
    res = jplhorizons.Horizons(id='Ceres', location='500@10',
                               epochs=2451544.5).elements()[0]

    assert res['targetname'] == "1 Ceres (A801 AA)"
    assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

    assert_quantity_allclose(
        [2451544.500000000, 7.837505574674922E-02, 2.549670145428669E+00,
         1.058336066935565E+01, 8.049436497808115E+01, 7.392278720553115E+01,
         2.451516163103133E+06, 2.141950384425567E-01, 6.069622713669460E+00,
         7.121194154895409E+00, 2.766494289599058E+00, 2.983318433769447E+00,
         1.680711199557247E+03],
        [res['datetime_jd'],
         res['e'], res['q'],
         res['incl'],
         res['Omega'], res['w'],
         res['Tp_jd'],
         res['n'], res['M'],
         res['nu'],
         res['a'], res['Q'],
         res['P']], rtol=1e-3)


def test_elements_vectors(patch_request):
    # check values of Ceres for a given epoch
    # orbital uncertainty of Ceres is basically zero
    res = jplhorizons.Horizons(id='Ceres', location='500@10',
                               epochs=2451544.5).vectors()[0]

    assert res['targetname'] == "1 Ceres (A801 AA)"
    assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

    assert_quantity_allclose(
        [2451544.500000000, -2.377530298472460E+00, 8.007772252240262E-01,
         4.628376138999674E-01, -3.605422185454561E-03, -1.057883338099071E-02,
         3.379790360574805E-04, 1.473392700164538E-02, 2.551100378548960E+00,
         1.007961335136809E-04],
        [res['datetime_jd'],
         res['x'], res['y'], res['z'],
         res['vx'], res['vy'], res['vz'],
         res['lighttime'], res['range'], res['range_rate']], rtol=1e-3)


def test_ephemerides_query_payload():
    obj = jplhorizons.Horizons(id='Halley', id_type='comet_name',
                               location='290',
                               epochs={'start': '2080-01-01',
                                       'stop': '2080-02-01',
                                       'step': '3h'})
    res = obj.ephemerides(airmass_lessthan=1.2, skip_daylight=True,
                          closest_apparition=True,
                          max_hour_angle=10,
                          solar_elongation=(150, 180),
                          get_query_payload=True)

    assert res == OrderedDict([
        ('format', 'text'),
        ('EPHEM_TYPE', 'OBSERVER'),
        ('QUANTITIES', "'1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,"
                       "18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,"
                       "33,34,35,36,37,38,39,40,41,42,43'"),
        ('COMMAND', '"COMNAM=Halley; CAP;"'),
        ('SOLAR_ELONG', '"150,180"'),
        ('LHA_CUTOFF', '10'),
        ('CSV_FORMAT', 'YES'),
        ('CAL_FORMAT', 'BOTH'),
        ('ANG_FORMAT', 'DEG'),
        ('APPARENT', 'AIRLESS'),
        ('REF_SYSTEM', 'ICRF'),
        ('EXTRA_PREC', 'NO'),
        ('CENTER', "'290'"),
        ('START_TIME', '"2080-01-01"'),
        ('STOP_TIME', '"2080-02-01"'),
        ('STEP_SIZE', '"3h"'),
        ('AIRMASS', '1.2'),
        ('SKIP_DAYLT', 'YES')])


def test_ephemerides_query_payload_with_optional_settings():
    """
    Assert that all optional settings are provided at query payload
    """
    obj = jplhorizons.Horizons(id='Halley', id_type='comet_name',
                               location='290',
                               epochs={'start': '2080-01-01',
                                       'stop': '2080-02-01',
                                       'step': '3h'})

    optional_settings = {"R_T_S_ONLY": "TVH", "TIME_DIGITS": "SECONDS"}

    res = obj.ephemerides(airmass_lessthan=1.2, skip_daylight=True,
                          closest_apparition=True,
                          max_hour_angle=10,
                          solar_elongation=(150, 180),
                          get_query_payload=True,
                          optional_settings=optional_settings)

    assert res == OrderedDict([
        ('format', 'text'),
        ('EPHEM_TYPE', 'OBSERVER'),
        ('QUANTITIES', "'1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,"
                       "18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,"
                       "33,34,35,36,37,38,39,40,41,42,43'"),
        ('COMMAND', '"COMNAM=Halley; CAP;"'),
        ('SOLAR_ELONG', '"150,180"'),
        ('LHA_CUTOFF', '10'),
        ('CSV_FORMAT', 'YES'),
        ('CAL_FORMAT', 'BOTH'),
        ('ANG_FORMAT', 'DEG'),
        ('APPARENT', 'AIRLESS'),
        ('REF_SYSTEM', 'ICRF'),
        ('EXTRA_PREC', 'NO'),
        ('CENTER', "'290'"),
        ('START_TIME', '"2080-01-01"'),
        ('STOP_TIME', '"2080-02-01"'),
        ('STEP_SIZE', '"3h"'),
        ('AIRMASS', '1.2'),
        ('SKIP_DAYLT', 'YES')
    ] + list(optional_settings.items()),
    )


def test_elements_query_payload():
    res = (jplhorizons.Horizons(id='Ceres', location='500@10',
                                epochs=2451544.5).elements(
                                    get_query_payload=True))

    assert res == OrderedDict([
        ('format', 'text'),
        ('EPHEM_TYPE', 'ELEMENTS'),
        ('MAKE_EPHEM', 'YES'),
        ('OUT_UNITS', 'AU-D'),
        ('COMMAND', '"Ceres"'),
        ('CENTER', "'500@10'"),
        ('CSV_FORMAT', 'YES'),
        ('ELEM_LABELS', 'YES'),
        ('OBJ_DATA', 'YES'),
        ('REF_SYSTEM', 'ICRF'),
        ('REF_PLANE', 'ECLIPTIC'),
        ('TP_TYPE', 'ABSOLUTE'),
        ('TLIST', '2451544.5')])


def test_vectors_query_payload():
    res = jplhorizons.Horizons(id='Ceres', location='500@10',
                               epochs=2451544.5).vectors(
                                   get_query_payload=True)
    assert res == OrderedDict([
        ('format', 'text'),
        ('EPHEM_TYPE', 'VECTORS'),
        ('OUT_UNITS', 'AU-D'),
        ('COMMAND', '"Ceres"'),
        ('CSV_FORMAT', '"YES"'),
        ('REF_PLANE', 'ECLIPTIC'),
        ('REF_SYSTEM', 'ICRF'),
        ('TP_TYPE', 'ABSOLUTE'),
        ('VEC_LABELS', 'YES'),
        ('VEC_CORR', '"NONE"'),
        ('VEC_DELTA_T', 'NO'),
        ('OBJ_DATA', 'YES'),
        ('CENTER', "'500@10'"),
        ('TLIST', '2451544.5')])


def test_no_H(patch_request):
    """testing missing H value (also applies for G, M1, k1, M2, k2)"""
    res = jplhorizons.Horizons(id='1935 UZ').ephemerides()[0]
    assert 'H' not in res


def test_id_type_deprecation():
    """Test deprecation warnings based on issue 1742.

    https://github.com/astropy/astroquery/pull/2161

    """

    with pytest.warns(AstropyDeprecationWarning):
        jplhorizons.Horizons(id='Ceres', id_type='id')

    with pytest.warns(AstropyDeprecationWarning):
        jplhorizons.Horizons(id='Ceres', id_type='majorbody')


def test_id_geodetic_coords():
    """Test target based on geodetic coordinates.

    From the Horizons manual:

    For example, while 301 specifies the target to be the center of the Moon,
    and Apollo-11 @ 301 specifies the Apollo-11 landing site as target, the
    following:

        g: 348.8, -43.3, 0 @ 301

    specifies an ephemeris for the crater Tycho on the Moon (body 301), at
    geodetic (planetodetic) coordinates 348.8 degrees east longitude, -43.3
    degrees latitude (south), and zero km altitude with respect to the Moon’s
    mean-Earth reference frame and ellipsoid surface.

    """

    target = {
        "lon": 348.8 * u.deg,
        "lat": -43.3 * u.deg,
        "elevation": 0 * u.m,
        "body": 301
    }

    q = jplhorizons.Horizons(id=target)
    for payload in (q.ephemerides(get_query_payload=True),
                    q.vectors(get_query_payload=True),
                    q.elements(get_query_payload=True)):
        assert payload["COMMAND"] == '"g:348.8,-43.3,0.0@301"'


def test_location_topocentric_coords():
    """Test location from topocentric coordinates.

    Similar to `test_id_geodetic_coords`.

    """

    location = {
        "lon": 348.8 * u.deg,
        "lat": -43.3 * u.deg,
        "elevation": 0 * u.m,
        "body": 301
    }

    q = jplhorizons.Horizons(id=399, location=location)
    for payload in (q.ephemerides(get_query_payload=True),
                    q.vectors(get_query_payload=True)):
        assert payload["CENTER"] == 'coord@301'
        assert payload["COORD_TYPE"] == "GEODETIC"
        assert payload["SITE_COORD"] == "'348.8,-43.3,0.0'"

    # not allowed for elements
    with pytest.raises(ValueError):
        q.elements(get_query_payload=True)
