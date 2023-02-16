# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from ... import open_exoplanet_catalogue as oec


# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_function():
    # use local version of database
    cata = oec.get_catalogue(filepath=data_path('systems.xml.gz'))

    assert len(cata.findall('.//planet')) > 0

    for planet in cata.findall(".//planet"):
        if oec.findvalue(planet, 'name') == "Kepler-67 b":
            kepler67b = planet
    assert oec.findvalue(kepler67b, 'name') == "Kepler-67 b"
    assert oec.findvalue(kepler67b, 'discoverymethod') == "transit"
