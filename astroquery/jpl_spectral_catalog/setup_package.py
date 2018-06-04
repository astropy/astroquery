

from __future__ import absolute_import

import os

def get_package_data():
    paths_test = [os.path.join('data','CO.data')]

    return {'astroquery.jpl_spectral_catalog.tests' : paths_test, }
