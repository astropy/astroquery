# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from ... import ned
import os
from astropy.tests.helper import pytest
from numpy import testing as npt
from astropy.table import Table
import astropy.utils.data as aud
import astropy.coordinates as coord
import astropy.units as u
import requests
from . import (HUBBLE_CONSTANT,
               CORRECT_REDSHIFT,
               OUTPUT_COORDINATE_FRAME,
               OUTPUT_EQUINOX,
               SORT_OUTPUT_BY)

DATA_FILES = {
               'object': 'query_object.xml',
               'Near Name Search': 'query_near_name.xml',
               'Near Position Search': 'query_near_position.xml',
               'IAU Search': 'query_iau_format.xml',
               'Diameters': 'query_diameters.xml',
               'image': 'query_images.fits.gz',
               'Photometry': 'query_phtometry.xml',
               'Positions': 'query_positions.xml',
               'Redshifts': 'query_redshifts.xml',
               'Reference': 'query_references.xml',
               'Search': 'query_refcode.xml',
               'error': 'error.xml',
               'extract_urls': 'image_extract.html'
              }

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

@pytest.fixture
def patch_get_readable_fileobj(request):
    def get_readable_fileobj_mockreturn(filename):
        return aud.get_readable_fileobj(data_path(DATA_FILES['image']))
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

def get_mockreturn(url, data, timeout=10):
    search_type = data.get('search_type')
    if search_type is not None:
        filename = data_path(DATA_FILES['search_type'])
    elif 'imgdata' in url:
        filename = data_path(DATA_FILES['extract_urls'])
    else:
        filename = data_path(DATA_FILES['object'])
    print(filename)
    content = open(filename, "r").read()
    return MockResponse(content)

class MockResponse(object):
    def __init__(self, content):
        self.content = content

@pytest.mark.parametrize(('radius', 'expected'),
                         [(5 * u.deg, 300),
                          ('0d5m0s', 5),
                          (5 * u.arcsec, 0.833)
                          ])
def test_parse_radius(radius, expected):
    # radius in any equivalent unit must be converted to minutes
    actual_radius = ned.core._parse_radius(radius)
    npt.assert_approx_equal(actual_radius, expected, significant=3)

def test_get_references_async(patch_get):
    response = ned.core.Ned.get_references_async()("m1", from_year=2010,
                                                   to_year=2013,
                                                   get_query_payload=True)
    assert response == {'objname': 'm1',
                        'ref_extend': 'no',
                        'begin_year': 2010,
                        'end_year': 2013,
                        'search_type': 'Reference'
                        }

@pytest.mark.xfail(reason="astropy issue #1266")
def test_get_references(patch_get):
    response = ned.core.Ned.get_references_async("m1", from_year=2010)
    assert response is not None
    result = ned.core.Ned.get_references("m1", to_year=2012, extended_search=True)
    assert isinstance(result, Table)

def test_get_positions_async(patch_get):
    response = ned.core.Ned.get_positions_async("m1", get_query_payload=True)
    assert response == {'objname': 'm1'}
    response =  ned.core.Ned.get_positions_async("m1")
    assert response is not None

def test_get_positions(patch_get):
    result =  ned.core.Ned.get_positions("m1")
    assert isinstance(result, Table)

def test_get_redshifts_async(patch_get):
    response = ned.core.Ned.get_redshifts_async("3c 273", get_query_paylaod=True)
    assert response == {'objname': '3c 273',
                       'search_type': 'Redshifts'}
    response = ned.core.Ned.get_redshifts_async("3c 273")
    assert response is not None

def test_get_redshifts(patch_get):
    result = ned.core.Ned.get_redshifts("3c 273")
    assert isinstance(result, Table)

def test_get_photometry_async(patch_get):
    response = ned.core.Ned.get_photometry_async("3c 273", output_table_format=3, get_query_payload=True)
    assert response == {'objname': '3c 273',
                        'meas_type': 'mjy',
                        'search_type': 'Photometry'
                        }
    response = ned.core.Ned.get_photometry_async("3C 273")
    assert response is not None

def test_photometry(patch_get):
    result = ned.core.Ned.get_photometry("3c 273")
    assert isinstance(result, Table)

def test_extract_image_urls():
    html_in = open(data_path(DATA_FILES['extract_urls']), 'r').read()
    url_list =ned.core.Ned.extract_image_urls(html_in)
    assert len(url_list) == 6
    for url in url_list:
        assert url.endswith('fits.gz')

def test_get_image_list(patch_get):
    response = ned.core.Ned.get_image_list('m1', True)
    assert response == {'objname': 'm1'}
    response = ned.core.Ned.get_image_list('m1')
    assert len(response) == 6

