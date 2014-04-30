# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Hanno Rein 2013
# hanno@hanno-rein.de

from ... import open_exoplanet_catalogue as oec
from astropy.tests.helper import pytest
from xml.etree import ElementTree as ET

class CatalogueOpeningError(Exception):
    pass


def test_simple():


    kepler67b = oec.query_planet('Kepler-67 b') # Return value is a python dictionary.
    print(kepler67b)

def get_a_system():

    xml = oec.query_system_xml('Kepler-67') # Return value is an XML string.
    return xml

def test_function():
    with pytest.raises(TypeError):
        xml = oec.query_system_xml("krypton") # testing imaginary system

    assert type(get_a_system()) == type("str")

    kepler67b = oec.query_planet('Kepler-67 b') # Return value is a python dictionary.
    assert kepler67b['name'] == "Kepler-67 b"
    assert kepler67b['discoverymethod'] == "transit"
