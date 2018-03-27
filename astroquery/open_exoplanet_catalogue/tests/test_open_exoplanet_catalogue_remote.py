# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
from ... import open_exoplanet_catalogue as oec


@remote_data
def test_function():

    cata = oec.get_catalogue()
    for planet in cata.findall(".//planet"):
        if oec.findvalue(planet, 'name') == "Kepler-67 b":
            kepler67b = planet
    assert oec.findvalue(kepler67b, 'name') == "Kepler-67 b"
    assert oec.findvalue(kepler67b, 'discoverymethod') == "transit"
