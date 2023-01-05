# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import requests
import os
import keyring

from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table, Column
from astropy.io.votable import parse
from astropy.io.votable.exceptions import W03, W50
from astroquery import log
import numpy as np

from astroquery.casda import Casda
from astroquery.exceptions import LoginError

try:
    from unittest.mock import Mock, MagicMock
except ImportError:
    pytest.skip("Install mock for the casda tests.", allow_module_level=True)

DATA_FILES = {'CIRCLE': 'cone.xml', 'RANGE': 'box.xml', 'DATALINK': 'datalink.xml', 'RUN_JOB': 'run_job.xml',
              'COMPLETED_JOB': 'completed_job.xml', 'DATALINK_NOACCESS': 'datalink_noaccess.xml',
              'cutout_CIRCLE_333.9092_-45.8418_0.5000': 'cutout_333.9092_-45.8418_0.5000.xml',
              'AVAILABILITY': 'availability.xml'}

USERNAME = 'user'
PASSWORD = 'password'


class MockResponse:

    def __init__(self, content):
        self.content = content
        self.text = content.decode()
        self.status_code = 200

    def raise_for_status(self):
        return


def get_mockreturn(self, method, url, data=None, timeout=10,
                   files=None, params=None, headers=None, **kwargs):
    log.debug("get_mockreturn url:{} params:{} kwargs:{}".format(url, params, kwargs))
    if kwargs and 'auth' in kwargs:
        auth = kwargs['auth']
        if auth and (auth[0] != USERNAME or auth[1] != PASSWORD):
            log.debug("Rejecting credentials")
            return create_auth_failure_response()

    if 'data/async' in str(url):
        # Responses for an asynchronous SODA job
        if str(url).endswith('data/async'):
            self.first_job_pass = True
            self.completed_job_key = "COMPLETED_JOB"
            return create_soda_create_response('111-000-111-000')
        elif str(url).endswith('/phase') and method == 'POST':
            key = "RUN_JOB"
        elif str(url).endswith('111-000-111-000/parameters') and method == 'POST':
            assert "POS" in data
            print(data['POS'])
            pos_parts = data['POS'].split(' ')
            assert len(pos_parts) == 4
            self.completed_job_key = 'cutout_{}_{:.4f}_{:.4f}_{:.4f}'.format(pos_parts[0], float(pos_parts[1]),
                                                                             float(pos_parts[2]), float(pos_parts[3]))
            return create_soda_create_response('111-000-111-000')
        elif str(url).endswith('111-000-111-000') and method == 'GET':
            key = "RUN_JOB" if self.first_job_pass else self.completed_job_key
            self.first_job_pass = False
        else:
            raise ValueError("Unexpected SODA async {} call to url {}".format(method, url))
    elif 'datalink' in str(url):
        if 'cube-244' in str(url):
            key = 'DATALINK'
        else:
            key = 'DATALINK_NOACCESS'
    elif str(url) == 'https://data.csiro.au/casda_vo_proxy/vo/tap/availability':
        key = 'AVAILABILITY'
    else:
        key = params['POS'].split()[0] if params['POS'] else None
    filename = data_path(DATA_FILES[key])
    log.debug('providing ' + filename)
    with open(filename, 'rb') as infile:
        content = infile.read()
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
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def isclose(value1, value2, abs_tol=1e-09):
    return abs(value1 - value2) < abs_tol


def fake_login(casda, username, password):
    casda.USERNAME = username
    casda._auth = (username, password)
    casda._authenticated = True


def test_login_no_default_user():
    casda = Casda()
    assert casda._authenticated is False
    assert casda.USERNAME == ''

    with pytest.raises(LoginError, match=r"If you do not pass a username to login\(\),"):
        Casda.login()

    assert casda._authenticated is False
    assert casda.USERNAME == ''
    assert hasattr(casda, '_auth') is False


@pytest.mark.skip('No keyring backend on the CI server')
def test_login_keyring(patch_get):
    casda = Casda()
    assert casda._authenticated is False
    assert casda.USERNAME == ''
    keyring.set_password("astroquery:casda.csiro.au", USERNAME, PASSWORD)

    casda.login(username=USERNAME)
    keyring.delete_password("astroquery:casda.csiro.au", USERNAME)
    assert casda._authenticated is True
    assert casda.USERNAME == USERNAME
    assert casda._auth == (USERNAME, PASSWORD)


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
    with pytest.warns(W03):
        all_records = parse(data_path('partial_unreleased.xml'), verify='warn').get_first_table().to_table()
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

    with pytest.raises(ValueError, match=r"Credentials must be supplied"):
        Casda.stage_data(table)


