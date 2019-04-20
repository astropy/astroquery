# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""
import os

from astroquery.cadc import Cadc, conf
import astroquery.cadc.core as cadc_core
from astroquery.utils.commons import parse_coordinates
from astroquery.cadc.tests.DummyTapHandler import DummyTapHandler
import pytest


# monkeypatch get_access_url to prevent internet calls
def get_access_url_mock(arg1, arg2):
    return "some.url"


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_get_tables(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    # default parameters
    parameters = {}
    parameters['only_names'] = False
    parameters['verbose'] = False
    tap.get_tables()
    dummyTapHandler.check_call('get_tables', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters = {}
    parameters['only_names'] = True
    parameters['verbose'] = True
    tap.get_tables(True, True)
    dummyTapHandler.check_call('get_tables', parameters)


def test_get_table(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    # default parameters
    parameters = {}
    parameters['table'] = 'table'
    parameters['verbose'] = False
    tap.get_table('table')
    dummyTapHandler.check_call('get_table', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters = {}
    parameters['table'] = 'table'
    parameters['verbose'] = True
    tap.get_table('table', verbose=True)
    dummyTapHandler.check_call('get_table', parameters)


def test_run_query(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    query = "query"
    operation = 'sync'
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
    tap.run_query(query, operation)
    dummyTapHandler.check_call('run_query', parameters)
    # test with parameters
    dummyTapHandler.reset()
    output_file = 'output'
    output_format = 'format'
    verbose = True
    upload_resource = 'upload_res'
    upload_table_name = 'upload_table'
    parameters['query'] = query
    parameters['name'] = None
    parameters['output_file'] = output_file
    parameters['output_format'] = output_format
    parameters['verbose'] = verbose
    parameters['dump_to_file'] = True
    parameters['upload_resource'] = upload_resource
    parameters['upload_table_name'] = upload_table_name
    tap.run_query(query,
                  operation,
                  output_file=output_file,
                  output_format=output_format,
                  verbose=verbose,
                  upload_resource=upload_resource,
                  upload_table_name=upload_table_name)
    dummyTapHandler.check_call('run_query', parameters)


def test_load_async_job(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    jobid = '123'
    # default parameters
    parameters = {}
    parameters['jobid'] = jobid
    parameters['verbose'] = False
    tap.load_async_job(jobid)
    dummyTapHandler.check_call('load_async_job', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters['jobid'] = jobid
    parameters['verbose'] = True
    tap.load_async_job(jobid, verbose=True)
    dummyTapHandler.check_call('load_async_job', parameters)


def test_list_async_jobs(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
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


def test_save_results(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    job = '123'
    # default parameters
    parameters = {}
    parameters['job'] = job
    parameters['filename'] = 'file.txt'
    parameters['verbose'] = False
    tap.save_results(job, 'file.txt')
    dummyTapHandler.check_call('save_results', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters['job'] = job
    parameters['filename'] = 'file.txt'
    parameters['verbose'] = True
    tap.save_results(job, 'file.txt', verbose=True)
    dummyTapHandler.check_call('save_results', parameters)


def test_login(monkeypatch):
    def get_access_url_mock(arg1, arg2):
        return "some.url"

    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    dummyTapHandler = DummyTapHandler()
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    user = 'user'
    password = 'password'
    cert = 'cert'
    # default parameters
    parameters = {}
    parameters['cookie_prefix'] = cadc_core.CADC_COOKIE_PREFIX
    parameters['login_url'] = "some.url"
    parameters['verbose'] = False
    parameters['user'] = None
    parameters['password'] = None
    parameters['certificate_file'] = None
    tap.login(None, None, None)
    dummyTapHandler.check_call('login', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters['user'] = user
    parameters['password'] = password
    parameters['certificate_file'] = cert
    tap.login(user, password, cert)
    dummyTapHandler.check_call('login', parameters)


def test_logout(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    tap = Cadc(tap_plus_handler=dummyTapHandler)
    # default parameters
    parameters = {}
    parameters['verbose'] = False
    tap.logout(False)
    dummyTapHandler.check_call('logout', parameters)
    # test with parameters
    dummyTapHandler.reset()
    parameters['verbose'] = True
    tap.logout(True)
    dummyTapHandler.check_call('logout', parameters)


def test_get_access_ur(monkeypatch):
    assert 'http://some.url' == cadc_core.get_access_url('http://some.url')

    def get(self, method, url, **kwargs):
        class ServiceResponse(object):
            def __init__(self):
                self.text = 'ivo://cadc.nrc.ca/mytap = http://my.org/mytap'

            def raise_for_status(self):
                pass

        class CapabilitiesResponse(object):
            def __init__(self):
                caps_file = data_path('tap_caps.xml')
                self.text = open(caps_file, 'r').read()

            def raise_for_status(self):
                pass
        if url == conf.CADC_REGISTRY_URL:
            return ServiceResponse()
        else:
            return CapabilitiesResponse()

    # don't know why the decorator doesnt work here
    monkeypatch.setattr(cadc_core.BaseQuery, '_request', get)
    monkeypatch.setattr(cadc_core.get_access_url, 'caps', {})
    assert 'http://my.org/mytap' == cadc_core.get_access_url('mytap')

    assert \
        'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap/tables' == \
        cadc_core.get_access_url('mytap', 'ivo://ivoa.net/std/VOSI#tables-1.1')


def test_get_data_urls(monkeypatch):
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)

    def get(*args, **kwargs):
        class CapsResponse(object):
            def __init__(self):
                self.status_code = 200
                self.content = b''

            def raise_for_status(self):
                pass
        return CapsResponse()

    class Result(object):
        pass

    vot_result = Result()
    vot_result.array = [{'semantics': b'#this',
                         'access_url': b'https://get.your.data/path'},
                        {'semantics': b'#aux',
                         'access_url': b'https://get.your.data/auxpath'}]

    monkeypatch.setattr(cadc_core, 'parse_single_table', lambda x: vot_result)
    dummyTapHandler = DummyTapHandler()
    cadc = Cadc(tap_plus_handler=dummyTapHandler)
    cadc._request = get  # mock the request
    assert [vot_result.array[0]['access_url'].decode('ascii')] == \
        cadc.get_data_urls({'caomPublisherID': ['ivo://cadc.nrc.ca/foo']})
    assert [vot_result.array[0]['access_url'].decode('ascii'),
            vot_result.array[1]['access_url'].decode('ascii')] == \
        cadc.get_data_urls({'caomPublisherID': ['ivo://cadc.nrc.ca/foo']},
                           include_auxiliaries=True)
    with pytest.raises(AttributeError):
        cadc.get_data_urls(None)
    with pytest.raises(AttributeError):
        cadc.get_data_urls({'noPublisherID': 'test'})


def test_misc(monkeypatch):
    dummyTapHandler = DummyTapHandler()
    monkeypatch.setattr(cadc_core, 'get_access_url', get_access_url_mock)
    cadc = Cadc(tap_plus_handler=dummyTapHandler)

    class Result(object):
        pass
    result = Result()
    result._phase = 'RUN'
    with pytest.raises(RuntimeError):
        cadc._parse_result(result)

    result._phase = 'COMPLETED'
    result.results = 'WELL DONE'
    assert result.results == cadc._parse_result(result)
    coords = '08h45m07.5s +54d18m00s'
    coords_ra = parse_coordinates(coords).ra.degree
    coords_dec = parse_coordinates(coords).dec.degree

    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 " \
           "AND (quality_flag IS NULL OR quality_flag != 'junk') " \
           "AND collection='CFHT'".format(coords_ra, coords_dec) == \
           cadc._args_to_payload(**{'coordinates': coords,
                                 'radius': 0.3, 'collection': 'CFHT'})['query']

    # no collection
    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 AND (quality_flag IS NULL OR " \
           "quality_flag != 'junk')".format(coords_ra, coords_dec) ==  \
           cadc._args_to_payload(**{'coordinates': coords,
                                 'radius': 0.3})['query']
