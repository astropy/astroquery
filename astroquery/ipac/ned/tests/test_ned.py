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


DATA_FILES = {
    'object': 'query_object.xml',
    'ConeSearchByTarget': 'query_near_name.xml',
    'ConeSearchByPosition': 'query_near_position.xml',
    'ConeSearchByIAUstyle': 'query_iau_format.xml',
    'CrossidsOfObject': 'query_crossids.xml',
    'DiametersOfObject': 'query_diameters.xml',
    'DistancesOfObject': 'query_distances.xml',
    'PhotometryOfObject': 'query_photometry.xml',
    'PositionsOfObject': 'query_positions.xml',
    'RedshiftsOfObject': 'query_redshifts.xml',
    'ExtinctionAtTarget': 'query_extinction.xml',
    'ReferencesOfObject': 'query_references.xml',
    'NotesOfObject': 'query_notes.xml',
    'ObjectsInRefcode': 'query_refcode.xml',
    'error': 'error.xml',
    'image': 'query_images.fits',
    'extract_urls': 'image_extract.html'
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
    # search_type = params.get('search_type')
    search_type = ned.Ned.SEARCH_TYPE
    if search_type is not None and search_type not in ['image', 'spectra']:
        filename = data_path(DATA_FILES[search_type])
    elif 'imgdata' in url:
        filename = data_path(DATA_FILES['extract_urls'])
    else:
        return None
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def test_get_references_async(patch_get):
    # from_year and to_year are ignored as they are not supported
    # by NED API of N36.1 release
    response = ned.Ned.get_table_async("m1",
                                       table='references',
                                       from_year=2010,
                                       to_year=2013,
                                       get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    # assert response['objname'] == 'm1'
    # assert response['ref_extend'] == 'no'
    # assert response['begin_year'] == 2010
    # assert response['end_year'] == 2013
    # assert response['search_type'] == 'Reference'
    assert response[ned.Ned.DBR_TARGET] == 'm1'
    assert s_type == ned.Ned.OBJSEARCH_REFERENCES

    response = ned.Ned.get_table_async("m1", table='references', max_rec=10)
    assert response is not None


def test_get_references(patch_get):
    # from_year and to_year are ignored as they are not supported
    # by NED API of N36.1 release
    result = ned.Ned.get_table(
        "m1", table='references', max_rec=10)
    assert isinstance(result, Table)
    response = ned.Ned.get_table("m1", table='references',
                                 get_query_payload=True)
    assert response is not None


def test_get_crossids_async(patch_get):
    response = ned.Ned.get_table_async(
        "3C 273", table='crossids', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == '3C 273'
    assert s_type == ned.Ned.OBJSEARCH_CROSSIDS
    response = ned.Ned.get_table_async("3C 273", table='crossids')
    assert response is not None


def test_get_crossids(patch_get):
    result = ned.Ned.get_table("3C 273", table='crossids')
    assert isinstance(result, Table)


def test_get_diameters_async(patch_get):
    response = ned.Ned.get_table_async(
        "m1", table='diameters', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == "m1"
    assert s_type == ned.Ned.OBJSEARCH_DIAMETERS
    response = ned.Ned.get_table_async("m1", table='diameters')
    assert response is not None


def test_get_diameters(patch_get):
    result = ned.Ned.get_table("m1", table='diameters')
    assert isinstance(result, Table)


def test_get_distances_async(patch_get):
    response = ned.Ned.get_table_async(
        "3C 273", table='distances', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == "3C 273"
    assert s_type == ned.Ned.OBJSEARCH_DISTANCES
    response = ned.Ned.get_table_async("3C 273", table='distances')
    assert response is not None


def test_get_distances(patch_get):
    result = ned.Ned.get_table("3C 273", table='distances')
    assert isinstance(result, Table)


def test_get_extinctions_async(patch_get):
    response = ned.Ned.get_table_async(
        "3C 273", table='extinctions', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == "3C 273"
    assert s_type == ned.Ned.OBJSEARCH_EXTINCTION

    response = ned.Ned.get_table_async("3C 273", table='extinctions')
    assert response is not None


def test_get_extinctions(patch_get):
    result = ned.Ned.get_table("3C 273", table='extinctions')
    assert isinstance(result, Table)


def test_get_positions_async(patch_get):
    response = ned.Ned.get_table_async(
        "m1", table='positions', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    # assert response['objname'] == 'm1'
    assert response[ned.Ned.DBR_TARGET] == 'm1'
    assert s_type == ned.Ned.OBJSEARCH_POSITIONS
    response = ned.Ned.get_table_async("m1", table='positions')
    assert response is not None


def test_get_positions(patch_get):
    result = ned.Ned.get_table("m1", table='positions')
    assert isinstance(result, Table)


def test_get_redshifts_async(patch_get):
    response = ned.Ned.get_table_async(
        "3c 273", table='redshifts', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    # assert response['objname'] == '3c 273'
    # assert response['search_type'] == 'Redshifts'
    assert response[ned.Ned.DBR_TARGET] == '3c 273'
    assert s_type == ned.Ned.OBJSEARCH_REDSHIFTS
    response = ned.Ned.get_table_async("3c 273", table='redshifts')
    assert response is not None


def test_get_redshifts(patch_get):
    result = ned.Ned.get_table("3c 273", table='redshifts')
    assert isinstance(result, Table)


def test_get_photometry_async(patch_get):
    response = ned.Ned.get_table_async(
        "3c 273", table='photometry', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == '3c 273'
    # assert response['meas_type'] == 'bot'
    # assert response['search_type'] == 'Photometry'
    assert s_type == ned.Ned.OBJSEARCH_PHOTOMETRY
    response = ned.Ned.get_table_async("3C 273", table='photometry', max_rec=10)
    assert response is not None


def test_photometry(patch_get):
    result = ned.Ned.get_table("3c 273", table='photometry', max_rec=10)
    assert isinstance(result, Table)


def test_extract_image_urls():
    with open(data_path(DATA_FILES['extract_urls']), 'r') as infile:
        html_in = infile.read()
    url_list = ned.Ned._extract_image_urls(html_in)
    assert len(url_list) == 5
    for url in url_list:
        assert url.endswith('fits.gz')


def test_get_image_list(patch_get):
    response = ned.Ned.get_image_list('m1', get_query_payload=True)
    assert response['objname'] == 'm1'
    response = ned.Ned.get_image_list('m1')
    assert len(response) == 5


def test_get_images_async(patch_get, patch_get_readable_fileobj):
    readable_objs = ned.Ned.get_images_async('m1')
    assert readable_objs is not None


def test_get_images(patch_get, patch_get_readable_fileobj):
    fits_images = ned.Ned.get_images('m1')
    assert fits_images is not None


def test_query_refcode_async(patch_get):
    response = ned.Ned.query_refcode_async('1997A&A...323...31K',
                                           get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    # assert response == {'search_type': 'Search',
    #                    'refcode': '1997A&A...323...31K',
    #                    'hconst': conf.hubble_constant,
    #                    'omegam': 0.27,
    #                    'omegav': 0.73,
    #                    'corr_z': conf.correct_redshift,
    #                    'out_csys': conf.output_coordinate_frame,
    #                    'out_equinox': conf.output_equinox,
    #                    'obj_sort': conf.sort_output_by,
    #                    'extend': 'no',
    #                    'img_stamp': 'NO',
    #                    'list_limit': 0,
    #                    'of': 'xml_main'
    #                    }
    assert s_type == ned.Ned.OBJSEARCH_INREFCODE
    assert response[ned.Ned.DBR_REFCODE] == '1997A&A...323...31K'
    response = ned.Ned.query_refcode_async('1997A&A...323...31K')
    assert response is not None


def test_query_refcode(patch_get):
    response = ned.Ned.query_refcode('1997A&A...323...31K', get_query_payload=True)
    assert response is not None
    result = ned.Ned.query_refcode('1997A&A...323...31K')
    assert isinstance(result, Table)


def test_query_region_iau_async(patch_get):
    response = ned.Ned.query_region_iau_async(
        '1234-423', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    # assert response['search_type'] == 'IAU Search'
    assert s_type == ned.Ned.CONESEARCH_IAU
    assert response[ned.Ned.DBR_IAU] == '1234-423'
    assert response[ned.Ned.DBR_EQUINOX] == 'B1950'
    response = ned.Ned.query_region_iau_async('1234-423', max_rec=10)
    assert response is not None


def test_query_region_iau(patch_get):
    response = ned.Ned.query_region_iau('1234-423', get_query_payload=True)
    assert response is not None
    result = ned.Ned.query_region_iau('1234-423', max_rec=10)
    assert isinstance(result, Table)


def mock_check_resolvable(name):
    if name != 'm31':
        raise coord.name_resolve.NameResolveError


def test_query_region_async(monkeypatch, patch_get):
    # check with the name
    monkeypatch.setattr(
        coord.name_resolve, 'get_icrs_coordinates', mock_check_resolvable)
    response = ned.Ned.query_region_async("m31", get_query_payload=True,
                                          z_constraint='Between', z_value1=4.2,
                                          z_value2=96, z_unit='km/s')
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == "m31"
    assert response['z_constraint'] == 'Between'
    assert response['z_value1'] == 4.2
    assert response['z_value2'] == 96
    assert response['z_unit'] == 'km/s'
    assert s_type == ned.Ned.CONESEARCH_TARGET
    # assert response['search_type'] == "Near Name Search"
    # check with Galactic coordinates
    response = ned.Ned.query_region_async(
        coord.SkyCoord(l=-67.02084 * u.deg, b=-29.75447 * u.deg,
                       frame="galactic"), get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert s_type == ned.Ned.CONESEARCH_POSITION
    # assert response['search_type'] == 'Near Position Search'
    npt.assert_approx_equal(
        float(response[ned.Ned.DBR_LON]) % 360, -67.02084 % 360, significant=5)
    npt.assert_approx_equal(float(response[ned.Ned.DBR_LAT]), -29.75447,
                            significant=5)
    response = ned.Ned.query_region_async("05h35m17.3s +22d00m52.2s")
    assert response is not None


def test_query_region(monkeypatch, patch_get):
    monkeypatch.setattr(
        coord.name_resolve, 'get_icrs_coordinates', mock_check_resolvable)
    result = ned.Ned.query_region("m31", z_constraint='Between',
                                  z_value1=4.2, z_value2=96, z_unit='km/s')
    assert isinstance(result, Table)
    response = ned.Ned.query_region(
        coord.SkyCoord(ra=-10.684793 * u.deg, dec=-41.269065 * u.deg,
                       frame="fk5"), get_query_payload=True)
    assert response is not None


def test_query_object_async(patch_get):
    response = ned.Ned.query_object_async('m1', get_query_payload=True)
    assert response[ned.Ned.DBR_TARGET] == 'm1'
    response = ned.Ned.query_object_async('m1')
    assert response is not None


def test_query_object(patch_get):
    response = ned.Ned.query_object('m1', get_query_payload=True)
    assert response[ned.Ned.DBR_TARGET] == 'm1'
    result = ned.Ned.query_object('m1')
    assert isinstance(result, Table)


def test_get_object_notes_async(patch_get):
    response = ned.Ned.get_table_async(
        'm1', table='object_notes', get_query_payload=True)
    s_type = ned.Ned.SEARCH_TYPE
    assert response[ned.Ned.DBR_TARGET] == 'm1'
    assert s_type == ned.Ned.OBJSEARCH_NOTES
    response = ned.Ned.get_table_async('m1', table='object_notes')
    assert response is not None


def test_get_object_notes(patch_get):
    result = ned.Ned.get_table('3c 273', table='object_notes')
    assert isinstance(result, Table)


def test_parse_result(capsys):
    with open(data_path(DATA_FILES['error']), 'rb') as infile:
        content = infile.read()
    response = MockResponse(content)

    with pytest.raises(RemoteServiceError) as exinfo:
        ned.Ned._parse_result(response)

    error_message = (
        "The remote service returned the following message.\nERROR: "
        "GeneralFault:\nService could not complete request; Please "
        "provide a valid search radius (6)")
    if hasattr(exinfo.value, 'message'):
        assert exinfo.value.message == (error_message)
    else:
        assert exinfo.value.args[0] == (error_message)


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.ned  # noqa: F401
