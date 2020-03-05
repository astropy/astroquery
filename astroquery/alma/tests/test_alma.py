# Licensed under a 3-clause BSD style license - see LICENSE.rst
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
    assert '2011.0.00497.S' in result['Project code']


def test_validator(monkeypatch):

    monkeypatch.setattr(Alma, '_get_dataarchive_url', _get_dataarchive_url)
    alma = Alma()
    monkeypatch.setattr(alma, '_get_dataarchive_url', _get_dataarchive_url)
    monkeypatch.setattr(alma, '_request', alma_request)

    with pytest.raises(InvalidQueryError) as exc:
        alma.query(payload={'invalid_parameter': 1})

    assert 'invalid_parameter' in str(exc.value)
