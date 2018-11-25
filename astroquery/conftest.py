# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import (PYTEST_HEADER_MODULES,
                                          enable_deprecations_as_exceptions,
                                          TESTED_VERSIONS)

try:
    packagename = os.path.basename(os.path.dirname(__file__))
    TESTED_VERSIONS[packagename] = version.version
except NameError:
    pass

# Add astropy to test header information and remove unused packages.
# Pytest header customisation was introduced in astropy 1.0.

try:
    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['APLpy'] = 'aplpy'
    PYTEST_HEADER_MODULES['pyregion'] = 'pyregion'
    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
except (NameError, KeyError):
    pass

# Uncomment the following line to treat all DeprecationWarnings as
# exceptions
#
# The workaround can be removed once pyopenssl 1.7.20+ is out.
import astropy
if int(astropy.__version__[0]) > 1:
    # The warnings_to_ignore_by_pyver parameter was added in astropy 2.0
    enable_deprecations_as_exceptions(modules_to_ignore_on_import=['requests'])

# This is to figure out the affiliated package version, rather than
# using Astropy's
try:
    from .version import version
except ImportError:
    version = 'dev'

packagename = os.path.basename(os.path.dirname(__file__))
TESTED_VERSIONS[packagename] = version
