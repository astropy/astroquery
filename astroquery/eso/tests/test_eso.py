# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from ...utils.testing_tools import MockResponse

from ...eso import Eso

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)

DATA_FILES = {'GET': {'http://archive.eso.org/wdb/wdb/eso/amber/form':
                      'amber_form.html',
                      'http://archive.eso.org/wdb/wdb/adp/phase3_main/form':
                      'vvv_sgra_form.html',
                      },
              'POST': {'http://archive.eso.org/wdb/wdb/eso/amber/query':
                       'amber_sgra_query.tbl',
                       'http://archive.eso.org/wdb/wdb/adp/phase3_main/query':
                       'vvv_sgra_survey_response.tbl',
                       }
              }


def eso_request(request_type, url, **kwargs):
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# @pytest.fixture
# def patch_get(request):
#    mp = request.getfuncargvalue("monkeypatch")
#    mp.setattr(Eso, 'request', eso_request)
#    return mp

# This test should attempt to access the internet and therefore should fail
# (_activate_form always connects to the internet)
# @pytest.mark.xfail
def test_SgrAstar(monkeypatch):
    # Local caching prevents a remote query here

    eso = Eso()

    # monkeypatch instructions from https://pytest.org/latest/monkeypatch.html
    monkeypatch.setattr(eso, '_request', eso_request)
    # set up local cache path to prevent remote query
    eso.cache_location = DATA_DIR

    # the failure should occur here
    result = eso.query_instrument('amber', target='Sgr A*')

    # test that max_results = 50
    assert len(result) == 50
    assert 'GC_IRS7' in result['Object']


def test_vvv(monkeypatch):
    eso = Eso()
    monkeypatch.setattr(eso, '_request', eso_request)
    eso.cache_location = DATA_DIR

    result_s = eso.query_surveys('VVV',
                                 coord1=266.41681662, coord2=-29.00782497,
                                 box='01 00 00',
                                )
    assert result_s is not None
    assert 'Object' in result_s.colnames
    assert 'b333' in result_s['Object']
