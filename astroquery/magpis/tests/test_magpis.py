# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os
import requests

import numpy.testing as npt
from astropy.tests.helper import pytest
import astropy.units as u
import astropy.coordinates as coord

from ...utils import commons
from ...utils.testing_tools import MockResponse
from ... import magpis

DATA_FILES = {'image': 'image.fits'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_parse_coordinates(request):
    def parse_coordinates_mock_return(c):
        return c
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp


@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp


def post_mockreturn(url, data, timeout, **kwargs):
    filename = data_path(DATA_FILES['image'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def test_list_surveys():
    surveys = magpis.core.Magpis.list_surveys()
    assert len(surveys) > 0


def test_get_images_async(patch_post, patch_parse_coordinates):
    response = magpis.core.Magpis.get_images_async(coord.GalacticCoordinates(10.5, 0.0, unit=(u.deg, u.deg)),
                                                   image_size=2 * u.deg, survey="gps6",
                                                   get_query_payload=True)
    npt.assert_approx_equal(response['ImageSize'], 120, significant=3)
    assert response['Survey'] == 'gps6'
    response = magpis.core.Magpis.get_images_async(coord.GalacticCoordinates(10.5, 0.0, unit=(u.deg, u.deg)))
    assert response is not None


def test_get_images(patch_post, patch_parse_coordinates):
    image = magpis.core.Magpis.get_images(coord.GalacticCoordinates(10.5, 0.0, unit=(u.deg, u.deg)))
    assert image is not None

