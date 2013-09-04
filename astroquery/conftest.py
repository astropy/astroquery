# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from .utils import turn_off_internet,turn_on_internet

from astropy.tests.helper import pytest, remote_data

# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import *

def pytest_configure(config):
    if config.getoption('remote_data'):
        turn_on_internet(verbose=config.option.verbose)
    else:
        turn_off_internet(verbose=config.option.verbose)
