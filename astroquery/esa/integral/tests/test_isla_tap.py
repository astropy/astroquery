# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==============
ISLA TAP tests
==============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
from astropy.coordinates import SkyCoord
from astropy.io.votable.tree import VOTableFile
from astropy.table import Table
from astroquery.esa.integral import IntegralClass
from astroquery.esa.integral import conf
from unittest.mock import MagicMock, PropertyMock, patch, Mock
import pytest
from pyvo.dal import DALResults

from requests import HTTPError

instruments_value = ["i1"]
bands_value = ["b1"]
instrument_band_mock_value = {"i1": "b1"}


def get_instrument_bands():
    return instruments_value, bands_value, instrument_band_mock_value


def get_dal_table():
    data = {
        "source_id": [123456789012345, 234567890123456, 345678901234567],
        "ra": [266.404997, 266.424512, 266.439127],
        "dec": [-28.936173, -28.925636, -28.917813]
    }

    # Create an Astropy Table with the mock data
    astropy_table = Table(data)

    return DALResults(VOTableFile.from_table(astropy_table))


def get_empty_table():
    data = {
        "source_id": [],
    }

    # Create an Astropy Table with the mock data
    return Table(data)


def get_sources_table():
    data = {
        "name": ['Crab'],
        "ra": [83.63320922851562],
        "dec": [22.01447105407715],
        "source_id": ['J053432.0+220052']
    }

    # Create an Astropy Table with the mock data
    astropy_table = Table(data)

    return DALResults(VOTableFile.from_table(astropy_table))


