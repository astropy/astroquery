# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
eJWST TAP tests
===============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call
import sys
import io


import astropy.units as u
import numpy as np
import pytest
from astropy import units
from astropy.coordinates.name_resolve import NameResolveError
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.io.votable import parse_single_table
from astropy.table import Table
from astropy.units import Quantity
from requests import Response

from astroquery.exceptions import TableParseError

from astroquery.esa.jwst import JwstClass
from astroquery.ipac.ned import Ned
from astroquery.simbad import SimbadClass
from astroquery.vizier import Vizier

from astroquery.esa.jwst import conf


JOB_DATA = (Path(__file__).with_name("data") / "job_1.vot").read_text()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_plane_id_mock(url, *args, **kwargs):
    return ['00000000-0000-0000-879d-ae91fa2f43e2'], 3


@pytest.fixture(autouse=True)
def plane_id_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(JwstClass, '_get_plane_id', get_plane_id_mock)
    return mp


def get_associated_planes_mock(url, *args, **kwargs):
    if kwargs.get("max_cal_level") == 2:
        return "('00000000-0000-0000-879d-ae91fa2f43e2')"
    else:
        return planeids


@pytest.fixture(autouse=True)
def associated_planes_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(JwstClass, '_get_associated_planes', get_associated_planes_mock)
    return mp


def get_product_mock(params, *args, **kwargs):
    if ('file_name' in kwargs and kwargs.get('file_name') == 'file_name_id'):
        return "00000000-0000-0000-8740-65e2827c9895"
    else:
        return "jw00617023001_02102_00001_nrcb4_uncal.fits"


@pytest.fixture(autouse=True)
def get_product_request(request):
    if 'noautofixt' in request.keywords:
        return
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(JwstClass, '_query_get_product', get_product_mock)
    return mp


planeids = "('00000000-0000-0000-879d-ae91fa2f43e2', '00000000-0000-0000-9852-a9fa8c63f7ef')"


