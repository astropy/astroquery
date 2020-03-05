from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import pytest
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from astropy.utils import minversion
from astropy.coordinates import SkyCoord

from ...nasa_exoplanet_archive import NasaExoplanetArchive

APY_LT12 = not minversion('astropy', '1.2')
LOCAL_TABLE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                'data', 'nasa_exoplanet_archive.csv')


@pytest.mark.remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_archive_apy_lt12():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_planet('HD 209458 b ')
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanets_archive_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_planet('HD 209458 b ')
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
def test_hd209458b_exoplanet_archive_coords():
    params = NasaExoplanetArchive.query_planet('HD 209458 b ')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'][0].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec


@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_archive_apy_lt12_local():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_planet('HD 209458 b ', table_path=LOCAL_TABLE_PATH)
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.skipif('not APY_LT12')
def test_hd209458b_exoplanets_archive_apy_gt12_local():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_planet('HD 209458 b ', table_path=LOCAL_TABLE_PATH)
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


def test_hd209458b_exoplanet_archive_coords_local():
    params = NasaExoplanetArchive.query_planet('HD 209458 b ', table_path=LOCAL_TABLE_PATH)
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'][0].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec


@pytest.mark.remote_data
def test_hd209458_stellar_exoplanet_archive():
    # Testing intentionally un-stripped string, no spaced:
    params = NasaExoplanetArchive.query_star('HD 209458')

    assert len(params) == 1
    assert str(params['pl_name'][0]) == 'HD 209458 b'
    assert_quantity_allclose(params['pl_orbper'], 3.52474859 * u.day,
                             atol=1e-5 * u.day)

    assert not params['pl_kepflag']
    assert not params['pl_ttvflag']


@pytest.mark.remote_data
def test_hd136352_stellar_exoplanet_archive():
    # Check for all planets around specific star
    params = NasaExoplanetArchive.query_star('HD 136352')

    assert len(params) == 3
    expected_planets = ['HD 136352 b', 'HD 136352 c', 'HD 136352 d']

    for planet in expected_planets:
        assert planet in params['pl_name']

    assert 'pl_trandep' not in params.colnames


@pytest.mark.remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458_stellar_exoplanets_archive_apy_lt12():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_star('HD 209458')
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
@pytest.mark.skipif('not APY_LT12')
def test_hd209458_stellar_exoplanets_archive_apy_gt12():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_star('HD 209458')
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
def test_hd209458_exoplanet_archive_coords():
    params = NasaExoplanetArchive.query_star('HD 209458')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'][0].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec


@pytest.mark.remote_data
def test_exoplanet_archive_query_all_columns():
    # Get all the columns from planet query
    params = NasaExoplanetArchive.query_planet('HD 209458 b ', cache=False, all_columns=True)

    # Check non-default column in table
    assert 'pl_tranflag' in params.columns


@pytest.mark.remote_data
def test_stellar_exoplanet_archive_query_all_columns():
    # Get all the columns from star query
    params = NasaExoplanetArchive.query_star('HD 209458 b ', cache=False, all_columns=True)

    # Check non-default column in table
    assert 'pl_tranflag' in params.columns


@pytest.mark.remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458_stellar_exoplanets_archive_apy_lt12_local():
    # Testing intentionally un-stripped string:
    params = NasaExoplanetArchive.query_star('HD 209458', table_path=LOCAL_TABLE_PATH)
    assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
@pytest.mark.skipif('not APY_LT12')
def test_hd209458_stellar_exoplanets_archive_apy_gt12_local():
    # Testing intentionally un-stripped string:
    with pytest.raises(ValueError):
        params = NasaExoplanetArchive.query_star('HD 209458', table_path=LOCAL_TABLE_PATH)
        assert_quantity_allclose(params['pl_radj'], 1.320 * u.Unit('R_jup'),
                                 atol=0.1 * u.Unit('R_jup'))


@pytest.mark.remote_data
def test_hd209458_exoplanet_archive_coords_local():
    params = NasaExoplanetArchive.query_star('HD 209458', table_path=LOCAL_TABLE_PATH)
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params['sky_coord'][0].separation(simbad_coords)

    assert abs(sep) < 5 * u.arcsec
