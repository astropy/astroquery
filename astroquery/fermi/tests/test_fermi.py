# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os

import astropy.coordinates as coord
import pytest

from astroquery.exceptions import RemoteServiceError
from astroquery.utils.mocks import MockResponse
from ... import fermi

QUERY_ID = 'L2601082002167F48EE3069'

DATA_FILES = {'submit': 'query_submit.json',
              'status_running': 'query_status_running.json',
              'status_complete': 'query_status_complete.json',
              'status_failed': 'query_status_failed.json',
              'results': 'query_results.json'}

EXPECTED_URLS = [
    'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/test/queries/'
    'L2601082002167F48EE3069_PH00.fits',
    'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/test/queries/'
    'L2601082002167F48EE3069_SC00.fits',
]

FK5_COORDINATES = coord.SkyCoord(10.68471, 41.26875, unit=('deg', 'deg'))


def data_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


def read_data(key):
    with open(data_path(DATA_FILES[key]), 'rb') as fh:
        return fh.read()


class _Router:
    """Dispatch mocked responses on (method, url), like the real API."""

    def __init__(self, status_key='status_complete'):
        self.status_key = status_key
        self.calls = []

    def __call__(self, method, url=None, **kwargs):
        self.calls.append((method, url, kwargs))

        if method == 'POST' and url.endswith('/query'):
            return MockResponse(read_data('submit'))
        if method == 'GET' and url.endswith(f'/query/{QUERY_ID}/status'):
            return MockResponse(read_data(self.status_key))
        if method == 'GET' and url.endswith(f'/query/{QUERY_ID}/results'):
            return MockResponse(read_data('results'))

        raise AssertionError(f"unexpected request: {method} {url}")


@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")
    router = _Router()
    mp.setattr(fermi.FermiLAT, '_request', router)
    # don't sleep between status polls
    mp.setattr(fermi.FermiLAT, 'check_frequency', 0)
    return router


def test_payload_field_names():
    payload = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, searchradius=15, energyrange_MeV='100,300000',
        obsdates='772109936,787661936', timesys='MET',
        get_query_payload=True)

    assert payload == {'coordfield': '10.68472,41.26875',
                       'coordsystem': 'J2000',
                       'shapefield': 15,
                       'timefield': '772109936,787661936',
                       'timetype': 'MET',
                       'energyfield': '100,300000',
                       'photonOrExtendedOrNone': 'Photon',
                       'spacecraft': 'on'}


def test_payload_defaults_radius_to_one_degree():
    payload = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, get_query_payload=True)
    assert payload['shapefield'] == 1


def test_payload_zenithangle_only_when_given():
    payload = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, get_query_payload=True)
    assert 'zenithangle' not in payload

    payload = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, zenithangle=85, get_query_payload=True)
    assert payload['zenithangle'] == 85


def test_payload_allsky_coordinates_pass_through():
    """An all-sky query submits "0.0,0.0" without hitting a name resolver."""
    payload = fermi.core.FermiLAT.query_object_async(
        '0.0,0.0', searchradius=180,
        obsdates='2008-08-04 15:43:36,2008-08-05 09:14:33',
        get_query_payload=True)
    assert payload['coordfield'] == '0.0,0.0'
    assert payload['shapefield'] == 180


def test_payload_galactic_coordsystem():
    payload = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, coordsystem='Galactic', get_query_payload=True)
    assert payload['coordsystem'] == 'Galactic'
    lon, lat = (float(x) for x in payload['coordfield'].split(','))
    assert lon == pytest.approx(121.174, abs=0.01)
    assert lat == pytest.approx(-21.573, abs=0.01)


def test_payload_bad_coordsystem():
    with pytest.raises(ValueError, match='Unsupported coordsystem'):
        fermi.core.FermiLAT.query_object_async(
            FK5_COORDINATES, coordsystem='Ecliptic', get_query_payload=True)


def test_query_object_async_returns_query_id(patch_request):
    result = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, energyrange_MeV='1000,100000',
        obsdates='2013-01-01 00:00:00,2013-01-02 00:00:00')
    assert result == QUERY_ID

    method, url, kwargs = patch_request.calls[0]
    assert method == 'POST'
    assert url.endswith('/query')
    # the payload must go out as JSON, not as a form body
    assert kwargs['json']['coordfield'] == '10.68472,41.26875'
    assert kwargs.get('data') is None


def test_get_status(patch_request):
    status = fermi.core.FermiLAT.get_status(QUERY_ID)
    assert status['state'] == 'Query completed'


def test_list_results(patch_request):
    files = fermi.core.FermiLAT.list_results(QUERY_ID)
    assert [f['name'] for f in files] == [
        'L2601082002167F48EE3069_PH00.fits',
        'L2601082002167F48EE3069_SC00.fits']


def test_get_file_urls(patch_request):
    assert fermi.core.FermiLAT.get_file_urls(QUERY_ID) == EXPECTED_URLS


def test_query_object(patch_request):
    result = fermi.core.FermiLAT.query_object(
        FK5_COORDINATES, energyrange_MeV='1000,100000',
        obsdates='2013-01-01 00:00:00,2013-01-02 00:00:00')
    assert result == EXPECTED_URLS


def test_failed_query_raises(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(fermi.FermiLAT, '_request', _Router(status_key='status_failed'))
    mp.setattr(fermi.FermiLAT, 'check_frequency', 0)

    with pytest.raises(RemoteServiceError, match='failed with state'):
        fermi.core.FermiLAT.get_file_urls(QUERY_ID)


def test_missing_query_id_raises(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(fermi.FermiLAT, '_request',
               lambda *a, **kw: MockResponse(json.dumps({'error': 'bad'}).encode()))

    with pytest.raises(RemoteServiceError, match="did not contain a 'query_id'"):
        fermi.core.FermiLAT.query_object_async(FK5_COORDINATES)


def test_file_url_prefers_absolute_url_from_server():
    """Forward-compatible: honour an absolute URL if the API starts sending one."""
    entry = {'name': 'x_PH00.fits',
             'url': 'https://example.org/somewhere/x_PH00.fits'}
    assert fermi.core._file_url(entry) == 'https://example.org/somewhere/x_PH00.fits'


def test_bad_input_surfaces_server_error_message(request):
    """A 400 with {"error": ...} is reported, not swallowed into a bare status."""
    mp = request.getfixturevalue("monkeypatch")
    body = json.dumps({'error': 'Invalid query parameters'}).encode()
    mp.setattr(fermi.FermiLAT, '_request',
               lambda *a, **kw: MockResponse(body, status_code=400))

    with pytest.raises(RemoteServiceError,
                       match='Invalid query parameters'):
        fermi.core.FermiLAT.query_object_async(
            FK5_COORDINATES, energyrange_MeV='999999,1')
