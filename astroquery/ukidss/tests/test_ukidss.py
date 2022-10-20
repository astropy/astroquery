# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from contextlib import contextmanager

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from ... import ukidss
from ...utils import commons
from astroquery.utils.mocks import MockResponse
from ...exceptions import InvalidQueryError

DATA_FILES = {"vo_results": "vo_results.html",
              "image_results": "image_results.html",
              "image": "image.fits",
              "votable": "votable.xml",
              "error": "error.html"
              }


galactic_skycoord = SkyCoord(l=10.625 * u.deg, b=-0.38 * u.deg, frame="galactic")
icrs_skycoord = SkyCoord(ra=83.633083 * u.deg, dec=22.0145 * u.deg, frame="icrs")


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests, 'get', get_mockreturn)
    mp.setattr(ukidss.Ukidss, '_request', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        is_binary = kwargs.get('encoding', None) == 'binary'
        mode = 'rb' if is_binary else 'r'
        if "fits" in filename:
            with open(data_path(DATA_FILES["image"]), mode) as file_obj:
                yield file_obj
        else:
            with open(data_path(DATA_FILES["votable"]), mode) as file_obj:
                yield file_obj

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


@pytest.fixture
def patch_parse_coordinates(request):
    def parse_coordinates_mock_return(c):
        return c

    # TODO: determine if this patch is ever used

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'parse_coordinates', parse_coordinates_mock_return)
    return mp


def get_mockreturn(method='GET', url='default_url',
                   params=None, timeout=10, **kwargs):
    if "Image" in url:
        filename = DATA_FILES["image_results"]
        url = "Image_URL"
    elif "SQL" in url:
        filename = DATA_FILES["vo_results"]
        url = "SQL_URL"
    elif "error" in url:
        filename = DATA_FILES["error"]
        url = "error.html"
    else:
        raise ValueError("Mismatch: no test made for specified URL")
    with open(data_path(filename), "rb") as infile:
        content = infile.read()
    return MockResponse(content=content, url=url, **kwargs)


def test_get_images(patch_get, patch_get_readable_fileobj):
    image = ukidss.core.Ukidss.get_images(
        icrs_skycoord, frame_type="interleave", programme_id="GCS", waveband="K",
        radius=20 * u.arcmin)
    assert image is not None


def test_get_images_async_1():
    payload = ukidss.core.Ukidss.get_images_async(
        icrs_skycoord, radius=20 * u.arcmin, get_query_payload=True, programme_id="GPS")

    assert 'xsize' not in payload
    assert 'ysize' not in payload

    payload = ukidss.core.Ukidss.get_images_async(
        icrs_skycoord, get_query_payload=True, programme_id="GPS")
    assert payload['xsize'] == payload['ysize']
    assert payload['xsize'] == 1

    get_mockreturn(url=ukidss.core.Ukidss.ARCHIVE_URL, params=payload)


def test_get_images_async_2(patch_get, patch_get_readable_fileobj):

    image_urls = ukidss.core.Ukidss.get_images_async(icrs_skycoord, programme_id="GPS")

    assert len(image_urls) == 1


def test_get_image_list(patch_get, patch_get_readable_fileobj):
    urls = ukidss.core.Ukidss.get_image_list(
        icrs_skycoord, frame_type="all", waveband="all", programme_id="GPS")
    print(urls)
    assert len(urls) == 1


def test_extract_urls():
    with open(data_path(DATA_FILES["image_results"]), 'r') as infile:
        html_in = infile.read()
    urls = ukidss.core.Ukidss.extract_urls(html_in)
    assert len(urls) == 1


def test_query_region(patch_get, patch_get_readable_fileobj):
    table = ukidss.core.Ukidss.query_region(
        galactic_skycoord, radius=6 * u.arcsec, programme_id="GPS")
    assert isinstance(table, Table)
    assert len(table) > 0


def test_query_region_async(patch_get):
    response = ukidss.core.Ukidss.query_region_async(
        galactic_skycoord, radius=6 * u.arcsec, get_query_payload=True,
        programme_id='GPS')

    assert response['radius'] == 0.1
    response = ukidss.core.Ukidss.query_region_async(
        galactic_skycoord, radius=6 * u.arcsec, programme_id="GPS")
    assert response is not None


def test_check_page_err(patch_get):
    with pytest.raises(InvalidQueryError):
        ukidss.core.Ukidss._check_page("error", "dummy")
