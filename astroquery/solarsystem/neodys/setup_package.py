# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os


def get_package_data():
    paths_test = [os.path.join('data', '2018vp1_eq0.txt')]

    return {'astroquery.solarsystem.neodys.tests': paths_test}
