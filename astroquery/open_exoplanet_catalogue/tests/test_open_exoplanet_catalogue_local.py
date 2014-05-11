


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
def patch_get(request):
	# create a mock request
        mp = request.getfuncargvalue("monkeypatch")
        mp.setattr(urllib2, "urlopen", get_mock_return)
        return mp


def get_mock_return(url, params=None, timeout=10,**kwargs):
	# dummy function to replace urllib2 get functionality
	# function returns what the http request would but with local data
	filename = url[url.rfind("/"):]
	content = open(filename, "r").read()
        return MockResponse(content, **kwargs)

def test_function():
    with pytest.raises(TypeError):
        xml = oec.query_system_xml("krypton") # testing imaginary system

    kepler67b = oec.query_planet('Kepler-67 b') # Return value is a python dictionary.
    assert kepler67b['name'] == "Kepler-67 b"
    assert kepler67b['discoverymethod'] == "transit"

    kepler67 = oec.query_system_to_obj('Kepler-67') # Return value is a System object 
    assert kepler67.distance == 1107

    kepler67bsys = oec.query_planet_to_obj('Kepler-67 b')
    assert kepler67bsys.name[0] == "Kepler-67 b"
    assert kepler67bsys.discoverymethod == "transit"
