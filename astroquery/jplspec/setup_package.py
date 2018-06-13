# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os

def get_package_data():
    paths_test1 = [os.path.join('data', 'CO.data')]
    paths_test2 = [os.path.join('data', 'CO_6.data')]
    paths_test3 = [os.path.join('data', 'multi.data')]
    paths_data = [os.path.join('data', 'catdir.cat')]

    return {'astroquery.jplspec.tests': paths_test1,
            'astroquery.jplspec.tests': paths_test2,
            'astroquery.jplspec.tests': paths_test3,
            'astroquery.jplspec': paths_data, }
