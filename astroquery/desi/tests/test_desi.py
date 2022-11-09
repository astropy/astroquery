import astropy.io.votable
import pytest
import os
import numpy as np
import pyvo as vo

from astropy.table import Table
from astropy.io import fits
from astropy import coordinates as coord
from astroquery.utils.mocks import MockResponse
from astroquery.utils import commons
from astroquery import desi
from urllib import parse
from contextlib import contextmanager


DATA_FILES = {
    'dummy_tap_table': 'dummy_table.txt',
    'dummy_tractor_fits': 'dummy_tractor.fits',
    'dummy_hdu_list_fits': 'hdu_list_images.fits'
}

coords = coord.SkyCoord('11h04m27s +38d12m32s', frame='icrs')
width = coord.Angle(0.5, unit='arcmin')
pixels = 60
data_release = 9
emispheres_list = ['north', 'south']


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(desi.DESILegacySurvey, '_request', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['dummy_hdu_list_fits'])  # TODO: add images option
        # f = None
        with open(file_obj, 'rb') as f:
            yield f

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


@pytest.fixture
def patch_tap(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(vo.dal.TAPService, 'run_sync', tap_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, **kwargs):
    parsed_url = parse.urlparse(url)
    splitted_parsed_url = parsed_url.path.split('/')
    url_filename = splitted_parsed_url[-1]
    filename = None
    content = None
    if url_filename.startswith('tractor-'):
        filename = data_path(DATA_FILES['dummy_tractor_fits'])

    if filename is not None:
        with open(filename, 'rb') as f:
            content = f.read()
    return MockResponse(content)


def tap_mockreturn(url, params=None, timeout=10, **kwargs):
    content_table = Table.read(data_path(DATA_FILES['dummy_tap_table']),
                               format='ascii.csv', comment='#')
    votable_table = astropy.io.votable.from_table(content_table)
    return vo.dal.TAPResults(votable_table)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def compare_result_data(result, data):
    for col in result.colnames:
        if result[col].dtype.type is np.string_ or result[col].dtype.type is np.str_:
            assert np.array_equal(result[col], data[col])
        else:
            np.testing.assert_allclose(result[col], data[col])


def image_tester(images, filetype):
    assert type(images) == list
    with fits.open(data_path(DATA_FILES[filetype])) as data:
        assert images[0][0].header == data[0].header
        assert np.array_equal(images[0][0].data, data[0].data)


def test_coords_query_region(patch_tap):
    result = desi.DESILegacySurvey.query_region(coords, width=width)
    data = Table.read(data_path(DATA_FILES['dummy_tap_table']),
                      format='ascii.csv', comment='#')
    data['objid'] = data['objid'].astype(np.int64)
    compare_result_data(result, data)


def test_coords_get_images(patch_get_readable_fileobj, dr=data_release):
    images_list = desi.DESILegacySurvey.get_images(coords, data_release=dr, width=width, pixels=pixels)

    image_tester(images_list, 'dummy_hdu_list_fits')
