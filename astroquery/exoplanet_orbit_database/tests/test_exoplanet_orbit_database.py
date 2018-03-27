from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose, remote_data, pytest
from astropy.utils import minversion
from astropy.coordinates import SkyCoord

from ...exoplanet_orbit_database import ExoplanetOrbitDatabase

APY_LT12 = not minversion('astropy', '1.2')
LOCAL_TABLE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                'data', 'exoplanet_orbit_database.csv')


@remote_data
def test_exoplanet_orbit_database_table():
    table = ExoplanetOrbitDatabase.get_table()

    # Number of columns expected as of Oct 8, 2016
    assert len(table) >= 315

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet.lower().replace(" ", "") in table['NAME_LOWERCASE']


def test_parameter_units():
    param_units = ExoplanetOrbitDatabase.param_units

    assert param_units['A'] == u.Unit('AU')
    assert param_units['PER'] == u.Unit('day')
    assert param_units['RR'] == u.Unit('')
    assert param_units['RA'] == u.Unit('hourangle')
    assert param_units['DEC'] == u.Unit('degree')


@remote_data
def test_hd209458b_exoplanet_orbit_database():
    # Testing intentionally un-stripped string:
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ')

    assert params['NAME'] == 'HD 209458 b'
    assert_quantity_allclose(params['PER'], 3.52474859 * u.day,
                             atol=1e-5 * u.day)
    assert_quantity_allclose(params['DEPTH'], u.Quantity(0.014607),
                             atol=u.Quantity(1e-5))

    assert not params['BINARY']
    assert not params['MICROLENSING']
    assert params['TRANSIT']


@remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanet_orbit_database_apy_lt12():
    # Testing intentionally un-stripped string:
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ')
    assert_quantity_allclose(params["R"], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@remote_data
@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanet_orbit_database_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ')
        assert_quantity_allclose(params['R'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


@remote_data
def test_hd209458b_exoplanet_orbit_database_coords():
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'].separation(simbad_coords)

    print(sep, type(sep))
    assert abs(sep) < 5 * u.arcsec


def test_hd209458b_exoplanet_orbit_database():
    # Testing intentionally un-stripped string:
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ',
                                                 table_path=LOCAL_TABLE_PATH)

    assert params['NAME'] == 'HD 209458 b'
    assert_quantity_allclose(params['PER'], 3.52474859 * u.day,
                             atol=1e-5 * u.day)
    assert_quantity_allclose(params['DEPTH'], u.Quantity(0.014607),
                             atol=u.Quantity(1e-5))

    assert not params['BINARY']
    assert not params['MICROLENSING']
    assert params['TRANSIT']


@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanet_orbit_database_apy_lt12():
    # Testing intentionally un-stripped string:
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ',
                                                 table_path=LOCAL_TABLE_PATH)
    assert_quantity_allclose(params["R"], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanet_orbit_database_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ',
                                                     table_path=LOCAL_TABLE_PATH)
        assert_quantity_allclose(params['R'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


def test_hd209458b_exoplanet_orbit_database_coords():
    params = ExoplanetOrbitDatabase.query_planet('HD 209458 b ',
                                                 table_path=LOCAL_TABLE_PATH)
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'].separation(simbad_coords)

    print(sep, type(sep))
    assert abs(sep) < 5 * u.arcsec
