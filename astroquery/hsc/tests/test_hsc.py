# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
import os

from astropy.table import Table
from astropy.io import fits
import astropy.coordinates as coord
import astropy.units as u

from ...utils.testing_tools import MockResponse
from ... import hsc
from ...hsc import conf


DATA_FILES = {'POST':
              # TODO: should I use instead directly the string?:
              # https://hsc-release.mtk.nao.ac.jp/datasearch/api/catalog_jobs/
              {conf.api_server + 'submit': 'response_query_region_async.dat',
               conf.api_server + 'status': 'response_query_region_async.dat',
               conf.api_server + 'delete': 'response_query_region_async.dat',
               conf.image_server + 'pdr1/cgi-bin/dasQuery': 'response_get_image.dat'},
              'HEAD': {conf.cutout_server: ''},
              'table': 'response_query_region.fits',
              'image': 'image.fits'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def nonremote_request(self, request_type, url, **kwargs):
    # kwargs are ignored in this case, but they don't have to be
    # (you could use them to define which data file to read)
    if request_type == 'HEAD':
        response = MockResponse(content=None, url=url)
    else:
        with open(data_path(DATA_FILES[request_type][url]), 'rb') as f:
            response = MockResponse(content=f.read(), url=url)

    return response


def nonremote_download_query_result(self, *args):
    with open(data_path(DATA_FILES['table']), 'rb') as f:
        content = f.read()

    return content


def nonremote_get_fits(self, *args):
    return fits.open(data_path(DATA_FILES['image']))


@pytest.fixture
def patch_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(hsc.core.HscClass, '_request',
               nonremote_request)
    return mp


@pytest.fixture
def patch_download_query_result(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(hsc.core.HscClass, '_download_query_result',
               nonremote_download_query_result)
    return mp


@pytest.fixture
def patch_get_fits(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(hsc.core.HscClass, 'get_fits',
               nonremote_get_fits)


def test_query_region_async(patch_request):
    hsc.core.Hsc._authenticated = True
    response = hsc.core.Hsc.query_region_async(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
        radius=6 * u.arcsec)

    assert response is not None


def test_query_region(patch_request, patch_download_query_result):
    hsc.core.Hsc._authenticated = True
    table = hsc.core.Hsc.query_region(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
        radius=6 * u.arcsec)

    assert isinstance(table, Table)
    assert len(table) > 0


def test_get_images_cutout(patch_request, patch_get_fits):
    image = hsc.core.Hsc.get_images(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

    assert len(image) == 1
    assert isinstance(image[0], fits.HDUList)


def test_get_images_async_cutout(patch_request):
    url_list = hsc.core.Hsc.get_images_async(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

    assert len(url_list) == 1


def test_get_image_list_cutout(patch_request):
    url_list = hsc.core.Hsc.get_image_list(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'))

    assert len(url_list) == 1


def test_get_images_coadd(patch_request, patch_get_fits):
    image = hsc.core.Hsc.get_images(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
        radius=6 * u.arcsec)

    assert len(image) == 1
    assert isinstance(image[0], fits.HDUList)


def test_get_images_async_coadd(patch_request):
    url_list = hsc.core.Hsc.get_images_async(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
        radius=6 * u.arcsec)

    assert len(url_list) == 1


def test_get_image_list_coadd(patch_request):
    url_list = hsc.core.Hsc.get_image_list(
        coord.SkyCoord(ra=34.0, dec=-5.0, unit='deg', frame='icrs'),
        radius=6 * u.arcsec)

    assert len(url_list) == 1


def test_list_surveys():
    surveys = hsc.core.Hsc.list_surveys()
    assert isinstance(surveys, list)


def test_list_releases():
    releases = hsc.core.Hsc.list_releases()
    assert isinstance(releases, list)
