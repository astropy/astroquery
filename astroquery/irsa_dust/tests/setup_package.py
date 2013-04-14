# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

def get_package_data():
    paths = [os.path.join('t', '*.xml'),
             os.path.join('t', '*.fits'),
             os.path.join('t', '*.tbl'),
             os.path.join('t', '*.txt')]
    return { 'astroquery.irsa_dust.tests': paths}
