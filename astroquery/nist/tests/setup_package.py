# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths_test = [os.path.join('data', '*.html')]
    return {'astroquery.nist.tests': paths_test}
