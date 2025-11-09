# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():

    paths_test = [os.path.join('data', 'CO.data'),
                  os.path.join('data', 'CO_6.data'),
                  os.path.join('data', 'multi.data')]
    paths_data = [os.path.join('data', 'catdir.cat')]

    return {'astroquery.linelists.jplspec.tests': paths_test,
            'astroquery.linelists.jplspec': paths_data, }
