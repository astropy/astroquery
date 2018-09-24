# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
# setup paths to the test data
# can specify a single file or a list of files


def get_package_data():
    paths = [os.path.join('data', '*.fit')] + [os.path.join('data', '*.fit.gz')]
    # finally construct and return a dict for the sub module
    return {'astroquery.astrometry_net.tests': paths}
