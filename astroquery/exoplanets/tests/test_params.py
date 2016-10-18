from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose, remote_data, pytest
from astropy.utils import minversion
from astropy.coordinates import SkyCoord

from ..planet_params import PlanetParams
from ..exoplanets_org import query_exoplanets_org_catalog, exoplanets_org_units
from ..exoplanet_archive import query_exoplanet_archive_catalog

APY_LT12 = not minversion('astropy', '1.2')


@remote_data
def test_exoplanets_org_table():
    table = query_exoplanets_org_catalog()

    # Number of columns expected as of Oct 8, 2016
    assert len(table) >= 315

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet.lower() in table['NAME_LOWERCASE']

@remote_data
def test_exoplanet_archive_table():
    table = query_exoplanet_archive_catalog()

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet.lower() in table['NAME_LOWERCASE']


def test_parameter_units():
    param_units = exoplanets_org_units()

    assert param_units['A'] == u.Unit('AU')
    assert param_units['PER'] == u.Unit('day')
    assert param_units['RR'] == u.Unit('')
    assert param_units['RA'] == u.Unit('hourangle')
    assert param_units['DEC'] == u.Unit('degree')


@remote_data
def test_hd209458b_exoplanets_org():
    # Testing intentionally un-stripped string:
    params = PlanetParams.from_exoplanets_org('HD 209458 b ')

    assert params.name == 'HD 209458 b'
    assert_quantity_allclose(params.per, 3.52474859 * u.day, atol=1e-5 * u.day)
    assert_quantity_allclose(params.depth, u.Quantity(0.014607),
                             atol=u.Quantity(1e-5))

    assert not params.binary
    assert not params.microlensing
    assert params.transit

@remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_org_apy_lt12():
    # Testing intentionally un-stripped string:
    params = PlanetParams.from_exoplanets_org('HD 209458 b ')
    assert_quantity_allclose(params.r, 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@remote_data
def test_hd209458b_exoplanet_archive():
    # Testing intentionally un-stripped string:
    params = PlanetParams.from_exoplanet_archive('HD 209458 b ')

    assert params.pl_hostname == 'HD 209458'
    assert_quantity_allclose(params.pl_orbper, 3.52474859 * u.day,
                             atol=1e-5 * u.day)

    assert not params.pl_kepflag
    assert not params.pl_ttvflag


@remote_data
@pytest.mark.skipif('APY_LT12')
def test_hd209458b_exoplanets_archive_apy_lt12():
    # Testing intentionally un-stripped string:
    params = PlanetParams.from_exoplanet_archive('HD 209458 b ')
    assert_quantity_allclose(params.pl_radj, 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))


@remote_data
def test_hd209458b_exoplanet_archive_coords():
    params = PlanetParams.from_exoplanet_archive('HD 209458 b ')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params.coord.separation(simbad_coords)

    assert abs(sep) < 1 * u.arcsec

@remote_data
def test_hd209458b_exoplanets_org_coords():
    params = PlanetParams.from_exoplanets_org('HD 209458 b ')
    simbad_coords = SkyCoord(ra='22h03m10.77207s', dec='+18d53m03.5430s')

    sep = params.coord.separation(simbad_coords)

    assert abs(sep) < 1 * u.arcsec

