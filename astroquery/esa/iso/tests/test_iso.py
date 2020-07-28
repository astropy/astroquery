# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Jesus Salgado
@contact: jesusjuansalgado@gmail.com

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 15 July 2020
"""

import pytest

from ..core import ISOClass
from ..tests.dummy_tap_handler import DummyISOTapHandler


class TestISO():

    def get_dummy_tap_handler(self):
        parameters = {'query': "select top 10 * from ida.observations",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyISOTapHandler("launch_job", parameters)
        return dummyTapHandler

    @pytest.mark.remote_data
    def test_download_data(self):
        parameters = {'observation_id': "0112880801",
                      'level': "BASIC_SCIENCE",
                      'filename': 'file.tar',
                      'verbose': False}
        xsa = ISOClass(self.get_dummy_tap_handler())
        xsa.download_data(**parameters)

  
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
