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

    @pytest.mark.remote_data
    def test_download_product(self):
        parameters = {'observation_id': "J6FL25S4Q",
                      'calibration_level': "RAW",
                      'filename': 'file',
                      'verbose': False}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.download_product(parameters['observation_id'],
                              parameters['calibration_level'],
                              parameters['filename'],
                              parameters['verbose'])

    @pytest.mark.remote_data
    def test_get_postcard(self):
        parameters = {'observation_id': "X0MC5101T",
                      'verbose': False}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.get_postcard("X0MC5101T")

    @pytest.mark.remote_data
    def test_query_target(self):
        parameters = {'name': "m31",
                      'verbose': False}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.query_target(parameters['name'])

    @pytest.mark.remote_data
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

        ehst = ESAHubbleClass(dummyTapHandler)
        ehst.cone_search(parameters['coordinates'],
                         parameters['radius'],
                         parameters['file_name'],
                         parameters['output_format'],
                         parameters['cache'])

    def test_query_hst_tap(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'async_job': False,
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        parameters2 = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}

        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.query_hst_tap(parameters['query'], parameters['async_job'],
                           parameters['output_file'],
                           parameters['output_format'], parameters['verbose'])
        self.get_dummy_tap_handler().check_call("launch_job", parameters2)

    def test_get_tables(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'only_names': True,
                       'verbose': True}

        dummyTapHandler = DummyHubbleTapHandler("get_tables", parameters2)
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.get_tables(True, True)

    def test_get_columns(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        parameters2 = {'table_name': "table",
                       'only_names': True,
                       'verbose': True}

        dummyTapHandler = DummyHubbleTapHandler("get_columns", parameters2)
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.get_columns("table", True, True)
        dummyTapHandler.check_call("get_columns", parameters2)

    def test_query_by_criteria(self):
        parameters1 = {'calibration_level': "PRODUCT",
                       'data_product_type': "image",
                       'intent': "SCIENCE",
                       'obs_collection': ['HST'],
                       'instrument_name': ['WFC3'],
                       'filters': ['F555W'],
                       'async_job': False,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True,
                       'get_query': True}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        test_query = ehst.query_by_criteria(parameters1['calibration_level'],
                                            parameters1['data_product_type'],
                                            parameters1['intent'],
                                            parameters1['obs_collection'],
                                            parameters1['instrument_name'],
                                            parameters1['filters'],
                                            parameters1['async_job'],
                                            parameters1['output_file'],
                                            parameters1['output_format'],
                                            parameters1['verbose'],
                                            parameters1['get_query'])
        parameters2 = {'query': test_query,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        parameters3 = {'query': "select o.*, p.calibration_level, "
                                "p.data_product_type from ehst.observation "
                                "AS o LEFT JOIN ehst.plane as p on "
                                "o.observation_uuid=p.observation_uuid where("
                                "p.calibration_level LIKE '%PRODUCT%' AND "
                                "p.data_product_type LIKE '%image%' AND "
                                "o.intent LIKE '%SCIENCE%' AND (o.collection "
                                "LIKE '%HST%') AND (o.instrument_name LIKE "
                                "'%WFC3%') AND (o.instrument_configuration "
                                "LIKE '%F555W%'))",
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", parameters2)
        dummy_tap_handler.check_call("launch_job", parameters3)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    pytest.main()
