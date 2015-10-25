# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data
from ...exceptions import LoginError

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False

if HAS_KEYRING:
    from ...cosmosim import CosmoSim

SKIP_TESTS = not HAS_KEYRING

@pytest.mark.skipif('SKIP_TESTS')
@remote_data
class TestCosmoSim:
    
    @pytest.fixture()
    def temp_dir(self, request):
        my_temp_dir = tempfile.mkdtemp()
        def fin():
            shutil.rmtree(my_temp_dir)
        request.addfinalizer(fin)
        return my_temp_dir

    def test_login(self):
        cs = CosmoSim()
        # wrong login credentials
        with pytest.raises(LoginError) as exc:
            cs.login(username='public', password='wrong')
        assert exc.value.args[0] == 'Authentication failed!'
        cs.logout()

