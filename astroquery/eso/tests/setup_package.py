# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths = [os.path.join('data', '*.pickle'),
             os.path.join('data', '*.html'),
             os.path.join('data', '*.tbl'),
             os.path.join('data', '*.xml'),
             os.path.join('data', '*.json'),
             os.path.join('data', '*.fits*')
             ]
    return {'astroquery.eso.tests': paths}
