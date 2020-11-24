# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os

import numpy.testing as npt
import pytest
import astropy.units as u

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
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(magpis.Magpis, '_request', post_mockreturn)
    return mp


def post_mockreturn(method, url, data, timeout, **kwargs):
    filename = data_path(DATA_FILES['image'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def test_list_surveys():
    surveys = magpis.core.Magpis.list_surveys()
    assert len(surveys) > 0


def test_get_images_async(patch_post, patch_parse_coordinates):
    response = magpis.core.Magpis.get_images_async(
        commons.GalacticCoordGenerator(10.5, 0.0, unit=(u.deg, u.deg)),
        image_size=2 * u.deg, survey="gps6epoch3", get_query_payload=True)
    npt.assert_approx_equal(response['ImageSize'], 120, significant=3)
    assert response['Survey'] == 'gps6epoch3'
    response = magpis.core.Magpis.get_images_async(
        commons.GalacticCoordGenerator(10.5, 0.0, unit=(u.deg, u.deg)))
    assert response is not None


def test_get_images(patch_post, patch_parse_coordinates):
    image = magpis.core.Magpis.get_images(
        commons.GalacticCoordGenerator(10.5, 0.0, unit=(u.deg, u.deg)))
    assert image is not None


@pytest.mark.xfail
def test_get_images_fail(patch_post, patch_parse_coordinates):
    magpis.core.Magpis.get_images(
        commons.GalacticCoordGenerator(10.5, 0.0, unit=(u.deg, u.deg)),
        survey='Not a survey')
