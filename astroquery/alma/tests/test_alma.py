# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import os
from astropy.tests.helper import pytest

from .. import Alma
from ...utils.testing_tools import MockResponse
from ...exceptions import (InvalidQueryError)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def data_path(filename):
    return os.path.join(DATA_DIR, filename)

DATA_FILES = {'GET': {'http://almascience.eso.org/aq/search.votable':
                      {'Sgr A*':'sgra_query.xml',
                       'NGC4945':'ngc4945.xml'},
                      'https://almascience.eso.org/rh/requests/anonymous/519752156':
                      'data_list_page.html',
                      'http://almascience.eso.org/rh/requests/anonymous/519752156/script':
                      'downloadRequest519752156script.sh',
                      'http://almascience.eso.org/rh/submission/d45d0552-8479-4482-9833-fecdef3f8b90':
                      'staging_submission.html',
                      'http://almascience.eso.org/aq/':
                      'querypage.html',
                      'http://almascience.eso.org/aq/validate':
                      'empty.html',
                      'http://almascience.eso.org/rh/requests/anonymous/786572566/script':
                      'downloadRequest786572566script.sh',
                      'http://almascience.eso.org/rh/requests/anonymous/786978956/script':
                      'downloadRequest786978956script.sh',
                      'http://almascience.eso.org/rh/requests/anonymous/787632764/script':
                      'downloadRequest787632764script.sh',
                     },
              'POST': {'http://almascience.eso.org/rh/submission':
                       'initial_response.html'}
              }

def url_mapping(url):
    """
    Map input URLs to output URLs for the staging test
    """
    mapping = {'http://almascience.eso.org/rh/submission':
               'http://almascience.eso.org/rh/submission/d45d0552-8479-4482-9833-fecdef3f8b90/submission',
               'http://almascience.eso.org/rh/submission/d45d0552-8479-4482-9833-fecdef3f8b90':
               'https://almascience.eso.org/rh/requests/anonymous/519752156',
              }
    if url not in mapping:
        return url
    else:
        return mapping[url]

def alma_request(request_type, url, params=None, payload=None, data=None,
                 **kwargs):
    if isinstance(DATA_FILES[request_type][url],dict):
        payload = (payload if payload is not None else
                   params if params is not None else
                   data if data is not None else
                   None)
        if payload is None:
            raise ValueError("Empty payload for query that requires a payload.")
        source_name = (payload['source_name_sesame']
                       if 'source_name_sesame' in payload
                       else payload['source_name-asu'])
        fn = DATA_FILES[request_type][url][source_name]
    else:
        fn = DATA_FILES[request_type][url]

    with open(data_path(fn), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    response.url = url_mapping(url)
    return response



def _get_dataarchive_url(*args):
    return 'http://almascience.eso.org'

def test_SgrAstar(monkeypatch):
    # Local caching prevents a remote query here

    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    monkeypatch.setattr(alma, '_get_dataarchive_url', _get_dataarchive_url)
    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    monkeypatch.setattr(alma, '_request', alma_request)
    # set up local cache path to prevent remote query
    alma.cache_location = DATA_DIR

    # the failure should occur here
    result = alma.query_object('Sgr A*')

    # test that max_results = 50
    assert len(result) == 82
    assert b'2011.0.00217.S' in result['Project_code']

def test_staging(monkeypatch):

    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_get_dataarchive_url', _get_dataarchive_url)
    monkeypatch.setattr(alma, '_request', alma_request)

    target = 'NGC4945'
    project_code = '2011.0.00121.S'
    payload = {'project_code-asu':project_code,
               'source_name-asu':target,}
    result = alma.query(payload=payload)

    uid_url_table = alma.stage_data(result['Asdm_uid'])
    assert len(uid_url_table) == 2


def test_validator(monkeypatch):

    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    monkeypatch.setattr(alma, '_get_dataarchive_url', _get_dataarchive_url)
    monkeypatch.setattr(alma, '_request', alma_request)


    with pytest.raises(InvalidQueryError) as exc:
        alma.query(payload={'invalid_parameter': 1})

    assert 'invalid_parameter' in str(exc.value)

def test_parse_staging_request_page_asdm(monkeypatch):
    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_request', alma_request)

    with open(data_path('request_786572566.html'), 'rb') as f:
        response = MockResponse(content=f.read())

    alma._staging_log = {'data_list_url': 'request_786572566.html'}
    tbl = alma._parse_staging_request_page(response)
    assert tbl[0]['URL'] == 'https://almascience.eso.org/dataPortal/requests/anonymous/786572566/ALMA/uid___A002_X3b3400_X90f/uid___A002_X3b3400_X90f.asdm.sdm.tar'
    assert tbl[0]['uid'] == 'uid___A002_X3b3400_X90f.asdm.sdm.tar'
    np.testing.assert_approx_equal(tbl[0]['size'], -1e-9)

def test_parse_staging_request_page_mous(monkeypatch):
    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_request', alma_request)

    with open(data_path('request_786978956.html'), 'rb') as f:
        response = MockResponse(content=f.read())

    alma._staging_log = {'data_list_url': 'request_786978956.html'}
    tbl = alma._parse_staging_request_page(response)
    assert tbl[0]['URL'] == 'https://almascience.eso.org/dataPortal/requests/anonymous/786978956/ALMA/2011.0.00772.S_2012-09-12_001_of_015.tar/2011.0.00772.S_2012-09-12_001_of_015.tar'
    assert tbl[0]['uid'] == 'uid://A002/X3216af/X31'
    np.testing.assert_approx_equal(tbl[0]['size'], 0.2093)
    assert len(tbl) == 26

def test_parse_staging_request_page_mous_cycle0(monkeypatch):
    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_request', alma_request)

    with open(data_path('request_787632764.html'), 'rb') as f:
        response = MockResponse(content=f.read())

    alma._staging_log = {'data_list_url': 'request_787632764.html'}
    tbl = alma._parse_staging_request_page(response)
    assert tbl[0]['URL'] == 'https://almascience.eso.org/dataPortal/requests/anonymous/787632764/ALMA/2011.0.00121.S_2012-08-16_001_of_002.tar/2011.0.00121.S_2012-08-16_001_of_002.tar'
    assert tbl[0]['uid'] == 'uid://A002/X327408/X246'
    np.testing.assert_approx_equal(tbl[0]['size'], 5.9)
    assert len(tbl) == 32
