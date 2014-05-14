


from ...utils.testing_tools import MockResponse 
from ... import open_exoplanet_catalogue as oec
from astropy.tests.helper import pytest
from xml.etree import ElementTree as ET
import os
import urllib2

# get file path of a static data file for testing
def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_quote():
    urllib2.quote = get_mock_quote

@pytest.fixture
def patch_get():
    # create a mock request
    urllib2.urlopen = get_mock_return

def get_mock_quote(system):
    return system

def get_mock_return(url, params=None, timeout=10,**kwargs):
    # dummy function to replace urllib2 get functionality
    # function returns what the http request would but with local data
    filename = url[url.rfind("/")+1:]
    content = open(data_path(filename), "r")
    return content


def test_function():
    patch_quote()
    patch_get()
    cata = oec.get_catalogue()
    assert len(cata.findall('.//planet')) > 0

    for planet in cata.findall(".//planet[name='Kepler-67 b']"):
        kepler67b = planet
    assert kepler67b.findtext('name') == "Kepler-67 b"
    assert kepler67b.findtext('discoverymethod') == "transit"

    for sys in cata.findall(".//system[name='Kepler-67']"):
        kepler67 = sys
    assert kepler67.findvalue('distance') == 1107
