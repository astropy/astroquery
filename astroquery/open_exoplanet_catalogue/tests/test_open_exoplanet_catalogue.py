# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ... import open_exoplanet_catalogue as oec

def test_simple():
    # Find the Kepler-67 system
    xml = oec.QuerySystem('Kepler-67')
    print(xml)

