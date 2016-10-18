from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from astropy.tests.helper import remote_data

from ..planet_params import PlanetParams
from ..exoplanets_org import query_exoplanets_org_catalog, exoplanets_org_units


@remote_data
def test_exoplanets_table():
    table = query_exoplanets_org_catalog()

    # Number of columns expected as of Oct 8, 2016
    assert len(table) >= 315

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet in table['NAME']


def test_parameter_units():
    param_units = exoplanets_org_units()

    assert param_units['A'] == u.Unit('AU')
    assert param_units['PER'] == u.Unit('day')
    assert param_units['RR'] == u.Unit('')
    assert param_units['R'] == u.Unit('R_jup')
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
    assert_quantity_allclose(params.r, 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))

    assert not params.binary
    assert not params.microlensing
    assert params.transit


@remote_data
def test_hd209458b_exoplanets_archive():
    # Testing intentionally un-stripped string:
    params = PlanetParams.from_exoplanet_archive('HD 209458 b ')

    assert params.pl_hostname == 'HD 209458'
    assert_quantity_allclose(params.pl_orbper, 3.52474859 * u.day,
                             atol=1e-5 * u.day)
    assert_quantity_allclose(params.pl_radj, 1.320 * u.Unit('R_jup'),
                             atol=0.1 * u.Unit('R_jup'))

    assert not params.pl_kepflag
    assert not params.pl_ttvflag


