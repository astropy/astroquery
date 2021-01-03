# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from pytest_astropy_header.display import (PYTEST_HEADER_MODULES,
                                           TESTED_VERSIONS)

from astropy.tests.helper import enable_deprecations_as_exceptions


def pytest_configure(config):
    config.option.astropy_header = True


# Add astropy to test header information and remove unused packages.
# Pytest header customisation was introduced in astropy 1.0.

try:
    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['APLpy'] = 'aplpy'
    PYTEST_HEADER_MODULES['pyregion'] = 'pyregion'
    PYTEST_HEADER_MODULES['pyVO'] = 'pyvo'
    # keyring doesn't provide __version__ any more
    # PYTEST_HEADER_MODULES['keyring'] = 'keyring'
    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
    del PYTEST_HEADER_MODULES['Pandas']
except (NameError, KeyError):
    pass

# ignoring pyvo can be removed once we require >0.9.3
enable_deprecations_as_exceptions(include_astropy_deprecations=False,
                                  warnings_to_ignore_entire_module=['pyregion', 'html5lib'],)

# add '_testrun' to the version name so that the user-agent indicates that
# it's being run in a test
from . import version
version.version += '_testrun'


# This is to figure out the affiliated package version, rather than
# using Astropy's
from .version import version, astropy_helpers_version


packagename = os.path.basename(os.path.dirname(__file__))
TESTED_VERSIONS[packagename] = version
TESTED_VERSIONS['astropy_helpers'] = astropy_helpers_version