class TestTap:

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_launch_sync_job(self, mock_query_tap):
        tap = JwstClass(show_messages=False)
        query = "query"
        # default parameters
        tap.launch_job(query)

        # test with parameters
        parameters={}
        parameters['query'] = query
        parameters['async_job'] = False
        parameters['output_file'] = 'output'
        parameters['output_format'] = 'format'
        parameters['verbose'] = True
        tap.launch_job(**parameters)

        assert mock_query_tap.call_args_list == [
            call('query', async_job=False, output_file=None, output_format='votable', verbose=False),
            call('query', async_job=False, output_file='output', output_format='format', verbose=True),
        ]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_launch_async_job(self, mock_query_tap):
        tap = JwstClass(show_messages=False)
        query = "query"
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['async_job'] = True
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        tap.launch_job(**parameters)

        # test with set parameters
        parameters['output_file'] = 'output'
        parameters['output_format'] = 'format'
        parameters['verbose'] = True
        tap.launch_job(**parameters)

        assert mock_query_tap.call_args_list == [
            call('query', async_job=True, output_file=None, output_format='votable', verbose=False),
            call('query', async_job=True, output_file='output', output_format='format', verbose=True),
        ]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_query_region(self, mock_query_tap):
        tap = JwstClass(show_messages=False)

        with pytest.raises(ValueError) as err:
            tap.query_region(coordinate=123)
        assert "coordinate must be either a string or astropy.coordinates" in err.value.args[0]

        with pytest.raises(NameResolveError) as err:
            tap.query_region(coordinate='test')
        assert ("Unable to find coordinates for name 'test'" in err.value.args[0] or "Unable to retrieve "
                "coordinates" in err.value.args[0])

        # The query contains decimals: force default response
        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree),
                      frame='icrs')
        with pytest.raises(ValueError) as err:
            tap.query_region(sc)
        assert "Missing required argument: 'width'" in err.value.args[0]

        width = 123
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width)
        assert "width must be either a string or units.Quantity" in err.value.args[0]

        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width)
        assert "Missing required argument: 'height'" in err.value.args[0]

        votable = parse_single_table(io.BytesIO(JOB_DATA.encode("utf-8")))
        results_table = votable.to_table(use_names_over_ids=True)

        # Mock job object returned by query_tap()
        mock_job = MagicMock()
        mock_job.get_results.return_value = results_table
        mock_query_tap.return_value = mock_job

        assert (isinstance(tap.query_region(sc, width=width, height=height), Table))

        # Test observation_id argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, observation_id=1)
        assert "observation_id must be string" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, observation_id="observation"), Table))
        # raise ValueError

        # Test cal_level argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, cal_level='a')
        assert "cal_level must be either 'Top' or an integer" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, cal_level='Top'), Table))
        assert (isinstance(tap.query_region(sc, width=width, height=height, cal_level=1), Table))

        # Test only_public
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, only_public='a')
        assert "only_public must be boolean" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, only_public=True), Table))

        # Test dataproduct_type argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, prod_type=1)
        assert "prod_type must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, prod_type='a')
        assert "prod_type must be one of: " in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, prod_type='image'), Table))

        # Test instrument_name argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, instrument_name=1)
        assert "instrument_name must be string" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, instrument_name='NIRCAM'), Table))

        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height,
                             instrument_name='a')
        assert "instrument_name must be one of: " in err.value.args[0]

        # Test filter_name argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, filter_name=1)
        assert "filter_name must be string" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, filter_name='filter'), Table))

        # Test proposal_id argument
        with pytest.raises(ValueError) as err:
            tap.query_region(sc, width=width, height=height, proposal_id=123)
        assert "proposal_id must be string" in err.value.args[0]

        assert (isinstance(tap.query_region(sc, width=width, height=height, proposal_id='123'), Table))

        table = tap.query_region(sc, width=width, height=height)
        assert len(table) == 3, f"Wrong job results (num rows). Expected: {3}, found {len(table)}"
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_region(sc, radius=radius)
        assert len(table) == 3, f"Wrong job results (num rows). Expected: {3}, found {len(table)}"
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_query_region_async(self, mock_query_tap):
        tap = JwstClass(show_messages=False)

        votable = parse_single_table(io.BytesIO(JOB_DATA.encode('utf-8')))
        results_table = votable.to_table(use_names_over_ids=True)

        # Mock job object returned by query_tap()
        mock_job = MagicMock()
        mock_job.get_results.return_value = results_table
        mock_query_tap.return_value = mock_job

        sc = SkyCoord(ra=29.0, dec=15.0, unit=(u.degree, u.degree),
                      frame='icrs')
        width = Quantity(12, u.deg)
        height = Quantity(10, u.deg)
        table = tap.query_region(sc, width=width, height=height, async_job=True)
        assert len(table) == 3, f"Wrong job results (num rows). Expected: {3}, found {len(table)}"
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        assert mock_query_tap.call_args.kwargs['async_job'] is True
        mock_query_tap.reset_mock()
        # by radius
        radius = Quantity(1, u.deg)
        table = tap.query_region(sc, radius=radius, async_job=True)
        assert len(table) == 3, f"Wrong job results (num rows). Expected: {3}, found {len(table)}"
        self.__check_results_column(table,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(table,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(table,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)
        assert mock_query_tap.call_args.kwargs['async_job'] is True

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_cone_search_sync(self, mock_query_tap):
        tap = JwstClass(show_messages=False)

        mock_job = MagicMock()
        mock_job.async_ = False
        mock_job.failed = False
        mock_job.get_phase.return_value = 'COMPLETED'

        votable = parse_single_table(io.BytesIO(JOB_DATA.encode("utf-8")))
        results_table = votable.to_table(use_names_over_ids=True)

        mock_job.get_results.return_value = results_table

        # query_tap returns this job
        mock_query_tap.return_value = mock_job
        ra = 19.0
        dec = 20.0
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        job = tap.cone_search(sc, radius)
        assert job is not None, "Expected a valid job"
        assert job.async_ is False, "Expected a synchronous job"
        assert job.get_phase() == 'COMPLETED', f"Wrong job phase. Expected: {'COMPLETED'}, found {job.get_phase()}"
        assert job.failed is False, "Wrong job status (set Failed = True)"
        # results
        results = job.get_results()
        assert len(results) == 3, f"Wrong job results (num rows). Expected: {3}, found {len(results)}"
        self.__check_results_column(results,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

        # Test observation_id argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, observation_id=1)
        assert "observation_id must be string" in err.value.args[0]

        # Test cal_level argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, cal_level='a')
        assert "cal_level must be either 'Top' or an integer" in err.value.args[0]

        # Test only_public
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, only_public='a')
        assert "only_public must be boolean" in err.value.args[0]

        # Test dataproduct_type argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, prod_type=1)
        assert "prod_type must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, prod_type='a')
        assert "prod_type must be one of: " in err.value.args[0]

        # Test instrument_name argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, instrument_name=1)
        assert "instrument_name must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, instrument_name='a')
        assert "instrument_name must be one of: " in err.value.args[0]

        # Test filter_name argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, filter_name=1)
        assert "filter_name must be string" in err.value.args[0]

        # Test proposal_id argument
        with pytest.raises(ValueError) as err:
            tap.cone_search(sc, radius, proposal_id=123)
        assert "proposal_id must be string" in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_cone_search_async(self, mock_query_tap):
        tap = JwstClass(show_messages=False)

        mock_job = MagicMock()
        mock_job.async_ = True
        mock_job.failed = False
        mock_job.get_phase.return_value = 'COMPLETED'

        votable = parse_single_table(io.BytesIO(JOB_DATA.encode("utf-8")))
        results_table = votable.to_table(use_names_over_ids=True)

        mock_job.get_results.return_value = results_table

        # query_tap returns this job
        mock_query_tap.return_value = mock_job

        ra = 19
        dec = 20
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)

        job = tap.cone_search(sc, radius, async_job=True)

        assert job is mock_job
        assert job is not None, "Expected a valid job"
        assert job.async_ is True, "Expected an asynchronous job"
        assert job.get_phase() == 'COMPLETED', f"Wrong job phase. Expected: {'COMPLETED'}, found {job.get_phase()}"
        assert job.failed is False, "Wrong job status (set Failed = True)"
        # results
        results = job.get_results()
        assert len(results) == 3, "Wrong job results (num rows). Expected: {3}, found {len(results)}"
        self.__check_results_column(results,
                                    'alpha',
                                    'alpha',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'delta',
                                    'delta',
                                    None,
                                    np.float64)
        self.__check_results_column(results,
                                    'source_id',
                                    'source_id',
                                    None,
                                    object)
        self.__check_results_column(results,
                                    'table1_oid',
                                    'table1_oid',
                                    None,
                                    np.int32)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    def test_get_product_by_artifactid(self, download_mock):
        jwst = JwstClass(show_messages=False)
        # default parameters

        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        parameters = {}
        parameters['output_file'] = 'jw00617023001_02102_00001_nrcb4_uncal.fits'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['TAPCLIENT'] = 'ASTROQUERY'
        param_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = param_dict

        jwst.get_product(artifact_id='00000000-0000-0000-8740-65e2827c9895')
        assert download_mock.call_count == 1

        # Check the arguments passed to download_file
        args,kwargs = download_mock.call_args

        assert kwargs["params"]["ARTIFACTID"] == "00000000-0000-0000-8740-65e2827c9895"
        assert kwargs["params"]["RETRIEVAL_TYPE"] == "PRODUCT"
        assert kwargs["params"]["TAPCLIENT"] == "ASTROQUERY"

        assert kwargs["filename"] == "jw00617023001_02102_00001_nrcb4_uncal.fits"
        assert kwargs["url"].startswith("https://jwst.esac.esa.int/server/data")
        assert "session" in kwargs

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    def test_get_product_by_filename(self, download_mock):
        jwst = JwstClass(show_messages=False)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        parameters = {}
        parameters['output_file'] = 'file_name_id'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['TAPCLIENT'] = 'ASTROQUERY'
        param_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = param_dict

        jwst.get_product(file_name='file_name_id')
        assert download_mock.call_count == 1

        # Check the arguments passed to download_file
        args, kwargs = download_mock.call_args

        assert kwargs["params"]["ARTIFACTID"] == "00000000-0000-0000-8740-65e2827c9895"
        assert kwargs["params"]["RETRIEVAL_TYPE"] == "PRODUCT"
        assert kwargs["params"]["TAPCLIENT"] == "ASTROQUERY"

        assert kwargs["filename"] == "file_name_id"
        assert kwargs["url"].startswith("https://jwst.esac.esa.int/server/data")
        assert "session" in kwargs

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_get_products_list(self, mock_query_tap):
        jwst = JwstClass(show_messages=False)
        observation_id = "jw00777011001_02104_00001_nrcblong"

        # Mock job and table results
        mock_job = MagicMock()
        expected_table = {"filename": ["f1.fits", "f2.fits"]}
        mock_job.get_results.return_value = expected_table
        mock_query_tap.return_value = mock_job

        result = jwst.get_product_list(observation_id=observation_id, product_type="science")

        query = (f"select distinct a.uri, a.artifactid, a.filename, "
                 f"a.contenttype, a.producttype, p.calibrationlevel, p.public "
                 f"FROM {conf.JWST_PLANE_TABLE} p JOIN {conf.JWST_ARTIFACT_TABLE} "
                 f"a ON (p.planeid=a.planeid) WHERE a.planeid "
                 f"IN {planeids} AND producttype ILIKE '%science%';")

        mock_query_tap.assert_called_once_with(query=query)
        assert result == expected_table

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    def test_get_products_list_error(self):
        jwst = JwstClass(show_messages=False)
        observation_id = "jw00777011001_02104_00001_nrcblong"

        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product_list()
        assert "Missing required argument: 'observation_id'" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            jwst.get_product_list(observation_id=observation_id, product_type=1)
        assert "product_type must be string" in err.value.args[0]

        with pytest.raises(ValueError) as err:
            jwst.get_product_list(observation_id=observation_id, product_type='test')
        assert "product_type must be one of" in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    def test_download_files_from_program(self):
        jwst = JwstClass(show_messages=False)
        with pytest.raises(TypeError) as err:
            jwst.download_files_from_program()
        assert "missing 1 required positional argument: 'proposal_id'" in err.value.args[0]

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.download_file')
    def test_get_obs_products(self, download_mock):
        get_obs_products_counter = 0
        jwst = JwstClass(show_messages=False)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_obs_products()
        assert "Missing required argument: 'observation_id'" in err.value.args[0]

        # test with parameters

        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_1"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        observation_id = 'jw00777011001_02104_00001_nrcblong'

        parameters = {}
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'OBSERVATION'
        param_dict['TAPCLIENT'] = 'ASTROQUERY'
        param_dict['planeid'] = planeids
        param_dict['calibrationlevel'] = 'ALL'
        parameters['params_dict'] = param_dict

        # Test single product tar
        file = data_path('single_product_retrieval.tar')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)
        parameters['output_file'] = output_file_full_path

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_1.fits'
        expected_files.append(extracted_file_1)
        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id, cal_level='ALL',
                              output_file=output_file_full_path))
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            shutil.rmtree(output_file_full_path_dir)

        # Test product_type paramater with a list
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_1"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('single_product_retrieval.tar')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)
        parameters['output_file'] = output_file_full_path

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_1.fits'
        expected_files.append(extracted_file_1)
        product_type_as_list = ['science', 'info']
        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id,
                              cal_level='ALL',
                              product_type=product_type_as_list,
                              output_file=output_file_full_path))
            parameters['params_dict']['product_type'] = 'science,info'

            args, kwargs = download_mock.call_args
            assert kwargs["params"]["product_type"] == "science,info"
            assert kwargs["params"]["RETRIEVAL_TYPE"] == "OBSERVATION"
            assert kwargs["filename"] == output_file_full_path

            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            shutil.rmtree(output_file_full_path_dir)
            del parameters['params_dict']['product_type']

        # Test single file
        output_file_full_path_dir = os.getcwd() + os.sep +\
            "temp_test_jwsttap_get_obs_products_2"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('single_product_retrieval_1.fits')
        output_file_full_path = output_file_full_path_dir + os.sep +\
            os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files = []
        expected_files.append(output_file_full_path)

        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id,
                              output_file=output_file_full_path))

            args, kwargs = download_mock.call_args
            assert kwargs["params"]["RETRIEVAL_TYPE"] == "OBSERVATION"
            assert kwargs["params"]["calibrationlevel"] == "ALL"

            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test single file zip
        output_file_full_path_dir = os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_3"
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('single_product_retrieval_3.fits.zip')
        output_file_full_path = output_file_full_path_dir + os.sep +\
            os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval.fits'
        expected_files.append(extracted_file_1)

        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id,
                              cal_level=1,
                              output_file=output_file_full_path))
            parameters['params_dict']['calibrationlevel'] = 'LEVEL1ONLY'

            args, kwargs = download_mock.call_args
            assert kwargs["params"]["calibrationlevel"] == "LEVEL1ONLY"
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        parameters['params_dict']['calibrationlevel'] = 'ALL'

        # Test single file gzip
        output_file_full_path_dir = (os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_4")
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('single_product_retrieval_2.fits.gz')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_2.fits.gz'
        expected_files.append(extracted_file_1)

        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id,
                              output_file=output_file_full_path))

            args, kwargs = download_mock.call_args
            assert kwargs["params"]["RETRIEVAL_TYPE"] == "OBSERVATION"
            assert kwargs["params"]["calibrationlevel"] == "ALL"

            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        # Test tar with 3 files, a normal one, a gzip one and a zip one
        output_file_full_path_dir = (os.getcwd() + os.sep + "temp_test_jwsttap_get_obs_products_5")
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('three_products_retrieval.tar')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        parameters['output_file'] = output_file_full_path

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + 'single_product_retrieval_1.fits'
        expected_files.append(extracted_file_1)
        extracted_file_2 = output_file_full_path_dir + os.sep + 'single_product_retrieval_2.fits.gz'
        expected_files.append(extracted_file_2)
        extracted_file_3 = output_file_full_path_dir + os.sep + 'single_product_retrieval_3.fits.zip'
        expected_files.append(extracted_file_3)

        try:
            files_returned = (jwst.get_obs_products(
                              observation_id=observation_id,
                              output_file=output_file_full_path))

            args, kwargs = download_mock.call_args
            assert kwargs["params"]["RETRIEVAL_TYPE"] == "OBSERVATION"
            assert kwargs["params"]["calibrationlevel"] == "ALL"

            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
            get_obs_products_counter += 1
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

        assert download_mock.call_count == get_obs_products_counter


    def test_gunzip_file(self):
        output_file_full_path_dir = (os.getcwd() + os.sep + "temp_test_jwsttap_gunzip")
        try:
            os.makedirs(output_file_full_path_dir, exist_ok=True)
        except OSError as err:
            print(f"Creation of the directory {output_file_full_path_dir} failed: {err.strerror}")
            raise err

        file = data_path('single_product_retrieval_2.fits.gz')
        output_file_full_path = output_file_full_path_dir + os.sep + os.path.basename(file)
        shutil.copy(file, output_file_full_path)

        expected_files = []
        extracted_file_1 = output_file_full_path_dir + os.sep + "single_product_retrieval_2.fits"
        expected_files.append(extracted_file_1)

        try:
            extracted_file = (JwstClass.gzip_uncompress_and_rename_single_file(
                              output_file_full_path))
            if extracted_file != extracted_file_1:
                raise ValueError(f"Extracted file not found: {extracted_file_1}")
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

    def __check_results_column(self, results, columnName, description, unit,
                               dataType):
        c = results[columnName]
        assert c.description == description, \
            f"Wrong description for results column '{columnName}'. Expected: '{description}', "\
            f"found '{c.description}'"
        assert c.unit == unit, \
            f"Wrong unit for results column '{columnName}'. Expected: '{unit}', found '{c.unit}'"
        assert c.dtype == dataType, \
            f"Wrong dataType for results column '{columnName}'. Expected: '{dataType}', found '{c.dtype}'"

    def __remove_folder_contents(self, folder):
        for root, dirs, files in os.walk(folder):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    def __check_extracted_files(self, files_expected, files_returned):
        if len(files_expected) != len(files_returned):
            raise ValueError(f"Expected files size error. "
                             f"Found {len(files_returned)}, "
                             f"expected {len(files_expected)}")
        for f in files_expected:
            if not os.path.exists(f):
                raise ValueError(f"Not found extracted file: "
                                 f"{f}")
            if f not in files_returned:
                raise ValueError(f"Not found expected file: {f}")

    def test_query_target_error(self):
        # need to patch simbad query object here
        with patch("astroquery.simbad.SimbadClass.query_object",
                   side_effect=lambda object_name: parse_single_table(
                       Path(__file__).parent / "data" / f"simbad_{object_name}.vot"
                   ).to_table()):
            jwst = JwstClass(show_messages=False)
            simbad = SimbadClass()
            ned = Ned()
            vizier = Vizier()
            # Testing default parameters
            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target(target_name="M1", target_resolver="")
                assert "This target resolver is not allowed" in err.value.args[0]
            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target("TEST")
                assert ('This target name cannot be determined with this '
                        'resolver: ALL' in err.value.args[0] or 'Failed to parse' in err.value.args[0])
            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target(target_name="M1", target_resolver="ALL")
                assert err.value.args[0] in ["This target name cannot be determined "
                                             "with this resolver: ALL", "Missing "
                                             "required argument: 'width'"]

            # Testing no valid coordinates from resolvers
            simbad_file = data_path('test_query_by_target_name_simbad_ned_error.vot')
            simbad_table = Table.read(simbad_file)
            simbad.query_object = MagicMock(return_value=simbad_table)
            ned_file = data_path('test_query_by_target_name_simbad_ned_error.vot')
            ned_table = Table.read(ned_file)
            ned.query_object = MagicMock(return_value=ned_table)
            vizier_file = data_path('test_query_by_target_name_vizier_error.vot')
            vizier_table = Table.read(vizier_file)
            vizier.query_object = MagicMock(return_value=vizier_table)

            # coordinate_error = 'coordinate must be either a string or astropy.coordinates'
            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target(target_name="TEST", target_resolver="SIMBAD",
                                  radius=units.Quantity(5, units.deg))
                assert ('This target name cannot be determined with this '
                        'resolver: SIMBAD' in err.value.args[0] or 'Failed to parse' in err.value.args[0])

            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target(target_name="TEST", target_resolver="NED",
                                  radius=units.Quantity(5, units.deg))
                assert ('This target name cannot be determined with this '
                        'resolver: NED' in err.value.args[0] or 'Failed to parse' in err.value.args[0])

            with pytest.raises((ValueError, TableParseError)) as err:
                jwst.query_target(target_name="TEST", target_resolver="VIZIER",
                                  radius=units.Quantity(5, units.deg))
                assert ('This target name cannot be determined with this resolver: '
                        'VIZIER' in err.value.args[0] or 'Failed to parse' in err.value.args[0])

    @patch.object(JwstClass, 'login')
    def test_login(self, login_mock):
        tap = JwstClass(show_messages=False)
        parameters = {}
        parameters['user'] = 'test_user'
        parameters['password'] = 'test_password'
        parameters['credentials_file'] = None
        parameters['verbose'] = False
        tap.login(user='test_user', password='test_password')
        login_mock.assert_called_once_with(
            user="test_user",
            password="test_password"
        )

    @patch.object(JwstClass, 'logout')
    def test_logout(self, logout_mock):
        tap = JwstClass(show_messages=False)
        parameters = {}
        parameters['verbose'] = False
        tap.logout()
        logout_mock.assert_called_once()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_set_token_ok(self, mock_execute_servlet_request):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        tap = JwstClass(show_messages=False)
        token = 'test_token'

        # Mock a successful servlet response
        mock_execute_servlet_request.return_value = SimpleNamespace(status=200)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('MAST token has been set successfully' in buffer.getvalue())
        mock_execute_servlet_request.assert_called_once_with(
            tap=tap.tap,
            query_params={'token': token},
            url=conf.JWST_DOMAIN_SERVER + conf.JWST_TARGET_ACTION,
        )

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_set_token_anonymous_error(self, mock_execute_servlet_request):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        tap = JwstClass(show_messages=False)
        token = 'test_token'

        # Mock 403 error
        mock_execute_servlet_request.return_value = SimpleNamespace(status=403)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('ERROR: MAST tokens cannot be assigned or requested by anonymous users' in buffer.getvalue())
        mock_execute_servlet_request.assert_called_once_with(
            tap=tap.tap,
            query_params={'token': token},
            url=conf.JWST_DOMAIN_SERVER + conf.JWST_TARGET_ACTION,
        )

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_set_token_server_error(self, mock_execute_servlet_request):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        tap = JwstClass(show_messages=False)
        token = 'test_token'

        # Mock 500 error
        mock_execute_servlet_request.return_value = SimpleNamespace(status=500)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('ERROR: Server error when setting the token' in buffer.getvalue())
        mock_execute_servlet_request.assert_called_once_with(
            tap=tap.tap,
            query_params={'token': token},
            url=conf.JWST_DOMAIN_SERVER + conf.JWST_TARGET_ACTION,
        )

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.execute_servlet_request')
    def test_get_messages_ok(self, mock_execute_servlet_request):
        old_stdout = sys.stdout # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        jwst = JwstClass(show_messages=False)

        # Fake response object for parse_messages_response
        class FakeResponse:
            def iter_lines(self):
                return [b"message=SERVER OK"]

        # Calls the parser method in execute_servlet_request using the fake response
        mock_execute_servlet_request.side_effect = lambda *args, **kwargs: kwargs["parser_method"](FakeResponse())

        jwst.get_status_messages()

        sys.stdout = old_stdout
        assert ('SERVER OK' in buffer.getvalue())
        mock_execute_servlet_request.assert_called_once()

    @pytest.mark.noautofixt
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_query_get_product(self, mock_query_tap):
        tap = JwstClass(show_messages=False)
        file = 'test_file'
        parameters = {}
        parameters['query'] = f"select * from jwst.artifact a where a.filename = '{file}'"
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False

        # Mock return value for job.get_results()
        mock_job = MagicMock()
        mock_job.get_results.side_effect = [{'artifactid': ['artifact123']}, {"filename": ["file456.fits"]}]
        mock_query_tap.return_value = mock_job

        result = tap._query_get_product(file_name=file)

        mock_query_tap.assert_called_once_with(query=f"select * from jwst.artifact a where a.filename = '{file}'")
        assert result == 'artifact123'

        mock_query_tap.reset_mock()

        artifact = 'test_artifact'
        parameters['query'] = f"select * from jwst.artifact a where a.artifactid = '{artifact}'"
        result = tap._query_get_product(artifact_id=artifact)
        mock_query_tap.assert_called_once_with(query=f"select * from jwst.artifact a where a.artifactid = '{artifact}'")
        assert result == 'file456.fits'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(JwstClass, 'query_tap')
    def test_get_related_observations(self, mock_query_tap):
        tap = JwstClass(show_messages=False)
        obs = 'dummyObs'

        mock_job_ok = MagicMock()
        mock_job_ok.get_results.return_value = {"observationid": ["OBS1", "OBS2"]}
        mock_query_tap.return_value = mock_job_ok

        result = tap.get_related_observations(observation_id=obs)
        assert result == ["OBS1", "OBS2"]
        mock_query_tap.assert_called_once_with(
            query=f"select * from {conf.JWST_MAIN_TABLE} m where m.members like '%{obs}%'"
        )

        mock_query_tap.reset_mock()
        mock_job_empty = MagicMock()
        mock_job_empty.get_results.return_value = {"observationid": [""]}
        mock_job_members = MagicMock()
        mock_job_members.get_results.return_value = {"members": ["caom:JWST/123 456 789"]}
        mock_query_tap.side_effect = [mock_job_empty, mock_job_members]

        result = tap.get_related_observations(observation_id=obs)
        assert result == ["123", "456", "789"]

        assert mock_query_tap.call_args_list[0].kwargs == {"query": f"select * from {conf.JWST_MAIN_TABLE} m where m.members like '%{obs}%'"}
        assert mock_query_tap.call_args_list[1].kwargs == {"query": f"select m.members from {conf.JWST_MAIN_TABLE} m where m.observationid='{obs}'"}

    def test_parse_messages_response(self):
        jwst = JwstClass(show_messages=False)
        response = Response()
        response.status_code = 200
        plain_text = (
            "notification_id1[type: type1,subtype1]=msg1\n"
            "notification_id2[type: type2,subtype2]=msg2\n"
            "notification_idn[type: typen,subtypen]=msgn"
        )
        response._content = plain_text.encode('utf-8')
        response.headers['Content-Type'] = 'text/plain'
        response.raw = io.BytesIO(response._content)
        messages = jwst.parse_messages_response(response)
        assert len(messages) == 3
        assert messages == ["msg1", "msg2", "msgn"]
