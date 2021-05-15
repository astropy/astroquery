# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import re

import six
import pytest
import astropy.units as u
from astropy.table import Table
import numpy as np

from ... import simbad
from ...utils.testing_tools import MockResponse
from ...utils import commons
from ...exceptions import TableParseError
from .test_simbad_remote import multicoords

GALACTIC_COORDS = commons.GalacticCoordGenerator(l=-67.02084, b=-29.75447,
                                                 unit=(u.deg, u.deg))
ICRS_COORDS = commons.ICRSCoordGenerator("05h35m17.3s -05h23m28s")
FK4_COORDS = commons.FK4CoordGenerator(ra=84.90759, dec=-80.89403,
                                       unit=(u.deg, u.deg))
FK5_COORDS = commons.FK5CoordGenerator(ra=83.82207, dec=-80.86667,
                                       unit=(u.deg, u.deg))

DATA_FILES = {
    'id': 'query_id.data',
    'coo': 'query_coo.data',
    'cat': 'query_cat.data',
    'bibobj': 'query_bibobj.data',
    'bibcode': 'query_bibcode.data',
    'objectids': 'query_objectids.data',
    'error': 'query_error.data',
    'sample': 'query_sample.data',
    'region': 'query_sample_region.data',
}


class MockResponseSimbad(MockResponse):
    query_regex = re.compile(r'query\s+([a-z]+)\s+')

    def __init__(self, script, cache=True, **kwargs):
        # preserve, e.g., headers
        super(MockResponseSimbad, self).__init__(**kwargs)
        self.content = self.get_content(script)

    def get_content(self, script):
        match = self.query_regex.search(script)
        if match:
            filename = DATA_FILES[match.group(1)]
            content = open(data_path(filename), "rb").read()
            return content


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(simbad.SimbadClass, '_request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data, timeout, **kwargs):
    response = MockResponseSimbad(data['script'], **kwargs)

    class last_query:
        pass

    self._last_query = last_query()
    self._last_query.data = data
    return response


@pytest.mark.parametrize(('radius', 'expected_radius'),
                         [('5d0m0s', '5.0d'),
                          ('5d', '5.0d'),
                          ('5.0d', '5.0d'),
                          (5 * u.deg, '5.0d'),
                          (5.0 * u.deg, '5.0d'),
                          (1.2 * u.deg, '1.2d'),
                          (0.5 * u.deg, '30.0m'),
                          ('0d1m12s', '1.2m'),
                          (0.003 * u.deg, '10.8s'),
                          ('0d0m15s', '15.0s')
                          ])
def test_parse_radius(radius, expected_radius):
    actual = simbad.core._parse_radius(radius)
    assert actual == expected_radius


@pytest.mark.parametrize(('ra', 'dec', 'expected_ra', 'expected_dec'),
                         [(ICRS_COORDS.ra, ICRS_COORDS.dec, u'5:35:17.3',
                           u'-80:52:00')
                          ])
def test_to_simbad_format(ra, dec, expected_ra, expected_dec):
    actual_ra, actual_dec = simbad.core._to_simbad_format(ra, dec)
    assert (actual_ra, actual_dec) == (expected_ra, expected_dec)


@pytest.mark.parametrize(('coordinates', 'expected_frame'),
                         [(GALACTIC_COORDS, 'GAL'),
                          (ICRS_COORDS, 'ICRS'),
                          (FK4_COORDS, 'FK4'),
                          (FK5_COORDS, 'FK5')
                          ])
def test_get_frame_coordinates(coordinates, expected_frame):
    actual_frame = simbad.core._get_frame_coords(coordinates)[2]
    assert actual_frame == expected_frame
    if actual_frame == 'GAL':
        l_gal, b_gal = simbad.core._get_frame_coords(coordinates)[:2]
        np.testing.assert_almost_equal(float(l_gal) % 360, -67.02084 % 360)
        np.testing.assert_almost_equal(float(b_gal), -29.75447)


def test_parse_result():
    result1 = simbad.core.Simbad._parse_result(
        MockResponseSimbad('query id '), simbad.core.SimbadVOTableResult)
    assert isinstance(result1, Table)
    with pytest.raises(TableParseError) as ex:
        simbad.core.Simbad._parse_result(MockResponseSimbad('query error '),
                                         simbad.core.SimbadVOTableResult)
    assert str(ex.value) == ('Failed to parse SIMBAD result! The raw response '
                             'can be found in self.last_response, and the '
                             'error in self.last_table_parse_error. '
                             'The attempted parsed result is in '
                             'self.last_parsed_result.\n Exception: 7:115: '
                             'no element found')
    assert isinstance(simbad.Simbad.last_response.text, six.string_types)
    assert isinstance(simbad.Simbad.last_response.content, six.binary_type)


votable_fields = ",".join(simbad.core.Simbad.get_votable_fields())


@pytest.mark.parametrize(('args', 'kwargs', 'expected_script'),
                         [(["m [0-9]"], dict(wildcard=True,
                                             caller='query_object_async'),
                           ("\nvotable {" + votable_fields + "}\n"
                            "votable open\n"
                            "query id wildcard m [0-9]  \n"
                            "votable close"
                            )),
                          (["2006ApJ"], dict(caller='query_bibcode_async',
                                             get_raw=True),
                           ("\n\nquery bibcode  2006ApJ  \n"))
                          ])
def test_args_to_payload(args, kwargs, expected_script):
    script = simbad.Simbad._args_to_payload(*args, **kwargs)['script']
    assert script == expected_script


@pytest.mark.parametrize(('epoch', 'equinox'),
                         [(2000, 'thousand'),
                          ('J-2000', None),
                          (None, '10e3b')
                          ])
def test_validation(epoch, equinox):
    with pytest.raises(ValueError):
        # only one of these has to raise an exception
        if equinox is not None:
            simbad.core.validate_equinox(equinox)
        if epoch is not None:
            simbad.core.validate_epoch(epoch)


@pytest.mark.parametrize(('bibcode', 'wildcard'),
                         [('2006ApJ*', True),
                          ('2005A&A.430.165F', None)
                          ])
def test_query_bibcode_async(patch_post, bibcode, wildcard):
    response1 = simbad.core.Simbad.query_bibcode_async(bibcode,
                                                       wildcard=wildcard)
    response2 = simbad.core.Simbad().query_bibcode_async(bibcode,
                                                         wildcard=wildcard)
    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


def test_query_bibcode_class(patch_post):
    result1 = simbad.core.Simbad.query_bibcode("2006ApJ*", wildcard=True)
    assert isinstance(result1, Table)


def test_query_bibcode_instance(patch_post):
    S = simbad.core.Simbad()
    result2 = S.query_bibcode("2006ApJ*", wildcard=True)
    assert isinstance(result2, Table)


def test_query_objectids_async(patch_post):
    response1 = simbad.core.Simbad.query_objectids_async('Polaris')
    response2 = simbad.core.Simbad().query_objectids_async('Polaris')
    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


def test_query_objectids(patch_post):
    result1 = simbad.core.Simbad.query_objectids('Polaris')
    result2 = simbad.core.Simbad().query_objectids('Polaris')
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


def test_query_bibobj_async(patch_post):
    response1 = simbad.core.Simbad.query_bibobj_async('2005A&A.430.165F')
    response2 = simbad.core.Simbad().query_bibobj_async('2005A&A.430.165F')
    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


def test_query_bibobj(patch_post):
    result1 = simbad.core.Simbad.query_bibobj('2005A&A.430.165F')
    result2 = simbad.core.Simbad().query_bibobj('2005A&A.430.165F')
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


def test_query_catalog_async(patch_post):
    response1 = simbad.core.Simbad.query_catalog_async('m')
    response2 = simbad.core.Simbad().query_catalog_async('m')
    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


def test_query_catalog(patch_post):
    result1 = simbad.core.Simbad.query_catalog('m')
    result2 = simbad.core.Simbad().query_catalog('m')
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


@pytest.mark.parametrize(('coordinates', 'radius', 'equinox', 'epoch'),
                         [(ICRS_COORDS, None, 2000.0, 'J2000'),
                          (GALACTIC_COORDS, 5 * u.deg, 2000.0, 'J2000'),
                          (FK4_COORDS, '5d0m0s', 2000.0, 'J2000'),
                          (FK5_COORDS, None, 2000.0, 'J2000'),
                          (multicoords, 0.5*u.arcsec, 2000.0, 'J2000'),
                          ])
def test_query_region_async(patch_post, coordinates, radius, equinox, epoch):
    response1 = simbad.core.Simbad.query_region_async(
        coordinates, radius=radius, equinox=equinox, epoch=epoch)

    response2 = simbad.core.Simbad().query_region_async(
        coordinates, radius=radius, equinox=equinox, epoch=epoch)

    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


@pytest.mark.parametrize(('coordinates', 'radius', 'equinox', 'epoch'),
                         [(ICRS_COORDS, None, 2000.0, 'J2000'),
                          (GALACTIC_COORDS, 5 * u.deg, 2000.0, 'J2000'),
                          (FK4_COORDS, '5d0m0s', 2000.0, 'J2000'),
                          (FK5_COORDS, None, 2000.0, 'J2000')
                          ])
def test_query_region(patch_post, coordinates, radius, equinox, epoch):
    result1 = simbad.core.Simbad.query_region(coordinates, radius=radius,
                                              equinox=equinox, epoch=epoch)
    result2 = simbad.core.Simbad().query_region(coordinates, radius=radius,
                                                equinox=equinox, epoch=epoch)
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


@pytest.mark.parametrize(('coordinates', 'radius', 'equinox', 'epoch'),
                         [(ICRS_COORDS, 0, 2000.0, 'J2000')])
def test_query_region_radius_error(patch_post, coordinates, radius,
                                   equinox, epoch):
    with pytest.raises(u.UnitsError):
        simbad.core.Simbad.query_region(
            coordinates, radius=radius, equinox=equinox, epoch=epoch)

    with pytest.raises(u.UnitsError):
        simbad.core.Simbad().query_region(
            coordinates, radius=radius, equinox=equinox, epoch=epoch)


@pytest.mark.parametrize(('coordinates', 'radius', 'equinox', 'epoch'),
                         [(ICRS_COORDS, "0d", 2000.0, 'J2000'),
                          (GALACTIC_COORDS, 1.0 * u.marcsec, 2000.0, 'J2000')
                          ])
def test_query_region_small_radius(patch_post, coordinates, radius,
                                   equinox, epoch):
    result1 = simbad.core.Simbad.query_region(coordinates, radius=radius,
                                              equinox=equinox, epoch=epoch)
    result2 = simbad.core.Simbad().query_region(coordinates, radius=radius,
                                                equinox=equinox, epoch=epoch)
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


@pytest.mark.parametrize(('object_name', 'wildcard'),
                         [("m1", None),
                          ("m [0-9]", True)
                          ])
def test_query_object_async(patch_post, object_name, wildcard):
    response1 = simbad.core.Simbad.query_object_async(object_name,
                                                      wildcard=wildcard)
    response2 = simbad.core.Simbad().query_object_async(object_name,
                                                        wildcard=wildcard)
    assert response1 is not None and response2 is not None
    assert response1.content == response2.content


@pytest.mark.parametrize(('object_name', 'wildcard'),
                         [("m1", None),
                          ("m [0-9]", True),
                          ])
def test_query_object(patch_post, object_name, wildcard):
    payload = simbad.core.Simbad.query_object(
        object_name, wildcard=wildcard, get_query_payload=True)
    expected_payload = {'script': '\nvotable {main_id,coordinates}\nvotable' +
                        ' open\nquery id {} {}  \nvotable close'.
                        format('wildcard' if wildcard else '', object_name)}
    assert payload == expected_payload
    result1 = simbad.core.Simbad.query_object(object_name,
                                              wildcard=wildcard)
    result2 = simbad.core.Simbad().query_object(object_name,
                                                wildcard=wildcard)
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)


