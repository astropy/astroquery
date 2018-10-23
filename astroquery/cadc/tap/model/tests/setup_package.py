# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
from __future__ import absolute_import

import os

def get_package_data():
    paths = [os.path.join('data', '*.vot')
             ]
    return {'astroquery.cadc.tap.model.tests': paths}
