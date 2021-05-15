# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths = [os.path.join('data', '*.dat')]  # etc, add other extensions

    return {'astroquery.jplsbdb.tests': paths,
            'astroquery.solarsystem.jpl.sbdb': paths}
