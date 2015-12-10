# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import os


# This is to figure out the astroquery version, rather than using Astropy's
from . import version


# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import *

try:
    packagename = os.path.basename(os.path.dirname(__file__))
    TESTED_VERSIONS[packagename] = version.version
except NameError:
    pass

# Add astropy to test header information and remove unused packages.
# Pytest header customisation was introduced in astropy 1.0.

try:
    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['APLpy'] = 'APLpy'
    PYTEST_HEADER_MODULES['pyregion'] = 'pyregion'
    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
except NameError:
    pass
