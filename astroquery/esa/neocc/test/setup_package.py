"""
This file only needs the get_package_data() function, which will tell
setup.py to include the relevant files when installing.
"""

import os


def get_package_data():
    paths_test = [os.path.join('data', '*.lst'),
                  os.path.join('data', '*.eph'),
                  os.path.join('data', '*.done'),
                  os.path.join('data', 'esa_*'),
                  os.path.join('data', '*.txt'),
                  os.path.join('data', 'past_impactors_list'),
                  os.path.join('data', '*.cat'),
                  os.path.join('data', '*.risk'),
                  os.path.join('data', '*.clolin'),
                  os.path.join('data', '*.phypro'),
                  os.path.join('data', '*.rwo'),
                  os.path.join('data', '*.ke*'),
                  os.path.join('data', '*.eq*'),
                  os.path.join('data', '*.csv*')]

    return {'astroquery.esa.neocc.test': paths_test}
