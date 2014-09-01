# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from astropy.tests.helper import pytest
from ... import lamda
from ...utils.testing_tools import MockResponse

DATA_FILES = {'co': 'co.txt'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_mockreturn(url, params=None, timeout=10, **kwargs):
    filename = data_path(DATA_FILES['co'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


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

def test_parser():
    collrates,radtransitions,enlevels = lamda.core.parse_lamda_datafile(data_path('co.txt'))

    assert set(collrates.keys()) == set(['PH2', 'OH2'])
    assert len(enlevels) == 41
    assert len(radtransitions) == 40
