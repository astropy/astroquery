# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
import os
import socket
import numpy as np
from numpy.testing import assert_allclose

import six
from astropy.io import fits
from astropy.table import Column, Table
import pytest

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
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(sdss.SDSS, '_request', get_mockreturn)
    return mp


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(sdss.SDSS, '_request', post_mockreturn)
    return mp


@pytest.fixture
def patch_get_slow(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(sdss.SDSS, '_request', get_mockreturn_slow)
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

    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj_slow(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        e = six.moves.urllib_error.URLError('timeout')
        e.reason = socket.timeout()
        raise e
        yield True
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=True, **kwargs):
    if 'SpecObjAll' in params['cmd']:
        filename = data_path(DATA_FILES['spectra_id'])
    else:
        filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def get_mockreturn_slow(method, url, params=None, timeout=0, **kwargs):
    raise TimeoutError


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
coords_column = Column(coords_list, name='coordinates')

# List of all data releases.
dr_list = list(range(1, sdss.conf.default_release + 1))


# We are not testing queries for DR11 because it is not easily available to
# query: "DR11 data are distributed primarily to provide reproducibility of
# published results based on the DR11 data set. As such, not all data-access
# interfaces are supported for DR11."
def url_tester(data_release):
    if data_release < 10:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/x_sql.asp'
    if data_release == 10:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/x_sql.aspx'
    if data_release == 11:
        return
    if data_release >= 12:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/x_results.aspx'
    assert sdss.SDSS._last_url == baseurl.format(data_release)


def url_tester_crossid(data_release):
    if data_release < 11:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/crossid/x_crossid.aspx'
    if data_release == 11:
        return
    if data_release >= 12:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/search/X_Results.aspx'
    assert sdss.SDSS._last_url == baseurl.format(data_release)


def compare_xid_data(xid, data):
    for col in xid.colnames:
        if xid[col].dtype.type is np.string_:
            assert xid[col] == data[col]
        else:
            assert_allclose(xid[col], data[col])


def image_tester(images, filetype):
    """Test that an image/spectrum is our fake data."""
    assert type(images) == list
    data = fits.open(data_path(DATA_FILES[filetype]))
    assert images[0][0].header == data[0].header
    assert images[0][0].data == data[0].data


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum(patch_get, patch_get_readable_fileobj, dr,
                       coords=coords):
    xid = sdss.SDSS.query_region(coords, data_release=dr, spectro=True)
    url_tester(dr)
    sp = sdss.SDSS.get_spectra(matches=xid, data_release=dr)
    image_tester(sp, 'spectra')
    url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum_mjd(patch_get, patch_get_readable_fileobj, dr):
    sp = sdss.SDSS.get_spectra(plate=2345, fiberID=572, data_release=dr)
    image_tester(sp, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum_coords(patch_get, patch_get_readable_fileobj, dr,
                              coords=coords):
    sp = sdss.SDSS.get_spectra(coords, data_release=dr)
    image_tester(sp, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
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
    xid = sdss.SDSS.query_sql(query, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_image_from_query_region(patch_get, patch_get_readable_fileobj,
                                      dr, coords=coords):
    xid = sdss.SDSS.query_region(coords, data_release=dr)
    # TODO test what img is
    img = sdss.SDSS.get_images(matches=xid)
    image_tester(img, 'images')
    url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_image_run(patch_get, patch_get_readable_fileobj, dr):
    img = sdss.SDSS.get_images(run=1904, camcol=3, field=164, data_release=dr)
    image_tester(img, 'images')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_image_coord(patch_get, patch_get_readable_fileobj, dr,
                          coord=coords):
    img = sdss.SDSS.get_images(coords, data_release=dr)
    image_tester(img, 'images')


def test_sdss_template(patch_get, patch_get_readable_fileobj):
    template = sdss.SDSS.get_spectral_template('qso')
    image_tester(template, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_specobj(patch_get, dr):
    xid = sdss.SDSS.query_specobj(plate=2340, data_release=dr)
    data = Table.read(data_path(DATA_FILES['spectra_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['specobjid'] = data['specobjid'].astype(np.int64)
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_photoobj(patch_get, dr):
    xid = sdss.SDSS.query_photoobj(
        run=1904, camcol=3, field=164, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_list_coordinates(patch_get, dr):
    xid = sdss.SDSS.query_region(coords_list, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates(patch_get, dr):
    xid = sdss.SDSS.query_region(coords_column, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester(dr)


def test_query_timeout(patch_get_slow, coord=coords):
    with pytest.raises(TimeoutError):
        sdss.SDSS.query_region(coords, timeout=1)


def test_spectra_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.SDSS.get_spectra(plate=2345, fiberID=572)


def test_images_timeout(patch_get, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.SDSS.get_images(run=1904, camcol=3, field=164)


@pytest.mark.parametrize("dr", dr_list)
def test_query_crossid(patch_post, dr):
    xid = sdss.SDSS.query_crossid(coords_column, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester_crossid(dr)


# ===========
# Payload tests

@pytest.mark.parametrize("dr", dr_list)
def test_list_coordinates_payload(patch_get, dr):
    expect = ("SELECT DISTINCT "
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field "
              "FROM PhotoObjAll AS p   WHERE "
              "((p.ra between 2.02291 and 2.02402) and "
              "(p.dec between 14.8393 and 14.8404)) or "
              "((p.ra between 2.02291 and 2.02402) and "
              "(p.dec between 14.8393 and 14.8404))")
    query_payload = sdss.SDSS.query_region(coords_list,
                                           get_query_payload=True,
                                           data_release=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_payload(patch_get, dr):
    expect = ("SELECT DISTINCT "
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field "
              "FROM PhotoObjAll AS p   WHERE "
              "((p.ra between 2.02291 and 2.02402) and "
              "(p.dec between 14.8393 and 14.8404)) or "
              "((p.ra between 2.02291 and 2.02402) and "
              "(p.dec between 14.8393 and 14.8404))")
    query_payload = sdss.SDSS.query_region(coords_column,
                                           get_query_payload=True,
                                           data_release=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'


def test_field_help_region(patch_get):
    valid_field = sdss.SDSS.query_region(coords, field_help=True)
    assert isinstance(valid_field, dict)
    assert 'photoobj_all' in valid_field

    existing_p_field = sdss.SDSS.query_region(coords,
                                              field_help='psfMag_r')

    existing_s_field = sdss.SDSS.query_region(coords,
                                              field_help='spectroSynFlux_r')

    non_existing_field = sdss.SDSS.query_region(coords,
                                                field_help='nonexist')

    assert existing_p_field is None
    assert existing_s_field is None

    assert len(non_existing_field) == 2
    assert set(non_existing_field.keys()) == set(('photoobj_all', 'specobj_all'))
