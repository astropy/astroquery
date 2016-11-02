# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths_data = [os.path.join('data', 'readme.txt'),
                  ]

    return {'astroquery.hitran': paths_data,
            }
