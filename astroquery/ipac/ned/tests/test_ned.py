# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from contextlib import contextmanager

from numpy import testing as npt
import pytest
from astropy.table import Table
import astropy.coordinates as coord
import astropy.units as u
from astroquery.exceptions import RemoteServiceError
from astroquery.utils.mocks import MockResponse

from astroquery.ipac import ned
from astroquery.utils import commons
from astroquery.ipac.ned import conf

DATA_FILES = {
    'object': 'query_object.xml',
    'Near Name Search': 'query_near_name.xml',
    'Near Position Search': 'query_near_position.xml',
    'IAU Search': 'query_iau_format.xml',
    'Diameters': 'query_diameters.xml',
    'image': 'query_images.fits',
    'Photometry': 'query_photometry.xml',
    'Positions': 'query_positions.xml',
    'Redshifts': 'query_redshifts.xml',
    'Reference': 'query_references.xml',
    'Search': 'query_refcode.xml',
    'error': 'error.xml',
    'extract_urls': 'image_extract.html',
    'Notes': 'query_notes.xml'
}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(ned.Ned, '_request', get_mockreturn)
    return mp


@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, cache=True, encoding=None,
                                        show_progress=True):
        # Need to read FITS files with binary encoding: should raise error
        # otherwise
        assert encoding == 'binary'
        with open(data_path(DATA_FILES['image']), 'rb') as infile:
            yield infile

    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'get_readable_fileobj',
               get_readable_fileobj_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, **kwargs):
    search_type = params.get('search_type')
    if search_type is not None:
        filename = data_path(DATA_FILES[search_type])
    elif 'imgdata' in url:
        filename = data_path(DATA_FILES['extract_urls'])
    else:
        filename = data_path(DATA_FILES['object'])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def test_get_references_async(patch_get):
    response = ned.core.Ned.get_table_async("m1", table='references',
                                            from_year=2010,
                                            to_year=2013,
                                            get_query_payload=True)
    assert response['objname'] == 'm1'
    assert response['ref_extend'] == 'no'
    assert response['begin_year'] == 2010
    assert response['end_year'] == 2013
    assert response['search_type'] == 'Reference'


def test_get_references(patch_get):
    response = ned.core.Ned.get_table_async(
        "m1", table='references', from_year=2010)
    assert response is not None
    result = ned.core.Ned.get_table(
        "m1", table='references', to_year=2012, extended_search=True)
    assert isinstance(result, Table)


def test_get_positions_async(patch_get):
    response = ned.core.Ned.get_table_async(
        "m1", table='positions', get_query_payload=True)
    assert response['objname'] == 'm1'
    response = ned.core.Ned.get_table_async("m1", table='positions')
    assert response is not None


def test_get_positions(patch_get):
    result = ned.core.Ned.get_table("m1", table='positions')
    assert isinstance(result, Table)


def test_get_redshifts_async(patch_get):
    response = ned.core.Ned.get_table_async(
        "3c 273", table='redshifts', get_query_payload=True)
    assert response['objname'] == '3c 273'
    assert response['search_type'] == 'Redshifts'
    response = ned.core.Ned.get_table_async("3c 273", table='redshifts')
    assert response is not None


def test_get_redshifts(patch_get):
    result = ned.core.Ned.get_table("3c 273", table='redshifts')
    assert isinstance(result, Table)


def test_get_photometry_async(patch_get):
    response = ned.core.Ned.get_table_async(
        "3c 273", table='photometry', get_query_payload=True)
    assert response['objname'] == '3c 273'
    assert response['meas_type'] == 'bot'
    assert response['search_type'] == 'Photometry'
    response = ned.core.Ned.get_table_async("3C 273", table='photometry')
    assert response is not None


def test_photometry(patch_get):
    result = ned.core.Ned.get_table("3c 273", table='photometry')
    assert isinstance(result, Table)


def test_extract_image_urls():
    with open(data_path(DATA_FILES['extract_urls']), 'r') as infile:
        html_in = infile.read()
    url_list = ned.core.Ned._extract_image_urls(html_in)
    assert len(url_list) == 5
    for url in url_list:
        assert url.endswith('fits.gz')


def test_get_image_list(patch_get):
    response = ned.core.Ned.get_image_list('m1', get_query_payload=True)
    assert response['objname'] == 'm1'
    response = ned.core.Ned.get_image_list('m1')
    assert len(response) == 5


def test_get_images_async(patch_get, patch_get_readable_fileobj):
    readable_objs = ned.core.Ned.get_images_async('m1')
    assert readable_objs is not None


