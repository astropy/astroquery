import os
from xml.etree import ElementTree as ET
from astropy.tests.helper import pytest
from ...utils.testing_tools import MockResponse
from ... import open_exoplanet_catalogue as oec


@pytest.fixture(autouse=True)
def patch_urlopen(request):
    mp = request.getfuncargvalue("monkeypatch")
    try:
        import urllib.request
        mp.setattr(urllib.request, 'urlopen', get_mock_return)
    except ImportError:
        import urllib2
        mp.setattr(urllib2, 'urlopen', get_mock_return)
    return mp

def get_mock_return(url, params=None, timeout=10,**kwargs):
    # dummy function to replace urllib get functionality
    # function returns what the http request would but with local data
    filename = data_path('systems.xml.gz')
    content = open(filename, "r")
    return content

# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

def test_function(patch_urlopen):
    cata = oec.get_catalogue()
    assert len(cata.findall('.//planet')) > 0

    for planet in cata.findall(".//planet[name]"):
        if oec.findvalue(planet, 'name') == "Kepler-67 b":
            kepler67b = planet
    assert oec.findvalue(kepler67b, 'name') == "Kepler-67 b"
    assert oec.findvalue(kepler67b, 'discoverymethod') == "transit"

    kepler67 = cata.find(".//system[name]")
    for star in cata.findall(".//planet[name]"):
        if oec.findvalue(star, 'name') == "Kepler-67":
            kepler67 = star 
    assert oec.findvalue(kepler67, 'distance') == "1107"