def test_list_votable_fields():
    simbad.core.Simbad.list_votable_fields()
    simbad.core.Simbad().list_votable_fields()


def test_get_field_description():
    simbad.core.Simbad.get_field_description('bibcodelist(y1-y2)')
    simbad.core.Simbad().get_field_description('bibcodelist(y1-y2)')
    with pytest.raises(Exception):
        simbad.core.Simbad.get_field_description('xyz')


def test_votable_fields():
    sb = simbad.core.Simbad()
    sb.add_votable_fields('rot', 'z_value', 'velocity')
    assert (set(sb.get_votable_fields()) ==
            set(['main_id', 'coordinates', 'rot', 'z_value', 'velocity']))
    try:
        sb.add_votable_fields('velocity')
    except KeyError:
        pass  # this is the expected response
    assert (set(sb.get_votable_fields()) ==
            set(['main_id', 'coordinates', 'rot', 'z_value', 'velocity']))
    sb.remove_votable_fields('rot', 'main_id', 'coordinates')
    assert set(sb.get_votable_fields()) == set(['z_value', 'velocity'])
    sb.remove_votable_fields('rot', 'main_id', 'coordinates')
    assert set(sb.get_votable_fields()) == set(['z_value', 'velocity'])
    sb.remove_votable_fields('z_value', 'velocity')
    assert (set(sb.get_votable_fields()) ==
            set(['main_id', 'coordinates']))
    sb.add_votable_fields('rot', 'z_value', 'velocity')
    sb.reset_votable_fields()
    assert (set(sb.get_votable_fields()) ==
            set(['main_id', 'coordinates']))


