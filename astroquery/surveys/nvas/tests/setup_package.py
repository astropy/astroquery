# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths_test = [os.path.join('data', '*.imfits'),
                  os.path.join('data', '*.html')]

    return {'astroquery.nvas.tests': paths_test}
