# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Hanno Rein 2013
# hanno@hanno-rein.de

from ... import open_exoplanet_catalogue as oec
from astropy.tests.helper import pytest
from xml.etree import ElementTree as ET


def get_a_system():

    sys = oec.query_system_to_obj('Kepler-67') # Return value is a System object 
    return sys 

def test_function():
    with pytest.raises(TypeError):
        xml = oec.query_system_xml("krypton") # testing imaginary system

    kepler67b = oec.query_planet('Kepler-67 b') # Return value is a python dictionary.
    assert kepler67b['name'] == "Kepler-67 b"
    assert kepler67b['discoverymethod'] == "transit"

    kepler67 = get_a_system()
    assert kepler67.distance == 1107

    kepler67bsys = oec.query_planet_to_obj('Kepler-67 b')
    assert kepler67bsys.name[0] == "Kepler-67 b"
    assert kepler67bsys.discoverymethod == "transit"
