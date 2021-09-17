# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():

    paths_test = [os.path.join('data', 'CO.data')]
    paths_data = [os.path.join('data', 'catdir.cat')]

    return {'astroquery.linelists.cdms.tests': paths_test,
            'astroquery.linelists.cdms': paths_data, }
