# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Hanno Rein 2013
# hanno@hanno-rein.de

from ... import open_exoplanet_catalogue as oec
from astropy.tests.helper import pytest
from xml.etree import ElementTree as ET

def test_function():

    cata = oec.get_catalogue()
    for planet in cata.findall(".//planet[name='Kepler-67 b']"):
        kepler67b = planet
    assert kepler67b.findtext('name') == "Kepler-67 b"
    assert kepler67b.findtext('discoverymethod') == "transit"

    for sys in cata.findall(".//system[name='Kepler-67']"):
        kepler67 = sys
    assert kepler67.findvalue('distance') == 1107
