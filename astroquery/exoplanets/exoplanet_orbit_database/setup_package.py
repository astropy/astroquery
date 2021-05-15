# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():

    paths_core = [os.path.join('data', '*.json'),
                  os.path.join('tests', 'data', '*.csv')]

    return {'astroquery.exoplanet_orbit_database': paths_core}
