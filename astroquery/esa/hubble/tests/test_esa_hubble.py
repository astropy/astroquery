# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Aug. 2018


"""
import pytest

from astroquery.esa.hubble import ESAHubbleClass
from astroquery.esa.hubble.tests.dummy_handler import DummyHandler
from astroquery.esa.hubble.tests.dummy_tap_handler import DummyHubbleTapHandler
from astropy import coordinates


class TestESAHubble():

    def get_dummy_tap_handler(self):
        parameterst = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)
        return dummyTapHandler

    def test_download_product(self):
        parameters = {'observation_id': "J6FL25S4Q",
                      'calibration_level': "RAW",
                      'filename': 'file',
                      'verbose': False}
        dummyHandler = DummyHandler("download_product", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.download_product(parameters['observation_id'],
                              parameters['calibration_level'],
                              parameters['filename'],
                              parameters['verbose'])
        dummyHandler.check_call("download_product", parameters)

    def test_get_postcard(self):
        parameters = {'observation_id': "X0MC5101T",
                      'verbose': False}
        dummyHandler = DummyHandler("get_postcard", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_postcard("X0MC5101T")
        dummyHandler.check_call("get_postcard", parameters)

    def test_query_target(self):
        parameters = {'name': "m31",
                      'verbose': False}
        dummyHandler = DummyHandler("query_target", parameters)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.query_target(parameters['name'])
        dummyHandler.check_call("query_target", parameters)

    def test_cone_search(self):
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')

        parameterst = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)

        parameters = {'coordinates': c,
                      'radius': 0.0,
                      'file_name': 'file_cone',
                      'output_format': 'votable',
                      'cache': True}
        dummyHandler = DummyHandler("cone_search", parameters)

        ehst = ESAHubbleClass(dummyHandler, dummyTapHandler)
        ehst.cone_search(parameters['coordinates'],
                         parameters['radius'],
                         parameters['file_name'],
                         parameters['output_format'],
                         parameters['cache'])
        dummyHandler.check_call("cone_search", parameters)

    def test_query_hst_tap(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        dummyHandler = DummyHandler("launch_job", parameters)

        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.query_hst_tap(parameters['query'], parameters['output_file'],
                           parameters['output_format'], parameters['verbose'])
        self.get_dummy_tap_handler().check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'only_names': True,
                       'verbose': True}

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyHubbleTapHandler("get_tables", parameters2)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_tables(True, True)
        dummyTapHandler.check_call("get_tables", parameters2)

    def test_get_columns(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'table_name': "table",
                       'only_names': True,
                       'verbose': True}

        dummyHandler = DummyHandler("launch_job", parameters)
        dummyTapHandler = DummyHubbleTapHandler("get_columns", parameters2)
        ehst = ESAHubbleClass(dummyHandler, self.get_dummy_tap_handler())
        ehst.get_columns("table", True, True)
        dummyTapHandler.check_call("get_columns", parameters2)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    pytest.main()
