import pytest
from astropy.tests.helper import remote_data
from requests.exceptions import Timeout, ReadTimeout
from astroquery.vo import Registry
from .shared_registry import SharedRegistryTests
from .. import conf


@remote_data
class TestRegistryRemote(SharedRegistryTests):
    ""

    def test_basic(self, capfd):
        self.query_basic(capfd)

    def test_counts(self, capfd):
        self.query_counts(capfd)

    def test_get(self):
        "Show the using GET returns same results as POST."
        result = Registry.query(source='heasarc', service_type='image', use_get=True)
        assert(self.table_comp(result, self.data_path(self.DATA_FILES['query_basic_result'])))

    def test_basic_timeout(self, capfd):
        try:
            with conf.set_temp('timeout', 0.001):
                self.query_basic(capfd)
        except (Timeout, ReadTimeout):
            pass
        except Exception as e:
            pytest.fail("Did not get expected timeout exception but did get: {}".format(e))
        else:
            pytest.fail("Did not get expected timeout exception.")

    def test_counts_timeout(self, capfd):
        try:
            with conf.set_temp('timeout', 0.001):
                self.query_counts(capfd)
        except (Timeout, ReadTimeout):
            pass
        except Exception as e:
            pytest.fail("Did not get expected timeout exception but did get: {}".format(e))
        else:
            pytest.fail("Did not get expected timeout exception.")