def test_get_images(patch_get, patch_get_readable_fileobj):
    fits_images = ned.core.Ned.get_images('m1')
    assert fits_images is not None


def test_query_refcode_async(patch_get):
    response = ned.core.Ned.query_refcode_async('1997A&A...323...31K', get_query_payload=True)
    assert response == {'search_type': 'Search',
                        'refcode': '1997A&A...323...31K',
                        'hconst': conf.hubble_constant,
                        'omegam': 0.27,
                        'omegav': 0.73,
                        'corr_z': conf.correct_redshift,
                        'out_csys': conf.output_coordinate_frame,
                        'out_equinox': conf.output_equinox,
                        'obj_sort': conf.sort_output_by,
                        'extend': 'no',
                        'img_stamp': 'NO',
                        'list_limit': 0,
                        'of': 'xml_main'
                        }
    response = ned.core.Ned.query_refcode_async('1997A&A...323...31K')
    assert response is not None


def test_query_refcode(patch_get):
    result = ned.core.Ned.query_refcode('1997A&A...323...31K')
    assert isinstance(result, Table)


def test_query_region_iau_async(patch_get):
    response = ned.core.Ned.query_region_iau_async(
        '1234-423', get_query_payload=True)
    assert response['search_type'] == 'IAU Search'
    assert response['iau_name'] == '1234-423'
    assert response['in_csys'] == 'Equatorial'
    assert response['in_equinox'] == 'B1950.0'
    response = ned.core.Ned.query_region_iau_async('1234-423')
    assert response is not None


def test_query_region_iau(patch_get):
    result = ned.core.Ned.query_region_iau('1234-423')
    assert isinstance(result, Table)


def mock_check_resolvable(name):
    if name != 'm1':
        raise coord.name_resolve.NameResolveError


def test_query_region_async(monkeypatch, patch_get):
    # check with the name
    monkeypatch.setattr(
        coord.name_resolve, 'get_icrs_coordinates', mock_check_resolvable)
    response = ned.core.Ned.query_region_async("m1", get_query_payload=True)
    assert response['objname'] == "m1"
    assert response['search_type'] == "Near Name Search"
    # check with Galactic coordinates
    response = ned.core.Ned.query_region_async(
        coord.SkyCoord(l=-67.02084 * u.deg, b=-29.75447 * u.deg, frame="galactic"),
        get_query_payload=True)
    assert response['search_type'] == 'Near Position Search'
    npt.assert_approx_equal(
        response['lon'] % 360, -67.02084 % 360, significant=5)
    npt.assert_approx_equal(response['lat'], -29.75447, significant=5)
    response = ned.core.Ned.query_region_async("05h35m17.3s +22d00m52.2s")
    assert response is not None


def test_query_region(monkeypatch, patch_get):
    monkeypatch.setattr(
        coord.name_resolve, 'get_icrs_coordinates', mock_check_resolvable)
    result = ned.core.Ned.query_region("m1")
    assert isinstance(result, Table)


def test_query_object_async(patch_get):
    response = ned.core.Ned.query_object_async('m1', get_query_payload=True)
    assert response['objname'] == 'm1'
    response = ned.core.Ned.query_object_async('m1')
    assert response is not None


def test_query_object(patch_get):
    result = ned.core.Ned.query_object('m1')
    assert isinstance(result, Table)


def test_get_object_notes_async(patch_get):
    response = ned.core.Ned.get_table_async(
        'm1', table='object_notes', get_query_payload=True)
    assert response['objname'] == 'm1'
    assert response['search_type'] == 'Notes'
    response = ned.core.Ned.get_table_async('m1', table='object_notes')
    assert response is not None


def test_get_object_notes(patch_get):
    result = ned.core.Ned.get_table('3c 273', table='object_notes')
    assert isinstance(result, Table)


def test_parse_result(capsys):
    with open(data_path(DATA_FILES['error']), 'rb') as infile:
        content = infile.read()
    response = MockResponse(content)
    with pytest.raises(RemoteServiceError) as exinfo:
        ned.core.Ned._parse_result(response)
    if hasattr(exinfo.value, 'message'):
        assert exinfo.value.message == ("The remote service returned the "
                                        "following error message.\nERROR:  "
                                        "No note found.")
    else:
        assert exinfo.value.args == ("The remote service returned the "
                                     "following error message.\nERROR:  "
                                     "No note found.",)


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.ned  # noqa: F401
