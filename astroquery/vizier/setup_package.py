# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

def get_package_data():
    paths_test = [os.path.join('data', 'viz.xml')]

    paths_core = [os.path.join('data', 'inverse_dict.json'),
                  os.path.join('data', 'keywords_dict.json')]

    return {
            'astroquery.vizier.tests': paths_test,
            'astroquery.vizier': paths_core
           }
