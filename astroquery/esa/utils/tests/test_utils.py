# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
ESA UTILS tests
===============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os.path
import shutil
import tempfile
from unittest.mock import patch, Mock, PropertyMock, MagicMock

import astroquery.esa.utils.utils as esautils
from astropy.io.registry import IORegistryError
from astropy.table import Table
from requests import HTTPError
from astropy import units as u

import pytest

from astroquery.esa.utils.tests import mocks


def get_dummy_table():
    data = {
        "name": ['Crab'],
        "ra": [83.63320922851562],
        "dec": [22.01447105407715],
    }

    # Create an Astropy Table with the mock data
    return Table(data)


def get_iter_content_mock():
    test_file_content = b"Mocked file content."
    for i in range(0, len(test_file_content), 8192):
        yield test_file_content[i:i + 8192]


def get_dummy_json():
    return {"resolver": "Test", "objects": [{"decDegrees": 22.0174, "raDegrees": 83.6324}]}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def close_file(file):
    file.close()


def close_files(file_list):
    for file in file_list:
        close_file(file['fits'])


def create_temp_folder():
    return tempfile.TemporaryDirectory()


def copy_to_temporal_path(data_path, temp_folder, filename):
    temp_data_dir = os.path.join(temp_folder.name, filename)
    shutil.copy(data_path, temp_data_dir)
    return temp_data_dir


class DummyTapTable:
    def __init__(self, columns):
        self.columns = columns


class DummyColumn:
    def __init__(self, name, description, unit, datatype, ucd, utype):
        self.name = name
        self.description = description
        self.unit = unit
        self.datatype = datatype
        self.ucd = ucd
        self.utype = utype


class DummyDatatype:
    def __init__(self, content):
        self.content = content


class DummyTapClass(esautils.EsaTap):
    ESA_ARCHIVE_NAME = "DummyClass"
    TAP_URL = "dummyUrl"
    LOGIN_URL = "dummyLogin"
    LOGOUT_URL = "dummyLogout"


