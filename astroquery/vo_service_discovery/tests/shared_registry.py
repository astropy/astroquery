import os
from astropy.table import Table
from astroquery.vo_service_discovery import Registry


class Helpers(object):
    ""

    DATA_FILES = {}

    def table2ecsv(self, current, filepath):
        """Dump a table and its meta data to ECSV"""
        current.write(filepath, format='ascii.ecsv', overwrite=True)

    def ecsv2table(self, filepath):
        """
        """
        table = Table.read(filepath, format='ascii.ecsv')
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
        """Check the meta data in the "astroquery.vo_service_discovery" area"""
        assert set(current.meta['astroquery.vo_service_discovery']) == \
            set(reference.meta['astroquery.vo_service_discovery']), (
                "Keys differ:  current={},\n          reference={}"
                .format(current.meta['astroquery.vo'].keys(),
                        reference.meta['astroquery.vo'].keys()))
        # Check their values
        for k in current.meta['astroquery.vo_service_discovery'].keys():
            if "text" in k:
                continue
            if k == 'url':
                continue
            assert current.meta['astroquery.vo_service_discovery'][k] == \
                reference.meta['astroquery.vo_service_discovery'][k], (
                    "The value of key {} differs:\ncurrent={},\nreference={}"
                    .format(k, current.meta['astroquery.vo'][k],
                            reference.meta['astroquery.vo'][k]))
        return True

    def table_stats_comp(self, current, reference):
        """Check some basic properties of the tables like length and columns.
        The test result length should be no less than 90% of the baseline.
        """
        assert len(current) >= 0.9 * len(reference), (
            "Current results have {} rows compared to reference with {}"
            .format(len(current), len(reference)))
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
        'query_counts_result': 'registry_query_counts_result.ecsv',
        'empty_votable': 'empty_votable.xml'
    }

    def rewrite(self):
        """Called by main below to re-generate the reference files."""
        self.query_basic(None, True)
        self.query_counts(None, True)

    ##
    #  Tests that make an http request:
    ##
    def query_basic(self, capfd, reinit=False):

        # Path of VOTable xml content of actual TAP query.
        content_baseline = self.data_path(self.DATA_FILES['query_basic_content'])

        # Path of ECSV representation of Astropy Table result.
        result_baseline = self.data_path(self.DATA_FILES['query_basic_result'])

        if reinit:
            # Overwrite the baseline files with new results
            dump_to_file = True
            output_file = content_baseline
        else:
            dump_to_file = False
            output_file = None

        # Perform the query, saving the content if reinit is True.
        result = Registry.query(source='astronet', service_type='cone',
                                dump_to_file=dump_to_file, output_file=output_file)

        if reinit:
            self.table2ecsv(result, result_baseline)
        else:
            assert(self.table_comp(result, result_baseline))

            # Then test with verbose to cover that code.
            result2 = Registry.query(source='astronet', service_type='cone', verbose=True)
            assert(self.table_comp(result2, result_baseline))
            out, _err = capfd.readouterr()
            assert "sending query ADQL" in out

    def query_counts(self, capfd, reinit=False):
        # Path of VOTable xml content of actual TAP query.
        content_baseline = self.data_path(self.DATA_FILES['query_counts_content'])

        # Path of ECSV representation of Astropy Table result.
        result_baseline = self.data_path(self.DATA_FILES['query_counts_result'])

        if reinit:
            # Overwrite the baseline files with new results
            dump_to_file = True
            output_file = content_baseline
        else:
            dump_to_file = False
            output_file = None

        # Perform the query, saving the content if reinit is True.
        result = Registry.query_counts('publisher', 15, dump_to_file=dump_to_file, output_file=output_file)

        if reinit:
            self.table2ecsv(result, result_baseline)
        else:
            assert(self.table_comp(result, result_baseline))

            # Then test with verbose to cover that code.
            result2 = Registry.query_counts('publisher', 15, verbose=True)
            assert(self.table_comp(result2, self.data_path(self.DATA_FILES['query_counts_result'])))
            out, _err = capfd.readouterr()
            assert "sending query_counts ADQL" in out


# This main can regenerate the stored ECSV for you after you've run a
# test and checked that the new results are correct.
if __name__ == "__main__":
    tests = SharedRegistryTests()
    tests.rewrite()
