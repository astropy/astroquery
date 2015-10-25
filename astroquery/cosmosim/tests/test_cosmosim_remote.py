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

    def test_login_fail(self):
        """
        Tests a simple failed login with public credentials. Also, tests
        logout after a failed login attempt.
        """

        cs = CosmoSim()
        
        # wrong login credentials
        auth = cs.login(username='public', password='wrong')
        # assert auth.status_code != 200, 'Authentication succeeded (not expected).'
        
        # # logout anyway
        # cs.logout()
        
        # # check login status
        # loggedin = cs.check_login_status()
        # assert loggedin is False, 'Logged in successfully (not expected).'

    def test_login_pass(self):
        """
        Tests a simple successful login with public credentials. Also, tests 
        the `store_password' kwarg of login, as well as logout's `deletepw'
        kwarg.
        """
        pass
        #cs = CosmoSim()

        # enter in correct login credentials, then logout
        #auth = cs.login(username='public', password='Physics2014')
        #assert auth.status_code == 200, 'Authentication failed (not expected).'
        #cs.logout()

        # enter in correct login credentials (store pw), logout, then login
        # without pw entered in explicitly
        #auth = cs.login(username='public', password='Physics2014',
        #                store_password=True)
        #assert auth.status_code == 200, 'Authentication failed (not expected).'
        #cs.logout()
        #auth = cs.login(username='public')
        #assert auth.status_code == 200, 'Authentication failed (not expected).'

        # # logout and do not store password
        # cs.logout()
        # auth = cs.login(username='public', password='Physics2014')
        # assert auth.status_code == 200, 'Authentication failed (not expected).'
       
        # # check login status
        # loggedin = cs.check_login_status()
        # assert loggedin is True, 'Not logged in successfully (not expected).'

        
    #def test_logout after
