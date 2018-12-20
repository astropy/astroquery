from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose, remote_data, pytest
from astropy.utils import minversion
from astropy.coordinates import SkyCoord

from ...nasa_exoplanet_archive import NasaExoplanetArchive

APY_LT12 = not minversion('astropy', '1.2')
LOCAL_TABLE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                'data', 'nasa_exoplanet_archive.csv')


@remote_data
def test_exoplanet_archive_table():
    table = NasaExoplanetArchive.get_confirmed_planets_table(cache=False)

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet.lower().replace(" ", "") in table['NAME_LOWERCASE']

    assert 'pl_trandep' not in table.colnames


@remote_data
def test_hd209458b_exoplanet_archive():
    # Testing intentionally un-stripped string, no spaced:
    params = NasaExoplanetArchive.query_planet('HD209458b ')

    assert str(params['pl_hostname']) == 'HD 209458'
    assert_quantity_allclose(params['pl_orbper'], 3.52474859 * u.day,
                             atol=1e-5 * u.day)

    assert not params['pl_kepflag']
    assert not params['pl_ttvflag']


@remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_archive_apy_lt12():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_planet('HD 209458 b ')
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@remote_data
@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanets_archive_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_planet('HD 209458 b ')
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


@remote_data
def test_hd209458b_exoplanet_archive_coords():
    params = NasaExoplanetArchive.query_planet('HD 209458 b ')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec


def test_hd209458b_exoplanet_archive():
    # Testing intentionally un-stripped string, no spaced:
    params = NasaExoplanetArchive.query_planet('HD209458b ',
                                               table_path=LOCAL_TABLE_PATH)

    assert str(params['pl_hostname']) == 'HD 209458'
    assert_quantity_allclose(params['pl_orbper'], 3.52474859 * u.day,
                             atol=1e-5 * u.day)

    assert not params['pl_kepflag']
    assert not params['pl_ttvflag']

    # Default columns don't include planet columns
    assert 'pl_tranflag' not in params.columns


@remote_data
def test_exoplanet_archive_query_plant_all_columns():
    # Same test as above but get all the columns
    params = NasaExoplanetArchive.query_planet('HD 209458 b ', cache=False, all_columns=True)

    # Check non-default column in table
    assert 'pl_tranflag' in params.columns


@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_archive_apy_lt12():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_planet('HD 209458 b ',
                                               table_path=LOCAL_TABLE_PATH)
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanets_archive_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_planet('HD 209458 b ',
                                                   table_path=LOCAL_TABLE_PATH)
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


def test_hd209458b_exoplanet_archive_coords():
    params = NasaExoplanetArchive.query_planet('HD 209458 b ',
                                               table_path=LOCAL_TABLE_PATH)
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec


@remote_data
def test_exoplanet_archive_table_all_columns():
    table = NasaExoplanetArchive.get_confirmed_planets_table(cache=False, all_columns=True)

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet.lower().replace(" ", "") in table['NAME_LOWERCASE']

    assert 'pl_trandep' in table.colnames
