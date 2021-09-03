# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():

    paths_test = [os.path.join('data', 'CO.data')]
    paths_data = [os.path.join('data', 'catdir.cat')]

    return {'astroquery.cdms.tests': paths_test,
            'astroquery.cdms': paths_data, }
