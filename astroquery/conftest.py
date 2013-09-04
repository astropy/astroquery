# Licensed under a 3-clause BSD style license - see LICENSE.rst
from .utils import turn_off_internet,turn_on_internet
turn_off_internet()

from astropy.tests.helper import pytest, remote_data

@remote_data
def test_turn_on_internet():
    # this is just a hack to globally restore internet connection if remote_data is enabled
    turn_on_internet()

# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from astropy.tests.pytest_plugins import *
