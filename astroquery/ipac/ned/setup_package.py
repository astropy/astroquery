# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths_core = [os.path.join('data', 'keywords_dict.json'),
                  ]

    paths_test = [os.path.join('data', '*.xml'),
                  os.path.join('data', '*.fits'),
                  os.path.join('data', '*.html'),
                  ]

    return {'astroquery.ipac.ned': paths_core,
            'astroquery.ipac.ned.tests': paths_test,
            }
