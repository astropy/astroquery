# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.tests.helper import pytest, remote_data
from .utils import turn_off_internet

# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import *


# pytest magic:
# http://pytest.org/latest/plugins.html#_pytest.hookspec.pytest_configure
# use pytest.set_trace() to interactively inspect config's features
def pytest_configure(config):
    if config.getoption('remote_data'):
        pass
    else:
        turn_off_internet(verbose=config.option.verbose)

    try:
        from astropy.tests.pytest_plugins import pytest_configure

        pytest_configure(config)
    except ImportError:
        # assume astropy v<0.3
        pass
