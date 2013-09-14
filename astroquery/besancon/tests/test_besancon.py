# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ... import besancon
import os
from contextlib import contextmanager
import astropy.utils.data as aud
from astropy.tests.helper import pytest
from astropy.io.ascii.tests.common import assert_equal
import requests

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

# to prevent test hanging
besancon.Besancon.TIMEOUT = 1
besancon.Besancon.ping_delay = 1

DATA_FILES = ('besancon_test.txt','besancon_test2.txt')

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.mark.parametrize(('filename','length','ncols'),zip(DATA_FILES,(13,6),(18,24)))
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

@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        #file_obj = StringIO.StringIO(filename)
        file_obj = open(data_path(filename), "rb")
        #file_obj = data_path(filename)
        yield file_obj
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp


def post_mockreturn(url, data, timeout=10, stream=True, params=None, **kwargs):
    #filename = data_path('1376235131.430670.resu')
    filename = data_path('query_return.iframe.html')
    content = open(filename, 'r').read()
    return MockResponse(content, filename, **kwargs)

def test_query(patch_post, patch_get_readable_fileobj):
    B = besancon.Besancon()
    B.url_download=''
    result = B.query(0,0,'adam.g.ginsburg@gmail.com')
    assert result is not None

class MockResponse(object):

    def __init__(self, content=None, url=None, headers={}):
        self.content = content
        self.text = content
        self.raw = url #StringIO.StringIO(url)
        self.headers = headers
