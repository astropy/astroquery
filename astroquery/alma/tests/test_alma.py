# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import os
import pytest
from ...utils.testing_tools import MockResponse
from ...exceptions import (InvalidQueryError)

from .. import Alma

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


DATA_FILES = {
    'GET': {'http://almascience.eso.org/aq/': {'eta carinae': 'etacar_query.xml',
                                               'NGC4945': 'ngc4945.xml',
                                               '': 'querypage.html',
                                               },
            'https://almascience.eso.org/rh/requests/anonymous/519752156':
                'data_list_page.html',
            'http://almascience.eso.org/rh/requests/anonymous/519752156/script':
                'downloadRequest519752156script.sh',
            'http://almascience.eso.org/rh/submission/d45d0552-8479-4482-9833-fecdef3f8b90':
                'staging_submission.html',
            'http://almascience.eso.org/aq/validate':
                'empty.html',
            'http://almascience.eso.org/rh/requests/anonymous/786572566/script':
                'downloadRequest786572566script.sh',
            'http://almascience.eso.org/rh/requests/anonymous/786978956/script':
                'downloadRequest786978956script.sh',
            'http://almascience.eso.org/rh/requests/anonymous/787632764/script':
                'downloadRequest787632764script.sh',
            'https://almascience.eso.org/rh/requests/anonymous/519752156/summary':
                'summary_519752156.json',
            },
    'POST': {'http://almascience.eso.org/rh/submission':
             'initial_response.html'}}


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
    if isinstance(DATA_FILES[request_type][url], dict):
        payload = (payload if payload is not None else
                   params if params is not None else
                   data if data is not None else
                   None)
        if payload is None:
            fn = DATA_FILES[request_type][url]['']
        else:
            source_name = (payload['source_name_resolver']
                           if 'source_name_resolver' in payload
                           else payload['source_name_alma'])
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
    result = alma.query_object('eta carinae')

    assert len(result) == 15
    assert b'2011.0.00497.S' in result['Project code']


def test_staging(monkeypatch):

    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_get_dataarchive_url', _get_dataarchive_url)
    monkeypatch.setattr(alma, '_request', alma_request)

    target = 'NGC4945'
    project_code = '2011.0.00121.S'
    payload = {'project_code': project_code,
               'source_name_resolver': target}
    result = alma.query(payload=payload)

    uid_url_table = alma.stage_data(result['Asdm uid'])
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
    """
    Example:
        Alma.stage_data('uid://A002/X47bd4d/X4c7')
        Alma._staging_log
{'data_list_page': <Response [200]>,
 'data_list_url': 'https://almascience.eso.org/rh/requests/anonymous/801926122',
 'data_page': <Response [200]>,
 'first_post_url': u'https://almascience.eso.org/rh/submission',
 'initial_response': <Response [200]>,
 'request_id': u'cf9ce7c8-b140-4c53-bd54-52fa3fb44f19',
 'staging_page_id': u'801926122',
 'staging_submission': <Response [200]>,
 'submission_url': u'https://almascience.eso.org/rh/submission/cf9ce7c8-b140-4c53-bd54-52fa3fb44f19'}
 with open('/Users/adam/repos/astroquery/astroquery/alma/tests/data/request_801926122.html','w') as f:
    f.write(Alma._staging_log['data_list_page'].content)
    """
    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    alma.dataarchive_url = _get_dataarchive_url()
    monkeypatch.setattr(alma, '_request', alma_request)

    with open(data_path('request_801926122.html'), 'rb') as f:
        response = MockResponse(content=f.read())

    alma._staging_log = {'data_list_url': 'request_801926122.html'}
    tbl = alma._parse_staging_request_page(response)
    assert tbl[0]['URL'] == 'None_Found'
    assert tbl[0]['uid'] == 'uid___A002_X47bd4d_X4c7.asdm.sdm.tar'
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
    assert tbl[0]['URL'] == 'https://almascience.eso.org/dataPortal/requests/anonymous/786978956/ALMA/2011.0.00772.S_2012-09-12_001_of_015.tar/2011.0.00772.S_2012-09-12_001_of_015.tar'  # noqa
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
    assert tbl[0]['URL'] == 'https://almascience.eso.org/dataPortal/requests/anonymous/787632764/ALMA/2011.0.00121.S_2012-08-16_001_of_002.tar/2011.0.00121.S_2012-08-16_001_of_002.tar'  # noqa
    assert tbl[0]['uid'] == 'uid://A002/X327408/X246'
    np.testing.assert_approx_equal(tbl[0]['size'], 5.9)
    assert len(tbl) == 32
