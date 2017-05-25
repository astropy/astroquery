# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.tests.helper import remote_data
from ...exceptions import LoginError

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

if HAS_KEYRING:
    from ...cosmosim import CosmoSim

SKIP_TESTS = not HAS_KEYRING

# @pytest.mark.skipif('SKIP_TESTS')
# @remote_data
# class TestEso:
#    def __init__():
