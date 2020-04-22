# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
import requests
import os

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table, Column
from astropy.io.votable import parse
from astropy import log

from astroquery.casda import Casda

try:
    from unittest.mock import Mock, patch, PropertyMock, MagicMock
except ImportError:
    pytest.skip("Install mock for the casda tests.", allow_module_level=True)

DATA_FILES = {'CIRCLE': 'cone.xml', 'RANGE': 'box.xml', 'DATALINK': 'datalink.xml', 'RUN_JOB': 'run_job.xml',
              'COMPLETED_JOB': 'completed_job.xml'}


class MockResponse(object):

    def __init__(self, content):
        self.content = content
        self.text = content.decode()

    def raise_for_status(self):
        return


first_job_pass = True


def get_mockreturn(self, method, url, data=None, timeout=10,
                   files=None, params=None, headers=None, **kwargs):
    log.debug("get_mockreturn url:{} params:{} kwargs:{}".format(url, params, kwargs))
    if kwargs and 'auth' in kwargs:
        auth = kwargs['auth']
        if auth and (auth[0] != 'user' or auth[1] != 'password'):
            log.debug("Rejecting credentials")
            return create_auth_failure_response()

    if 'data/async' in str(url):
        # Responses for an asynchronous SODA job
        if str(url).endswith('data/async'):
            self.first_job_pass = True
            return create_soda_create_response('111-000-111-000')
        elif str(url).endswith('/phase') and method == 'POST':
            key = "RUN_JOB"
        elif str(url).endswith('111-000-111-000') and method == 'GET':
            key = "RUN_JOB" if self.first_job_pass else "COMPLETED_JOB"
            self.first_job_pass = False
        else:
            raise ValueError("Unexpected SODA async {} call to url {}".format(method, url))
    elif 'datalink' in str(url):
        key = 'DATALINK'
    else:
        key = params['POS'].split()[0] if params['POS'] else None
    filename = data_path(DATA_FILES[key])
    log.debug('providing ' + filename)
    content = open(filename, 'rb').read()
    return MockResponse(content)


def create_soda_create_response(jobid):
    job_url = 'https://casda.csiro.au/casda_data_access/data/async/' + jobid
    create_response_headers = [
        ['location', job_url]
    ]

    create_response = Mock(spec=requests.Response)
    create_response.configure_mock(status_code=303, message='OK', headers=create_response_headers, url=job_url)
    return create_response


def create_auth_failure_response():
    unauthenticated_headers = [
        ['WWW-Authenticate', 'Basic realm="ATNF OPAL Login"']
    ]
    create_response = MagicMock(spec=requests.Response)
    attrs = {'raise_for_status.side_effect': requests.exceptions.HTTPError()}
    create_response.configure_mock(status_code=401, message='OK', headers=unauthenticated_headers, **attrs)
    return create_response


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def isclose(value1, value2, abs_tol=1e-09):
    return abs(value1 - value2) < abs_tol


def test_query_region_text_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    query_payload = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=radius * u.deg, cache=False,
                                       get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 3


def test_query_region_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region(centre, radius=radius * u.deg, cache=False, get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region(centre, radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 3


def test_query_region_async_radius(patch_get):
    ra = 333.9092
    dec = -45.8418
    radius = 0.5
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region_async(centre, radius=radius * u.deg, cache=False, get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('CIRCLE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), ra, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), dec, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), radius)
    assert len(pos_parts) == 4

    responses = Casda.query_region_async(centre, radius=0.5 * u.deg, cache=False)
    assert isinstance(responses, MockResponse)


def test_query_region_box(patch_get):
    ra = 333.9092
    dec = -45.8418
    width = 0.5
    height = 0.2
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region(centre, width=width * u.deg, height=height * u.deg, cache=False,
                                       get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('RANGE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'RANGE'
    assert isclose(float(pos_parts[1]), ra - width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), ra + width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), dec - height / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[4]), dec + height / 2, abs_tol=1e-5)
    assert len(pos_parts) == 5

    responses = Casda.query_region(centre, width=width * u.deg, height=height * u.deg, cache=False)
    assert isinstance(responses, Table)
    assert len(responses) == 2


def test_query_region_async_box(patch_get):
    ra = 333.9092
    dec = -45.8418
    width = 0.5
    height = 0.2
    centre = SkyCoord(ra, dec, unit=('deg', 'deg'))
    query_payload = Casda.query_region_async(centre, width=width * u.deg, height=height * u.deg, cache=False,
                                             get_query_payload=True)
    assert isinstance(query_payload, dict)
    assert 'POS' in query_payload
    assert query_payload['POS'].startswith('RANGE 333')
    pos_parts = query_payload['POS'].split(' ')
    assert pos_parts[0] == 'RANGE'
    assert isclose(float(pos_parts[1]), ra - width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[2]), ra + width / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[3]), dec - height / 2, abs_tol=1e-5)
    assert isclose(float(pos_parts[4]), dec + height / 2, abs_tol=1e-5)
    assert len(pos_parts) == 5

    responses = Casda.query_region_async(centre, width=width * u.deg, height=height * u.deg, cache=False)
    assert isinstance(responses, MockResponse)


def test_filter_out_unreleased():
    all_records = parse(data_path('partial_unreleased.xml'), pedantic=False).get_first_table().to_table()
    assert all_records[0]['obs_release_date'] == '2017-08-02T03:51:19.728Z'
    assert all_records[1]['obs_release_date'] == '2218-01-02T16:51:00.728Z'
    assert all_records[2]['obs_release_date'] == ''
    assert len(all_records) == 3

    # This should filter out the rows with either a future obs_release_date or no obs_release_date
    filtered = Casda.filter_out_unreleased(all_records)
    assert filtered[0]['obs_release_date'] == '2017-08-02T03:51:19.728Z'
    assert filtered[0]['obs_publisher_did'] == 'cube-502'
    assert len(filtered) == 1


def test_stage_data_unauthorised(patch_get):
    table = Table()

    with pytest.raises(ValueError) as excinfo:
        Casda.stage_data(table)

    assert "Credentials must be supplied" in str(excinfo.value)


def test_stage_data_empty(patch_get):
    table = Table()
    casda = Casda('user', 'password')
    urls = casda.stage_data(table)
    assert urls == []


def test_stage_data_invalid_credentials(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-220']
    table = Table([Column(data=access_urls, name='access_url')])

    casda = Casda('user', 'notthepassword')
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        casda.stage_data(table)


def test_stage_data(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-244']
    table = Table([Column(data=access_urls, name='access_url')])
    casda = Casda('user', 'password')
    casda.POLL_INTERVAL = 1
    urls = casda.stage_data(table, verbose=True)
    assert urls == ['http://casda.csiro.au/download/web/111-000-111-000/askap_img.fits.checksum',
                    'http://casda.csiro.au/download/web/111-000-111-000/askap_img.fits']