def test_query_criteria1(patch_post):
    Simbad = simbad.core.Simbad()
    result = Simbad.query_criteria(
        "region(box, GAL, 49.89 -0.3, 0.5d 0.5d)", otype='HII')
    assert isinstance(result, Table)
    assert "region(box, GAL, 49.89 -0.3, 0.5d 0.5d)" in Simbad._last_query.data['script']


def test_query_criteria2(patch_post):
    S = simbad.core.Simbad()
    S.add_votable_fields('ra(d)', 'dec(d)')
    S.remove_votable_fields('coordinates')
    assert S.get_votable_fields() == ['main_id', 'ra(d)', 'dec(d)']
    result = S.query_criteria(otype='SNR')
    assert isinstance(result, Table)
    assert 'otype=SNR' in S._last_query.data['script']


def test_simbad_settings1():
    sb = simbad.core.Simbad()
    assert sb.get_votable_fields() == ['main_id', 'coordinates']
    sb.add_votable_fields('ra', 'dec(5)')
    sb.remove_votable_fields('ra', 'dec')
    assert (sb.get_votable_fields() ==
            ['main_id', 'coordinates', 'dec(5)'])
    sb.reset_votable_fields()


def test_simbad_settings2():
    sb = simbad.core.Simbad()
    assert sb.get_votable_fields() == ['main_id', 'coordinates']
    sb.add_votable_fields('ra', 'dec(5)')
    sb.remove_votable_fields('ra', 'dec', strip_params=True)
    assert sb.get_votable_fields() == ['main_id', 'coordinates']


