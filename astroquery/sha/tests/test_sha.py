# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sha
from ...utils.testing_tools import MockResponse
import os
from astropy.tests.helper import pytest
import requests

DATA_FILES = {'img': 'img.fits',
              'nid_t': 'nid_t.txt',
              'pid_t': 'pid_t.txt',  # truncated to save space
              'pos_t': 'pos_t.txt',
              'rqk_t': 'rqk_t.txt',
              }


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_mockreturn(url, params=None, stream=False, timeout=10, **kwargs):
    if stream:
        filename = data_path(DATA_FILES['img'])
        return MockResponse(open(filename, 'rb').read(),
                            content_type='image/fits', **kwargs)
    elif params['RA'] == 163.6136:
        filename = data_path(DATA_FILES['pos_t'])
    elif params['NAIFID'] == 2003226:
        filename = data_path(DATA_FILES['nid_t'])
    elif params['PID'] == 30080:
        filename = data_path(DATA_FILES['pid_t'])
    elif params['REQKEY'] == 21641216:
        filename = data_path(DATA_FILES['rqk_t'])
    else:
        raise ValueError("Query not pre-loaded.")

    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


def test_pos_t(patch_get):
    # Example queries for SHA API help page
    pos_t = sha.query(ra=163.6136, dec=-11.784, size=0.5)


def test_nid_t(patch_get):
    nid_t = sha.query(naifid=2003226)


def test_pid_t(patch_get):
    pid_t = sha.query(pid=30080)


def test_rqk_t(patch_get):
    rqk_t = sha.query(reqkey=21641216)


def test_get_file(patch_get):
    pid_t = sha.query(pid=30080)
    # Get table and fits URLs
    # not used table_url = pid_t['accessUrl'][10]
    image_url = pid_t['accessUrl'][16]
    # Not implemented because running will download file
    # sha.save_file(table_url)
    # sha.save_file(image_url)
    img = sha.get_file(image_url)
