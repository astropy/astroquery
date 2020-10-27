# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Aug. 2018


"""
import pytest
import os

from requests.models import Response
from astroquery.esa.hubble import ESAHubbleClass
from astroquery.esa.hubble.tests.dummy_tap_handler import DummyHubbleTapHandler
from astroquery.utils.testing_tools import MockResponse
from astropy import coordinates
from unittest.mock import MagicMock
from astropy.table.table import Table
import shutil


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_mockreturn(method, request, url, params, *args, **kwargs):
    file = 'm31.vot'
    if 'OBSERVATION_ID' in params:
        file = params['OBSERVATION_ID'] + ".vot"
    response = data_path(file)
    shutil.copy(response + '.test', response)
    return response


@pytest.fixture(autouse=True)
def ehst_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(ESAHubbleClass, '_request', get_mockreturn)
    return mp


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
                      'filename': "J6FL25S4Q.vot",
                      'verbose': True}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.download_product(parameters['observation_id'],
                              parameters['calibration_level'],
                              parameters['filename'],
                              parameters['verbose'])

    def test_get_postcard(self):
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.get_postcard(observation_id="X0MC5101T",
                          filename="X0MC5101T.vot",
                          verbose=True)

    def test_query_target(self):
        parameters = {'name': "m31",
                      'verbose': True}
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.query_target(name=parameters['name'],
                          verbose=parameters['verbose'])

    @pytest.mark.remote_data
    def test_cone_search(self):
        coords = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')

        parameterst = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)

        parameters = {'coordinates': coords,
                      'radius': 0.0,
                      'file_name': 'file_cone',
                      'output_format': 'votable',
                      'cache': True}

        ehst = ESAHubbleClass(dummyTapHandler)
        target_file = data_path('cone_search.vot')
        with open(target_file, mode='rb') as file:
            target_obj = file.read()
            response = Response()
            response._content = target_obj
            ehst._request = MagicMock(return_value=response)
            ehst.cone_search(parameters['coordinates'],
                             parameters['radius'],
                             parameters['file_name'],
                             parameters['output_format'],
                             parameters['cache'])

    @pytest.mark.remote_data
    def test_cone_search_coords(self):
        coords = "00h42m44.51s +41d16m08.45s"

        parameterst = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)

        parameters = {'coordinates': coords,
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
        parameters[coordinates] = 1234
        with pytest.raises(ValueError) as err:
            ehst.cone_search(parameters['coordinates'],
                             parameters['radius'],
                             parameters['file_name'],
                             parameters['output_format'],
                             parameters['cache'])
        assert "coordinate must be either a string or "\
               "astropy.coordinates" in err.value.args[0]

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

    def test_query_criteria(self):
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
        test_query = ehst.query_criteria(parameters1['calibration_level'],
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

    def test_query_criteria_numeric_calibration(self):
        parameters1 = {'calibration_level': 1,
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
        test_query = ehst.query_criteria(parameters1['calibration_level'],
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
                                "p.calibration_level LIKE '%RAW%' AND "
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
        parameters1['calibration_level'] = 4
        with pytest.raises(KeyError) as err:
            ehst.query_criteria(parameters1['calibration_level'],
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
        assert "Calibration level must be between 0 and 3" in err.value.args[0]

    def test_query_criteria_no_params(self):
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        ehst.query_criteria(async_job=False,
                            output_file="output_test_query_"
                            "by_criteria.vot.gz",
                            output_format="votable",
                            verbose=True)
        parameters = {'query': "select o.*, p.calibration_level, "
                               "p.data_product_type from ehst.observation "
                               "AS o LEFT JOIN ehst.plane as p on "
                               "o.observation_uuid=p.observation_uuid",
                      'output_file': "output_test_query_by_criteria.vot.gz",
                      'output_format': "votable",
                      'verbose': False}
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", parameters)
        dummy_tap_handler.check_call("launch_job", parameters)

    def test_empty_list(self):
        ehst = ESAHubbleClass(self.get_dummy_tap_handler())
        with pytest.raises(ValueError) as err:
            ehst.query_criteria(instrument_name=[1],
                                async_job=False,
                                output_file="output_test_query_"
                                "by_criteria.vot.gz",
                                output_format="votable",
                                verbose=True)
        assert "One of the lists is empty or there are "\
               "elements that are not strings" in err.value.args[0]
