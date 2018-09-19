import json, os
import pytest
from astropy.tests.helper import remote_data
from astropy.io import ascii
from requests.exceptions import Timeout, ReadTimeout
from astroquery.vo import Registry
from .shared_registry import SharedRegistryTests
from .. import conf


@remote_data
class TestRegistryRemote(SharedRegistryTests):
    ""

    def test_basic(self):
        self.query_basic()

    def test_counts(self):
        self.query_counts()

    def test_basic_timeout(self):
        try:
            with conf.set_temp('timeout', 0.001):
                self.query_basic()
        except (Timeout, ReadTimeout):
            pass
        except Exception as e:
            pytest.fail("Did not get expected timeout exception but did get: {}".format(e))
        else:
            pytest.fail("Did not get expected timeout exception.")

    def test_counts_timeout(self):
        try:
            with conf.set_temp('timeout', 0.001):
                self.query_counts()
        except (Timeout, ReadTimeout):
            pass
        except Exception as e:
            pytest.fail("Did not get expected timeout exception but did get: {}".format(e))
        else:
            pytest.fail("Did not get expected timeout exception.")
