# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ... import besancon
import os
from astropy.tests.helper import pytest
from astropy.io.ascii.tests.common import assert_equal
import requests
import StringIO

# SKIP - don't run tests because Besancon folks don't want them (based on the fact that your@email.net is now rejected)
# def test_besancon_reader():
# assert os.path.exists('besancon_test.txt')
#     B = asciitable.read('t/besancon_test.txt',Reader=besancon.BesanconFixed,guess=False)
#     assert_equal(len(B),12)
#
# def test_basic():
#     besancon_model = besancon.request_besancon('astropy.astroquery@gmail.com',10.5,0.0,soli=0.0001)
#     B = asciitable.read(besancon_model,Reader=besancon.BesanconFixed,guess=False)
#     B.pprint()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.mark.parametrize(('filename','length','ncols'),zip(('besancon_test.txt','besancon_test2.txt'),(13,6),(18,24)))
def test_reader(filename,length,ncols):
    besancon_model = data_path(filename)
    with open(besancon_model,'r') as f:
        data = f.read()
    B = besancon.core.parse_besancon_model_string(data)
    B.pprint()
    assert_equal(len(B),length)
    assert_equal(len(B.columns),ncols)


@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp


def post_mockreturn(url, data, timeout=10, stream=True, params=None):
    filename = data_path('1376235131.430670.resu')
    content = open(filename, 'r').read()
    return MockResponse(content, filename)


class MockResponse(object):

    def __init__(self, content, url):
        self.content = content
        self.raw = StringIO.StringIO(url)


def test_query(patch_post):
    besancon.Besancon.query(0,0,'adam.g.ginsburg@gmail.com')
