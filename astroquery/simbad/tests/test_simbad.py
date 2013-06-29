# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import simbad
from astropy.tests.helper import pytest, remote_data
import astropy.coordinates as coord
import astropy.units as u
from astropy.table import Table
import sys
import os
import re
import requests
is_python3 = (sys.version_info >= (3,))

GALACTIC_COORDS = coord.GalacticCoordinates(l=-67.02084, b=-29.75447, unit=(u.deg, u.deg))
ICRS_COORDS = coord.ICRSCoordinates("05h35m17.3s -05h23m28s")
FK4_COORDS = coord.FK4Coordinates(ra=84.90759, dec=-80.89403, unit=(u.deg, u.deg))
FK5_COORDS = coord.FK5Coordinates(ra=83.82207, dec=-80.86667, unit=(u.deg, u.deg))

DATA_FILES = {
              'id' : 'query_id.data',
              'coo' : 'query_coo.data',
              'cat' : 'query_cat.data',
              'bibobj' : 'query_bibobj.data',
              'bibcode' : 'query_bibcode.data'
             }


def data_path(filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp

def post_mockreturn(url, data):
    class MockResponse(object):
        query_regex = re.compile(r'query\s+([a-z]+)\s+')
        def __init__(self, script):
            self.content = self.get_content(script)

        def get_content(self, script):
            match = MockResponse.query_regex.search(script)
            if match:
                filename = DATA_FILES[match.group(1)]
                content = open(data_path(filename), "w").read()
                return content

    response = MockResponse(data['script'])
    return response

@pytest.mark.parametrize(('radius', 'expected_radius'),
                         [('5d0m0s', '5.0d'),
                          (0.432 * u.deg, '25.92m'),
                          ('0d1m12s', '1.2m'),
                          (0.003 * u.deg, '10.8s'),
                          ('0d0m15s', '15.0s')
                          ])
def test_parse_radius(radius, expected_radius):
    actual = simbad.queries._parse_radius(radius)
    assert actual == expected_radius

@pytest.mark.parametrize(('ra', 'dec', 'expected_ra', 'expected_dec'),
                         [(GALACTIC_COORDS.lonangle, GALACTIC_COORDS.latangle,
                         u'-4:28:05.00160', u'-1:59:01.07280'),
                          (ICRS_COORDS.ra, ICRS_COORDS.dec, u'5:35:17.30000',
                           u'-5:23:28.00000')
                          ])
def test_to_simbad_format(ra, dec, expected_ra, expected_dec):
    actual_ra, actual_dec = simbad.queries._to_simbad_format(ra, dec)
    assert (actual_ra, actual_dec) == (expected_ra, expected_dec)

@pytest.mark.parametrize(('coordinates', 'expected_frame'),
                         [(GALACTIC_COORDS, 'GAL'),
                          (ICRS_COORDS, 'ICRS'),
                          (FK4_COORDS, 'FK4'),
                          (FK5_COORDS, 'FK5')
                          ])
def test_get_frame_coordinates(coordinates, expected_frame):
    actual_frame = simbad.queries._get_frame_coords(coordinates)[2]
    assert actual_frame == expected_frame

def test_parse_result():
        pass

votable_fields = ",".join(simbad.queries.Simbad.VOTABLE_FIELDS)
@pytest.mark.parametrize(('args', 'kwargs', 'expected_script'),
                         [([ICRS_COORDS], dict(radius=5 * u.deg, frame='ICRS',
                                               equi=2000.0, epoch='J2000',
                                               caller='query_region_async'),
                          ("\nvotable {"+ votable_fields +"}\n"
                           "votable open\n"
                           "query coo  5:35:17.30000 -5:23:28.00000 "
                           "radius=5.0d frame=ICRS equi=2000.0 epoch=J2000 \n"
                           "votable close")),
                          (["m [0-9]"], dict(wildcard=True, caller='query_object_async'),
                           ("\nvotable {" + votable_fields  +"}\n"
                            "votable open\n"
                            "query id wildcard  m [0-9]  \n"
                            "votable close"
                            )),
                          (["2006ApJ"], dict(caller='query_bibcode_async', get_raw=True),
                           ("\n\n\nquery bibcode  2006ApJ  \n"))
                          ])
def test_args_to_payload(args, kwargs, expected_script):
    script = simbad.Simbad._args_to_payload(*args, **kwargs)['script']
    assert script == expected_script

@pytest.mark.parametrize(('bibcode', 'wildcard'),
                         [('2006ApJ*', True),
                          ('2005A&A.430.165F', None)
                          ])
def test_query_bibcode_async(bibcode, wildcard):
    response1 = simbad.queries.Simbad.query_bibcode_async(bibcode,
                                                          wildcard=wildcard)
    response2 = simbad.queries.Simbad().query_bibcode_async(bibcode,
                                                          wildcard=wildcard)
    assert response1 is not None and response2 is not None
    assert response1 == response2

def test_query_bibcode(patch_post):
    result1 = simbad.queries.Simbad.query_bibcode("2006ApJ*", wildcard=True)
    result2 = simbad.queries.Simbad.query_bibcode("2006ApJ*", wildcard=True)
    assert isinstance(result1, Table)
    assert isinstance(result2, Table)
