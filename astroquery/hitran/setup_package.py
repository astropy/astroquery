# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths_data = [os.path.join('data', 'readme.txt')]
    paths_test = [os.path.join('data', 'H2O.data')]

    return {'astroquery.hitran': paths_data,
            'astroquery.hitran.tests': paths_test,
            }
