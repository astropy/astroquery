# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

import os


# setup paths to the test data
# can specify a single file or a list of files
def get_package_data():
    paths = [os.path.join('data', '*.vot'),
             os.path.join('data', '*.xml'),
             os.path.join('data', '*.csv'),
             os.path.join('data', '*.ecsv'),
             os.path.join('data', '*.json'),
             os.path.join('data', '*.fits'),
             os.path.join('data', '*.fits.gz'),
             os.path.join('data/test_upload_file', '*.vot'),
             os.path.join('data/test_upload_file', '*.xml'),
             os.path.join('data/test_upload_file', '*.csv'),
             os.path.join('data/test_upload_file', '*.ecsv'),
             os.path.join('data/test_upload_file', '*.json'),
             os.path.join('data/test_upload_file', '*.fits'),
             ]  # etc, add other extensions
    # you can also enlist files individually by names
    # finally construct and return a dict for the sub module
    return {'astroquery.utils.tap.tests': paths}
