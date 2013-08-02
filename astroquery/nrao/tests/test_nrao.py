# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os
import requests
from contextlib import contextmanager

import numpy.testing as npt
import astropy.coordinates as coord
import astropy.units as u
import astropy.utils.data as aud
from astropy.tests.helper import pytest

from ...import nrao
from ...utils import commons

COORDS_GAL = coord.GalacticCoordinates(l=49.489, b=-0.37, unit=(u.deg, u.deg)) # ARM 2000
COORDS_ICRS = coord.ICRSCoordinates("12h29m06.69512s +2d03m08.66276s") # 3C 273

DATA_FILES = {'image': 'image.imfits',
              'image_search': 'image_results.html'}

def data_path(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

class MockResponse(object):
    def __init__(self, content):
        self.content = content

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

@pytest.fixture
def patch_parse_coordinates(request):
    def parse_coordinates_mock_return(c):
        return c
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp

def post_mockreturn(url, data, timeout):
    filename = data_path(DATA_FILES['image_search'])
    content = open(filename, 'r').read()
    response = MockResponse(content)
    return response

@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = open(data_path(DATA_FILES["image"]), "rb")
        yield file_obj
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

@pytest.mark.parametrize(('radius'), ['5d0m0s', 5 * u.deg])
def test_parse_radius(radius):
    out = nrao.core._parse_radius(radius)
    npt.assert_approx_equal(out, 300, significant=3)

@pytest.mark.parametrize(('coordinates'), [COORDS_GAL, COORDS_ICRS])
def test_parse_coordinates(coordinates):
    out_str = nrao.core._parse_coordinates(coordinates)
    new_coords = coord.ICRSCoordinates(out_str, unit=(u.hour, u.deg))
    # if all goes well new_coords and coordinates have same ra and dec
    npt.assert_approx_equal(new_coords.icrs.ra.degrees, coordinates.icrs.ra.degrees, significant=3)
    npt.assert_approx_equal(new_coords.icrs.dec.degrees, coordinates.icrs.dec.degrees, significant=3)

def test_extract_image_urls():
    html_in = open(data_path(DATA_FILES['image_search']), 'r').read()
    image_list = nrao.core.Nrao.extract_image_urls(html_in)
    assert len(image_list) == 2

def test_get_images_async(patch_post, patch_parse_coordinates):
    image_list = nrao.core.Nrao.get_images_async(COORDS_ICRS, band='K',
                                                 radius=2 * u.arcsec,
                                                 max_rms=100)
    assert len(image_list) == 2

def test_get_images(patch_post, patch_parse_coordinates, patch_get_readable_fileobj):
    images = nrao.core.Nrao.get_images(COORDS_GAL, radius='5d0m0s', band='all')
    assert images is not None

def test_get_image_list(patch_post, patch_parse_coordinates):
    image_list = nrao.core.Nrao.get_image_list(COORDS_GAL, radius=15 * u.arcsec,
                                               max_rms=500, band="all", get_query_payload=True)
    npt.assert_approx_equal(image_list["nvas_rad"], 0.25, significant=2)
    assert image_list["nvas_bnd"] == ""
    assert image_list["nvas_rms"] == 500
    image_list = nrao.core.Nrao.get_image_list(COORDS_GAL, radius=15 * u.arcsec,
                                               max_rms=500, band="all")
    assert len(image_list) == 2
