# Licensed under a 3-clause BSD style license - see LICENSE.rst
from contextlib import contextmanager
from urllib.error import URLError
import os
import socket
import numpy as np
from numpy.testing import assert_allclose

import astropy.units as u
from astropy.io import fits
from astropy.coordinates import Angle
from astropy.table import Column, Table
import pytest

from ... import sdss
from astroquery.utils.mocks import MockResponse
from ...exceptions import TimeoutError
from ...utils import commons

# actual spectra/data are a bit heavy to include in astroquery, so we don't try
# to deal with them.  Would be nice to find a few very small examples

DATA_FILES = {'spectra_id': 'xid_sp.txt',
              'images_id': 'xid_im.txt',
              'spectra': 'emptyfile.fits',
              'images': 'emptyfile.fits'}


@pytest.fixture
def patch_request(request):
    def mockreturn(method, url, **kwargs):
        if 'data' in kwargs:
            cmd = kwargs['data']['uquery']
        else:
            cmd = kwargs['params']['cmd']
        if 'SpecObjAll' in cmd:
            filename = data_path(DATA_FILES['spectra_id'])
        else:
            filename = data_path(DATA_FILES['images_id'])

        with open(filename, 'rb') as infile:
            content = infile.read()

        return MockResponse(content, url)

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(sdss.SDSS, '_request', mockreturn)
    return mp


