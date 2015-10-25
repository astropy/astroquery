# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data

try:
    import keyring
    HAS_KEYRING = True
except:
    HAS_KEYRING = False
try:
    from ...cosmosim import CosmoSim
    COSMOSIM_IMPORTED = True
except:
    COSMOSIM_IMPORTED = False
from ...exceptions import LoginError
SKIP_TESTS = not(HAS_KEYRING and COSMOSIM_IMPORTED)

# @pytest.mark.skipif('SKIP_TESTS')
# @remote_data
# class TestCosmoSim:
#     @pytest.fixture()
#     def temp_dir(self, request):
#         my_temp_dir = tempfile.mkdtemp()
#         def fin():
#             shutil.rmtree(my_temp_dir)
#         request.addfinalizer(fin)
#         return my_temp_dir

#     def test_login(self):
#         """
#         Tests a simple login with public credentials.
#         """
#         cosmosim = CosmoSim()
#         # wrong login credentials
#         with pytest.raises(LoginError) as exc:
#             cosmosim.login(username='public', password='wrong')
#         assert exc.value.args[0] == 'Authentication failed!'
#         cosmosim.logout()

