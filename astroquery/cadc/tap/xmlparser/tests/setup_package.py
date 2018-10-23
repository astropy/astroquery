# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
from __future__ import absolute_import

import os

def get_package_data():
    paths = [os.path.join('data', '*.data'),
            os.path.join('data', '*.xml')
             ]
    return {'astroquery.cadc.tap.xmlparser.tests': paths}
