from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np
import astropy.units as u
from astropy.tests.helper import assert_quantity_allclose
from astropy.tests.helper import remote_data

from ..exoplanets_org import PlanetParams, exoplanets_table, parameter_units

@remote_data
def test_exoplanets_table():
    table = exoplanets_table()

    # Number of columns expected as of Oct 8, 2016
    assert len(table) >= 315

    # Check some planets are in the table
    expected_planets = ['HD 189733 b', 'Kepler-186 f', 'TRAPPIST-1 b',
                        'HD 209458 b', 'Kepler-62 f', 'GJ 1214 b']

    for planet in expected_planets:
        assert planet in table['NAME']

def test_parameter_units():
    param_units = parameter_units()

    assert param_units['A'] == u.Unit('AU')
    assert param_units['PER'] == u.Unit('day')
    assert param_units['RR'] == u.Unit('')
    assert param_units['R'] == u.Unit('jupiterRad')
    assert param_units['RA'] == u.Unit('hourangle')
    assert param_units['DEC'] == u.Unit('degree')

@remote_data
def test_hd189733b():
    # Testing intentionally un-stripped string:
    params = PlanetParams('HD 209458 b ')

    assert params.name == 'HD 209458 b'
    assert_quantity_allclose(params.per, 3.52474859 * u.day, atol=1e-5 * u.day)
    assert_quantity_allclose(params.depth, u.Quantity(0.014607),
                             atol=u.Quantity(1e-5))

    assert not params.binary
    assert not params.microlensing
    assert params.transit


