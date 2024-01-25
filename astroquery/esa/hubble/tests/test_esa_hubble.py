# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==============
eHST Tap Tests
==============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import os
import shutil
import gzip
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest
from astropy import coordinates
from astropy.table.table import Table
from requests.models import Response

from astroquery.esa.hubble import ESAHubbleClass
import astroquery.esa.utils.utils as esautils
from astroquery.esa.hubble.tests.dummy_tap_handler import DummyHubbleTapHandler
from astropy.utils.exceptions import AstropyDeprecationWarning


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
    except AttributeError:
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(ESAHubbleClass, '_request', get_mockreturn)
    return mp


def get_cone_mockreturn(params, *args, **kwargs):
    file = data_path('cone_search_m31_5.vot')
    if 'OBSERVATION_ID' in kwargs:
        file = kwargs['OBSERVATION_ID'] + ".vot"
    response = data_path(file)
    shutil.copy(response + '.test', response)
    return response


@pytest.fixture(autouse=True)
def ehst_cone_search(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(ESAHubbleClass, 'cone_search', get_cone_mockreturn)
    return mp


class MockResponse:
    observation_id = 'test'

    @staticmethod
    def pformat():
        return True


class TestESAHubble:

    def get_dummy_tap_handler(self, method='launch_job', query=None):
        if query is None:
            query = "select top 10 * from hsc_v2.hubble_sc2"
        parameterst = {'query': query,
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyHubbleTapHandler(method, parameterst)
        return dummyTapHandler

    def test_download_product_errors(self):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)

        with pytest.raises(ValueError) as err:
            ehst.download_product(observation_id="J6FL25S4Q",
                                  product_type="DUMMY")
        assert "This product_type is not allowed" in err.value.args[0]

    def test_download_product_by_calibration(self, tmp_path):
        parameters = {'observation_id': "J6FL25S4Q",
                      'cal_level': "RAW",
                      'filename': Path(tmp_path, "J6FL25S4Q.vot.test"),
                      'verbose': True}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.download_product(observation_id=parameters['observation_id'],
                              calibration_level=parameters['cal_level'],
                              filename=parameters['filename'],
                              verbose=parameters['verbose'])

    def test_download_product_by_product_type(self, tmp_path):
        parameters = {'observation_id': "J6FL25S4Q",
                      'product_type': "SCIENCE",
                      'filename': Path(tmp_path, "J6FL25S4Q.vot.test"),
                      'verbose': True}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.download_product(observation_id=parameters['observation_id'],
                              product_type=parameters['product_type'],
                              filename=parameters['filename'],
                              verbose=parameters['verbose'])
        parameters['product_type'] = "SCIENCE"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.download_product(observation_id=parameters['observation_id'],
                              product_type=parameters['product_type'],
                              filename=parameters['filename'],
                              verbose=parameters['verbose'])
        parameters['product_type'] = "PREVIEW"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.download_product(observation_id=parameters['observation_id'],
                              product_type=parameters['product_type'],
                              filename=parameters['filename'],
                              verbose=parameters['verbose'])

    def test_get_postcard(self, tmp_path):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.get_postcard(observation_id="X0MC5101T",
                          filename=Path(tmp_path, "X0MC5101T.vot"),
                          verbose=True)
        ehst.get_postcard(observation_id="X0MC5101T",
                          filename=Path(tmp_path, "X0MC5101T.vot"), resolution=1024,
                          verbose=True)

    @patch.object(ESAHubbleClass, 'cone_search')
    @patch.object(ESAHubbleClass, '_query_tap_target')
    def test_query_target(self, mock_query_tap_target, mock_cone_search):
        mock_query_tap_target.return_value = 10, 10
        mock_cone_search.return_value = "test"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        table = ehst.query_target(name="test")
        assert table == "test"

    def test_cone_search(self):
        coords = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s",
                                      frame='icrs')
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        parameters = {'coordinates': coords,
                      'radius': 0.0,
                      'filename': 'file_cone',
                      'output_format': 'votable',
                      'cache': True}
        target_file = data_path('cone_search.vot')
        with open(target_file, mode='rb') as file:
            target_obj = file.read()
            response = Response()
            response._content = target_obj
            ehst._request = MagicMock(return_value=response)
            ehst.cone_search(coordinates=parameters['coordinates'],
                             radius=parameters['radius'],
                             filename=parameters['filename'],
                             output_format=parameters['output_format'],
                             cache=parameters['cache'])
            DummyHubbleTapHandler("cone_search", parameters)

    def test_cone_search_coords(self):
        coords = "00h42m44.51s +41d16m08.45s"

        parameterst = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': True}
        dummyTapHandler = DummyHubbleTapHandler("launch_job", parameterst)

        parameters = {'coordinates': coords,
                      'radius': 0.0,
                      'filename': 'file_cone',
                      'async_job': False,
                      'output_format': 'votable',
                      'cache': True,
                      'verbose': True}

        ehst = ESAHubbleClass(tap_handler=dummyTapHandler, show_messages=False)
        ehst.cone_search(coordinates=parameters['coordinates'],
                         radius=parameters['radius'],
                         filename=parameters['filename'],
                         output_format=parameters['output_format'],
                         async_job=parameters['async_job'],
                         cache=parameters['cache'],
                         verbose=parameters['verbose'])
        with pytest.raises(ValueError) as err:
            ehst._getCoordInput(1234)
        assert "Coordinates must be either a string or " \
               "astropy.coordinates" in err.value.args[0]

    def test_query_tap(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'async_job': False,
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        parameters2 = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}

        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.query_tap(query=parameters['query'],
                       async_job=parameters['async_job'],
                       output_file=parameters['output_file'],
                       output_format=parameters['output_format'],
                       verbose=parameters['verbose'])
        self.get_dummy_tap_handler().check_call("launch_job", parameters2)

    def test_get_tables(self):
        parameters = {'only_names': True,
                      'verbose': True}

        DummyHubbleTapHandler("get_tables", parameters)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.get_tables(only_names=True, verbose=True)

    def test_get_artifact(self, tmp_path):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        path = Path(tmp_path, "w0ji0v01t_c2f.fits.gz")
        ehst.get_artifact(artifact_id=path)

    def test_download_file(self, tmp_path):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        file = 'w0ji0v01t_c2f.fits'
        path = Path(tmp_path, file + '.gz')
        ehst.download_file(file=path, filename=path)

    def test_get_associated_files(self):
        observation_id = 'test'
        query = (f"select art.artifact_id as filename, p.calibration_level, art.archive_class as type, "
                 f"pg_size_pretty(art.size_uncompr) as size_uncompressed from ehst.artifact art "
                 f"join ehst.plane p on p.plane_id = art.plane_id where "
                 f"art.observation_id = '{observation_id}'")
        parameters = {'query': query,
                      'output_file': 'test2.vot',
                      'output_format': "votable",
                      'verbose': False}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(query=query), show_messages=False)
        ehst.get_associated_files(observation_id=observation_id)
        self.get_dummy_tap_handler(query=query).check_call("launch_job", parameters)

    @patch.object(ESAHubbleClass, 'get_associated_files')
    def test_download_fits(self, mock_associated_files):
        observation_id = 'test'
        query = (f"select art.artifact_id as filename, p.calibration_level, art.archive_class as type, "
                 f"pg_size_pretty(art.size_uncompr) as size_uncompressed from ehst.artifact art "
                 f"join ehst.plane p on p.plane_id = art.plane_id where "
                 f"art.observation_id = '{observation_id}'")
        parameters = {'query': query,
                      'output_file': 'test2.vot',
                      'output_format': "votable",
                      'verbose': False}
        mock_associated_files.return_value = [{'filename': 'test.fits'}]
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(query=query), show_messages=False)
        ehst.download_fits_files(observation_id=observation_id)
        self.get_dummy_tap_handler(query=query).check_call("launch_job", parameters)

    def test_is_not_gz(self, tmp_path):
        target_file = data_path('cone_search.vot')
        ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        assert esautils.check_rename_to_gz(target_file) in target_file

    def test_is_gz(self, tmp_path):
        ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        # test_file = data_path('m31.vot.test')
        temp_file = 'testgz'
        target_file = os.path.join(tmp_path, temp_file)
        with gzip.open(target_file, 'wb') as f:
            f.write(b'')
        # with open(test_file, 'rb') as f_in, gzip.open(target_file, 'wb') as f_out:
        #     f_out.writelines(f_in)
        assert esautils.check_rename_to_gz(target_file) in f"{target_file}.fits.gz"

    def test_get_columns(self):
        parameters = {'table_name': "table",
                      'only_names': True,
                      'verbose': True}

        dummyTapHandler = DummyHubbleTapHandler("get_columns", parameters)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.get_columns(table_name="table", only_names=True, verbose=True)
        dummyTapHandler.check_call("get_columns", parameters)

    def test_query_criteria_proposal(self):
        parameters1 = {'proposal': 12345,
                       'async_job': False,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True,
                       'get_query': True}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        test_query = ehst.query_criteria(proposal=parameters1['proposal'],
                                         async_job=parameters1['async_job'],
                                         output_file=parameters1['output_file'],
                                         output_format=parameters1['output_format'],
                                         verbose=parameters1['verbose'],
                                         get_query=parameters1['get_query'])
        parameters2 = {'query': test_query,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        parameters3 = {'query': "select * from ehst.archive where("
                                "proposal_id = '12345')",
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", parameters2)
        dummy_tap_handler.check_call("launch_job", parameters3)

    def test_retrieve_observations_from_proposal(self):
        program = 12345
        parameters1 = {'proposal': program,
                       'async_job': False,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True,
                       'get_query': True}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        ehst.get_observations_from_program(program=parameters1['proposal'])
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", None)
        dummy_tap_handler.check_method("launch_job")

    @patch.object(ESAHubbleClass, 'get_associated_files')
    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_download_fits_from_proposal(self, mock_observations, mock_files):
        mock_observations.return_value = {'observation_id': ['test']}
        mock_files.return_value = [{'filename': 'test.fits'}]
        tap_handler = self.get_dummy_tap_handler("load_data")
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler("load_data"), show_messages=False)
        ehst.download_files_from_program(program=12345, only_fits=True)
        tap_handler.check_method("load_data")

    @patch.object(ESAHubbleClass, 'get_associated_files')
    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_download_all_from_proposal(self, mock_observations, mock_files):
        mock_observations.return_value = {'observation_id': ['test']}
        mock_files.return_value = {'filename': ['test.fits']}
        tap_handler = self.get_dummy_tap_handler("load_data")
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler("load_data"), show_messages=False)
        ehst.download_files_from_program(program=12345, only_fits=False)
        tap_handler.check_method("load_data")

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
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        test_query = ehst.query_criteria(calibration_level=parameters1['calibration_level'],
                                         data_product_type=parameters1['data_product_type'],
                                         intent=parameters1['intent'],
                                         obs_collection=parameters1['obs_collection'],
                                         instrument_name=parameters1['instrument_name'],
                                         filters=parameters1['filters'],
                                         async_job=parameters1['async_job'],
                                         output_file=parameters1['output_file'],
                                         output_format=parameters1['output_format'],
                                         verbose=parameters1['verbose'],
                                         get_query=parameters1['get_query'])
        parameters2 = {'query': test_query,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        parameters3 = {'query': "select * from ehst.archive where("
                                "calibration_level=3 AND "
                                "data_product_type LIKE '%image%' AND "
                                "intent LIKE '%science%' AND (collection "
                                "LIKE '%HST%') AND (instrument_name LIKE "
                                "'%WFC3%') AND (filter "
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
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        test_query = ehst.query_criteria(calibration_level=parameters1['calibration_level'],
                                         data_product_type=parameters1['data_product_type'],
                                         intent=parameters1['intent'],
                                         obs_collection=parameters1['obs_collection'],
                                         instrument_name=parameters1['instrument_name'],
                                         filters=parameters1['filters'],
                                         async_job=parameters1['async_job'],
                                         output_file=parameters1['output_file'],
                                         output_format=parameters1['output_format'],
                                         verbose=parameters1['verbose'],
                                         get_query=parameters1['get_query'])
        parameters2 = {'query': test_query,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        parameters3 = {'query': "select * from ehst.archive where("
                                "calibration_level=1 AND "
                                "data_product_type LIKE '%image%' AND "
                                "intent LIKE '%science%' AND (collection "
                                "LIKE '%HST%') AND (instrument_name LIKE "
                                "'%WFC3%') AND (filter "
                                "LIKE '%F555W%'))",
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", parameters2)
        dummy_tap_handler.check_call("launch_job", parameters3)
        parameters1['calibration_level'] = 4
        with pytest.raises(KeyError) as err:
            ehst.query_criteria(calibration_level=parameters1['calibration_level'],
                                data_product_type=parameters1['data_product_type'],
                                intent=parameters1['intent'],
                                obs_collection=parameters1['obs_collection'],
                                instrument_name=parameters1['instrument_name'],
                                filters=parameters1['filters'],
                                async_job=parameters1['async_job'],
                                output_file=parameters1['output_file'],
                                output_format=parameters1['output_format'],
                                verbose=parameters1['verbose'],
                                get_query=parameters1['get_query'])
        assert "Calibration level must be between 0 and 3" in err.value.args[0]

    def test_cone_search_criteria(self):
        parameters1 = {'target': "m31",
                       'radius': 7,
                       'data_product_type': "image",
                       'obs_collection': ['HST'],
                       'instrument_name': ['ACS/WFC'],
                       'filters': ['F435W'],
                       'async_job': False,
                       'filename': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True}
        test_query = "select o.*, p.calibration_level, p.data_product_type, " \
                     "pos.ra, pos.dec from ehst.observation AS o JOIN " \
                     "ehst.plane as p on o.observation_uuid=p.observation_" \
                     "uuid JOIN ehst.position as pos on p.plane_id = " \
                     "pos.plane_id where((o.collection LIKE '%HST%') AND " \
                     "(o.instrument_name LIKE '%WFPC2%') AND " \
                     "(o.filter LIKE '%F606W%') AND " \
                     "1=CONTAINS(POINT('ICRS', pos.ra, pos.dec)," \
                     "CIRCLE('ICRS', 10.6847083, 41.26875, " \
                     "0.11666666666666667)))"
        parameters3 = {'query': test_query,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': False}
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        query_criteria_query = "select o.*, p.calibration_level, " \
                               "p.data_product_type, pos.ra, pos.dec from " \
                               "ehst.observation AS o JOIN ehst.plane as p " \
                               "on o.observation_uuid=p.observation_uuid " \
                               "JOIN ehst.position as pos on p.plane_id = " \
                               "pos.plane_id where((o.collection LIKE " \
                               "'%HST%') AND (o.instrument_name LIKE " \
                               "'%WFPC2%') AND (o.filter " \
                               "LIKE '%F606W%'))"
        ehst.query_criteria = MagicMock(return_value=query_criteria_query)
        target = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        ehst._query_tap_target = MagicMock(return_value=target)
        ehst.cone_search_criteria(target=parameters1['target'],
                                  radius=parameters1['radius'],
                                  data_product_type=parameters1
                                  ['data_product_type'],
                                  obs_collection=parameters1['obs_collection'],
                                  instrument_name=parameters1
                                  ['instrument_name'],
                                  filters=parameters1['filters'],
                                  async_job=parameters1['async_job'],
                                  filename=parameters1['filename'],
                                  output_format=parameters1['output_format'],
                                  verbose=parameters1['verbose'])
        dummy_tap_handler = DummyHubbleTapHandler("launch_job", parameters3)
        dummy_tap_handler.check_call("launch_job", parameters3)
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        ehst.cone_search_criteria(coordinates=c,
                                  radius=parameters1['radius'],
                                  data_product_type=parameters1
                                  ['data_product_type'],
                                  obs_collection=parameters1['obs_collection'],
                                  instrument_name=parameters1
                                  ['instrument_name'],
                                  filters=parameters1['filters'],
                                  async_job=parameters1['async_job'],
                                  filename=parameters1['filename'],
                                  output_format=parameters1['output_format'],
                                  verbose=parameters1['verbose'])
        with pytest.raises(TypeError) as err:
            ehst.cone_search_criteria(target=parameters1['target'],
                                      coordinates=123,
                                      radius=parameters1['radius'],
                                      data_product_type=parameters1
                                      ['data_product_type'],
                                      obs_collection=parameters1
                                      ['obs_collection'],
                                      instrument_name=parameters1
                                      ['instrument_name'],
                                      filters=parameters1['filters'],
                                      async_job=parameters1['async_job'],
                                      filename=parameters1['filename'],
                                      output_format=parameters1
                                      ['output_format'],
                                      verbose=parameters1['verbose'])
        assert "Please use only target or coordinates as" \
               "parameter." in err.value.args[0]

    def test_query_criteria_no_params(self):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
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
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        with pytest.raises(ValueError) as err:
            ehst.query_criteria(instrument_name=[1],
                                async_job=False,
                                output_file="output_test_query_"
                                            "by_criteria.vot.gz",
                                output_format="votable",
                                verbose=True)
        assert "One of the lists is empty or there are " \
               "elements that are not strings" in err.value.args[0]

    def test__get_decoded_string(self):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        dummy = '\x74\x65\x73\x74'
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == 'test'

    def test__get_decoded_string_unicodedecodeerror(self):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        dummy = '\xd0\x91'
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == dummy

    def test__get_decoded_string_attributeerror(self):
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        dummy = True
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == dummy

    @patch.object(ESAHubbleClass, 'query_tap')
    def test__select_related_composite(self, mock_query):
        arr = {'a': np.array([1, 4], dtype=np.int32),
               'b': [2.0, 5.0],
               'observation_id': ['x', 'y']}
        data_table = Table(arr)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst._select_related_composite(observation_id=dummy_obs_id)
        assert set(['x', 'y']).issubset(set(oids))

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_select_related_members(self, mock_query):
        arr = {'a': np.array([1, 4], dtype=np.int32),
               'b': [2.0, 5.0],
               'members': ['caom:HST/test', 'y']}
        data_table = Table(arr)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst._select_related_members(observation_id=dummy_obs_id)
        assert oids == ['test']

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_get_observation_type(self, mock_query):
        arr = {'a': np.array([1, 4], dtype=np.int32),
               'b': [2.0, 5.0],
               'obs_type': ['HST Test', 'y']}
        data_table = Table(arr)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst.get_observation_type(observation_id=dummy_obs_id)
        assert oids == 'HST Test'

    def test_get_observation_type_obs_id_none_valueerror(self):
        with pytest.raises(ValueError):
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            dummy_obs_id = None
            ehst.get_observation_type(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_get_observation_type_invalid_obs_id_valueerror(self, mock_query):
        with pytest.raises(ValueError):
            arr = {'a': np.array([], dtype=np.int32),
                   'b': [],
                   'obs_type': []}
            data_table = Table(arr)
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            mock_query.return_value = data_table
            dummy_obs_id = '1234'
            ehst.get_observation_type(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'query_tap')
    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_hst_link(self, mock_observation_type, mock_query):
        mock_observation_type.return_value = "HST"
        arr = {'a': np.array([1], dtype=np.int32),
               'b': [2.0],
               'observation_id': ['1234']}
        data_table = Table(arr)
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst.get_hap_hst_link(observation_id=dummy_obs_id)
        assert oids == ['1234']

    @patch.object(ESAHubbleClass, 'get_observation_type')
    @patch.object(ESAHubbleClass, '_select_related_members')
    def test_get_hap_link(self, mock_select_related_members, mock_observation_type):
        mock_select_related_members.return_value = 'test'
        mock_observation_type.return_value = "HAP"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        dummy_obs_id = "1234"
        oids = ehst.get_hap_hst_link(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_hap_hst_link_invalid_id_valueerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "valueerror"
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_hap_hst_link(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_hap_hst_link_compositeerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "HAP Composite"
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_hap_hst_link(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, '_select_related_members')
    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_composite(self, mock_observation_type, mock_select_related_members):
        mock_observation_type.return_value = "Composite"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_select_related_members.return_value = 'test'
        dummy_obs_id = "1234"
        oids = ehst.get_member_observations(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, '_select_related_composite')
    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_simple(self, mock_observation_type, mock_select_related_composite):
        mock_observation_type.return_value = "Simple"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        mock_select_related_composite.return_value = 'test'
        dummy_obs_id = "1234"
        oids = ehst.get_member_observations(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_invalid_id_valueerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "valueerror"
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_member_observations(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'query_criteria')
    @patch.object(ESAHubbleClass, '_query_tap_target')
    @patch.object(ESAHubbleClass, 'query_tap')
    def test_cone_search_criteria_only_target(self, mock_query_tap, mock__query_tap_target, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        mock__query_tap_target.return_value = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        mock_query_tap.return_value = "table"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        oids = ehst.cone_search_criteria(target="m11", radius=1)
        assert oids == 'table'

    @patch.object(ESAHubbleClass, 'query_criteria')
    @patch.object(ESAHubbleClass, 'query_tap')
    def test_cone_search_criteria_only_coordinates(self, mock_query_tap, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        mock_query_tap.return_value = "table"
        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        oids = ehst.cone_search_criteria(coordinates="00h42m44.51s +41d16m08.45s", radius=1)
        assert oids == 'table'

    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_cone_search_criteria_typeerror(self, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        with pytest.raises(TypeError):
            ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
            ehst.cone_search_criteria(coordinates="00h42m44.51s +41d16m08.45s", target="m11", radius=1)

    def test_query_hst_tap(self):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'async_job': False,
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        ehst = ESAHubbleClass(tap_handler=self.get_dummy_tap_handler(), show_messages=False)
        with pytest.warns(AstropyDeprecationWarning):
            ehst.query_hst_tap(query=parameters['query'],
                               async_job=parameters['async_job'],
                               output_file=parameters['output_file'],
                               output_format=parameters['output_format'],
                               verbose=parameters['verbose'])

    @patch("http.client.HTTPSConnection")
    @patch("http.client.HTTPResponse")
    def test_show_messages(self, mock_conn, mock_res):
        mock_res.status = 400
        mock_conn.getresponse = MagicMock(return_value=mock_res)
        ESAHubbleClass()
        mock_res.assert_called()
