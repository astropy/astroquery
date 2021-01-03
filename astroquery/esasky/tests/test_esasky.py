# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest

import os

from ...utils.testing_tools import MockResponse
from ...esasky import ESASky


DATA_FILES = {'GET':
              {'http://sky.esa.int/esasky-tap/observations':
               'observations.txt',
               'http://sky.esa.int/esasky-tap/catalogs':
               'catalogs.txt'
               },
              }


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def nonremote_request(request_type, url, **kwargs):
    with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


@pytest.fixture(autouse=True)
def esasky_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(ESASky, '_request', nonremote_request)
    return mp


def test_esasky_query_region_maps_invalid_position():
    with pytest.raises(ValueError):
        ESASky.query_region_maps(51, "5 arcmin")


def test_esasky_query_region_maps_invalid_radius():
    with pytest.raises(ValueError):
        ESASky.query_region_maps("M51", 5)


def test_esasky_query_region_maps_invalid_mission():
    with pytest.raises(ValueError):
        ESASky.query_region_maps("M51", "5 arcmin", missions=True)


def test_list_catalogs():
    result = ESASky.list_catalogs()
    assert len(result) == 13
