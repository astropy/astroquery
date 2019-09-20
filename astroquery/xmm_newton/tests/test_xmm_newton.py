# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 4 Sept. 2019
"""

import pytest

from astroquery.xmm_newton.core import XMMNewtonClass
from astroquery.xmm_newton.tests.dummy_handler import DummyHandler
from astroquery.xmm_newton.tests.dummy_tap_handler import DummyXMMNewtonTapHandler
from astropy import coordinates


class TestXMMNewton():

    def get_dummy_tap_handler(self):
        parameterst = {'query': "select top 10 * from v_public_observations",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyXMMNewtonTapHandler("launch_job", parameterst)
        return dummyTapHandler

    def test_download_data(self):
        parameters = {'observation_id': "0112880801",
                      'level': "ODF",
                      'instname': None,
                      'instmode': None,
                      'filter': None,
                      'expflag': None,
                      'expno': None,
                      'name': None,
                      'datasubsetno': None,
                      'sourceno': None,
                      'extension': None,
                      'filename': 'file',
                      'verbose': False}
        dummyHandler = DummyHandler("download_product", parameters)
        xsa = XMMNewtonClass(dummyHandler, self.get_dummy_tap_handler())
        xsa.download_data(parameters['observation_id'],
                             parameters['level'],
                             parameters['instname'],
                             parameters['instmode'],
                             parameters['filter'],
                             parameters['expflag'],
                             parameters['expno'],
                             parameters['name'],
                             parameters['datasubsetno'],
                             parameters['sourceno'],
                             parameters['extension'],
                             parameters['filename'],
                             parameters['verbose'])
        dummyHandler.check_call("download_product", parameters)

    def test_get_postcard(self):
        parameters = {'observation_id': "0112880801",
                      'image_type': "OBS_EPIC",
                      'filename': None,
                      'verbose': False}
        dummyHandler = DummyHandler("get_postcard", parameters)
        xsa = XMMNewtonClass(dummyHandler, self.get_dummy_tap_handler())
        xsa.get_postcard(parameters['observation_id'],
                         parameters['image_type'],
                         parameters['filename'],
                         parameters['verbose'])
        dummyHandler.check_call("get_postcard", parameters)

    def test_query_xsa_tap(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        dummyHandler = DummyHandler("launch_job", parameters)

        xsa = XMMNewtonClass(dummyHandler, self.get_dummy_tap_handler())
        xsa.query_xsa_tap(parameters['query'], parameters['output_file'],
                          parameters['output_format'], parameters['verbose'])
        self.get_dummy_tap_handler().check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'only_names': True,
                       'verbose': True}

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyXMMNewtonTapHandler("get_tables", parameters2)
        xsa = XMMNewtonClass(dummyHandler, self.get_dummy_tap_handler())
        xsa.get_tables(True, True)
        dummyTapHandler.check_call("get_tables", parameters2)

    def test_get_columns(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'table_name': "table",
                       'only_names': True,
                       'verbose': True}

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyXMMNewtonTapHandler("get_columns", parameters2)
        xsa = XMMNewtonClass(dummyHandler, self.get_dummy_tap_handler())
        xsa.get_columns("table", True, True)
        dummyTapHandler.check_call("get_columns", parameters2)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    pytest.main()
