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
from unittest.mock import MagicMock, patch
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
from astroquery.exceptions import TableParseError

from astroquery.esa.jwst import JwstClass
from astroquery.esa.jwst.tests.DummyTapHandler import DummyTapHandler
from astroquery.ipac.ned import Ned
from astroquery.simbad import SimbadClass
from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse
from astroquery.utils.tap.core import TapPlus
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

    def test_load_tables(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        # default parameters
        parameters = {}
        parameters['only_names'] = False
        parameters['include_shared_tables'] = False
        parameters['verbose'] = False
        tap.load_tables()
        dummyTapHandler.check_call('load_tables', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['only_names'] = True
        parameters['include_shared_tables'] = True
        parameters['verbose'] = True
        tap.load_tables(only_names=True, include_shared_tables=True, verbose=True)
        dummyTapHandler.check_call('load_tables', parameters)

    def test_load_table(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        # default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        tap.load_table('table')
        dummyTapHandler.check_call('load_table', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        tap.load_table('table', verbose=True)
        dummyTapHandler.check_call('load_table', parameters)

    def test_launch_sync_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        query = "query"
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_job(query)
        dummyTapHandler.check_call('launch_job', parameters)
        # test with parameters
        dummyTapHandler.reset()
        name = 'name'
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        parameters['query'] = query
        parameters['name'] = name
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        tap.launch_job(query,
                       name=name,
                       output_file=output_file,
                       output_format=output_format,
                       verbose=verbose,
                       dump_to_file=dump_to_file,
                       upload_resource=upload_resource,
                       upload_table_name=upload_table_name)
        dummyTapHandler.check_call('launch_job', parameters)

    def test_launch_async_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        query = "query"
        # default parameters
        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['background'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap.launch_job(query, async_job=True)
        dummyTapHandler.check_call('launch_job_async', parameters)
        # test with parameters
        dummyTapHandler.reset()
        name = 'name'
        output_file = 'output'
        output_format = 'format'
        verbose = True
        dump_to_file = True
        background = True
        upload_resource = 'upload_res'
        upload_table_name = 'upload_table'
        parameters['query'] = query
        parameters['name'] = name
        parameters['output_file'] = output_file
        parameters['output_format'] = output_format
        parameters['verbose'] = verbose
        parameters['dump_to_file'] = dump_to_file
        parameters['background'] = background
        parameters['upload_resource'] = upload_resource
        parameters['upload_table_name'] = upload_table_name
        tap.launch_job(query,
                       name=name,
                       output_file=output_file,
                       output_format=output_format,
                       verbose=verbose,
                       dump_to_file=dump_to_file,
                       background=background,
                       upload_resource=upload_resource,
                       upload_table_name=upload_table_name,
                       async_job=True)
        dummyTapHandler.check_call('launch_job_async', parameters)

    def test_list_async_jobs(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        # default parameters
        parameters = {}
        parameters['verbose'] = False
        tap.list_async_jobs()
        dummyTapHandler.check_call('list_async_jobs', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters['verbose'] = True
        tap.list_async_jobs(verbose=True)
        dummyTapHandler.check_call('list_async_jobs', parameters)

    def test_query_region(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)

        with pytest.raises(ValueError) as err:
            tap.query_region(coordinate=123)
        assert "coordinate must be either a string or astropy.coordinates" in err.value.args[0]

        with pytest.raises(NameResolveError) as err:
            tap.query_region(coordinate='test')
        assert ("Unable to find coordinates for name 'test'" in err.value.args[0] or "Unable to retrieve "
                "coordinates" in err.value.args[0])

        # Launch response: we use default response because the
        # query contains decimals
        responseLaunchJob = DummyResponse(200)
        responseLaunchJob.set_data(method='POST', body=JOB_DATA)
        # The query contains decimals: force default response
        connHandler.set_default_response(responseLaunchJob)
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

    def test_query_region_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)
        jobid = '12345'
        # Launch response
        responseLaunchJob = DummyResponse(303)
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [['location', 'http://test:1111/tap/async/' + jobid]]
        responseLaunchJob.set_data(method='POST', headers=launchResponseHeaders)
        connHandler.set_default_response(responseLaunchJob)
        # Phase response
        responsePhase = DummyResponse(200)
        responsePhase.set_data(method='GET', body="COMPLETED")
        req = "async/" + jobid + "/phase"
        connHandler.set_response(req, responsePhase)
        # Results response
        responseResultsJob = DummyResponse(200)
        responseResultsJob.set_data(method='GET', body=JOB_DATA)
        req = "async/" + jobid + "/results/result"
        connHandler.set_response(req, responseResultsJob)
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

    def test_cone_search_sync(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)
        # Launch response: we use default response because the
        # query contains decimals
        responseLaunchJob = DummyResponse(200)
        responseLaunchJob.set_data(method='POST', body=JOB_DATA)
        ra = 19.0
        dec = 20.0
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        connHandler.set_default_response(responseLaunchJob)
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

    def test_cone_search_async(self):
        connHandler = DummyConnHandler()
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)
        jobid = '12345'
        # Launch response
        responseLaunchJob = DummyResponse(303)
        # list of list (httplib implementation for headers in response)
        launchResponseHeaders = [['location', 'http://test:1111/tap/async/' + jobid]]
        responseLaunchJob.set_data(method='POST', headers=launchResponseHeaders)
        ra = 19
        dec = 20
        sc = SkyCoord(ra=ra, dec=dec, unit=(u.degree, u.degree), frame='icrs')
        radius = Quantity(1.0, u.deg)
        connHandler.set_default_response(responseLaunchJob)
        # Phase response
        responsePhase = DummyResponse(200)
        responsePhase.set_data(method='GET', body="COMPLETED")
        req = "async/" + jobid + "/phase"
        connHandler.set_response(req, responsePhase)
        # Results response
        responseResultsJob = DummyResponse(200)
        responseResultsJob.set_data(method='GET', body=JOB_DATA)
        req = "async/" + jobid + "/results/result"
        connHandler.set_response(req, responseResultsJob)
        job = tap.cone_search(sc, radius, async_job=True)
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

    def test_get_product_by_artifactid(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        parameters = {}
        parameters['output_file'] = 'jw00617023001_02102_00001_nrcb4_uncal.fits'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['TAPCLIENT'] = 'ASTROQUERY'
        param_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = param_dict

        jwst.get_product(artifact_id='00000000-0000-0000-8740-65e2827c9895')
        dummyTapHandler.check_call('load_data', parameters)

    def test_get_product_by_filename(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id' or 'file_name'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

        parameters = {}
        parameters['output_file'] = 'file_name_id'
        parameters['verbose'] = False

        param_dict = {}
        param_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        param_dict['TAPCLIENT'] = 'ASTROQUERY'
        param_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = param_dict

        jwst.get_product(file_name='file_name_id')
        dummyTapHandler.check_call('load_data', parameters)

    def test_get_products_list(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)

        # test with parameters
        dummyTapHandler.reset()

        observation_id = "jw00777011001_02104_00001_nrcblong"

        query = (f"select distinct a.uri, a.artifactid, a.filename, "
                 f"a.contenttype, a.producttype, p.calibrationlevel, p.public "
                 f"FROM {conf.JWST_PLANE_TABLE} p JOIN {conf.JWST_ARTIFACT_TABLE} "
                 f"a ON (p.planeid=a.planeid) WHERE a.planeid "
                 f"IN {planeids} AND producttype ILIKE '%science%';")

        parameters = {}
        parameters['query'] = query
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None

        jwst.get_product_list(observation_id=observation_id, product_type='science')
        dummyTapHandler.check_call('launch_job', parameters)

    def test_get_products_list_error(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)
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

    def test_download_files_from_program(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)
        with pytest.raises(TypeError) as err:
            jwst.download_files_from_program()
        assert "missing 1 required positional argument: 'proposal_id'" in err.value.args[0]

    def test_get_obs_products(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, data_handler=dummyTapHandler, show_messages=False)
        # default parameters
        with pytest.raises(ValueError) as err:
            jwst.get_obs_products()
        assert "Missing required argument: 'observation_id'" in err.value.args[0]

        # test with parameters
        dummyTapHandler.reset()

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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
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
            dummyTapHandler.check_call('load_data', parameters)
            self.__check_extracted_files(files_expected=expected_files,
                                         files_returned=files_returned)
        finally:
            # self.__remove_folder_contents(folder=output_file_full_path_dir)
            shutil.rmtree(output_file_full_path_dir)

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

    def test_remove_jobs(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        job_list = ['dummyJob']
        parameters = {}
        parameters['jobs_list'] = job_list
        parameters['verbose'] = False
        tap.remove_jobs(jobs_list=job_list)
        dummyTapHandler.check_call('remove_jobs', parameters)

    def test_save_results(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        job = 'dummyJob'
        parameters = {}
        parameters['job'] = job
        parameters['verbose'] = False
        tap.save_results(job)
        dummyTapHandler.check_call('save_results', parameters)

    def test_login(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        parameters = {}
        parameters['user'] = 'test_user'
        parameters['password'] = 'test_password'
        parameters['credentials_file'] = None
        parameters['verbose'] = False
        tap.login(user='test_user', password='test_password')
        dummyTapHandler.check_call('login', parameters)

    def test_logout(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        parameters = {}
        parameters['verbose'] = False
        tap.logout()
        dummyTapHandler.check_call('logout', parameters)

    def test_set_token_ok(self):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        connHandler = DummyConnHandler()
        response = DummyResponse(200)
        response.set_data(method='GET', body='OK')
        token = 'test_token'
        connHandler.set_response(f"{conf.JWST_TOKEN}?token={token}", response)
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('MAST token has been set successfully' in buffer.getvalue())

    def test_set_token_anonymous_error(self):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        connHandler = DummyConnHandler()
        response = DummyResponse(403)
        response.set_data(method='GET', body='OK')
        token = 'test_token'
        connHandler.set_response(f"{conf.JWST_TOKEN}?token={token}", response)
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('ERROR: MAST tokens cannot be assigned or requested by anonymous users' in buffer.getvalue())

    def test_set_token_server_error(self):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        connHandler = DummyConnHandler()
        response = DummyResponse(500)
        response.set_data(method='GET', body='OK')
        token = 'test_token'
        connHandler.set_response(f"{conf.JWST_TOKEN}?token={token}", response)
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)

        tap.set_token(token=token)

        sys.stdout = old_stdout
        assert ('ERROR: Server error when setting the token' in buffer.getvalue())

    def test_get_messages_ok(self):
        old_stdout = sys.stdout  # Memorize the default stdout stream
        sys.stdout = buffer = io.StringIO()

        connHandler = DummyConnHandler()
        response = DummyResponse(200)
        response.set_data(method='GET', body='message=SERVER OK')
        connHandler.set_response(f"{conf.JWST_MESSAGES}", response)
        tapplus = TapPlus(url="http://test:1111/tap", connhandler=connHandler)
        tap = JwstClass(tap_plus_handler=tapplus, show_messages=False)

        tap.get_status_messages()
        sys.stdout = old_stdout
        assert ('SERVER OK' in buffer.getvalue())

    @pytest.mark.noautofixt
    def test_query_get_product(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        file = 'test_file'
        parameters = {}
        parameters['query'] = f"select * from jwst.artifact a where a.filename = '{file}'"
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        tap._query_get_product(file_name=file)
        dummyTapHandler.check_call('launch_job', parameters)

        artifact = 'test_artifact'
        parameters['query'] = f"select * from jwst.artifact a where a.artifactid = '{artifact}'"
        tap._query_get_product(artifact_id=artifact)
        dummyTapHandler.check_call('launch_job', parameters)

    def test_get_related_observations(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        obs = 'dummyObs'
        tap.get_related_observations(observation_id=obs)
        parameters = {}
        parameters['query'] = f"select * from jwst.main m where m.members like '%{obs}%'"
        parameters['name'] = None
        parameters['output_file'] = None
        parameters['output_format'] = 'votable'
        parameters['verbose'] = False
        parameters['dump_to_file'] = False
        parameters['upload_resource'] = None
        parameters['upload_table_name'] = None
        dummyTapHandler.check_call('launch_job', parameters)

    def test_load_async_job(self):
        dummyTapHandler = DummyTapHandler()
        tap = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        tap.load_async_job(jobid=101222)
        parameters = {}
        parameters['jobid'] = 101222
        parameters['name'] = None
        parameters['verbose'] = False
        dummyTapHandler.check_call('load_async_job', parameters)
