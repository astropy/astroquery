# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
import requests
import os
import socket

from astropy.extern import six
from astropy.tests.helper import pytest
import astropy
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
    # mp.setattr(requests, 'get', get_mockreturn)
    mp.setattr(sdss.core.SDSS, '_request', get_mockreturn)
    return mp

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(sdss.core.SDSS, '_request', post_mockreturn)
    return mp

@pytest.fixture
def patch_get_slow(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(sdss.core.SDSS, '_request', get_mockreturn_slow)
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
        e = six.moves.urllib_error.URLError('timeout')
        e.reason = socket.timeout()
        raise e
        yield True
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

def get_mockreturn(method, url, params=None, timeout=0, **kwargs):
    if 'SpecObjAll' in params['cmd']:
        filename = data_path(DATA_FILES['spectra_id'])
    else:
        filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)

def get_mockreturn_slow(method, url, params=None, timeout=0, **kwargs):
    raise TimeoutError
    # raise requests.exceptions.Timeout('timeout')

def post_mockreturn(method, url, params=None, timeout=0, **kwargs):
    filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'rb').read()
    return MockResponse(content)

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# Test Case: A Seyfert 1 galaxy
coords = commons.ICRSCoordGenerator('0h8m05.63s +14d50m23.3s')

# Test Case: list of coordinates
coords_list = [coords, coords]

# Test Case: Column of coordinates
coords_column = astropy.table.Column(coords_list, name='coordinates')

# We are not testing queries for DR11 because it is not easily available to query:
# "DR11 data are distributed primarily to provide reproducibility of published results based
# on the DR11 data set. As such, not all data-access interfaces are supported for DR11."
def _url_tester_search(dr):
    if dr < 11:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/sql.asp'
    if dr >= 12:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/x_sql.aspx'
    assert sdss.core.SDSS.url == baseurl.format(dr)

def _url_tester_crossid(dr):
    baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/crossid/x_crossid.aspx'
    assert sdss.core.SDSS.url == baseurl.format(dr)


def _compare_xid_data(xid ,data):
    if six.PY3:
        pytest.xfail('xid/data comparison fails in PY3 because the instrument column is bytes in xid and str in data')
    else:
        return all(xid == data)

def _image_tester(images,filetype):
    """Test that an image/spectrum is our fake data."""
    assert type(images) == list
    data = astropy.io.fits.open(data_path(DATA_FILES[filetype]))
    assert images[0][0].header == data[0].header
    assert images[0][0].data == data[0].data


@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_spectrum(patch_get, patch_get_readable_fileobj, dr, coords=coords):
    xid = sdss.core.SDSS.query_region(coords, spectro=True, dr=dr)
    sp = sdss.core.SDSS.get_spectra(matches=xid, dr=dr)
    _image_tester(sp,'spectra')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_spectrum_mjd(patch_get, patch_get_readable_fileobj, dr):
    sp = sdss.core.SDSS.get_spectra(plate=2345, fiberID=572, dr=dr)
    _image_tester(sp,'spectra')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_spectrum_coords(patch_get, patch_get_readable_fileobj, dr,
                              coords=coords):
    sp = sdss.core.SDSS.get_spectra(coords, dr=dr)
    _image_tester(sp,'spectra')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_sql(patch_get, patch_get_readable_fileobj, dr):
    query = """
            select top 10
              z, ra, dec, bestObjID
            from
              specObj
            where
              class = 'galaxy'
              and z > 0.3
              and zWarning = 0
            """
    xid = sdss.core.SDSS.query_sql(query, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['images_id']),format='ascii.csv',comment='#')
    assert _compare_xid_data(xid, data)
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_image_from_query_region(patch_get, patch_get_readable_fileobj, dr, coords=coords):
    xid = sdss.core.SDSS.query_region(coords, dr=dr)
    img = sdss.core.SDSS.get_images(matches=xid)
    _image_tester(img,'images')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_image_run(patch_get, patch_get_readable_fileobj, dr):
    img = sdss.core.SDSS.get_images(run=1904, camcol=3, field=164, dr=dr)
    _image_tester(img,'images')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_image_coord(patch_get, patch_get_readable_fileobj, dr, coord=coords):
    img = sdss.core.SDSS.get_images(coords, dr=dr)
    _image_tester(img,'images')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_template(patch_get, patch_get_readable_fileobj, dr):
    template = sdss.core.SDSS.get_spectral_template('qso', dr=dr)
    _image_tester(template,'images')
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_specobj(patch_get, dr):
    xid = sdss.core.SDSS.query_specobj(plate=2340, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['spectra_id']),format='ascii.csv',comment='#')
    assert _compare_xid_data(xid, data)
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_sdss_photoobj(patch_get, dr):
    xid = sdss.core.SDSS.query_photoobj(run=1904, camcol=3, field=164, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['images_id']),format='ascii.csv',comment='#')
    assert _compare_xid_data(xid, data)
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_list_coordinates(patch_get, dr):
    xid = sdss.core.SDSS.query_region(coords_list, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['images_id']),format='ascii.csv',comment='#')
    assert _compare_xid_data(xid, data)
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_column_coordinates(patch_get, dr):
    xid = sdss.core.SDSS.query_region(coords_column, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['images_id']),format='ascii.csv',comment='#')
    assert _compare_xid_data(xid, data)
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_query_crossid(patch_post, dr):
    xid = sdss.core.SDSS.query_crossid(coords_column, dr=dr)
    data = astropy.table.Table.read(data_path(DATA_FILES['images_id']),format='ascii.csv',comment='#')
    assert all(xid == data)
    _url_tester_crossid(dr)


# ===========
# Payload tests

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_list_coordinates_payload(dr):
    expect = "SELECT DISTINCT p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field FROM PhotoObjAll AS p   WHERE ((p.ra between 2.02291 and 2.02402) and (p.dec between 14.8393 and 14.8404)) or ((p.ra between 2.02291 and 2.02402) and (p.dec between 14.8393 and 14.8404))"
    query_payload = sdss.core.SDSS.query_region(coords_list,get_query_payload=True,dr=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'
    _url_tester_search(dr)

@pytest.mark.parametrize("dr", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12])
def test_column_coordinates_payload(dr):
    expect = "SELECT DISTINCT p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field FROM PhotoObjAll AS p   WHERE ((p.ra between 2.02291 and 2.02402) and (p.dec between 14.8393 and 14.8404)) or ((p.ra between 2.02291 and 2.02402) and (p.dec between 14.8393 and 14.8404))"
    query_payload = sdss.core.SDSS.query_region(coords_column,get_query_payload=True,dr=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'
    _url_tester_search(dr)


# ===========
# Timeout tests: these will fail if the query doesn't raise an exception.

def test_query_timeout(patch_get_slow, coord=coords):
    with pytest.raises(TimeoutError):
        sdss.core.SDSS.query_region(coords)

def test_spectra_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.core.SDSS.get_spectra(plate=2345, fiberID=572)

def test_images_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.core.SDSS.get_images(run=1904, camcol=3, field=164)


def test_field_help_region(patch_get):
    valid_field = sdss.core.SDSS.query_region(coords, field_help=True)
    assert isinstance(valid_field, dict)
    assert 'photoobj_all' in valid_field

    existing_p_field = sdss.core.SDSS.query_region(coords,
                                                   field_help='psfmag_r')

    existing_p_s_field = sdss.core.SDSS.query_region(coords,
                                                     field_help='psfmag_r')

    non_existing_field = sdss.core.SDSS.query_region(coords,
                                                     field_help='nonexist')