@pytest.fixture
def patch_request_slow(request):
    def mockreturn_slow(method, url, **kwargs):
        raise TimeoutError

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(sdss.SDSS, '_request', mockreturn_slow)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectra'])  # TODO: add images option
        encoding = kwargs.get('encoding', None)
        if encoding == 'binary':
            with open(file_obj, 'rb') as infile:
                yield infile
        else:
            with open(file_obj, 'r', encoding=encoding) as infile:
                yield infile

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj_slow(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        error = URLError('timeout')
        error.reason = socket.timeout()
        raise error
        yield True

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


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
dr_list = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17)


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
    if data_release < 10:
        baseurl = 'http://skyserver.sdss.org/dr{}/en/tools/crossid/x_crossid.asp'
    if data_release == 10:
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
    with fits.open(data_path(DATA_FILES[filetype])) as data:
        assert images[0][0].header == data[0].header
        assert images[0][0].data == data[0].data


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum(patch_request, patch_get_readable_fileobj, dr,
                       coords=coords):
    xid = sdss.SDSS.query_region(coords, data_release=dr, spectro=True)
    url_tester_crossid(dr)
    sp = sdss.SDSS.get_spectra(matches=xid, data_release=dr)
    image_tester(sp, 'spectra')
    # url_tester(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum_mjd(patch_request, patch_get_readable_fileobj, dr):
    sp = sdss.SDSS.get_spectra(plate=2345, fiberID=572, data_release=dr)
    image_tester(sp, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_spectrum_coords(patch_request, patch_get_readable_fileobj, dr,
                              coords=coords):
    sp = sdss.SDSS.get_spectra(coords, data_release=dr)
    image_tester(sp, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_sql(patch_request, patch_get_readable_fileobj, dr):
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
def test_sdss_image_from_query_region(patch_request, patch_get_readable_fileobj,
                                      dr, coords=coords):
    xid = sdss.SDSS.query_region(coords, data_release=dr)
    url_tester_crossid(dr)
    # TODO test what img is
    img = sdss.SDSS.get_images(matches=xid)
    image_tester(img, 'images')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_image_run(patch_request, patch_get_readable_fileobj, dr):
    img = sdss.SDSS.get_images(run=1904, camcol=3, field=164, data_release=dr)
    image_tester(img, 'images')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_image_coord(patch_request, patch_get_readable_fileobj, dr,
                          coord=coords):
    img = sdss.SDSS.get_images(coords, data_release=dr)
    image_tester(img, 'images')


def test_sdss_template(patch_request, patch_get_readable_fileobj):
    template = sdss.SDSS.get_spectral_template('qso')
    image_tester(template, 'spectra')


@pytest.mark.parametrize("dr", dr_list)
def test_sdss_specobj(patch_request, dr):
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
def test_sdss_photoobj(patch_request, dr):
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
def test_list_coordinates(patch_request, dr):
    xid = sdss.SDSS.query_region(coords_list, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester_crossid(dr)


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates(patch_request, dr):
    xid = sdss.SDSS.query_region(coords_column, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester_crossid(dr)


def test_query_timeout(patch_request_slow, coord=coords):
    with pytest.raises(TimeoutError):
        sdss.SDSS.query_region(coords, timeout=1)


def test_spectra_timeout(patch_request, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.SDSS.get_spectra(plate=2345, fiberID=572)


def test_images_timeout(patch_request, patch_get_readable_fileobj_slow):
    with pytest.raises(TimeoutError):
        sdss.SDSS.get_images(run=1904, camcol=3, field=164)


@pytest.mark.parametrize("dr", dr_list)
def test_query_crossid(patch_request, dr):
    xid = sdss.SDSS.query_crossid(coords_column, data_release=dr)
    data = Table.read(data_path(DATA_FILES['images_id']),
                      format='ascii.csv', comment='#')
    # The following line is needed for systems where the default integer type
    # is int32, the column will then be interpreted as string which makes the
    # test fail.
    data['objid'] = data['objid'].astype(np.int64)
    compare_xid_data(xid, data)
    url_tester_crossid(dr)


def test_query_crossid_large_radius(patch_request):
    """Test raising an exception if too large a search radius.
    """
    with pytest.raises(ValueError, match="radius must be less than"):
        xid = sdss.SDSS.query_crossid(coords_column, radius=5.0 * u.arcmin)


def test_query_crossid_invalid_radius(patch_request):
    """Test raising an exception if search radius can't be parsed.
    """
    with pytest.raises(TypeError, match="radius should be either Quantity"):
        xid = sdss.SDSS.query_crossid(coords_column, radius='2.0 * u.arcmin')


def test_query_crossid_invalid_names(patch_request):
    """Test raising an exception if user-supplied object names are invalid.
    """
    with pytest.raises(ValueError, match="Number of coordinates and obj_names"):
        xid = sdss.SDSS.query_crossid(coords_column, obj_names=['A1'])


def test_query_crossid_parse_angle_value(patch_request):
    """Test parsing angles with astropy.coordinates.Angle.
    """
    query_payload, files = sdss.SDSS.query_crossid(coords_column,
                                                   radius='3 arcsec',
                                                   get_query_payload=True)

    assert query_payload['radius'] == 0.05


def test_query_crossid_explicit_angle_value(patch_request):
    """Test parsing angles with astropy.coordinates.Angle.
    """
    query_payload, files = sdss.SDSS.query_crossid(coords_column,
                                                   radius=Angle('3 arcsec'),
                                                   get_query_payload=True)

    assert query_payload['radius'] == 0.05


# ===========
# Payload tests

@pytest.mark.parametrize("dr", dr_list)
def test_list_coordinates_region_payload(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload = sdss.SDSS.query_region(coords_list,
                                           get_query_payload=True,
                                           data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'allObj'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_region_payload(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload = sdss.SDSS.query_region(coords_column,
                                           get_query_payload=True,
                                           data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'allObj'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_region_spectro_payload(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field, "
              "s.z, s.plate, s.mjd, s.fiberID, s.specobjid, s.run2d "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "JOIN SpecObjAll AS s ON p.objID = s.bestObjID "
              "ORDER BY x.up_id")
    query_payload = sdss.SDSS.query_region(coords_column, spectro=True,
                                           get_query_payload=True,
                                           data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'allObj'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_region_payload_custom_fields(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.r, p.psfMag_r "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload = sdss.SDSS.query_region(coords_column,
                                           get_query_payload=True,
                                           fields=['r', 'psfMag_r'],
                                           data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'allObj'


@pytest.mark.parametrize("dr", dr_list)
def test_list_coordinates_cross_id_payload(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.ra, p.dec, p.psfMag_u, p.psfMagerr_u, p.psfMag_g, p.psfMagerr_g, "
              "p.psfMag_r, p.psfMagerr_r, p.psfMag_i, p.psfMagerr_i, p.psfMag_z, p.psfMagerr_z, "
              "dbo.fPhotoTypeN(p.type) AS type "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload, files = sdss.SDSS.query_crossid(coords_list,
                                                   get_query_payload=True,
                                                   data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'nearPrim'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_cross_id_payload(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.ra, p.dec, p.psfMag_u, p.psfMagerr_u, p.psfMag_g, p.psfMagerr_g, "
              "p.psfMag_r, p.psfMagerr_r, p.psfMag_i, p.psfMagerr_i, p.psfMag_z, p.psfMagerr_z, "
              "dbo.fPhotoTypeN(p.type) AS type "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload, files = sdss.SDSS.query_crossid(coords_column,
                                                   get_query_payload=True,
                                                   data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'nearPrim'


@pytest.mark.parametrize("dr", dr_list)
def test_column_coordinates_cross_id_payload_custom_fields(patch_request, dr):
    expect = ("SELECT\r\n"
              "p.r, p.psfMag_r, dbo.fPhotoTypeN(p.type) AS type "
              "FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID "
              "ORDER BY x.up_id")
    query_payload, files = sdss.SDSS.query_crossid(coords_column,
                                                   get_query_payload=True,
                                                   fields=['r', 'psfMag_r'],
                                                   data_release=dr)
    assert query_payload['uquery'] == expect
    assert query_payload['format'] == 'csv'
    assert query_payload['photoScope'] == 'nearPrim'


@pytest.mark.parametrize("dr", dr_list)
def test_photoobj_run_camcol_field_payload(patch_request, dr):
    expect = ("SELECT DISTINCT "
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field "
              "FROM PhotoObjAll AS p WHERE "
              "(p.run=5714 AND p.camcol=6 AND p.rerun=301)")
    query_payload = sdss.SDSS.query_photoobj_async(run=5714, camcol=6,
                                                   get_query_payload=True,
                                                   data_release=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'


@pytest.mark.parametrize("dr", dr_list)
def test_spectra_plate_mjd_payload(patch_request, dr):
    expect = ("SELECT DISTINCT "
              "p.ra, p.dec, p.objid, p.run, p.rerun, p.camcol, p.field, "
              "s.z, s.plate, s.mjd, s.fiberID, s.specobjid, s.run2d "
              "FROM PhotoObjAll AS p "
              "JOIN SpecObjAll AS s ON p.objID = s.bestObjID "
              "WHERE "
              "(s.plate=751 AND s.mjd=52251)")
    query_payload = sdss.SDSS.query_specobj_async(plate=751, mjd=52251,
                                                  get_query_payload=True,
                                                  data_release=dr)
    assert query_payload['cmd'] == expect
    assert query_payload['format'] == 'csv'


def test_field_help_region(patch_request):
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
