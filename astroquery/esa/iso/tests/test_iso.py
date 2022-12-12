# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=====================
ISO Astroquery Module
=====================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import pytest

from astroquery.esa.iso import ISOClass
from astroquery.esa.iso.tests.dummy_tap_handler import DummyISOTapHandler


class TestISO:

    def get_dummy_tap_handler(self):
        parameters = {'query': "select top 10 * from ida.observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        dummyTapHandler = DummyISOTapHandler("launch_job", parameters)
        return dummyTapHandler

    def test_get_download_link(self):
        parameters = {'tdt': "40001501",
                      'level': "DEFAULT_DATA_SET",
                      'retrieval_type': "OBSERVATION",
                      'filename': "file",
                      'verbose': False}
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_download_link(**parameters)

    def test_get_download_link_verbose(self):
        parameters = {'tdt': "40001501",
                      'level': "DEFAULT_DATA_SET",
                      'retrieval_type': "OBSERVATION",
                      'filename': "file",
                      'verbose': True}
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_download_link(**parameters)

    def test_get_postcard_link(self):
        parameters = {'tdt': "40001501",
                      'filename': "file",
                      'verbose': False}
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_postcard_link(**parameters)

    def test_get_postcard_link_verbose(self):
        parameters = {'tdt': "40001501",
                      'filename': "file",
                      'verbose': True}
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_postcard_link(**parameters)

    @pytest.mark.remote_data
    def test_download_data(self, tmp_cwd):
        parameters = {'tdt': "40001501",
                      'product_level': "DEFAULT_DATA_SET",
                      'retrieval_type': "OBSERVATION",
                      'filename': "file",
                      'verbose': False}
        ida = ISOClass(self.get_dummy_tap_handler())
        res = ida.download_data(**parameters)
        assert res == "file.tar", "File name is " + res + " and not file.tar"

    @pytest.mark.remote_data
    def test_download_postcard(self, tmp_cwd):
        parameters = {'tdt': "40001501",
                      'filename': "file",
                      'verbose': False}
        ida = ISOClass(self.get_dummy_tap_handler())
        res = ida.get_postcard(**parameters)
        assert res == "file.png", "File name is " + res + " and not file.png"

    def test_query_ida_tap(self):
        parameters = {'query': "select top 10 * from ida.observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        ida = ISOClass(self.get_dummy_tap_handler())
        ida.query_ida_tap(**parameters)
        self.get_dummy_tap_handler().check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters = {'only_names': True,
                      'verbose': True}

        dummyTapHandler = DummyISOTapHandler("get_tables", parameters)
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_tables(only_names=True, verbose=True)
        dummyTapHandler.check_call("get_tables", parameters)

    def test_get_columns(self):
        parameters = {'table_name': "table",
                      'only_names': True,
                      'verbose': True}

        dummyTapHandler = DummyISOTapHandler("get_columns", parameters)
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_columns("table", only_names=True, verbose=True)
        dummyTapHandler.check_call("get_columns", parameters)

    def test_get_tables_onlynames_false(self):
        parameters = {'only_names': False,
                      'verbose': True}

        DummyISOTapHandler("get_tables", parameters)
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_tables(only_names=False, verbose=True)

    def test_get_columns_onlynames_false(self):
        parameters = {'table_name': "table",
                      'only_names': False,
                      'verbose': True}

        DummyISOTapHandler("get_columns", parameters)
        ida = ISOClass(self.get_dummy_tap_handler())
        ida.get_columns("table", only_names=False, verbose=True)
