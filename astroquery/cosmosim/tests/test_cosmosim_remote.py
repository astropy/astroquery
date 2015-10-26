# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os, sys
import tempfile
import shutil
import getpass
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

    def test_login_fail(self, monkeypatch):
        """
        Tests a simple failed login with public credentials. Also, tests
        logout after a failed login attempt.
        """
        
        cs = CosmoSim()
        cs.logout()

        # wrong login credentials
        auth = cs.login(username='public', password='wrong')
        assert auth.status_code != 200, 'Authentication succeeded (not expected).'
        
        # logout anyway
        cs.logout()
        
        # check login status
        loggedin = cs.check_login_status()
        assert loggedin is False, 'Logged in successfully (not expected).'
        
    def test_login_pass(self):
        """
        Tests a simple successful login with public credentials. Also, tests 
        the `store_password' kwarg of login, as well as logout's `deletepw'
        kwarg.
        """

        cs = CosmoSim()

        # enter in correct login credentials, then logout
        auth = cs.login(username='public', password='Physics2014')
        assert auth.status_code == 200, 'Authentication failed (not expected).'
        cs.logout()

        # enter in correct login credentials (store pw), logout, then login
        # without pw entered in explicitly
        auth = cs.login(username='public', password='Physics2014',
                        store_password=True)
        assert auth.status_code == 200, 'Authentication failed (not expected).'
        cs.logout()
        auth = cs.login(username='public')
        assert auth.status_code == 200, 'Authentication failed (not expected).'
        
        # now delete pw from keychain (for the current test and future tests)
        cs.logout(deletepw=True)

    def test_login_pass_prompt(self, monkeypatch):
        """
        Tests a simple successful login with public credentials. Tests the prompt
        for a password.
        """

        # login and store password
        cs = CosmoSim()
        auth = cs.login(username='public', password='Physics2014',
                        store_password=True)
        assert auth.status_code == 200, 'Authentication failed (not expected).'
        
        def mock_raw_input(*args, **kwargs):
            """
            Mock raw input
            """
            return 'Physics2014'

        # logout and delete password
        cs.logout(deletepw=True)

        # try to login without pw afterwards
        monkeypatch.setattr(getpass, 'getpass', mock_raw_input)
        auth = cs.login(username='public')

        # using mock input by user at prompt to login
        loggedin = cs.check_login_status()
        assert loggedin is True, 'Logged in failed (not expected).'
        cs.logout()

    def test_login_twice(self, capsys):
        """
        Test that login twice prompts correct message.
        """

        cs = CosmoSim()
        print('hello')
        cs.login(username='public', password ='Physics2014')
        cs.login(username='public', password ='Physics2014')
        sys.stderr.write("world\n")
        out, err = capsys.readouterr()
        
