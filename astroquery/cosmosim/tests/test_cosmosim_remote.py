# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data
try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False
try:
    from ...cosmosim import CosmoSim
    COSMOSIM_IMPORTED = True
except ImportError:
    COSMOSIM_IMPORTED = False
from ...exceptions import LoginError

SKIP_TESTS = not(HAS_KEYRING and COSMOSIM_IMPORTED)

#@pytest.mark.skipif('SKIP_TESTS')
#@remote_data
#class TestEso:
#    def __init__():
        