class TestTap:

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

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.get_job')
    @patch('astroquery.esa.integral.core.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, mock_get_job, isla_job_mock):
        jobid = '101'
        mock_job = Mock()
        mock_job.job_id = '101'
        isla_job_mock.return_value = mock_job
        mock_get_job.return_value = mock_job
        isla = IntegralClass()

        job = isla.get_job(jobid=jobid)
        assert job.job_id == '101'

    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.get_job_list')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '101'
        mock_get_job_list.return_value = [mock_job]
        isla = IntegralClass()

        jobs = isla.get_job_list()
        print(jobs)
        assert len(jobs) == 1

    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_success(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = get_instrument_bands()

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

    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_error(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = get_instrument_bands()

        error_message = "Mocked HTTP error"
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(error_message)

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        with pytest.raises(HTTPError) as err:
            isla.login(user='dummyUser', password='dummyPassword')
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_success(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = get_instrument_bands()

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

    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_error(self, mock_post, instrument_band_mock):
        instrument_band_mock.return_value = get_instrument_bands()

        error_message = "Mocked HTTP error"
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError(error_message)

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        isla = IntegralClass()
        with pytest.raises(HTTPError) as err:
            isla.logout()
        assert error_message in err.value.args[0]

    @patch('astropy.table.Table.write')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.search')
    def test_query_tap_sync(self, search_mock, instrument_band_mock, table_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        search_mock.return_value = get_dal_table()

        query = 'select * from ivoa.obscore'
        isla = IntegralClass()
        isla.query_tap(query=query, output_file='dummy.vot')
        search_mock.assert_called_with(query)
        table_mock.assert_called()

    @patch('pyvo.dal.AsyncTAPJob')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    @patch('astroquery.esa.integral.core.pyvo.dal.TAPService.submit_job')
    def test_query_tap_async(self, submit_job_mock, instrument_band_mock, async_job_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        async_job_mock.phase.return_value = 'COMPLETE'
        async_job_mock.fetch_result.return_value = get_dal_table()

        query = 'select * from ivoa.obscore'
        isla = IntegralClass()
        isla.query_tap(query=query, async_job=True)
        submit_job_mock.assert_called_with(query)

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_success_catalogue(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()

        query_tap_mock.return_value = get_sources_table().to_table()
        isla = IntegralClass()
        isla.get_sources(target_name='Crab')

        query_tap_mock.assert_called_with(query="select distinct src.name, src.ra, src.dec, src.source_id from "
                                                "ila.v_cat_source src where src.name ilike '%Crab%' order by "
                                                "src.name asc", async_job=False, output_file=None, output_format=None)

    @patch('astroquery.esa.utils.utils.resolve_target')
    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_success_resolver(self, instrument_band_mock, query_tap_mock, resolve_target_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")
        query = conf.ISLA_CONE_TARGET_CONDITION.format(12.0, 13.0, 0.0833)

        query_tap_mock.side_effect = [get_empty_table(), get_sources_table().to_table()]
        isla = IntegralClass()
        isla.get_sources(target_name='test')

        query_tap_mock.assert_called_with(query=query, async_job=False, output_file=None, output_format=None)

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_sources_error(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()

        query_tap_mock.return_value = get_empty_table()
        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.get_sources(target_name='test')
        assert 'Target test cannot be resolved for ISLA' in err.value.args[0]

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_error(self, instrument_band_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        query_tap_mock.return_value = get_empty_table()

        isla = IntegralClass()
        with pytest.raises(TypeError) as err:
            isla.get_observations(target_name='test', coordinates='test')
        assert 'Please use only target or coordinates as parameter.' in err.value.args[0]

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_t1(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        get_sources_mock.return_value = get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = get_dal_table().to_table()
        isla = IntegralClass()
        isla.get_observations(target_name='crab', radius=12.0, start_revno='0290', end_revno='0599')
        query_tap_mock.assert_called_with(query="select * from ila.cons_pub_obs where "
                                                "1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS'"
                                                ",83.63320922851562,22.01447105407715,12.0)) AND "
                                                "end_revno >= '0290' AND start_revno <= '0599' order by obsid",
                                          async_job=False,
                                          output_file=None,
                                          output_format=None)
        print('test')

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_t2(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        get_sources_mock.return_value = get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = get_dal_table().to_table()
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

    @patch('astroquery.esa.integral.core.IntegralClass.query_tap')
    @patch('astroquery.esa.integral.core.IntegralClass.get_sources')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_get_observations_query(self, instrument_band_mock, get_sources_mock, query_tap_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        get_sources_mock.return_value = get_sources_table().to_table()

        # Coordinates
        query_tap_mock.return_value = get_dal_table().to_table()
        isla = IntegralClass()
        query = isla.get_observations(target_name='crab', radius=12.0, start_time='2024-12-13T00:00:00',
                                      end_time='2024-12-14T00:00:00', verbose=True)
        assert (query == "select * from ila.cons_pub_obs where "
                         "1=CONTAINS(POINT('ICRS',ra,dec),"
                         "CIRCLE('ICRS',83.63320922851562,22.01447105407715,12.0)) AND "
                         "endtime >= '2024-12-13 00:00:00' AND starttime <= "
                         "'2024-12-14 00:00:00' order by obsid")

    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_download_science_windows_error(self, instrument_band_mock, download_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        download_mock.return_value = 'file.test'

        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.download_science_windows()
        assert 'Input parameters are wrong' in err.value.args[0]

        with pytest.raises(ValueError) as err:
            isla.download_science_windows(science_windows='sc', observation_id='obs')
        assert 'Only one parameter can be provided at a time.' in err.value.args[0]

    @patch('astroquery.esa.utils.utils.download_file')
    @patch('astroquery.esa.integral.core.IntegralClass.get_instrument_band_map')
    def test_download_science_windows(self, instrument_band_mock, download_mock):
        instrument_band_mock.return_value = get_instrument_bands()
        download_mock.return_value = 'file.test'

        isla = IntegralClass()
        with pytest.raises(ValueError) as err:
            isla.download_science_windows()
        assert 'Input parameters are wrong' in err.value.args[0]

        with pytest.raises(ValueError) as err:
            isla.download_science_windows(science_windows='sc', observation_id='obs')
        assert 'Only one parameter can be provided at a time.' in err.value.args[0]

    def test_get_timeline(self):
        print('test')

    def test_get_epochs(self):
        print('test')

    def test_get_long_term_timeseries(self):
        print('test')

    def test_download_long_term_timeseries(self):
        print('test')

    def test_get_short_term_timeseries(self):
        print('test')

    def test_download_short_term_timeseries(self):
        print('test')

    def test_get_spectra(self):
        print('test')

    def test_download_spectra(self):
        print('test')

    def test_get_mosaic(self):
        print('test')

    def test_download_mosaic(self):
        print('test')

    def test_get_source_metadata(self):
        print('test')
