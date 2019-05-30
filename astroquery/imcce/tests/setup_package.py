# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths = [os.path.join('data', '*.dat')]  # etc, add other extensions

    return {'astroquery.imcce.tests': paths}
