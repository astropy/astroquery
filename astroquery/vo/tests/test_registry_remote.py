import json, os
from astropy.tests.helper import remote_data
from astropy.io import ascii
## Why can't I import astroquery.vo ?
from astroquery.vo import Registry
from .shared_registry import SharedRegistryTests

##
##  Regenerate the output JSON files using:
##
##  astroquery/vo > python tests/thetests.py


@remote_data
class TestRegistryRemote(SharedRegistryTests):
    ""

    def test_query_basic(self):
        self.query_basic()

    def test_query_counts(self):
        self.query_counts()

    def test_query_timeout(self):
        self.query_timeout()

