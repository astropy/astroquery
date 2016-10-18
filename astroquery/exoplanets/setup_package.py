# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():

    paths_core = [os.path.join('data', '*.json')]

    return {'astroquery.exoplanets': paths_core}
