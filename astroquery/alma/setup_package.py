# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    paths = [os.path.join('data', 'cycle0_delivery_asdm_mapping.txt'),
             ]
    return {'astroquery.alma': paths}
