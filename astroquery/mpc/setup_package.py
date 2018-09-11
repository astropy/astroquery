# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os


def get_package_data():
    paths_test = [os.path.join('data', 'comet_object_C20112S1.json'),
                  os.path.join('data', '*.html')]

    return {'astroquery.mpc.tests': paths_test}
