# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths_test = [os.path.join('data', '*.txt')]

    return {'astroquery.ogle.tests': paths_test}
