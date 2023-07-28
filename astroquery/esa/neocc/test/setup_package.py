"""
This file only needs the get_package_data() function, which will tell
setup.py to include the relevant files when installing.
"""

import os

def get_package_data():
    paths_test = [os.path.join('data', '*.lst')]

    return {'astroquery.esa.neocc.test': paths_test}
