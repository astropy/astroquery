# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


# setup paths to the test data
# can specify a single file or a list of files
def get_package_data():
    paths = [os.path.join('data', '*.vot'),
             os.path.join('data', '*.xml'),
             os.path.join('data', '*.pem'),
             os.path.join('data', '*.fits'),
             ]  # etc, add other extensions
    # you can also enlist files individually by names
    # finally construct and return a dict for the sub module
    return {'astroquery.cadc.tests': paths}
