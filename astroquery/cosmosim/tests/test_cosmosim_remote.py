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
        # wrong login credentials
        with pytest.raises(LoginError) as exc:
            cosmosim.login(username='public',password='wrong')
        assert exc.value.args[0] == "Authentication failed!"
        cosmosim.logout()

    @pytest.mark.skipif('not CosmoSim.USERNAME')
    def test_runsql(self):
        cosmosim = CosmoSim()
        cosmosim.login(username='public',password='Physics2014')
        query="SELECT p.* FROM MDR1.FOFMtree AS p, (SELECT fofTreeId, lastProgId FROM MDR1.FOFMtree WHERE fofId=85000000010) AS mycl WHERE p.fofTreeId BETWEEN mycl.fofTreeId AND mycl.lastProgId AND np>200 ORDER BY p.treeSnapnum"
        result = cosmosim.run_sql_query(query_string=query,cache=False)
        cosmosim._existing_tables()
        ipdb.set_trace()
        assert cosmosim.job_dict[result] in ['COMPLETED','EXECUTING','ABORTED','QUEUED']
        cosmosim.delete_job(jobid=result,squash=True)
        assert len(cosmosim.job_dict.keys()) == 0

    @pytest.mark.skipif('not CosmoSim.USERNAME')
    def test_download(self):
        cosmosim = CosmoSim()
        cosmosim.cache_location = temp_dir
        cosmosim.login(username='public',password='Physics2014')
        query="SELECT 0.25*(0.5+FLOOR(LOG10(Mvir)/0.25)) AS log_mass, COUNT(*) AS num FROM MDR1.BDMV WHERE snapnum=85 GROUP BY FLOOR(LOG10(Mvir)/0.25) ORDER BY log_mass"
        result = cosmosim.run_sql_query(query_string=query,tablename='testtable',cache=False)
        cosmosim._existing_tables()
        assert cosmosim.job_dict[result] is 'COMPLETED'
        ipdb.set_trace()
        cosmosim.delete_job(jobid=result,squash=True)
        assert len(cosmosim.job_dict.keys()) == 0

