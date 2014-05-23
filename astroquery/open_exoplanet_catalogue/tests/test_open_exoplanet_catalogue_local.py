import os
import urllib
from xml.etree import ElementTree as ET
from astropy.tests.helper import pytest
from ...utils.testing_tools import MockResponse
from ... import open_exoplanet_catalogue as oec

@pytest.fixture(autouse=True)
def patch_urlopen(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(urllib, 'urlopen', get_mock_return)
    return mp

def get_mock_return(url, params=None, timeout=10,**kwargs):
    # dummy function to replace urllib get functionality
    # function returns what the http request would but with local data
    content = open('data/systems.xml.gz', "r").read()
    return MockResponse(content, **kwargs)

# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

def test_function(patch_urlopen):
    cata = oec.get_catalogue()
    assert len(cata.findall('.//planet')) > 0

    kepler67b =  cata.find(".//planet[name='Kepler-67 b']")
    assert kepler67b.findtext('name') == "Kepler-67 b"
    assert kepler67b.findtext('discoverymethod') == "transit"

    kepler67 = cata.find(".//system[name='Kepler-67']")
    assert kepler67.findvalue('distance') == 1107
