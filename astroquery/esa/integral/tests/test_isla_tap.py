# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==============
ISLA TAP tests
==============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import shutil
import tempfile

from astropy.coordinates import SkyCoord
from astroquery.esa.integral import IntegralClass
from astroquery.esa.integral import conf
from unittest.mock import PropertyMock, patch, Mock
import pytest

from requests import HTTPError

from astroquery.esa.integral.tests import mocks


def mock_instrument_bands(isla_module):
    isla_module.instruments, isla_module.bands, isla_module.instrument_band_map = mocks.get_instrument_bands()


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


class TestIntegralTap:

    def test_get_tables(self):
        # default parameters
        table_set = PropertyMock()
        table_set.keys.return_value = ['ila.epoch', 'ila.cons_pub_obs']
        table_set.values.return_value = ['ila.epoch', 'ila.cons_pub_obs']
        with patch('astroquery.esa.integral.core.pyvo.dal.TAPService', autospec=True) as isla_mock:
            isla_mock.return_value.tables = table_set
            isla = IntegralClass()
            assert len(isla.get_tables(only_names=True)) == 2
            assert len(isla.get_tables()) == 2

    def test_get_table(self):
        table_set = PropertyMock()
        tables_result = [Mock() for _ in range(3)]
        tables_result[0].name = 'ila.epoch'
        tables_result[1].name = 'ila.cons_pub_obs'
        table_set.values.return_value = tables_result

        with patch('astroquery.esa.integral.core.pyvo.dal.TAPService', autospec=True) as isla_mock:
            isla_mock.return_value.tables = table_set
            isla = IntegralClass()
            assert isla.get_table('ila.cons_pub_obs').name == 'ila.cons_pub_obs'
            assert isla.get_table('test') is None

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.tap')
    @patch('astroquery.esa.integral.core.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, isla_job_mock, mock_tap):
        jobid = '101'
        mock_job = Mock()
        mock_job.job_id = '101'
        isla_job_mock.job_id.return_value = '101'
        mock_tap.get_job.return_value = mock_job
        isla = IntegralClass()

        job = isla.get_job(jobid=jobid)
        assert job.job_id == '101'

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.tap')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '101'
        mock_get_job_list.get_job_list.return_value = [mock_job]
        isla = IntegralClass()

        jobs = isla.get_job_list()
        assert len(jobs) == 1

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_success(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        isla.login(user='dummyUser', password='dummyPassword')

        mock_post.assert_called_once_with(url=conf.ISLA_LOGIN_SERVER,
                                          data={"username": "dummyUser", "password": "dummyPassword"},
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_error(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        error_message = "Mocked HTTP error"
        mock_response = mocks.get_mock_response()

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        with pytest.raises(HTTPError) as err:
            isla.login(user='dummyUser', password='dummyPassword')
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_success(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        isla.logout()

        mock_post.assert_called_once_with(url=conf.ISLA_LOGOUT_SERVER,
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_error(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        error_message = "Mocked HTTP error"
        mock_response = mocks.get_mock_response()

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        with pytest.raises(HTTPError) as err:
            isla.logout()
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astropy.table.Table.write')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.search')
    def test_query_tap_sync(self, search_mock, instrument_band_mock, table_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        search_mock.return_value = mocks.get_dal_table()

        query = 'select * from ivoa.obscore'
        isla = IntegralClass()
        isla.query_tap(query=query, output_file='dummy.vot')
        search_mock.assert_called_with(query)
        table_mock.assert_called()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('pyvo.dal.AsyncTAPJob')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.submit_job')
    def test_query_tap_async(self, submit_job_mock, instrument_band_mock, async_job_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        async_job_mock.phase.return_value = 'COMPLETE'
        async_job_mock.fetch_result.return_value = mocks.get_dal_table()

        query = 'select * from ivoa.obscore'
        isla = IntegralClass()
        isla.query_tap(query=query, async_job=True)
        submit_job_mock.assert_called_with(query)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_success_catalogue(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        query_tap_mock.return_value = mocks.get_sources_table().to_table()
        isla = IntegralClass()
        isla.get_sources(target_name='Crab')

        query_tap_mock.assert_called_with(query="select distinct src.name, src.ra, src.dec, src.source_id from "
                                                "ila.v_cat_source src where src.name ilike '%Crab%' order by "
                                                "src.name asc", async_job=False, output_file=None, output_format=None)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.resolve_target')
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_success_resolver(self, instrument_band_mock, query_tap_mock, resolve_target_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")
        query = conf.ISLA_CONE_TARGET_CONDITION.format(12.0, 13.0, 0.0833)

        query_tap_mock.side_effect = [mocks.get_empty_table(), mocks.get_sources_table().to_table()]
        isla = IntegralClass()
        isla.get_sources(target_name='test')

        query_tap_mock.assert_called_with(query=query, async_job=False, output_file=None, output_format=None)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.resolve_target')
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_error(self, instrument_band_mock, query_tap_mock, resolve_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        query_tap_mock.return_value = mocks.get_empty_table()
        resolve_mock.return_value = None
        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.get_sources(target_name='test')
        assert 'Target test cannot be resolved for ISLA' in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_error(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        query_tap_mock.return_value = mocks.get_empty_table()

        isla = IntegralClass()
        with pytest.raises(TypeError) as err:
            isla.get_observations(target_name='test', coordinates='test')
        assert 'Please use only target or coordinates as parameter.' in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_t1(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        get_sources_mock.return_value = mocks.get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = mocks.get_dal_table().to_table()
        isla = IntegralClass()
        isla.get_observations(target_name='crab', radius=12.0, start_revno='0290', end_revno='0599')
        query_tap_mock.assert_called_with(query="select * from ila.cons_pub_obs where "
                                                "1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS'"
                                                ",83.63320922851562,22.01447105407715,12.0)) AND "
                                                "end_revno >= '0290' AND start_revno <= '0599' order by obsid",
                                          async_job=False,
                                          output_file=None,
                                          output_format=None)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_t2(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        get_sources_mock.return_value = mocks.get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = mocks.get_dal_table().to_table()
        isla = IntegralClass()
        isla.get_observations(target_name='crab', radius=12.0, start_time='2024-12-13T00:00:00',
                              end_time='2024-12-14T00:00:00')
        query_tap_mock.assert_called_with(query="select * from ila.cons_pub_obs where "
                                                "1=CONTAINS(POINT('ICRS',ra,dec),"
                                                "CIRCLE('ICRS',83.63320922851562,22.01447105407715,12.0)) AND "
                                                "endtime >= '2024-12-13 00:00:00' AND starttime <= "
                                                "'2024-12-14 00:00:00' order by obsid",
                                          async_job=False,
                                          output_file=None,
                                          output_format=None)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_query(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        get_sources_mock.return_value = mocks.get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = mocks.get_dal_table().to_table()
        isla = IntegralClass()
        query = isla.get_observations(target_name='crab', radius=12.0, start_time='2024-12-13T00:00:00',
                                      end_time='2024-12-14T00:00:00', verbose=True)
        assert (query == "select * from ila.cons_pub_obs where "
                         "1=CONTAINS(POINT('ICRS',ra,dec),"
                         "CIRCLE('ICRS',83.63320922851562,22.01447105407715,12.0)) AND "
                         "endtime >= '2024-12-13 00:00:00' AND starttime <= "
                         "'2024-12-14 00:00:00' order by obsid")

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_download_science_windows_error(self, instrument_band_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        download_mock.return_value = 'file.test'

        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.download_science_windows()
        assert 'Input parameters are wrong' in err.value.args[0]

        with pytest.raises(ValueError) as err:
            isla.download_science_windows(science_windows='sc', observation_id='obs')
        assert 'Only one parameter can be provided at a time.' in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_download_science_windows(self, instrument_band_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.download_science_windows()
        assert 'Input parameters are wrong' in err.value.args[0]

        with pytest.raises(ValueError) as err:
            isla.download_science_windows(science_windows='sc', observation_id='obs')
        assert 'Only one parameter can be provided at a time.' in err.value.args[0]

        temp_path = create_temp_folder()
        temp_file = copy_to_temporal_path(data_path=data_path('zip_file.zip'), temp_folder=temp_path,
                                          filename='zip_file.zip')
        download_mock.return_value = temp_file

        sc = isla.download_science_windows(science_windows='sc')

        args, kwargs = download_mock.call_args
        assert kwargs['params']['RETRIEVAL_TYPE'] == 'SCW'

        close_files(sc)
        temp_path.cleanup()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_timeline(self, instrument_band_mock, servlet_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        servlet_mock.return_value = mocks.get_mock_timeline()

        isla = IntegralClass()
        coords = SkyCoord(ra=83.63320922851562, dec=22.01447105407715, unit="deg")
        timeline = isla.get_timeline(coordinates=coords)

        assert len(timeline['timeline']['scwRevs']) > 0

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_epochs_error(self, instrument_band_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.get_epochs(target_name='J011705.1-732636', instrument='i2')
        assert 'This is not a valid value for instrument or band.' in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_epochs(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_epochs(target_name='J011705.1-732636', instrument='i1')

        query_tap_mock.assert_called_with("select distinct epoch from ila.epoch where "
                                          "source_id = 'J011705.1-732636' and "
                                          "(instrument_oid = id1 or band_oid = id2)")

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_long_term_timeseries_error(self, instrument_band_mock, log_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        error_message = 'Error'
        download_mock.side_effect = HTTPError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)

        isla.get_long_term_timeseries(target_name='J174537.0-290107', band='b1')
        log_mock.error.assert_called_with('No long term timeseries have been found with these inputs. ' + error_message)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_long_term_timeseries_exception(self, instrument_band_mock, log_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        error_message = 'Error'
        download_mock.side_effect = ValueError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)

        isla.get_long_term_timeseries(target_name='J174537.0-290107', band='b1')
        log_mock.error.assert_called_with('Problem when retrieving long term timeseries. ' + error_message)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_long_term_timeseries(self, instrument_band_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()

        temp_path = create_temp_folder()
        temp_file = copy_to_temporal_path(data_path=data_path('zip_file.zip'), temp_folder=temp_path,
                                          filename='zip_file.zip')
        download_mock.return_value = temp_file

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        lt_timeseries_list_extracted = isla.get_long_term_timeseries(target_name='J174537.0-290107', band='b1')

        assert len(lt_timeseries_list_extracted) == 2
        lt_timeseries_list_compressed = isla.get_long_term_timeseries(target_name='J174537.0-290107', band='b1',
                                                                      read_fits=False)
        assert type(lt_timeseries_list_compressed) is str
        close_files(lt_timeseries_list_extracted)
        temp_path.cleanup()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_short_term_timeseries_error(self, instrument_band_mock, epoch_mock, download_mock, log_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        error_message = 'Error'
        download_mock.side_effect = HTTPError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_short_term_timeseries(target_name='target',
                                       band='b1', epoch='time')
        log_mock.error.assert_called_with(
            'No short term timeseries have been found with these inputs. {0}'.format(error_message))

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_short_term_timeseries_exception(self, instrument_band_mock, epoch_mock, download_mock, log_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        error_message = 'Error'
        download_mock.side_effect = ValueError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_short_term_timeseries(target_name='target',
                                       band='b1', epoch='time')
        log_mock.error.assert_called_with('Problem when retrieving short term timeseries. ' + error_message)

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_short_term_timeseries_epoch_error(self, instrument_band_mock, epoch_mock):

        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time2']}

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        with pytest.raises(ValueError) as err:
            isla.get_short_term_timeseries(target_name='target',
                                           band='b1', epoch='time')
        assert 'Epoch time is not available for this target and instrument/band.' in err.value.args[0]

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_short_term_timeseries(self, instrument_band_mock, epoch_mock, download_mock):

        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        temp_path = create_temp_folder()
        temp_file = copy_to_temporal_path(data_path=data_path('tar_file.tar'), temp_folder=temp_path,
                                          filename='tar_file.tar')
        download_mock.return_value = temp_file

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        st_timeseries_list_extracted = isla.get_short_term_timeseries(target_name='target',
                                                                      band='b1', epoch='time')
        assert len(st_timeseries_list_extracted) == 3

        st_timeseries_list_compressed = isla.get_short_term_timeseries(target_name='target',
                                                                       band='b1', epoch='time', read_fits=False)
        assert type(st_timeseries_list_compressed) is str

        close_files(st_timeseries_list_extracted)
        temp_path.cleanup()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_spectra_error_server(self, instrument_band_mock, epoch_mock, servlet_mock, log_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        error_message = 'Error'
        servlet_mock.side_effect = HTTPError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_spectra(target_name='target',
                         band='b1', epoch='time')
        log_mock.error.assert_called_with('Problem when retrieving spectra. '
                                          'Error')

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_spectra_no_values(self, instrument_band_mock, epoch_mock, servlet_mock, log_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        servlet_mock.return_value = []

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_spectra(target_name='target',
                         band='b1', epoch='time')
        log_mock.error.assert_called_with('Spectra are not available with these inputs. '
                                          'Please try with different input parameters.')

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_spectra_exception(self, instrument_band_mock, servlet_mock, log_mock, epoch_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        mock_response = mocks.get_mock_response()
        servlet_mock.side_effect = mock_response

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_spectra(target_name='target',
                         band='b1', epoch='time')
        log_mock.error.assert_called_with("Problem when retrieving spectra. "
                                          "object of type 'Mock' has no len()")

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_spectra(self, instrument_band_mock, servlet_mock, epoch_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        servlet_mock.return_value = mocks.get_mock_spectra()
        epoch_mock.return_value = {'epoch': ['today']}
        temp_path = create_temp_folder()
        temp_file = copy_to_temporal_path(data_path=data_path('tar_file.tar'), temp_folder=temp_path,
                                          filename='tar_file.tar')
        download_mock.return_value = temp_file

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        spectra_list_extracted = isla.get_spectra(target_name='target',
                                                  epoch='today', band='b1')
        assert len(spectra_list_extracted) == 3

        spectra_list_compressed = isla.get_spectra(target_name='target',
                                                   epoch='today', band='b1', read_fits=False)
        assert type(spectra_list_compressed) is list

        close_files(spectra_list_extracted)
        temp_path.cleanup()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_mosaic_no_values(self, instrument_band_mock, epoch_mock, servlet_mock, log_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        servlet_mock.return_value = []

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_mosaic(epoch='time', instrument='i1')
        log_mock.error.assert_called_with('Mosaics are not available for these inputs. '
                                          'Please try with different input parameters.')

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.integral.core.log')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_mosaic_exception(self, instrument_band_mock, servlet_mock, log_mock, epoch_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        epoch_mock.return_value = {'epoch': ['time']}
        error_message = 'Error'
        servlet_mock.side_effect = HTTPError(error_message)

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_mosaic(epoch='time', instrument='i1')
        log_mock.error.assert_called_with("Problem when retrieving mosaics. "
                                          "Error")

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_epochs')
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_mosaic(self, instrument_band_mock, servlet_mock, epoch_mock, download_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        servlet_mock.return_value = mocks.get_mock_mosaic()
        epoch_mock.return_value = {'epoch': ['today']}
        temp_path = create_temp_folder()
        temp_file = copy_to_temporal_path(data_path=data_path('tar_gz_file.gz'), temp_folder=temp_path,
                                          filename='tar_gz_file.gz')
        download_mock.return_value = temp_file

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        mosaics_extracted = isla.get_mosaic(epoch='today', instrument='i1')
        assert len(mosaics_extracted) == 2

        mosaics_compressed = isla.get_mosaic(epoch='today', instrument='i1', read_fits=False)

        assert type(mosaics_compressed) is list
        close_files(mosaics_extracted)
        temp_path.cleanup()

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_source_metadata(self, instrument_band_mock, servlet_mock):
        instrument_band_mock.return_value = mocks.get_instrument_bands()
        servlet_mock.return_value = {}

        isla = IntegralClass()
        mock_instrument_bands(isla_module=isla)
        isla.get_source_metadata(target_name='test')

        args, kwargs = servlet_mock.call_args
        assert kwargs['query_params']['REQUEST'] == 'sources'
