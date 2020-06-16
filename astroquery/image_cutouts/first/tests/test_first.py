# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import numpy.testing as npt
import pytest
import astropy.units as u

from ....utils import commons
from ....utils.testing_tools import MockResponse
from ... import first

DATA_FILES = {'image': 'image.fits'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_parse_coordinates(request):
    def parse_coordinates_mock_return(c):
        return c
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(first.First, '_request', post_mockreturn)
    return mp


def post_mockreturn(method, url, data, timeout, **kwargs):
    filename = data_path(DATA_FILES['image'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def test_get_images_async(patch_post, patch_parse_coordinates):
    response = first.core.First.get_images_async(
        commons.ICRSCoordGenerator(162.530, 30.677, unit=(u.deg, u.deg)),
        image_size=0.2 * u.deg, get_query_payload=True)
    npt.assert_approx_equal(response['ImageSize'], 12, significant=3)
    response = first.core.First.get_images_async(
        commons.ICRSCoordGenerator(162.530, 30.677, unit=(u.deg, u.deg)))
    assert response is not None


def test_get_images(patch_post, patch_parse_coordinates):
    image = first.core.First.get_images(
        commons.ICRSCoordGenerator(162.530, 30.677, unit=(u.deg, u.deg)))
    assert image is not None
