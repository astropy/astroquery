

from __future__ import absolute_import

import os

def get_package_data():
    paths_test = [os.path.join('data','CO.data')]

    return {'astroquery.jplspec.tests' : paths_test, }
