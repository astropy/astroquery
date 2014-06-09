import os
from xml.etree import ElementTree as ET
from astropy.tests.helper import pytest
from ...utils.testing_tools import MockResponse
from ... import open_exoplanet_catalogue as oec


# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

def test_function(patch_urlopen):
    cata = oec.get_catalogue(data_path('systems.xml.gz')) # use local version of database
    assert len(cata.findall('.//planet')) > 0

    for planet in cata.findall(".//planet[name]"):
        if oec.findvalue(planet, 'name') == "Kepler-67 b":
            kepler67b = planet
    assert oec.findvalue(kepler67b, 'name') == "Kepler-67 b"
    assert oec.findvalue(kepler67b, 'discoverymethod') == "transit"

    kepler67 = cata.find(".//system[name]")
    for star in cata.findall(".//planet[name]"):
        if oec.findvalue(star, 'name') == "Kepler-67":
            kepler67 = star 
    assert oec.findvalue(kepler67, 'distance') == "1107"
