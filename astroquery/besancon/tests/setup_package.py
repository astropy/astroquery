# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os


def get_package_data():
    paths = [os.path.join('data', '*.txt'),
             os.path.join('data', '*.resu'),
             ]
    return {'astroquery.besancon.tests': paths}