class TestEsaUtils:

    @patch('pyvo.auth.authsession.AuthSession._request')
    def test_esa_auth_session_url(self, mock_get):
        mock_get.return_value = {}

        esa_session = esautils.ESAAuthSession()
        esa_session._request('GET', 'https://dummy.com/service')

        mock_get.assert_called_once_with('GET', 'https://dummy.com/service',
                                         params={'TAPCLIENT': 'ASTROQUERY'})

    def test_get_degree_radius(self):
        assert esautils.get_degree_radius(12.0) == 12.0
        assert esautils.get_degree_radius(12) == 12.0
        assert esautils.get_degree_radius(30 * u.arcmin) == 0.5

    def test_download_table(self, tmp_cwd):
        dummy_table = get_dummy_table()
        filename = 'test.votable'
        esautils.download_table(dummy_table, output_file=filename, output_format='votable')
        assert os.path.exists(filename)

        with pytest.raises(IORegistryError) as err:
            esautils.download_table(dummy_table, output_file=filename)
        assert 'Format could not be identified' in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService')
    def test_execute_servlet_request(self, mock_tap):

        mock_tap._session.get.raise_for_status.return_value = None
        mock_tap._session.get.json.return_value = {"status": "success", "token": "mocked_token"}

        query_params = {'test': 'dummy'}
        esautils.execute_servlet_request(url='https://dummyurl.com/service', tap=mock_tap, query_params=query_params)

        mock_tap._session.get.assert_called_once_with(url='https://dummyurl.com/service',
                                                      params={'test': 'dummy', 'TAPCLIENT': 'ASTROQUERY'})

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService')
    def test_execute_servlet_request_with_parser_method(self, mock_tap):
        mock_parser_method = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_tap._session.get.return_value = mock_response
        query_params = {'test': 'dummy'}
        esautils.execute_servlet_request(
            url='https://dummyurl.com/service',
            tap=mock_tap,
            query_params=query_params,
            parser_method=mock_parser_method
        )

        mock_tap._session.get.assert_called_once_with(url='https://dummyurl.com/service',
                                                      params={'test': 'dummy', 'TAPCLIENT': 'ASTROQUERY'})

        mock_parser_method.assert_called_once()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService')
    def test_execute_servlet_request_error(self, mock_tap):
        error_message = "Mocked HTTP error"
        mock_tap._session.get.side_effect = HTTPError(error_message)

        query_params = {'test': 'dummy'}

        with pytest.raises(HTTPError) as err:
            esautils.execute_servlet_request(url='https://dummyurl.com/service',
                                             tap=mock_tap, query_params=query_params)
        assert error_message in err.value.args[0]

    @patch("pyvo.auth.authsession.AuthSession.get")
    def test_download_local(self, mock_get, tmp_cwd):
        iter_content_mock = get_iter_content_mock()
        mock_response = Mock()
        mock_response.iter_content.side_effect = iter_content_mock
        mock_response.json.return_value = iter_content_mock
        mock_response.raise_for_status.return_value = None

        mock_get.iter_content.return_value = mock_response

        esa_session = esautils.ESAAuthSession()

        filename = 'test_file.fits'
        esautils.download_file(url='http://dummyurl.com/download', session=esa_session,
                               params={'file': filename}, filename=filename)

        mock_get.assert_called_once_with('http://dummyurl.com/download', stream=True,
                                         params={'file': filename, 'TAPCLIENT': 'ASTROQUERY'})

        assert os.path.exists(filename)

    @patch("pyvo.auth.authsession.AuthSession.get")
    def test_download_cache(self, mock_get, tmp_cwd):
        iter_content_mock = get_iter_content_mock()
        mock_response = Mock()
        mock_response.iter_content.side_effect = iter_content_mock
        mock_response.json.return_value = iter_content_mock
        mock_response.raise_for_status.return_value = None

        mock_get.iter_content.return_value = mock_response

        esa_session = esautils.ESAAuthSession()

        filename = 'test_file2.fits'
        cache_folder = './cache/'
        esautils.download_file(url='http://dummyurl.com/download', session=esa_session,
                               params={'file': filename}, filename=filename,
                               cache=True, cache_folder=cache_folder)

        mock_get.assert_called_once_with('http://dummyurl.com/download', stream=True,
                                         params={'file': filename, 'TAPCLIENT': 'ASTROQUERY'})

        assert not os.path.exists(filename)
        assert os.path.exists(esautils.get_cache_filepath(filename=filename, cache_path=cache_folder))

    def test_read_tar(self):
        temp_path = create_temp_folder()
        tar_file = copy_to_temporal_path(data_path=data_path('tar_file.tar'), temp_folder=temp_path,
                                         filename='tar_file.tar')

        files = esautils.read_downloaded_fits([tar_file])

        assert len(files) == 1
        assert files[0]['filename'] == 'test.fits'

        close_files(files)
        temp_path.cleanup()

    def test_read_tar_gz(self):
        temp_path = create_temp_folder()
        tar_gz_file = copy_to_temporal_path(data_path=data_path('tar_gz_file.tar.gz'), temp_folder=temp_path,
                                            filename='tar_gz_file.tar.gz')

        files = esautils.read_downloaded_fits([tar_gz_file])

        # Only 1 FITS file inside, the other file is a .txt file, so it should not be read
        assert len(files) == 1
        assert files[0]['filename'] == 'test.fits'

        close_files(files)
        temp_path.cleanup()

    def test_read_zip(self):
        temp_path = create_temp_folder()
        zip_file = copy_to_temporal_path(data_path=data_path('zip_file.zip'), temp_folder=temp_path,
                                         filename='zip_file.zip')

        files = esautils.read_downloaded_fits([zip_file])

        assert len(files) == 1
        assert files[0]['filename'] == 'test.fits'

        close_files(files)
        temp_path.cleanup()

    def test_read_uncompressed(self, tmp_cwd):
        uncompressed_file = data_path('test.fits')

        files = esautils.read_downloaded_fits([uncompressed_file])
        assert len(files) == 1
        assert files[0]['filename'] == 'test.fits'

        close_files(files)

    @patch('astroquery.esa.utils.utils.ESAAuthSession.get')
    def test_resolve_target(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = get_dummy_json()
        mock_get.return_value.__enter__.return_value = mock_response

        esa_session = esautils.ESAAuthSession()

        target = esautils.resolve_target(url='http://dummyurl.com/target_resolver', session=esa_session,
                                         target_name='dummy_target', target_resolver='ALL')
        assert target.ra.degree == 83.6324
        assert target.dec.degree == 22.0174

    @patch('astroquery.esa.utils.utils.ESAAuthSession.get')
    def test_resolve_target_error(self, mock_get):

        error_message = "Mocked HTTP error"
        mock_get.side_effect = ValueError(error_message)

        esa_session = esautils.ESAAuthSession()

        with pytest.raises(ValueError) as err:
            esautils.resolve_target(url='http://dummyurl.com/target_resolver', session=esa_session,
                                    target_name='dummy_target', target_resolver='ALL')
        assert 'This target cannot be resolved' in err.value.args[0]

    # Tests to for EsaTap class

    def test_get_alternative_tap(self):
        esa_tap = DummyTapClass(tap_url="https://dummytap.es")
        assert esa_tap.TAP_URL == "https://dummytap.es"

    def test_get_tables(self):
        # default parameters
        table_set = PropertyMock()
        table_set.keys.return_value = ['ila.epoch', 'ila.cons_pub_obs']
        table_set.values.return_value = ['ila.epoch', 'ila.cons_pub_obs']
        with patch('astroquery.esa.utils.utils.pyvo.dal.TAPService', autospec=True) as esa_tap_mock:
            esa_tap_mock.return_value.tables = table_set
            esa_tap = DummyTapClass()
            assert len(esa_tap.get_tables(only_names=True)) == 2
            assert len(esa_tap.get_tables()) == 2

    def test_get_table(self):
        table_set = PropertyMock()
        tables_result = [Mock() for _ in range(3)]
        tables_result[0].name = 'ila.epoch'
        tables_result[1].name = 'ila.cons_pub_obs'
        table_set.values.return_value = tables_result

        with patch('astroquery.esa.utils.utils.pyvo.dal.TAPService', autospec=True) as esa_tap_mock:
            esa_tap_mock.return_value.tables = table_set
            esa_tap = DummyTapClass()
            assert esa_tap.get_table('ila.cons_pub_obs').name == 'ila.cons_pub_obs'
            assert esa_tap.get_table('test') is None

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.tap')
    @patch('astroquery.esa.utils.utils.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, esa_tap_job_mock, mock_tap):
        jobid = '101'
        mock_job = Mock()
        mock_job.job_id = '101'
        esa_tap_job_mock.job_id.return_value = '101'
        mock_tap.get_job.return_value = mock_job
        esa_tap = DummyTapClass()

        job = esa_tap.get_job(jobid=jobid)
        assert job.job_id == '101'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.tap')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '101'
        mock_get_job_list.get_job_list.return_value = [mock_job]
        esa_tap = DummyTapClass()

        jobs = esa_tap.get_job_list()
        assert len(jobs) == 1

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        esa_tap = DummyTapClass()
        esa_tap.login(user='dummyUser', password='dummyPassword')

        mock_post.assert_called_once_with(url="dummyLogin",
                                          data={"username": "dummyUser", "password": "dummyPassword"},
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_error(self, mock_post):
        error_message = "Mocked HTTP error"
        mock_response = mocks.get_mock_response()

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        esa_tap = DummyTapClass()
        with pytest.raises(HTTPError) as err:
            esa_tap.login(user='dummyUser', password='dummyPassword')
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        esa_tap = DummyTapClass()
        esa_tap.logout()

        mock_post.assert_called_once_with(url="dummyLogout",
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_error(self, mock_post):

        error_message = "Mocked HTTP error"
        mock_response = mocks.get_mock_response()

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        esa_tap = DummyTapClass()
        with pytest.raises(HTTPError) as err:
            esa_tap.logout()
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astropy.table.Table.write')
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.search')
    def test_query_tap_sync(self, search_mock, table_mock):
        search_mock.return_value = mocks.get_dal_table()

        query = 'select * from ivoa.obscore'
        esa_tap = DummyTapClass()
        esa_tap.query_tap(query=query, output_file='dummy.vot')
        search_mock.assert_called_with(query)
        table_mock.assert_called()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.run_async')
    def test_query_tap_async(self, async_job_mock):
        async_job_mock.return_value = mocks.get_dal_table()

        query = 'select * from ivoa.obscore'
        esa_tap = DummyTapClass()
        esa_tap.query_tap(query=query, async_job=True)
        async_job_mock.assert_called_with(query)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.search')
    def test_query_table(self, async_job_mock):
        async_job_mock.return_value = mocks.get_dal_table()

        query = 'select * from ivoa.obscore'
        esa_tap = DummyTapClass()
        esa_tap.query_tap(query=query, async_job=False)
        async_job_mock.assert_called_with(query)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_tap')
    def test_query_table_basic(self, query_tap_mock):
        query_tap_mock.return_value = mocks.get_dal_table()

        esa_tap = DummyTapClass()
        esa_tap.query_table(table_name='table1')
        query_tap_mock.assert_called_with(query='SELECT * FROM table1 ',
                                          async_job=False,
                                          output_file=None,
                                          output_format='votable',
                                          verbose=True)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_tap')
    def test_query_table_custom_filter(self, query_tap_mock):
        query_tap_mock.return_value = mocks.get_dal_table()

        esa_tap = DummyTapClass()
        esa_tap.query_table(table_name='table1', columns=['column1', 'column2'], custom_filters="column1 = 12",
                            get_metadata=False)
        query_tap_mock.assert_called_with(query="SELECT column1, column2 FROM table1 WHERE column1 = 12",
                                          async_job=False,
                                          output_file=None,
                                          output_format='votable',
                                          verbose=True)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_tap')
    def test_query_table_filtered(self, query_tap_mock):
        query_tap_mock.return_value = mocks.get_dal_table()

        esa_tap = DummyTapClass()
        esa_tap.query_table(table_name='table1', columns=['column1', 'column2'], custom_filters=None,
                            get_metadata=False, table_filter='value1')
        query_tap_mock.assert_called_with(query="SELECT column1, column2 FROM table1  WHERE table_filter = 'value1'",
                                          async_job=False,
                                          output_file=None,
                                          output_format='votable',
                                          verbose=True)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.get_table')
    def test_get_metadata(self, table_mock):
        # Prepare mock TAP columns
        columns = [DummyColumn('ra', 'Right Ascension',
                               'deg', DummyDatatype('float'), 'pos.eq.ra', None)]

        table = DummyTapTable(columns)

        tap_class = DummyTapClass()
        table_mock.return_value = table

        meta = tap_class.get_metadata("dummy_table")

        assert type(meta) is Table

        # Validate first row
        assert meta[0]["Column"] == "ra"
        assert meta[0]["Description"] == "Right Ascension"