def test_regression_votablesettings():
    sb = simbad.Simbad()
    assert sb.get_votable_fields() == ['main_id', 'coordinates']
    sb.add_votable_fields('ra', 'dec(5)')
    # this is now allowed:
    sb.add_votable_fields('ra(d)', 'dec(d)')
    assert sb.get_votable_fields() == ['main_id', 'coordinates', 'ra',
                                       'dec(5)', 'ra(d)', 'dec(d)']
    # cleanup
    sb.remove_votable_fields('ra', 'dec', strip_params=True)
    assert sb.get_votable_fields() == ['main_id', 'coordinates']


def test_regression_votablesettings2():
    sb = simbad.Simbad()
    assert sb.get_votable_fields() == ['main_id', 'coordinates']
    sb.add_votable_fields('fluxdata(J)')
    sb.add_votable_fields('fluxdata(H)')
    sb.add_votable_fields('fluxdata(K)')
    assert (sb.get_votable_fields() ==
            ['main_id', 'coordinates',
             'fluxdata(J)', 'fluxdata(H)', 'fluxdata(K)'])
    sb.remove_votable_fields('fluxdata', strip_params=True)
    assert sb.get_votable_fields() == ['main_id', 'coordinates']


def test_regression_issue388():
    # This is a python-3 issue: content needs to be decoded?
    response = MockResponseSimbad('\nvotable {main_id,coordinates}\nvotable '
                                  'open\nquery id  m1  \nvotable close')
    with open(data_path('m1.data'), "rb") as f:
        response.content = f.read()
    parsed_table = simbad.Simbad._parse_result(response,
                                               simbad.core.SimbadVOTableResult)
    truth = b'M   1' if commons.ASTROPY_LT_4_1 else 'M   1'
    assert parsed_table['MAIN_ID'][0] == truth
    assert len(parsed_table) == 1
