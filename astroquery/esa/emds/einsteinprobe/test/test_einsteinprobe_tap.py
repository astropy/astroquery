# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
EinsteinProbe (EPSA) tests
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
from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
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
    @patch('astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.tap')
    @patch('astroquery.esa.utils.utils.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, epsa_job_mock, mock_tap):
        jobid = '101'
        mock_job = Mock()
        mock_job.job_id = '101'
        epsa_job_mock.job_id.return_value = '101'
        mock_tap.get_job.return_value = mock_job
        epsa = EinsteinProbeClass()

        job = epsa.get_job(jobid=jobid)
        assert job.job_id == '101'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.tap')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '101'
        mock_get_job_list.get_job_list.return_value = [mock_job]
        epsa = EinsteinProbeClass()

        jobs = epsa.get_job_list()
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
        epsa = EinsteinProbeClass()
        epsa.login(user='dummyUser', password='dummyPassword')

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

        epsa = EinsteinProbeClass()
        with pytest.raises(HTTPError) as err:
            epsa.login(user="dummyUser", password="dummyPassword")

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
        epsa = EinsteinProbeClass()
        epsa.logout()

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

        epsa = EinsteinProbeClass()
        with pytest.raises(HTTPError) as err:
            epsa.logout()

        assert error_message in str(err.value)
        mock_response.raise_for_status.assert_called_once()

    def test_get_tables(self):
        table_set = PropertyMock()
        table_set.keys.return_value = ["einsteinprobe.obscore_extended"]

        t1 = Mock()
        t1.name = "einsteinprobe.obscore_extended"
        table_set.values.return_value = [t1]

        with patch("astroquery.esa.utils.utils.pyvo.dal.TAPService", autospec=True) as tap_mock:
            tap_mock.return_value.tables = table_set
            epsa = EinsteinProbeClass()
            assert len(epsa.get_tables(only_names=True)) == 1
            assert len(epsa.get_tables()) == 1

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astropy.table.Table.write")
    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.search")
    def test_query_tap_sync(self, search_mock, table_write_mock):
        # Simulate pyvo search() result with a .to_table() method
        mock_result = Mock()
        mock_result.to_table.return_value = Table({"a": [1]})
        search_mock.return_value = mock_result

        epsa = EinsteinProbeClass()
        epsa.query_tap(query="SELECT 1", output_file="dummy.vot")

        search_mock.assert_called_once_with("SELECT 1")
        table_write_mock.assert_called()  # called when writing output_file

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.run_async")
    def test_query_tap_async(self, run_async_mock):
        mock_job = Mock()
        mock_job.to_table.return_value = Table({"a": [1]})
        run_async_mock.return_value = mock_job

        epsa = EinsteinProbeClass()
        epsa.query_tap(query="SELECT 1", async_job=True)

        run_async_mock.assert_called_once()

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_basic_calls_query_table(self, query_table_mock):
        epsa = EinsteinProbeClass()
        epsa.get_observations()

        query_table_mock.assert_called_once_with(
            table_name="einsteinprobe.obscore_extended",
            columns=None,
            custom_filters=None,
            get_metadata=False,
            async_job=True,
            output_file=None,
        )

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_with_columns(self, query_table_mock):
        epsa = EinsteinProbeClass()
        epsa.get_observations(columns=["obs_id", "s_ra", "s_dec"])

        query_table_mock.assert_called_once_with(
            table_name="einsteinprobe.obscore_extended",
            columns=["obs_id", "s_ra", "s_dec"],
            custom_filters=None,
            get_metadata=False,
            async_job=True,
            output_file=None,
        )

    def test_get_observations_error_target_and_coordinates(self):
        epsa = EinsteinProbeClass()

        with pytest.raises(TypeError) as err:
            epsa.get_observations(target_name="M31", coordinates="12 13")

        assert "Please use only target or coordinates" in str(err.value)

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_with_filters(self, query_table_mock):
        epsa = EinsteinProbeClass()
        epsa.get_observations(
            columns=["obs_id", "obs_collection", "instrument_name"],
            obs_collection="EPSA",
            instrument_name="FXT",
            dataproduct_type=["img", "pha"],
            t_min=(">", 60000),
        )

        query_table_mock.assert_called_once()

        # Check core arguments
        _, kwargs = query_table_mock.call_args
        assert kwargs["table_name"] == "einsteinprobe.obscore_extended"
        assert kwargs["columns"] == ["obs_id", "obs_collection", "instrument_name"]
        assert kwargs["custom_filters"] is None
        assert kwargs["get_metadata"] is False
        assert kwargs["async_job"] is True
        assert kwargs["output_file"] is None

        # Check that filters are forwarded
        assert kwargs["obs_collection"] == "EPSA"
        assert kwargs["instrument_name"] == "FXT"
        assert kwargs["dataproduct_type"] == ["img", "pha"]
        assert kwargs["t_min"] == (">", 60000)

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_get_metadata(self, query_table_mock):
        epsa = EinsteinProbeClass()
        epsa.get_observations(get_metadata=True)

        query_table_mock.assert_called_once()

        _, kwargs = query_table_mock.call_args
        assert kwargs["table_name"] == "einsteinprobe.obscore_extended"
        assert kwargs["get_metadata"] is True
        assert kwargs["async_job"] is True

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.core.commons.parse_coordinates")
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_coordinates_builds_cone_filter(
        self, query_table_mock, parse_coordinates_mock
    ):
        # Force deterministic coordinates
        parse_coordinates_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")

        epsa = EinsteinProbeClass()
        epsa.get_observations(coordinates="12 13", radius=1.0)

        query_table_mock.assert_called_once()
        _, kwargs = query_table_mock.call_args

        assert kwargs["table_name"] == "einsteinprobe.obscore_extended"
        assert kwargs["async_job"] is True

        cone = kwargs["custom_filters"]
        assert cone is not None
        assert "CONTAINS" in cone
        assert "CIRCLE" in cone
        assert "s_ra" in cone
        assert "s_dec" in cone
        assert "12.0" in cone
        assert "13.0" in cone

    @patch("astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities", [])
    @patch("astroquery.esa.emds.core.esautils.resolve_target")
    @patch("astroquery.esa.emds.einsteinprobe.core.EinsteinProbeClass.query_table")
    def test_get_observations_target_name_builds_cone_filter(
        self, query_table_mock, resolve_target_mock
    ):
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")

        epsa = EinsteinProbeClass()
        epsa.get_observations(target_name="M31", radius=1.0)

        query_table_mock.assert_called_once()
        _, kwargs = query_table_mock.call_args

        assert kwargs["table_name"] == "einsteinprobe.obscore_extended"
        assert kwargs["async_job"] is True

        cone = kwargs["custom_filters"]
        assert cone is not None
        assert "CONTAINS" in cone
        assert "CIRCLE" in cone
        assert "s_ra" in cone
        assert "s_dec" in cone
        assert "12.0" in cone
        assert "13.0" in cone

    def test_get_products_adds_required_columns(self):
        epsa = EinsteinProbeClass()

        with patch.object(EinsteinProbeClass, "query_table", autospec=True) as qmock:
            epsa.get_products(
                obs_id="OBS123",
                columns=["obs_id", "dataproduct_type"]
            )

            assert qmock.called
            _, kwargs = qmock.call_args

            assert kwargs["table_name"] == "einsteinprobe.obscore_extended"

            # Required download columns appended
            cols = kwargs["columns"]
            assert "filename" in cols
            assert "filepath" in cols

            assert "custom_filters" in kwargs
            assert "OBS123" in (kwargs["custom_filters"] or "")

    def test_get_products_default_columns_include_download_fields(self):
        epsa = EinsteinProbeClass()

        with patch.object(EinsteinProbeClass, "query_table", autospec=True) as qmock:
            epsa.get_products(obs_id="OBS123")

            _, kwargs = qmock.call_args
            cols = kwargs["columns"]
            assert "filename" in cols
            assert "filepath" in cols