def test_get_images_async(patch_get_readable_fileobj):
    readable_objs = ned.core.Ned.get_images_async('m1')
    assert readable_objs is not None

def test_get_images(patch_get_readable_fileobj):
    fits_images = ned.core.Ned.get_images('m1')
    assert fits_images is not None

def test_query_refcode_async(patch_get):
    response = ned.core.Ned.query_refcode_async('1997A&A...323...31K', True)
    assert response == {'search_type': 'Search',
                        'refcode': '1997A&A...323...31K',
                        'hconst': HUBBLE_CONSTANT(),
                        'omegam': 0.27,
                        'omegav': 0.73,
                        'corr_z': CORRECT_REDSHIFT(),
                        'out_csys': OUTPUT_COORDINATE_FRAME(),
                        'out_equinox': OUTPUT_EQUINOX(),
                        'obj_sort': SORT_OUTPUT_BY()
                        }
    response = ned.core.Ned.query_refcode_async('1997A&A...323...31K')
    assert response is not None

def test_query_refcode(patch_get):
    result = ned.core.Ned.query_refcode('1997A&A...323...31K')
    assert isinstance(result, Table)

def test_query_region_iau_async(patch_get):
    response = ned.core.Ned.query_region_iau_async('1234-423', get_query_payload=True)
    assert response['search_type'] == 'IAU Search'
    assert response['iau_name'] == '1234-423'
    assert response['in_csys'] == 'Equatorial'
    assert response['in_equinox'] == 'B1950.0'
    response = ned.core.Ned.query_region_iau_async('1234-423')
    assert response is not None

def test_query_region_iau(patch_get):
    result = ned.core.Ned.query_region_iau('1234-423')
    assert isinstance(result, Table)

def test_query_region_async(patch_get, coordinates):
    # check with the name
    response = ned.core.Ned.query_region_async("m1", get_query_payload=True)
    assert response['objname'] == "m1"
    assert response['search_type'] == "Near Name Search"
    # check with ICRS coordinates
    response = ned.core.Ned.query_region_async("05h35m17.3s +22d00m52.2s", get_query_payload=True)
    assert response['lon'] == "05h35m17.3s"
    assert response['lat'] == "22d00m52.2s"
    assert response['search_type'] == 'Near Position Search'
    # check with Galactic coordinates
    response = ned.core.Ned.query_region_async(coord.GalacticCoordinates(l=-67.02084, b=-29.75447, unit=(u.deg, u.deg)),
                                               get_query_payload=True)
    assert response['lon'] == -67.02084
    assert response['lat'] == -29.75447
    response = ned.core.Ned.query_region_async("05h35m17.3s +22d00m52.2s")
    assert response is not None

def test_query_region(patch_get):
    result = ned.core.Ned.query_region("05h35m17.3s +22d00m52.2s")
    assert isinstance(result, Table)

def test_query_object_async(patch_get):
    response = ned.core.Ned.query_object_async('m1', get_query_payload=True)
    assert response['objname'] == 'm1'
    response = ned.core.Ned.query_object_async('m1')
    assert response is not None

def test_query_object(patch_get):
    result = ned.core.Ned.query_object('m1')
    assert isinstance(result, Table)

#---------------------------------------

def test_objname():
    result = ned.query_ned_by_objname()

def test_nearname():
    result = ned.query_ned_nearname()

def test_near_iauname():
    result = ned.query_ned_near_iauname()

def test_by_refcode():
    result = ned.query_ned_by_refcode()

def test_names():
    result = ned.query_ned_names()

def test_basic_posn():
    result = ned.query_ned_basic_posn()

def test_ned_external():
    result = ned.query_ned_external()

# I cannot get this to pass.  It just gives timeout errors.
#try:
#    #time.sleep(1)  # wait before running another query
#    def test_ned_allsky():
#        result = ned.query_ned_allsky(ra_constraint='Between',
#                                      ra_1='00h00m00.0',
#                                      ra_2='01h00m00.0',
#                                      z_constraint='Larger Than',
#                                      z_value1=2.0)
#except Exception as error: #socket.error:
#    print "Some kind of error: ",error

def test_ned_photometry():
    result = ned.query_ned_photometry()

def test_ned_diameters():
    result = ned.query_ned_diameters()

def test_ned_redshifts():
    result = ned.query_ned_redshifts()

def test_ned_notes():
    result = ned.query_ned_notes()

def test_ned_position():
    result = ned.query_ned_position()

def test_ned_nearpos():
    result = ned.query_ned_nearpos()
