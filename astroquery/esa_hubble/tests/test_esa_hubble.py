# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
import pytest

from astroquery.esa_hubble.core import ESAHubbleClass
from astroquery.esa_hubble.tests.dummy_handler import DummyHandler
from astroquery.esa_hubble.tests.dummy_tap_handler import DummyHubbleTapHandler
from astropy import coordinates
# from astropy.tests.helper import remote_data


class TestESAHubble():

    def get_dummy_tap_handler(self):
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)
        return dummyTapHandler

    def test_download_product(self):
        parameters = {}
        parameters['observation_id'] = "J6FL25S4Q"
        parameters['calibration_level'] = "RAW"
        parameters['filename'] = 'file'
        parameters['verbose'] = False
        dummyHandler = DummyHandler("download_product", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.download_product(parameters['observation_id'],
                              parameters['calibration_level'],
                              parameters['filename'],
                              parameters['verbose'])
        dummyHandler.check_call("download_product", parameters)

    def test_get_postcard(self):
        parameters = {}
        parameters['observation_id'] = "X0MC5101T"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("get_postcard", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_postcard("X0MC5101T")
        dummyHandler.check_call("get_postcard", parameters)

    def test_query_target(self):
        parameters = {}
        parameters['name'] = "m31"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("query_target", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.query_target(parameters['name'])
        dummyHandler.check_call("query_target", parameters)

    def test_cone_search(self):
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        parameterst = {}
        parameterst['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst['output_file'] = "test2.vot"
        parameterst['output_format'] = "votable"
        parameterst['verbose'] = False
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)

        parameters = {}
        parameters['coordinates'] = c
        parameters['radius'] = 0.0
        parameters['file_name'] = 'file_cone'
        parameters['output_format'] = 'votable'
        parameters['cache'] = True
        dummyHandler = DummyHandler("cone_search", parameters)

        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.cone_search(parameters['coordinates'],
                         parameters['radius'],
                         parameters['file_name'],
                         parameters['output_format'],
                         parameters['cache'])
        dummyHandler.check_call("cone_search", parameters)

    def test_query_hst_tap(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False
        dummyHandler = DummyHandler("launch_job", parameters)

        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.query_hst_tap(parameters['query'], parameters['output_file'],
                           parameters['output_format'], parameters['verbose'])
        self.get_dummy_tap_handler().check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False

        parameters2 = {}
        parameters2['only_names'] = True
        parameters2['verbose'] = True

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyHubbleTapHandler("get_tables", parameters2)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_tables(True, True)
        dummyTapHandler.check_call("get_tables", parameters2)

    def test_get_columns(self):
        parameters = {}
        parameters['query'] = "select top 10 * from hsc_v2.hubble_sc2"
        parameters['output_file'] = "test2.vot"
        parameters['output_format'] = "votable"
        parameters['verbose'] = False

        parameters2 = {}
        parameters2['table_name'] = "table"
        parameters2['only_names'] = True
        parameters2['verbose'] = True

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyHubbleTapHandler("get_columns", parameters2)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_columns("table", True, True)
        dummyTapHandler.check_call("get_columns", parameters2)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    pytest.main()
