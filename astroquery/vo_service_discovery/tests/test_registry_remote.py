from astropy.tests.helper import remote_data
from .shared_registry import SharedRegistryTests


@remote_data
class TestRegistryRemote(SharedRegistryTests):
    ""

    def test_basic(self, capfd):
        self.query_basic(capfd)

    def test_counts(self, capfd):
        self.query_counts(capfd)
