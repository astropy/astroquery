# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os


def get_package_data():
    return {'astroquery.xmatch.tests': [os.path.join('data', '*.csv')]}
