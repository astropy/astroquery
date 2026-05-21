# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
CHEOPS tests
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import shutil
import tempfile
import pytest
from unittest.mock import PropertyMock, patch, Mock
from astropy.table import Table
from astroquery.esa.emds.cheops import CheopsClass
from astroquery.esa.emds import conf
from requests import HTTPError
from astropy.coordinates import SkyCoord


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def create_temp_folder():
    return tempfile.TemporaryDirectory()


def copy_to_temporal_path(data_path, temp_folder, filename):
    temp_data_dir = os.path.join(temp_folder.name, filename)
    shutil.copy(data_path, temp_data_dir)
    return temp_data_dir


def close_file(file):
    file.close()


def close_files(file_list):
    for file in file_list:
        close_file(file['fits'])


class TestEmdsTap:

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.tap')
    @patch('astroquery.esa.utils.utils.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, cheops_job_mock, mock_tap):
        jobid = '201'
        mock_job = Mock()
        mock_job.job_id = jobid
        cheops_job_mock.job_id.return_value = jobid
        mock_tap.get_job.return_value = mock_job
        cheops = CheopsClass()

        job = cheops.get_job(jobid=jobid)
        assert job.job_id == jobid

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.tap')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '201'
        mock_get_job_list.get_job_list.return_value = [mock_job]
        cheops = CheopsClass()

        jobs = cheops.get_job_list()
        assert len(jobs) == 1
        mock_get_job_list.get_job_list.assert_called_once()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        cheops = CheopsClass()
        cheops.login(user='dummyUser', password='dummyPassword')

        mock_post.assert_called_once_with(url=conf.EMDS_LOGIN_SERVER,
                                          data={"username": "dummyUser", "password": "dummyPassword"},
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})
        mock_response.raise_for_status.assert_called_once()

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.ESAAuthSession.post")
    def test_login_error(self, mock_post):
        error_message = "Mocked HTTP error"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(error_message)
        mock_response.json.return_value = {"status": "error"}

        mock_post.return_value = mock_response

        cheops = CheopsClass()
        with pytest.raises(HTTPError) as err:
            cheops.login(user="dummyUser", password="dummyPassword")

        assert error_message in str(err.value)
        mock_response.raise_for_status.assert_called_once()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        cheops = CheopsClass()
        cheops.logout()

        mock_post.assert_called_once_with(url=conf.EMDS_LOGOUT_SERVER,
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})
        mock_response.raise_for_status.assert_called_once()

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.ESAAuthSession.post")
    def test_logout_error(self, mock_post):
        error_message = "Mocked HTTP error"

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(error_message)
        mock_response.json.return_value = {"status": "error"}

        mock_post.return_value = mock_response

        cheops = CheopsClass()
        with pytest.raises(HTTPError) as err:
            cheops.logout()

        assert error_message in str(err.value)
        mock_response.raise_for_status.assert_called_once()

    def test_get_tables(self):
        table_set = PropertyMock()
        table_set.keys.return_value = ["cheops.observation_request"]

        t1 = Mock()
        t1.name = "cheops.observation_request"
        table_set.values.return_value = [t1]

        with patch("astroquery.esa.utils.utils.pyvo.dal.TAPService", autospec=True) as tap_mock:
            tap_mock.return_value.tables = table_set
            cheops = CheopsClass()
            assert len(cheops.get_tables(only_names=True)) == 1
            assert len(cheops.get_tables()) == 1

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astropy.table.Table.write")
    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.search")
    def test_query_tap_sync(self, search_mock, table_write_mock):
        # Simulate pyvo search() result with a .to_table() method
        mock_result = Mock()
        mock_result.to_table.return_value = Table({"a": [1]})
        search_mock.return_value = mock_result

        cheops = CheopsClass()
        cheops.query_tap(query="SELECT 1", output_file="dummy.vot")

        search_mock.assert_called_once_with("SELECT 1")
        table_write_mock.assert_called()  # called when writing output_file

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.run_async")
    def test_query_tap_async(self, run_async_mock):
        mock_job = Mock()
        mock_job.to_table.return_value = Table({"a": [1]})
        run_async_mock.return_value = mock_job

        cheops = CheopsClass()
        cheops.query_tap(query="SELECT 1", async_job=True)

        run_async_mock.assert_called_once()

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_basic_calls_query_table(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(coordinates="81.1238 17.4175")

        query_table_mock.assert_called_once_with(
            table_name="cheops.observation_request",
            columns=None,
            custom_filters="1=CONTAINS(POINT('ICRS', ra, dec),CIRCLE('ICRS', 81.1238, 17.4175, 0.01))",
            get_metadata=False,
            async_job=False,
            output_file=None,
            output_format='votable',
        )

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_with_columns(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(columns=["obs_cat", "ra", "dec"])

        query_table_mock.assert_called_once_with(
            table_name="cheops.observation_request",
            columns=["obs_cat", "ra", "dec"],
            custom_filters=None,
            get_metadata=False,
            async_job=False,
            output_file=None,
            output_format='votable',
        )

    def test_get_observations_error_target_and_coordinates(self):
        cheops = CheopsClass()

        with pytest.raises(TypeError) as err:
            cheops.get_observations(target_name="M31", coordinates="12 13")

        assert "Please use only target or coordinates" in str(err.value)

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_with_filters(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(
            request_id=3000240001,
        )

        query_table_mock.assert_called_once()

        # Check core arguments
        _, kwargs = query_table_mock.call_args
        assert kwargs["table_name"] == "cheops.observation_request"
        assert kwargs["columns"] is None
        assert kwargs["custom_filters"] is None
        assert kwargs["get_metadata"] is False
        assert kwargs["async_job"] is False
        assert kwargs["output_file"] is None
        assert kwargs["output_format"] == 'votable'

        # Check that filters are forwarded
        assert kwargs["request_id"] == 3000240001

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_get_metadata(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(get_metadata=True)

        query_table_mock.assert_called_once()

        _, kwargs = query_table_mock.call_args
        assert kwargs["table_name"] == "cheops.observation_request"
        assert kwargs["get_metadata"] is True
        assert kwargs["async_job"] is False

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.core.commons.parse_coordinates")
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_coordinates_builds_cone_filter(
        self, query_table_mock, parse_coordinates_mock
    ):
        # Force deterministic coordinates
        parse_coordinates_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")

        cheops = CheopsClass()
        cheops.get_observations(coordinates="12 13")

        query_table_mock.assert_called_once()
        _, kwargs = query_table_mock.call_args

        assert kwargs["table_name"] == "cheops.observation_request"
        assert kwargs["async_job"] is False

        cone = kwargs["custom_filters"]
        assert cone is not None
        assert "CONTAINS" in cone
        assert "CIRCLE" in cone
        assert "ra" in cone
        assert "dec" in cone
        assert "12.0" in cone
        assert "13.0" in cone
        assert "0.01" in cone

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.core.esautils.resolve_target")
    @patch("astroquery.esa.emds.cheops.core.CheopsClass.query_table")
    def test_get_observations_target_name_builds_cone_filter(
        self, query_table_mock, resolve_target_mock
    ):
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")

        cheops = CheopsClass()
        cheops.get_observations(target_name="M31", radius=2.2)

        query_table_mock.assert_called_once()
        _, kwargs = query_table_mock.call_args

        assert kwargs["table_name"] == "cheops.observation_request"
        assert kwargs["async_job"] is False

        cone = kwargs["custom_filters"]
        assert cone is not None
        assert "CONTAINS" in cone
        assert "CIRCLE" in cone
        assert "ra" in cone
        assert "dec" in cone
        assert "12.0" in cone
        assert "13.0" in cone
        assert "2.2" in cone


    def test_get_products_by_observation_id(self):
        cheops = CheopsClass()

        with patch.object(CheopsClass, "query_tap", autospec=True) as qmock:
            qmock.return_value = [1]

            cheops.get_products(observation_id=2652014)

            assert qmock.called
            _, kwargs = qmock.call_args

            assert "select * from cheops.data_product a where a.visit_oid in (select distinct b.visit_oid from cheops.visit b where b.obsid = '2652014')" ==  kwargs["query"]

    def test_get_products_by_visit_id(self):
        cheops = CheopsClass()

        with patch.object(CheopsClass, "query_tap", autospec=True) as qmock:
            qmock.return_value = [1]

            cheops.get_products(visit_id=250033000701, output_file="download.txt")


            assert qmock.called
            _, kwargs = qmock.call_args

            assert "select * from cheops.data_product a where a.visit_oid in (select distinct b.visit_oid from cheops.visit b where b.visit_id = '250033000701')" ==  kwargs["query"]
            assert "download.txt" == kwargs["output_file"]

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.pyvo.auth.authsession.AuthSession.get")
    def test_download_method_from_utils(self, mock_get):
        cheops = CheopsClass()
        cheops.download_product("dummy_file")

        mock_get.assert_called_once_with('https://emds.esac.esa.int/service/data?', stream=True,
                                         params={'retrieval_type': 'PRODUCT',
                                                 'QUERY': "SELECT filepath, filename FROM "
                                                          "cheops.data_product WHERE "
                                                          "filename = 'dummy_file'",
                                                 'TAPCLIENT': 'ASTROQUERY'})

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.pyvo.auth.authsession.AuthSession.get", None)
    def test_missing_parameters(self):
        cheops = CheopsClass()
        cheops.conf.EMDS_DATA_SERVER = None

        with pytest.raises(ValueError) as err:
            cheops.download_product("dummy_file")
        assert 'Data server URL is not configured (EMDS_DATA_SERVER).' in err.value.args[0]