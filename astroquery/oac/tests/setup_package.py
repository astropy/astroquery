# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    # All data as text files to test http response processing
    paths = [os.path.join('data', '*.txt')]

    return {'astroquery.oac.tests': paths}