def test_stage_data_empty(patch_get):
    table = Table()
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    urls = casda.stage_data(table)
    assert urls == []


def test_stage_data_invalid_credentials(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-220']
    table = Table([Column(data=access_urls, name='access_url')])

    casda = Casda()
    # Update the casda object to indicate that it has been authenticated
    casda.USERNAME = USERNAME
    casda._auth = (USERNAME, 'notthepassword')
    casda._authenticated = True

    with pytest.raises(requests.exceptions.HTTPError):
        casda.stage_data(table)


def test_stage_data_no_link(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-240']
    table = Table([Column(data=access_urls, name='access_url')])
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    casda.POLL_INTERVAL = 1

    with pytest.raises(ValueError, match=r"You do not have access to any of the requested data files\."):
        casda.stage_data(table)


def test_stage_data(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-244']
    table = Table([Column(data=access_urls, name='access_url')])
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    casda.POLL_INTERVAL = 1
    with pytest.warns(W50, match="Invalid unit string 'pixels'"):
        urls = casda.stage_data(table, verbose=True)
    assert urls == ['http://casda.csiro.au/download/web/111-000-111-000/askap_img.fits.checksum',
                    'http://casda.csiro.au/download/web/111-000-111-000/askap_img.fits']


def test_cutout(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-244']
    table = Table([Column(data=access_urls, name='access_url')])
    ra = 333.9092*u.deg
    dec = -45.8418*u.deg
    radius = 30*u.arcmin
    centre = SkyCoord(ra, dec)

    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    casda.POLL_INTERVAL = 1
    with pytest.warns(W50, match="Invalid unit string 'pixels'"):
        urls = casda.cutout(table, coordinates=centre, radius=radius, verbose=True)
    assert urls == ['http://casda.csiro.au/download/web/111-000-111-000/cutout.fits.checksum',
                    'http://casda.csiro.au/download/web/111-000-111-000/cutout.fits']


def test_cutout_no_args(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-244']
    table = Table([Column(data=access_urls, name='access_url')])

    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    casda.POLL_INTERVAL = 1
    with pytest.raises(ValueError,
                       match=r"Please provide cutout parameters such as coordinates, band or channel\."):
        with pytest.warns(W50, match="Invalid unit string 'pixels'"):
            casda.cutout(table)


def test_cutout_unauthorised(patch_get):
    prefix = 'https://somewhere/casda/datalink/links?'
    access_urls = [prefix + 'cube-244']
    table = Table([Column(data=access_urls, name='access_url')])
    ra = 333.9092*u.deg
    dec = -45.8418*u.deg
    radius = 30*u.arcmin
    centre = SkyCoord(ra, dec)

    with pytest.raises(ValueError, match=r"Credentials must be supplied to download CASDA image data"):
        Casda.cutout(table, coordinates=centre, radius=radius, verbose=True)


def test_cutout_no_table(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    casda.POLL_INTERVAL = 1
    result = casda.cutout(None)
    assert result == []


def test_args_to_payload_band(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    payload = casda._args_to_payload(band=(0.195*u.m, 0.215*u.m))
    assert payload['BAND'] == '0.195 0.215'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(0.215*u.m, 0.195*u.m))
    assert payload['BAND'] == '0.195 0.215'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(0.195*u.m, 21.5*u.cm))
    assert payload['BAND'] == '0.195 0.215'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(None, 0.215*u.m))
    assert payload['BAND'] == '-Inf 0.215'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(0.195*u.m, None))
    assert payload['BAND'] == '0.195 +Inf'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(1.42*u.GHz, 1.5*u.GHz))
    assert payload['BAND'] == '0.19986163866666667 0.21112144929577467'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=np.array([1.5, 1.42])*u.GHz)
    assert payload['BAND'] == '0.19986163866666667 0.21112144929577467'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(None, 1.5*u.GHz))
    assert payload['BAND'] == '0.19986163866666667 +Inf'
    assert list(payload.keys()) == ['BAND']

    payload = casda._args_to_payload(band=(1.42*u.GHz, None))
    assert payload['BAND'] == '-Inf 0.21112144929577467'
    assert list(payload.keys()) == ['BAND']


def test_args_to_payload_band_invalid(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band='foo')
    assert "The 'band' value must be a list of 2 wavelength or frequency values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band=(0.195*u.m, 0.215*u.m, 0.3*u.m))
    assert "The 'band' value must be a list of 2 wavelength or frequency values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band=('a', 0.215*u.m))
    assert "The 'band' value must be a list of 2 wavelength or frequency values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band=(1.42*u.GHz, 21*u.cm))
    assert "The 'band' values must have the same kind of units." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band=[1.42*u.radian, 21*u.deg])
    assert "The 'band' values must be wavelengths or frequencies." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(band=(1.42*u.GHz, 1.5*u.GHz), channel=(5, 10))
    assert "Either 'channel' or 'band' values may be provided but not both." in str(excinfo.value)


