# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
PLATO TAP tests
===============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import shutil
import sys
import tempfile
import types

from astropy.coordinates import SkyCoord

from astroquery.esa.plato import PlatoClass
from astroquery.esa.plato import conf
from unittest.mock import PropertyMock, patch, Mock
import pytest

from requests import HTTPError

from astroquery.esa.plato.tests import mocks


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


class FakePyplotAPI:
    def ion(self):
        ...

    def subplots(self, *args, **kwargs):
        ...

    def show(self, *args, **kwargs):
        ...

    def close(self, *args, **kwargs):
        ...


class FakeAxes:
    def __init__(self, name="ax"):
        self.name = name

        # Add the methods your code uses:
        self.scatter = Mock(name=f"{name}.scatter")
        self.set_xlabel = Mock(name=f"{name}.set_xlabel")
        self.set_ylabel = Mock(name=f"{name}.set_ylabel")
        self.invert_xaxis = Mock(name=f"{name}.invert_xaxis")
        self.set_title = Mock(name=f"{name}.set_title")
        self.errorbar = Mock(name=f"{name}.errorbar")
        self.collections = [1, 2]


class FakeFigure:
    def __init__(self, name="ax", n_axes=1):
        self.name = name
        self.axes = [FakeAxes() for _ in range(n_axes)]
        self.colorbar = Mock(name=f"{name}.colorbar")


