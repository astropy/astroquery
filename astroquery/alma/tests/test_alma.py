# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from astropy.tests.helper import pytest

from .. import Alma
from ...utils.testing_tools import MockResponse

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def data_path(filename):
    return os.path.join(DATA_DIR, filename)

DATA_FILES = {'GET': {'http://almascience.org/aq/search.votable':
                      {'Sgr A*':'sgra_query.xml',
                       'NGC4945':'ngc4945.xml'},
                      'https://almascience.eso.org/rh/requests/anonymous/519752156':
                      'data_list_page.html',
                      'http://almascience.eso.org/rh/submission/d45d0552-8479-4482-9833-fecdef3f8b90':
                      'staging_submission.html',
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

    uid_url_table = alma.stage_data(result['Asdm_uid'], cache=False)
    assert len(uid_url_table) == 2


