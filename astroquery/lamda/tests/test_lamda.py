# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import lamda
import requests
from astropy.tests.helper import pytest
import os

DATA_FILES = {'co':'co.txt'}

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class MockResponse(object):

    def __init__(self, content):
        self.content = content

    def iter_lines(self):
        c = self.content.split("\n")
        for l in c:
            yield l

def get_mockreturn(url, params=None, timeout=10):
    filename = data_path(DATA_FILES['co'])
    content = open(filename, 'r').read()
    return MockResponse(content)

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


def test_print_query():
    lamda.print_mols()


def test_query_levels(patch_get):
    lamda.query(mol='co', query_type='erg_levels')


def test_query_radtrans(patch_get):
    lamda.query(mol='co', query_type='rad_trans')


def test_query_collrates(patch_get):
    lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)
