import json, os
from astropy.tests.helper import pytest
from requests.exceptions import Timeout, ReadTimeout
from astropy.tests.helper import remote_data
from astropy.io import ascii
from astropy.table import Table
from astroquery.vo import Registry


class Helpers(object):
    ""

    DATA_FILES = {}

    def table2ecsv(self, current, filepath):
        """Dump a table and its meta data to ECSV"""
        from astropy.io import ascii
        try:
            ascii.write(current, filepath, format='ecsv', overwrite=True)
        except Exception as e:
            raise e

    def ecsv2table(self, filepath):
        """
        """
        try:
            with open(filepath, 'r') as f:
                table = Table.read(f.read(), format='ascii.ecsv')
        except Exception as e:
            raise
        return table

    def content2file(self, content, filepath):
        with open(filepath, mode='wb') as file:
            file.write(content)

    def file2content(self, filepath):
        with open(filepath, mode='rb') as file:
            fileContent = file.read()
            return fileContent

    def data_path(self, filename):
        """ In case these paths change depending on test methods?"""
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
        return os.path.join(data_dir, filename)

    def table_comp(self, current_table, reference_file):
        """Compare the resulting Tables piece by piece

        Trying to give more info than just a failed assertion.
        """
        reference = self.ecsv2table(reference_file)
        self.table_meta_comp(current_table, reference)
        self.table_stats_comp(current_table, reference)

        return True

    def table_meta_comp(self, current, reference):
        """Check the meta data in the "astroquery.vo" area"""
        assert set(current.meta['astroquery.vo']) == set(reference.meta['astroquery.vo']), "Keys differ:  current={},\n          reference={}".format(current.meta['astroquery.vo'].keys(), reference.meta['astroquery.vo'].keys())
        ## Check their values
        for k in current.meta['astroquery.vo'].keys():
            if "text" in k: continue
            if k == 'url': continue
            assert current.meta['astroquery.vo'][k] == reference.meta['astroquery.vo'][k], "The value of key {} differs:\ncurrent={},\nreference={}".format(k, current.meta['astroquery.vo'][k], reference.meta['astroquery.vo'][k])
        return True

    def table_stats_comp(self, current, reference):
        """Check some basic properties of the tables like length and columns."""
        assert len(current) >= len(reference), "Current results have {} rows compared to reference with {}".format(len(current), len(reference))
        for col in reference.colnames:
            assert col in current.colnames, "Column {} missing from current result.".format(col)
        return True


class SharedRegistryTests(Helpers):
    "This class contains tests that should be run in both local and remote modes, along with helper functions."

    # Map from queries to result reference files.
    DATA_FILES = {
        'query_basic_content': 'registry_query_basic_content.xml',
        'query_counts_content': 'registry_query_counts_content.xml',
        'query_basic_result': 'registry_query_basic_result.ecsv',
        "query_counts_result": "registry_query_counts_result.ecsv"
    }

    def rewrite(self):
        """Called by main below to re-generate the reference files."""
        print("DEBUGGING: calling basic(True)")
        self.query_basic(True)
        self.query_counts(True)

    ##
    ##  Tests that make an http request:
    ##
    def query_basic(self, reinit=False):
        result, http_response = Registry.query(source='heasarc', service_type='image', return_http_response=True)
        if reinit:
            self.table2ecsv(result, self.data_path(self.DATA_FILES['query_basic_result']))
            self.content2file(http_response.content, self.data_path(self.DATA_FILES['query_basic_content']))
        else:
            assert(self.table_comp(result, self.data_path(self.DATA_FILES['query_basic_result'])))

    def query_counts(self, reinit=False):
        result, http_response = Registry.query_counts('publisher', 15, return_http_response=True)
        if reinit:
            self.table2ecsv(result, self.data_path(self.DATA_FILES['query_counts_result']))
            self.content2file(http_response.content, self.data_path(self.DATA_FILES['query_counts_content']))
        else:
            assert(self.table_comp(result, self.data_path(self.DATA_FILES['query_counts_result'])))

    def query_timeout(self):
        myReg = Registry()
        myReg._TIMEOUT = 0.0001
        try:
            result = myReg.query(source='heasarc', service_type='image')
        except (Timeout, ReadTimeout, ConnectionError):
            pass
        except Exception as e:
            pytest.fail("Did not get the expected timeout exception but {}".format(e))
        else:
            pytest.fail("Did not get the expected timeout exception but none")


## This main can regenerate the stored JSON for you after you've run a
## test and checked that the new results are correct.
if __name__ == "__main__":
    tests = SharedRegistryTests()
    tests.rewrite()
