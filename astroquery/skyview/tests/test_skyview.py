# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os.path
import types

import pytest
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError
from astropy import units as u

from astroquery.utils.mocks import MockResponse
from ...skyview import SkyView

objcoords = {"Eta Carinae": SkyCoord(ra=161.264775 * u.deg, dec=-59.6844306 * u.deg,
                                     frame="icrs")}


@pytest.fixture
def patch_fromname(request):

    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")

    def fromname(self, name, frame=None):
        if isinstance(name, str):
            return objcoords[name]
        else:
            raise NameResolveError
    mp.setattr(SkyCoord, "from_name", types.MethodType(fromname, SkyCoord))


class MockResponseSkyView(MockResponse):
    def __init__(self):
        super().__init__()

    def get_content(self):
        return self.content


class MockResponseSkyviewForm(MockResponse):
    def __init__(self, method, url, cache=False, params=None, **kwargs):
        super().__init__(**kwargs)
        self.content = self.get_content(method, url)

    def get_content(self, method, url):
        if 'basicform.pl' in url and method == 'GET':
            with open(data_path('query_page.html'), 'r') as f:
                return f.read()
        elif 'runquery.pl' in url and method == 'GET':
            with open(data_path('results.html'), 'r') as f:
                return f.read()
        else:
            raise ValueError("Invalid method/url passed to "
                             "Mock Skyview request")


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(SkyView, '_request', MockResponseSkyviewForm)
    return mp


def test_get_image_list_local(patch_get, patch_fromname):
    urls = SkyView.get_image_list(position='Eta Carinae',
                                  survey=['Fermi 5', 'HRI', 'DSS'])
    assert len(urls) == 3
    for url in urls:
        assert url.startswith('../../tempspace/fits/')


def test_survey_validation(patch_get):
    with pytest.raises(ValueError) as ex:
        SkyView.get_image_list(position='doesnt matter',
                               survey=['not_a_valid_survey'])
    assert str(ex.value) == ("Survey is not among the surveys hosted "
                             "at skyview.  See list_surveys or "
                             "survey_dict for valid surveys.")


def test_get_image_list_size(patch_get, patch_fromname):
    # Test with Quantities (as expected)
    SkyView.get_image_list(position='Eta Carinae',
                           survey='DSS',
                           width=1 * u.deg, height=1 * u.deg)
    with pytest.raises(u.UnitConversionError):
        # Test with invalid Quantities
        SkyView.get_image_list(position='Eta Carinae',
                               survey='DSS',
                               width=1, height='1 meter')
    with pytest.raises(ValueError):
        # Test with incomplete input
        SkyView.get_image_list(position='Eta Carinae',
                               survey='DSS',
                               width=1 * u.deg, height=None)
