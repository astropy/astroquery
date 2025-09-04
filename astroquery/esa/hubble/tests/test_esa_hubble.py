# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==============
eHST Tap Tests
==============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import os
import functools
import gzip
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock
from unittest.mock import patch
import xml.etree.ElementTree as ET
from requests.models import Response
import io


import numpy as np
import pytest
from astropy import coordinates
from astropy.table.table import Table
from pyvo.dal import DALQuery

from astroquery.esa.hubble import ESAHubbleClass
import astroquery.esa.utils.utils as esautils


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class FakeHTTPResponse:
    def __init__(self, data):
        self._data = data
        self._read_called = False

    def read(self, decode_content=True, **kwargs):
        if not self._read_called:
            self._read_called = True
            return self._data
        return b""  # EOF after first read


class TestESAHubble:

    def test_download_product_errors(self):
        ehst = ESAHubbleClass(show_messages=False)

        with pytest.raises(ValueError) as err:
            ehst.download_product(observation_id="J6FL25S4Q",
                                  product_type="DUMMY")
        assert "This product_type is not allowed" in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.utils.utils.check_rename_to_gz')
    def test_download_product_by_calibration(self, rename_mock, download_mock, tmp_path):
        path = Path(tmp_path, "J6FL25S4Q.vot.test")
        parameters = {'observation_id': "J6FL25S4Q",
                      'cal_level': "RAW",
                      'filename': path,
                      'verbose': True}
        rename_mock.return_value = path
        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.download_product(
            observation_id=parameters['observation_id'],
            calibration_level=parameters['cal_level'],
            filename=parameters['filename'],
            verbose=parameters['verbose'])
        assert rename_mock.call_count == 1
        assert download_mock.call_count == 1
        assert result == path

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.utils.utils.check_rename_to_gz')
    def test_download_product_by_product_type(self, rename_mock, download_mock, tmp_path):
        path = Path(tmp_path, "J6FL25S4Q.vot.test")
        parameters = {'observation_id': "J6FL25S4Q",
                      'product_type': "SCIENCE",
                      'filename': path,
                      'verbose': True}
        rename_mock.return_value = path
        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.download_product(
            observation_id=parameters['observation_id'],
            product_type=parameters['product_type'],
            filename=parameters['filename'],
            verbose=parameters['verbose'])
        assert rename_mock.call_count == 1
        assert download_mock.call_count == 1
        assert result == path

        parameters['product_type'] = "SCIENCE"
        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.download_product(
            observation_id=parameters['observation_id'],
            product_type=parameters['product_type'],
            filename=parameters['filename'],
            verbose=parameters['verbose'])

        assert rename_mock.call_count == 2
        assert download_mock.call_count == 2
        assert result == path

        parameters['product_type'] = "PREVIEW"
        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.download_product(
            observation_id=parameters['observation_id'],
            product_type=parameters['product_type'],
            filename=parameters['filename'],
            verbose=parameters['verbose'])

        assert rename_mock.call_count == 3
        assert download_mock.call_count == 3
        assert result == path

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    def test_get_postcard(self, download_mock, tmp_path):
        path = Path(tmp_path, "X0MC5101T.vot")
        ehst = ESAHubbleClass(show_messages=False)
        observation_id = "X0MC5101T"
        result = ehst.get_postcard(
            observation_id=observation_id,
            filename=path.__str__(),
            verbose=True)
        args, kwargs = download_mock.call_args
        assert kwargs["params"]["PRODUCTTYPE"] == 'THUMBNAIL'
        assert download_mock.call_count == 1
        assert result == path.__str__()

        result = ehst.get_postcard(
            observation_id=observation_id,
            filename=path.__str__(), resolution=1024,
            verbose=True)
        args, kwargs = download_mock.call_args
        assert kwargs["params"]["PRODUCTTYPE"] == 'PREVIEW'
        assert download_mock.call_count == 2
        assert result == path.__str__()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch.object(ESAHubbleClass, 'cone_search')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_query_target(self, mock_servlet_request, mock_cone_search):
        mock_servlet_request.return_value = {'objects': [{"raDegrees": 90, "decDegrees": 90}]}
        mock_cone_search.return_value = "test"
        ehst = ESAHubbleClass(show_messages=False)
        table = ehst.query_target(name="test")
        assert table == "test"

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    def test_cone_search(self):
        coords = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s",
                                      frame='icrs')
        # query_tap_mock.return_value = "test result"
        ehst = ESAHubbleClass(show_messages=False)
        parameters = {'coordinates': coords,
                      'radius': 0.0,
                      'output_format': 'votable',
                      'cache': True}
        target_file = data_path('cone_search.vot')
        with open(target_file, mode='rb') as file:
            target_obj = file.read()
            fake_response = FakeHTTPResponse(target_obj)
            read_partial = functools.partial(fake_response.read)
            mock_response = MagicMock()
            mock_response.read = read_partial
            with patch.object(DALQuery, 'execute_stream', return_value=mock_response):

                result = ehst.cone_search(
                    coordinates=parameters['coordinates'],
                    radius=parameters['radius'],
                    output_format=parameters['output_format'],
                    cache=parameters['cache'])

                # Trying to get number of elements read
                # Define the namespace map
                ns = {'v': 'http://www.ivoa.net/xml/VOTable/v1.2'}
                # Parse XML string
                root = ET.fromstring(target_obj.decode('utf8'))
                # Find all TR elements inside TABLEDATA (with namespace)
                trs = root.findall('.//v:TABLEDATA/v:TR', ns)
                # Extract first <TD> from each <TR> and count occurrences
                first_column_values = [tr.find('v:TD', ns).text for tr in trs if tr.find('v:TD', ns) is not None]
                # Count unique values
                counts = Counter(first_column_values)
                unique_list = list(counts.keys())

                assert len(unique_list) == len(result)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService')
    def test_cone_search_coords(self, mock_tap):
        coords = "00h42m44.51s +41d16m08.45s"

        parameters = {'coordinates': coords,
                      'radius': 0.0,
                      'async_job': False,
                      'output_format': 'votable',
                      'cache': True,
                      'verbose': True}

        ehst = ESAHubbleClass(show_messages=False)
        ehst.cone_search(coordinates=parameters['coordinates'],
                         radius=parameters['radius'],
                         output_format=parameters['output_format'],
                         async_job=parameters['async_job'],
                         cache=parameters['cache'],
                         verbose=parameters['verbose'])
        with pytest.raises(ValueError) as err:
            ehst._getCoordInput(1234)
        assert "Coordinates must be either a string or " \
               "astropy.coordinates" in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.run_sync')
    def test_query_tap(self, mock_search):
        parameters = {'query': "select top 10 * from hsc_v2.hubble_sc2",
                      'async_job': False,
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        ehst = ESAHubbleClass(show_messages=False)
        ehst.query_tap(query=parameters['query'],
                       async_job=parameters['async_job'],
                       output_file=parameters['output_file'],
                       output_format=parameters['output_format'],
                       verbose=parameters['verbose'])

        mock_search.assert_called_once_with(parameters['query'])

    def test_get_tables(self):
        table_set = PropertyMock()
        table_set.keys.return_value = ['caom2.harveststate', 'caom2.publications']
        table_set.values.return_value = ['caom2.harveststate', 'caom2.publications']
        with patch('astroquery.esa.integral.core.pyvo.dal.TAPService', autospec=True) as hubble_mock:
            hubble_mock.return_value.tables = table_set
            ehst = ESAHubbleClass(show_messages=False)
            tables = ehst.get_tables()
            assert len(tables) == 2

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.utils.utils.check_rename_to_gz')
    def test_get_artifact(self, rename_mock, download_mock, tmp_path):
        filename = "w0ji0v01t_c2f.fits.gz"
        ehst = ESAHubbleClass(show_messages=False)
        path = Path(tmp_path, filename)
        rename_mock.return_value = path
        assert ehst.get_artifact(artifact_id=path) == path

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.utils.utils.check_rename_to_gz')
    def test_download_file(self, rename_mock, download_mock, tmp_path):
        ehst = ESAHubbleClass(show_messages=False)
        file = 'w0ji0v01t_c2f.fits'
        path = Path(tmp_path, file + '.gz')
        rename_mock.return_value = path
        assert ehst.download_file(file=path, filename=path) == path

    @patch.object(ESAHubbleClass, 'tap', new_callable=PropertyMock)
    def test_get_associated_files(self, mock_tap_prop):
        observation_id = 'test'
        # Mock the return of self.vo
        mock_tap_service = MagicMock()
        mock_tap_prop.return_value = mock_tap_service

        # Mock the chain: search().to_table()
        mock_table = "mocked table result"
        mock_search_result = MagicMock()
        mock_search_result.to_table.return_value = mock_table
        mock_tap_service.run_sync.return_value = mock_search_result

        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.get_associated_files(observation_id=observation_id)
        assert result == mock_table

    @patch.object(ESAHubbleClass, 'download_file')
    @patch.object(ESAHubbleClass, 'get_associated_files')
    def test_download_fits(self, mock_associated_files, mock_download_file):
        observation_id = 'test'
        filename = "test.fits"
        path = "/dummy/path/" + filename
        mock_associated_files.return_value = [{'filename': filename}]
        mock_download_file.return_value = path
        ehst = ESAHubbleClass(show_messages=False)
        ehst.download_fits_files(observation_id=observation_id)
        mock_download_file.assert_called_once_with(file=filename, filename=filename, folder=None, verbose=False)

    def test_is_not_gz(self, tmp_path):
        target_file = data_path('cone_search.vot')
        ESAHubbleClass(show_messages=False)
        assert esautils.check_rename_to_gz(target_file) in target_file

    def test_is_gz(self, tmp_path):
        ESAHubbleClass(show_messages=False)
        temp_file = 'testgz'
        target_file = os.path.join(tmp_path, temp_file)
        with gzip.open(target_file, 'wb') as f:
            f.write(b'')
        assert esautils.check_rename_to_gz(target_file) in f"{target_file}.fits.gz"

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch.object(ESAHubbleClass, 'get_tables')
    def test_get_columns(self, get_tables_mock):
        # Create a mock VOSITable object
        mock_table1 = MagicMock()
        mock_table1.name = "table1"
        mock_table1_col1 = MagicMock()
        mock_table1_col1.name = "column1"
        mock_table1_col2 = MagicMock()
        mock_table1_col2.name = "column2"
        mock_table1.columns = [mock_table1_col1, mock_table1_col2]

        mock_table2 = MagicMock()
        mock_table2.name = "table2"
        mock_table2.columns = [MagicMock(name="column3"), MagicMock(name="column4")]

        get_tables_mock.return_value = [mock_table1, mock_table2]
        ehst = ESAHubbleClass(show_messages=False)
        result = ehst.get_columns(table_name="table1", only_names=True, verbose=True)
        assert len(result) == 2
        assert result[0] == "column1"
        assert result[1] == "column2"

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    def test_query_criteria_proposal(self):
        parameters1 = {'proposal': 12345,
                       'async_job': False,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True,
                       'get_query': True}
        ehst = ESAHubbleClass(show_messages=False)
        test_query = ehst.query_criteria(proposal=parameters1['proposal'],
                                         async_job=parameters1['async_job'],
                                         output_file=parameters1['output_file'],
                                         output_format=parameters1['output_format'],
                                         verbose=parameters1['verbose'],
                                         get_query=parameters1['get_query'])
        assert test_query == "select * from ehst.archive where(proposal_id = '12345')"

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch.object(ESAHubbleClass, 'query_tap')
    def test_retrieve_observations_from_proposal(self, mock_query_tap):
        program = 12345
        parameters1 = {'proposal': program,
                       'async_job': False,
                       'output_file': "output_test_query_by_criteria.vot.gz",
                       'output_format': "votable",
                       'verbose': True,
                       'get_query': True}
        ehst = ESAHubbleClass(show_messages=False)
        ehst.get_observations_from_program(program=parameters1['proposal'])
        mock_query_tap.assert_called_once_with(
            query="select * from ehst.archive where(proposal_id = '12345')", output_file=None,
            output_format=parameters1['output_format'],
            async_job=parameters1['async_job'],
            verbose=False)

    @patch.object(ESAHubbleClass, 'download_file')
    @patch.object(ESAHubbleClass, 'get_associated_files')
    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_download_fits_from_proposal(self, mock_observations, mock_files, mock_download_file):
        mock_observations.return_value = {'observation_id': ['test']}
        mock_files.return_value = [{'filename': 'test.fits'}]
        ehst = ESAHubbleClass(show_messages=False)
        ehst.download_files_from_program(program=12345, only_fits=True)
        mock_download_file.assert_called_once_with(file='test.fits', filename='test.fits', folder=None, verbose=False)

    @patch.object(ESAHubbleClass, 'download_file')
    @patch.object(ESAHubbleClass, 'get_associated_files')
    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_download_all_from_proposal(self, mock_observations, mock_files, mock_download_file):
        mock_observations.return_value = {'observation_id': ['test']}
        mock_files.return_value = {'filename': ['test.fits', 'test2.fits']}
        ehst = ESAHubbleClass(show_messages=False)
        ehst.download_files_from_program(program=12345, only_fits=False)
        mock_download_file.assert_any_call(file='test.fits', folder=None)
        mock_download_file.assert_any_call(file='test2.fits', folder=None)
        assert mock_download_file.call_count == 2

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
        ehst = ESAHubbleClass(show_messages=False)
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
        assert test_query == ("select * from ehst.archive where("
                              "calibration_level=3 AND "
                              "data_product_type LIKE '%image%' AND "
                              "intent LIKE '%science%' AND (collection "
                              "LIKE '%HST%') AND (instrument_name LIKE "
                              "'%WFC3%') AND (filter "
                              "LIKE '%F555W%'))")

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
        ehst = ESAHubbleClass(show_messages=False)
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
        assert test_query == (
            "select * from ehst.archive where("
            "calibration_level=1 AND "
            "data_product_type LIKE '%image%' AND "
            "intent LIKE '%science%' AND (collection "
            "LIKE '%HST%') AND (instrument_name LIKE "
            "'%WFC3%') AND (filter "
            "LIKE '%F555W%'))")
        parameters1['calibration_level'] = 4
        with pytest.raises(KeyError) as err:
            ehst.query_criteria(
                calibration_level=parameters1['calibration_level'],
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

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_cone_search_criteria(self, mock_query_tap):
        parameters1 = {
            'target': "m31",
            'radius': 7,
            'data_product_type': "image",
            'obs_collection': ['HST'],
            'instrument_name': ['ACS/WFC'],
            'filters': ['F435W'],
            'async_job': False,
            'filename': "output_test_query_by_criteria.vot.gz",
            'output_format': "votable",
            'verbose': True
        }
        ehst = ESAHubbleClass(show_messages=False)
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
        mock_query_tap.assert_called_once()

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
        assert mock_query_tap.call_count == 2
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

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_query_criteria_no_params(self, mock_query_tap):
        ehst = ESAHubbleClass(show_messages=False)
        ehst.query_criteria(async_job=False,
                            output_file="output_test_query_"
                                        "by_criteria.vot.gz",
                            output_format="votable",
                            verbose=True)
        mock_query_tap.assert_called_once_with(query='select * from ehst.archive', async_job=False,
                                               output_file="output_test_query_by_criteria.vot.gz",
                                               output_format="votable",
                                               verbose=True)

    def test_empty_list(self):
        ehst = ESAHubbleClass(show_messages=False)
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
        ehst = ESAHubbleClass(show_messages=False)
        dummy = '\x74\x65\x73\x74'
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == 'test'

    def test__get_decoded_string_unicodedecodeerror(self):
        ehst = ESAHubbleClass(show_messages=False)
        dummy = '\xd0\x91'
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == dummy

    def test__get_decoded_string_attributeerror(self):
        ehst = ESAHubbleClass(show_messages=False)
        dummy = True
        decoded_string = ehst._get_decoded_string(dummy)
        assert decoded_string == dummy

    @patch.object(ESAHubbleClass, 'query_tap')
    def test__select_related_composite(self, mock_query):
        arr = {'a': np.array([1, 4], dtype=np.int32),
               'b': [2.0, 5.0],
               'observation_id': ['x', 'y']}
        data_table = Table(arr)
        ehst = ESAHubbleClass(show_messages=False)
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
        ehst = ESAHubbleClass(show_messages=False)
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
        ehst = ESAHubbleClass(show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst.get_observation_type(observation_id=dummy_obs_id)
        assert oids == 'HST Test'

    def test_get_observation_type_obs_id_none_valueerror(self):
        with pytest.raises(ValueError):
            ehst = ESAHubbleClass(show_messages=False)
            dummy_obs_id = None
            ehst.get_observation_type(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'query_tap')
    def test_get_observation_type_invalid_obs_id_valueerror(self, mock_query):
        with pytest.raises(ValueError):
            arr = {'a': np.array([], dtype=np.int32),
                   'b': [],
                   'obs_type': []}
            data_table = Table(arr)
            ehst = ESAHubbleClass(show_messages=False)
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
        ehst = ESAHubbleClass(show_messages=False)
        mock_query.return_value = data_table
        dummy_obs_id = "1234"
        oids = ehst.get_hap_hst_link(observation_id=dummy_obs_id)
        assert oids == ['1234']

    @patch.object(ESAHubbleClass, 'get_observation_type')
    @patch.object(ESAHubbleClass, '_select_related_members')
    def test_get_hap_link(self, mock_select_related_members, mock_observation_type):
        mock_select_related_members.return_value = 'test'
        mock_observation_type.return_value = "HAP"
        ehst = ESAHubbleClass(show_messages=False)
        dummy_obs_id = "1234"
        oids = ehst.get_hap_hst_link(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_hap_hst_link_invalid_id_valueerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "valueerror"
            ehst = ESAHubbleClass(show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_hap_hst_link(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_hap_hst_link_compositeerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "HAP Composite"
            ehst = ESAHubbleClass(show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_hap_hst_link(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, '_select_related_members')
    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_composite(self, mock_observation_type, mock_select_related_members):
        mock_observation_type.return_value = "Composite"
        ehst = ESAHubbleClass(show_messages=False)
        mock_select_related_members.return_value = 'test'
        dummy_obs_id = "1234"
        oids = ehst.get_member_observations(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, '_select_related_composite')
    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_simple(self, mock_observation_type, mock_select_related_composite):
        mock_observation_type.return_value = "Simple"
        ehst = ESAHubbleClass(show_messages=False)
        mock_select_related_composite.return_value = 'test'
        dummy_obs_id = "1234"
        oids = ehst.get_member_observations(observation_id=dummy_obs_id)
        assert oids == 'test'

    @patch.object(ESAHubbleClass, 'get_observation_type')
    def test_get_member_observations_invalid_id_valueerror(self, mock_observation_type):
        with pytest.raises(ValueError):
            mock_observation_type.return_value = "valueerror"
            ehst = ESAHubbleClass(show_messages=False)
            dummy_obs_id = "1234"
            ehst.get_member_observations(observation_id=dummy_obs_id)

    @patch.object(ESAHubbleClass, 'query_criteria')
    @patch.object(ESAHubbleClass, '_query_tap_target')
    @patch.object(ESAHubbleClass, 'query_tap')
    def test_cone_search_criteria_only_target(self, mock_query_tap, mock__query_tap_target, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        mock__query_tap_target.return_value = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        mock_query_tap.return_value = "table"
        ehst = ESAHubbleClass(show_messages=False)
        oids = ehst.cone_search_criteria(target="m11", radius=1)
        assert oids == 'table'

    @patch.object(ESAHubbleClass, 'query_criteria')
    @patch.object(ESAHubbleClass, 'query_tap')
    def test_cone_search_criteria_only_coordinates(self, mock_query_tap, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        mock_query_tap.return_value = "table"
        ehst = ESAHubbleClass(show_messages=False)
        oids = ehst.cone_search_criteria(coordinates="00h42m44.51s +41d16m08.45s", radius=1)
        assert oids == 'table'

    @patch.object(ESAHubbleClass, 'query_criteria')
    def test_cone_search_criteria_typeerror(self, mock_query_criteria):
        mock_query_criteria.return_value = "Simple query"
        with pytest.raises(TypeError):
            ehst = ESAHubbleClass(show_messages=False)
            ehst.cone_search_criteria(coordinates="00h42m44.51s +41d16m08.45s", target="m11", radius=1)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_show_messages(self, mock_execute_servlet_request):
        ESAHubbleClass()
        mock_execute_servlet_request.assert_called()

    def test_parse_messages_response(self):
        ehst = ESAHubbleClass(show_messages=False)
        response = Response()
        response.status_code = 200
        plain_text = (
            "notification_id1[type: type1,subtype1]=msg1\n"
            "notification_id2[type: type2,subtype2]=msg2\n"
            "notification_idn[type: typen,subtypen]=msgn"
        )
        response._content = plain_text.encode('utf-8')  # encode to bytes
        response.headers['Content-Type'] = 'text/plain'
        response.raw = io.BytesIO(response._content)
        messages = ehst.parse_messages_response(response)
        assert len(messages) == 3
        assert messages == ["msg1", "msg2", "msgn"]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch.object(ESAHubbleClass, 'query_tap')
    @patch.object(ESAHubbleClass, '_get_decoded_string')
    def test_get_datalabs_path(self, mock_get_decoded_string, mock_query_tap):
        ehst = ESAHubbleClass(show_messages=False)

        with patch('os.path.exists') as mock_exists:
            # Set up the return values for the query_tap method
            values = [
                {"file_path": ["path/to/file"]},   # First query result
                {"observation_id": ["obs123"]},    # Second query result
                {"instrument_name": ["instrumentXYZ"]}   # Third query result
            ]
            mock_query_tap.side_effect = values + values
            # Set up the return value for the _get_decoded_string method
            mock_get_decoded_string.return_value = "/hstdata/hstdata_i/i/b4x/04"
            # Set up the return value for os.path.exists
            mock_exists.return_value = True
            # Example usage
            filename = "ib4x04ivq_flt.jpg"
            default_volume = None
            full_path = ehst.get_datalabs_path(filename=filename, default_volume=default_volume)
            assert full_path == "/data/user/hub_hstdata_i/i/b4x/04/ib4x04ivq_flt.jpg"

            # Test with default_volume provided
            default_volume = "myPath"

            full_path = ehst.get_datalabs_path(filename=filename, default_volume=default_volume)
            assert full_path == "/data/user/myPath/i/b4x/04/ib4x04ivq_flt.jpg"
