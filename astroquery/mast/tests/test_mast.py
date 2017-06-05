# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os
import re
import requests
import numpy as np

from astropy.table import Table
from astropy.tests.helper import pytest
import astropy.coordinates as coord

from ...utils.testing_tools import MockResponse

from ... import mast


DATA_FILES = {'Mast.Caom.Cone': 'caom.json',
              'Mast.Name.Lookup': 'resolver.json'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(mast.Mast,'_request', post_mockreturn)
    mp.setattr(mast.Observations,'_request', post_mockreturn)
    return mp


def post_mockreturn(method="POST", url=None, data=None, timeout=10, **kwargs):
    service  = re.search("service%22%3A%20%22([\w\.]*)%22", data).group(1)
    filename = data_path(DATA_FILES[service])
    content = open(filename, 'rb').read()
    
    # returning as list because this is what the mast _request function does
    return [MockResponse(content)] 



# Mast MastClass tests
def test_mast_service_request_async(patch_post):
    service = 'Mast.Name.Lookup'
    params ={'input':"M103",
             'format':'json'}       
    responses = mast.Mast.service_request_async(service, params)
    print(responses[0].content)
    output = responses[0].json()
        
    assert isinstance(responses, list)
    assert output


def test_mast_service_request(patch_post):
    service = 'Mast.Caom.Cone'
    params ={'ra':23.34086,
             'dec':60.658,
             'radius':0.2}      
    result = mast.Mast.service_request(service, params)
        
    assert isinstance(result, Table)
   

# ObservationsClass tests

regionCoords = coord.SkyCoord(23.34086, 60.658, unit=('deg', 'deg'))

def test_observations_query_region_async(patch_post):
    responses = mast.Observations.query_region_async(regionCoords,radius="0.2 deg")
    assert isinstance(responses, list)

def test_observations_query_region(patch_post):
    result = mast.Observations.query_region(regionCoords,radius="0.2 deg")
    assert isinstance(result, Table)

def test_observations_query_object_async(patch_post):
    responses = mast.Observations.query_object_async("M103",radius=".02 deg")
    assert isinstance(responses, list)

def test_observations_query_object(patch_post):
    result = mast.Observations.query_object("M103",radius=".02 deg")
    assert isinstance(result, Table)
