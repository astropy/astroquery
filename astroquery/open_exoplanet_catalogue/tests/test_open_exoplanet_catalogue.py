# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Hanno Rein 2013
# hanno@hanno-rein.de

from ... import open_exoplanet_catalogue as oec

def test_simple():
    # Find the Kepler-67 system and print the raw XML data.
    xml = oec.query_system_xml('Kepler-67') # Return value is an XML string.
    print(xml)


    # Find 'Kepler-67 b'.
    kepler67b = oec.query_planet('Kepler-67 b') # Return value is a python dictionary.
    # Print radius and period.
    print ("Period of Kepler-67 b:\t %s \t [days]"% kepler67b['period'])
    print ("Radius of Kepler-67 b:\t %s \t [R_Jupiter]"% kepler67b['radius'])