class TestPlatoTap:

    def test_get_tables(self):
        # default parameters
        table_set = PropertyMock()
        table_set.keys.return_value = ['uplink.camera', 'uplink.ccd']
        table_set.values.return_value = ['uplink.camera', 'uplink.ccd']
        with patch('astroquery.esa.utils.utils.pyvo.dal.TAPService', autospec=True) as plato_mock:
            plato_mock.return_value.tables = table_set
            plato = PlatoClass()
            assert len(plato.get_tables(only_names=True)) == 2
            assert len(plato.get_tables()) == 2

    def test_get_table(self):
        table_set = PropertyMock()
        tables_result = [Mock() for _ in range(3)]
        tables_result[0].name = 'uplink.camera'
        tables_result[1].name = 'uplink.ccd'
        table_set.values.return_value = tables_result

        with patch('astroquery.esa.utils.utils.pyvo.dal.TAPService', autospec=True) as plato_mock:
            plato_mock.return_value.tables = table_set
            plato = PlatoClass()
            assert plato.get_table('uplink.ccd').name == 'uplink.ccd'
            assert plato.get_table('test') is None

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.plato.core.PlatoClass.tap')
    @patch('astroquery.esa.utils.utils.pyvo.dal.AsyncTAPJob')
    def test_load_job(self, plato_job_mock, mock_tap):
        jobid = '101'
        mock_job = Mock()
        mock_job.job_id = '101'
        plato_job_mock.job_id.return_value = '101'
        mock_tap.get_job.return_value = mock_job
        plato = PlatoClass()

        job = plato.get_job(jobid=jobid)
        assert job.job_id == '101'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.plato.core.PlatoClass.tap')
    def test_get_job_list(self, mock_get_job_list):
        mock_job = Mock()
        mock_job.job_id = '101'
        mock_get_job_list.get_job_list.return_value = [mock_job]
        plato = PlatoClass()

        jobs = plato.get_job_list()
        assert len(jobs) == 1

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_login_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        plato = PlatoClass()
        plato.login(user='dummyUser', password='dummyPassword')

        mock_post.assert_called_once_with(url=conf.PLATO_LOGIN_SERVER,
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
        plato = PlatoClass()
        with pytest.raises(HTTPError) as err:
            plato.login(user='dummyUser', password='dummyPassword')
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_success(self, mock_post):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None  # Simulate no HTTP error
        mock_response.json.return_value = {"status": "success", "token": "mocked_token"}

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        plato = PlatoClass()
        plato.logout()

        mock_post.assert_called_once_with(url=conf.PLATO_LOGOUT_SERVER,
                                          headers={'Content-type': 'application/x-www-form-urlencoded',
                                                   'Accept': 'text/plain'})

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.ESAAuthSession.post')
    def test_logout_error(self, mock_post):
        error_message = "Mocked HTTP error"
        mock_response = mocks.get_mock_response()

        # Configure the mock post method to return the mock Response
        mock_post.return_value = mock_response
        plato = PlatoClass()
        with pytest.raises(HTTPError) as err:
            plato.logout()
        assert error_message in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astropy.table.Table.write')
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.search')
    def test_query_tap_sync(self, search_mock, table_mock):
        search_mock.return_value = mocks.get_dal_table()

        query = 'select * from uplink.camera'
        plato = PlatoClass()
        plato.query_tap(query=query, output_file='dummy.vot')
        search_mock.assert_called_with(query)
        table_mock.assert_called()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.run_async')
    def test_query_tap_async(self, async_job_mock):
        async_job_mock.return_value = mocks.get_dal_table()

        query = 'select * from uplink.camera'
        plato = PlatoClass()
        plato.query_tap(query=query, async_job=True)
        async_job_mock.assert_called_with(query)

    @patch.dict(sys.modules, {"matplotlib": types.ModuleType("matplotlib")})
    def test_creates_new_figure(self):

        # Fake matplotlib
        fake_pyplot = Mock(spec=FakePyplotAPI)
        fake_pyplot.subplots.return_value = (Mock(name="fig"), Mock(name="ax"))

        with patch.dict(sys.modules, {"matplotlib.pyplot": fake_pyplot}):
            plato = PlatoClass()

            x = [1, 2, 3]
            y = [4, 5, 6]

            fig, ax = plato.plot_plato_results(x, y, "X", "Y", "Title")

            assert fig is not None
            assert ax is not None

    @patch.dict(sys.modules, {"matplotlib": types.ModuleType("matplotlib")})
    def test_uses_existing_figure(self):
        # Fake matplotlib
        fake_pyplot = Mock(spec=FakePyplotAPI)
        fake_pyplot.subplots.return_value = (Mock(name="fig"), Mock(name="ax"))

        with patch.dict(sys.modules, {"matplotlib.pyplot": fake_pyplot}):
            from matplotlib import pyplot as plt

            plato = PlatoClass()

            fig, ax = plt.subplots()
            new_fig, new_ax = plato.plot_plato_results(
                [1, 2], [3, 4], "X", "Y", "Title", fig=fig, ax=ax
            )

            assert fig == new_fig
            assert ax == new_ax

    @patch.dict(sys.modules, {"matplotlib": types.ModuleType("matplotlib")})
    def test_colormap_scatter(self):
        # Fake matplotlib
        fake_pyplot = Mock(spec=FakePyplotAPI)
        fake_pyplot.subplots.return_value = (Mock(name="fig"), Mock(name="ax"))

        # Fake axes
        fig = FakeFigure(n_axes=3)
        ax = fig.axes[0]
        fake_pyplot.subplots.return_value = (fig, ax)

        with patch.dict(sys.modules, {"matplotlib.pyplot": fake_pyplot}):
            plato = PlatoClass()

            z = [10, 20, 30]

            fig, ax = plato.plot_plato_results(
                [1, 2, 3], [4, 5, 6], "X", "Y", "Title", z=z, z_label="Z-axis"
            )
            # A colorbar adds an additional axes to the figure
            assert len(fig.axes) >= 2

    @patch.dict(sys.modules, {"matplotlib": types.ModuleType("matplotlib")})
    def test_error_bars_are_added(self):
        # Fake matplotlib
        fake_pyplot = Mock(spec=FakePyplotAPI)
        fake_pyplot.subplots.return_value = (Mock(name="fig"), Mock(name="ax"))

        # Fake axes
        fig = FakeFigure(n_axes=2)
        ax = fig.axes[0]
        fake_pyplot.subplots.return_value = (fig, ax)

        with patch.dict(sys.modules, {"matplotlib.pyplot": fake_pyplot}):
            plato = PlatoClass()
            fig, ax = plato.plot_plato_results(
                [1, 2, 3], [4, 5, 6], "X", "Y", "Title",
                error_x=[0.1, 0.1, 0.1])
            assert len(ax.collections) >= 1

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.plato.core.PlatoClass.query_table')
    @patch('astroquery.esa.utils.utils.resolve_target')
    def test_search_pic_target_go_target_name(self, resolve_target_mock, query_table_mock):
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")
        plato = PlatoClass()
        plato.search_pic_target_go(target_name="m31")

        query_table_mock.assert_called_once_with(table_name='pic_go.pic_target_go',
                                                 columns=None,
                                                 custom_filters="1=CONTAINS(POINT('ICRS', RAdeg, DEdeg),"
                                                                "CIRCLE('ICRS', 12.0, 13.0, 0.016666666666666666))",
                                                 get_metadata=False,
                                                 async_job=True,
                                                 output_file=None)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_table')
    def test_search_pic_target_go_coordinates(self, query_table_mock):
        plato = PlatoClass()
        plato.search_pic_target_go(coordinates="12 13")
        query_table_mock.assert_called_once_with(table_name='pic_go.pic_target_go',
                                                 columns=None,
                                                 custom_filters="1=CONTAINS(POINT('ICRS', RAdeg, DEdeg),"
                                                                "CIRCLE('ICRS', 12.0, 13.0, 0.016666666666666666))",
                                                 get_metadata=False,
                                                 async_job=True,
                                                 output_file=None)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    def test_search_pic_target_go_error_target_coordinates(self):
        plato = PlatoClass()

        with pytest.raises(TypeError) as err:
            plato.search_pic_target_go(target_name="m31", coordinates="12 13")
        assert 'Please use only target or coordinates as parameter.' in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.get_metadata')
    def test_search_pic_target_go_get_metadata(self, query_table_mock):
        plato = PlatoClass()
        plato.search_pic_target_go(get_metadata=True)
        query_table_mock.assert_called_once_with('pic_go.pic_target_go')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_table')
    def test_search_pic_target_go_with_columns(self, query_table_mock):
        plato = PlatoClass()
        plato.search_pic_target_go(columns=['c1', 'c2'])
        query_table_mock.assert_called_once_with(async_job=True, columns=['c1', 'c2'],
                                                 custom_filters=None,
                                                 get_metadata=False,
                                                 output_file=None,
                                                 table_name='pic_go.pic_target_go')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.EsaTap.query_table')
    def test_search_pic_target_go_with_filters(self, query_table_mock):
        plato = PlatoClass()
        plato.search_pic_target_go(filter1=12, filter2='dummy', filter3='dummy%')

        query_table_mock.assert_called_once_with(async_job=True, columns=None,
                                                 custom_filters=None,
                                                 get_metadata=False,
                                                 output_file=None,
                                                 table_name='pic_go.pic_target_go',
                                                 filter1=12,
                                                 filter2='dummy',
                                                 filter3='dummy%')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.plato.core.PlatoClass.query_table')
    @patch('astroquery.esa.utils.utils.resolve_target')
    def test_search_pic_contaminant_go_target_name(self, resolve_target_mock, query_table_mock):
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit="deg")
        plato = PlatoClass()
        plato.search_pic_contaminant_go(target_name="m31")

        query_table_mock.assert_called_once_with(table_name='pic_go.pic_contaminant_go',
                                                 columns=None,
                                                 custom_filters="1=CONTAINS(POINT('ICRS', RAdeg, DEdeg),"
                                                                "CIRCLE('ICRS', 12.0, 13.0, 0.016666666666666666))",
                                                 get_metadata=False,
                                                 async_job=True,
                                                 output_file=None)
