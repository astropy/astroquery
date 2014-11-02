import tempfile
import shutil
from astropy.tests.helper import pytest, remote_data
import ipdb
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
        cosmosim = CosmoSim()
        with pytest.raises(LoginError) as exc:
            cosmosim.login(username='public',password='wrong')
        assert exc.value.args[0] == "Authentication failed!"
        cosmosim.login
