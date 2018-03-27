# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths = [os.path.join('data', '*.dat'),
             os.path.join('data', '*.xml'),
             os.path.join('data', '*.csv'),
             os.path.join('data', '*.xml.gz')]
    return {'astroquery.open_exoplanet_catalogue.tests': paths}
