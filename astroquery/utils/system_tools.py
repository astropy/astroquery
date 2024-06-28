# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os


# If there is an update issue of astropy#2793 that got merged, this should
# be replaced with it.

def in_ipynb():
    return 'JPY_PARENT_PID' in os.environ
