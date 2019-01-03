# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import pytest

from astropy import coordinates as coord
from astropy import units as u
from astropy.table import Table

from astroquery.utils.mocks import MockResponse
from astroquery.herschel import higal
from astroquery.herschel.higal.core import HiGalClass


DATA_FILES = {
    ('GET', 'https://tools.ssdc.asi.it/MMCAjaxFunction'): 'catalog_blue.json',
    ('GET', 'https://tools.ssdc.asi.it/HiGALSearch.jsp'): 'frontpage.html',
    ('POST', 'https://tools.ssdc.asi.it/HiGALSearch.jsp'): 'cutout_page.html',
}


def data_path(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


def nonremote_request(self, request_type, url, **kwargs):
    with open(data_path(DATA_FILES[(request_type, url)]), 'rb') as f:
        return MockResponse(content=f.read(), url=url)


@pytest.fixture
def patch_request(monkeypatch):
    monkeypatch.setattr(HiGalClass, '_request', nonremote_request)


class FakeCookie:
    def __init__(self, name='JSESSIONID', path='/', domain=''):
        self.name = name
        self.path = path
        self.domain = domain


class FakeCookieJar(list):
    def values(self):
        return self

    def clear(self, *args, **kwargs):
        return


@pytest.fixture
def hg(patch_request):
    """A HiGalClass instance with a pre-seeded fake session, so the lazy
    session-bootstrap code in `_args_to_payload` is skipped."""
    instance = HiGalClass()
    instance._session.cookies = FakeCookieJar([FakeCookie(), FakeCookie()])
    instance._session_id = 'fake-session-id'
    return instance


def test_args_to_payload_catalog(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    payload = hg._args_to_payload(coords=target, radius=10*u.arcmin,
                                  catalog_id=4047, catalog_query=True)
    assert payload['mission'] == 'Hi-GAL'
    assert payload['action'] == 'getMMCCatalogData'
    assert payload['catalogId'] == 4047
    assert payload['radius'] == '10.0'


def test_args_to_payload_cutout(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    payload = hg._args_to_payload(coords=target, radius=10*u.arcmin,
                                  catalog_query=False)
    assert payload['HIGAL'] == 'HIGAL'
    assert payload['radiusInput'] == '10.0'
    assert payload['sessionId'] == 'fake-session-id'
    assert payload['coordsType'] == 'RADEC'
    assert payload['catalog'] == [4047, 4048, 4049, 4050, 4051]


def test_query_region_catalog(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    result = hg.query_region(coordinates=target, radius=0.25*u.deg,
                             catalog='blue', catalog_query=True)
    assert isinstance(result, Table)
    assert len(result) == 2
    assert 'DESIGNATION' in result.colnames
    assert result['DESIGNATION'][0] == 'HIGALPB049.5000-0.3000'


def test_query_region_get_query_payload(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    payload = hg.query_region(coordinates=target, radius=0.25*u.deg,
                              catalog='blue', catalog_query=True,
                              get_query_payload=True)
    assert payload['catalogId'] == higal.core.HiGal.HIGAL_CATALOGS['blue']


def test_invalid_catalog_name(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    with pytest.raises(KeyError):
        hg.query_region(coordinates=target, radius=0.25*u.deg,
                        catalog='bogus', catalog_query=True)


def test_get_image_list(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    image_list = hg.get_image_list(target, radius=3*u.arcmin)
    # the cutout page contains all 5 wavelengths
    assert len(image_list) == 5
    # filenames had .jpeg → translated to .fits
    for url in image_list:
        assert url.endswith('.fits')
        assert url.startswith('https://tools.ssdc.asi.it/')
    # ordering follows HIGAL_CATALOGS dict ordering
    assert 'blue' in image_list[0]


def test_get_image_list_get_query_payload(hg):
    target = coord.SkyCoord(49.5, -0.3, frame='galactic',
                            unit=(u.deg, u.deg))
    payload = hg.get_image_list(target, radius=3*u.arcmin,
                                get_query_payload=True)
    assert payload == {}
