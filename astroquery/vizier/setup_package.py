# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os


def get_package_data():
    paths_test = [os.path.join('data', 'viz.xml'),
                  os.path.join('data', 'kang2010.xml'),
                  os.path.join('data', 'afgl2591_iram.xml'),
                  os.path.join('data', 'find_kangapj70683.xml'),
                  ]

    paths_core = [os.path.join('data', 'inverse_dict.json'),
                  os.path.join('data', 'keywords_dict.json')]

    return {'astroquery.vizier.tests': paths_test,
            'astroquery.vizier': paths_core,
            }
