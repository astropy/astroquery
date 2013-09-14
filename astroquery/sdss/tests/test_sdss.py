# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sdss
from ...utils.testing_tools import MockResponse
from astropy import coordinates
from astropy.tests.helper import pytest
from contextlib import contextmanager
import astropy.utils.data as aud
import requests
import io
import os

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
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectra']) # TODO: add images option
        yield file_obj
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

def get_mockreturn(url, params=None, timeout=10, **kwargs):
    if 'SpecObjAll' in params['cmd']:
        filename = data_path(DATA_FILES['spectra_id'])
    else:
        filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'r').read()
    return MockResponse(content, **kwargs)

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')

def test_sdss_spectrum(patch_get, patch_get_readable_fileobj, coords=coords):
    xid = sdss.core.SDSS.query_region(coords, spectro=True)
    sp = sdss.core.SDSS.get_spectra(xid)
    
def test_sdss_image(patch_get, patch_get_readable_fileobj, coords=coords):
    xid = sdss.core.SDSS.query_region(coords)
    img = sdss.core.SDSS.get_images(xid)
    
def test_sdss_template(patch_get, patch_get_readable_fileobj):
    template = sdss.core.SDSS.get_spectral_template('qso')

