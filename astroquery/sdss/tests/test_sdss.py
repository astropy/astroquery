# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
import requests
import os
import socket
from astropy.extern.six.moves.urllib_error import URLError
from astropy.tests.helper import pytest
from ... import sdss
from ...utils.testing_tools import MockResponse
from ...exceptions import TimeoutError
from ...utils import commons

# actual spectra/data are a bit heavy to include in astroquery, so we don't try
# to deal with them.  Would be nice to find a few very small examples

DATA_FILES = {'spectra_id': 'xid_sp.txt',
              'images_id': 'xid_im.txt',
              'spectra': 'emptyfile.fits',
              'images': 'emptyfile.fits'}


@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_slow(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn_slow)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectra'])  # TODO: add images option
        encoding = kwargs.get('encoding', None)
        if encoding == 'binary':
            yield open(file_obj, 'rb')
        else:
            yield open(file_obj, 'r', encoding=encoding)

    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj_slow(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        e = URLError('timeout')
        e.reason = socket.timeout()
        raise e
        yield True
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp


def get_mockreturn(url, params=None, timeout=10, **kwargs):
    if 'SpecObjAll' in params['cmd']:
        filename = data_path(DATA_FILES['spectra_id'])
    else:
        filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def get_mockreturn_slow(url, params=None, timeout=10, **kwargs):
    raise requests.exceptions.Timeout('timeout')


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# Test Case: A Seyfert 1 galaxy
coords = commons.ICRSCoordGenerator('0h8m05.63s +14d50m23.3s')


def test_sdss_spectrum(patch_get, patch_get_readable_fileobj, coords=coords):
    xid = sdss.core.SDSS.query_region(coords, spectro=True)
    sp = sdss.core.SDSS.get_spectra(matches=xid)


def test_sdss_spectrum_mjd(patch_get, patch_get_readable_fileobj):
    sp = sdss.core.SDSS.get_spectra(plate=2345, fiberID=572)


def test_sdss_spectrum_coords(patch_get, patch_get_readable_fileobj,
                              coords=coords):
    sp = sdss.core.SDSS.get_spectra(coords)


def test_sdss_image(patch_get, patch_get_readable_fileobj, coords=coords):
    xid = sdss.core.SDSS.query_region(coords)
    img = sdss.core.SDSS.get_images(matches=xid)


def test_sdss_image_run(patch_get, patch_get_readable_fileobj):
    img = sdss.core.SDSS.get_images(run=1904, camcol=3, field=164)


def test_sdss_image_coord(patch_get, patch_get_readable_fileobj, coord=coords):
    img = sdss.core.SDSS.get_images(coords)


def test_sdss_template(patch_get, patch_get_readable_fileobj):
    template = sdss.core.SDSS.get_spectral_template('qso')


def test_sdss_specobj(patch_get):
    xid = sdss.core.SDSS.query_specobj(plate=2340)


def test_sdss_photoobj(patch_get):
    xid = sdss.core.SDSS.query_photoobj(run=1904, camcol=3, field=164)


def test_query_timeout(patch_get_slow, coord=coords):
    with pytest.raises(TimeoutError):
        xid = sdss.core.SDSS.query_region(coords, timeout=1)


def test_spectra_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sp = sdss.core.SDSS.get_spectra(plate=2345, fiberID=572)


def test_images_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        img = sdss.core.SDSS.get_images(run=1904, camcol=3, field=164)
