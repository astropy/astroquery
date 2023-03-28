# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
========================
XMM-Newton Setup Package
========================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""


import os


# setup paths to the test data
# can specify a single file or a list of files
def get_package_data():
    paths = [os.path.join('data', '*.tar'),
             os.path.join('data', '*.xml'),
             os.path.join('data', '*.ini')
             ]  # etc, add other extensions
    # you can also enlist files individually by names
    # finally construct and return a dict for the sub module
    return {'astroquery.esa.xmm_newton.tests': paths}
