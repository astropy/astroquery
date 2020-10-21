# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths_test = [os.path.join('data', 'CO_colons.csv'),
                  ]

    paths_data = [os.path.join('data', '*.json'),
                  ]

    return {'astroquery.splatalogue.tests': paths_test,
            'astroquery.splatalogue': paths_data,
            }