def test_args_to_payload_channel(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    payload = casda._args_to_payload(channel=(0, 30))
    assert payload['CHANNEL'] == '0 30'
    assert list(payload.keys()) == ['CHANNEL']

    payload = casda._args_to_payload(channel=np.array([17, 23]))
    assert payload['CHANNEL'] == '17 23'
    assert list(payload.keys()) == ['CHANNEL']

    payload = casda._args_to_payload(channel=(23, 17))
    assert payload['CHANNEL'] == '17 23'
    assert list(payload.keys()) == ['CHANNEL']


def test_args_to_payload_channel_invalid(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(channel='one')
    assert "The 'channel' value must be a list of 2 integer values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(channel=(1.42*u.GHz, 1.5*u.GHz))
    assert "The 'channel' value must be a list of 2 integer values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(channel=(None, 5))
    assert "The 'channel' value must be a list of 2 integer values." in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        casda._args_to_payload(channel=(5))
    assert "The 'channel' value must be a list of 2 integer values." in str(excinfo.value)


def test_args_to_payload_coordinates(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    cutout_coords = SkyCoord(ra=345.245*u.degree, dec=-32.125*u.degree, frame='icrs')
    payload = casda._args_to_payload(coordinates=cutout_coords)
    assert payload['POS'].startswith('CIRCLE 345')
    pos_parts = payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), 345.245, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), -32.125, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), 1/60)
    assert len(pos_parts) == 4
    assert list(payload.keys()) == ['POS']

    cutout_coords = SkyCoord(ra=187.5*u.degree, dec=-60.0*u.degree, frame='icrs')
    payload = casda._args_to_payload(coordinates=cutout_coords, radius=900*u.arcsec)
    assert payload['POS'].startswith('CIRCLE 187')
    pos_parts = payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), 187.5, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), -60.0, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), 0.25)
    assert len(pos_parts) == 4
    assert list(payload.keys()) == ['POS']

    cutout_coords = SkyCoord(ra=187.5*u.degree, dec=-60.0*u.degree, frame='icrs')
    payload = casda._args_to_payload(coordinates=cutout_coords, width=2*u.arcmin, height=3*u.arcmin)
    assert payload['POS'].startswith('RANGE 187')
    pos_parts = payload['POS'].split(' ')
    assert pos_parts[0] == 'RANGE'
    assert isclose(float(pos_parts[1]), 187.5-1/60, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), 187.5+1/60, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), -60.0-1.5/60, abs_tol=1e-4)
    assert isclose(float(pos_parts[4]), -60.0+1.5/60, abs_tol=1e-4)
    assert len(pos_parts) == 5
    assert list(payload.keys()) == ['POS']


def test_args_to_payload_combined(patch_get):
    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)
    cutout_coords = SkyCoord(ra=187.5*u.degree, dec=-60.0*u.degree, frame='icrs')
    payload = casda._args_to_payload(coordinates=cutout_coords, channel=(17, 23))
    assert payload['POS'].startswith('CIRCLE 187')
    pos_parts = payload['POS'].split(' ')
    assert pos_parts[0] == 'CIRCLE'
    assert isclose(float(pos_parts[1]), 187.5, abs_tol=1e-4)
    assert isclose(float(pos_parts[2]), -60.0, abs_tol=1e-4)
    assert isclose(float(pos_parts[3]), 1/60)
    assert len(pos_parts) == 4
    assert payload['CHANNEL'] == '17 23'
    assert set(payload.keys()) == set(['CHANNEL', 'POS'])


def test_download_file(patch_get):
    urls = [
        'https://ingest.pawsey.org/bucket_name/path/askap_img.fits?security=stuff',
        'http://casda.csiro.au/download/web/111-000-111-000/askap_img.fits.checksum',
        'https://ingest.pawsey.org.au/casda-prd-as110-01/dc52217/primary_images/RACS-DR1_0000%2B18A.fits?security=stuff'
    ]

    casda = Casda()
    fake_login(casda, USERNAME, PASSWORD)

    # skip the actual downloading of the file
    download_mock = MagicMock()
    casda._download_file = download_mock

    filenames = casda.download_files(urls)
    assert filenames[0].endswith('askap_img.fits')
    assert filenames[1].endswith('askap_img.fits.checksum')
    assert filenames[2].endswith('RACS-DR1_0000+18A.fits')
