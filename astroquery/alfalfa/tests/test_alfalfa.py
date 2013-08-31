# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import alfalfa
from astropy import coordinates

DATA_FILES = {}

class MockResponse(object):

    def __init__(self, content):
        self.content = content

@pytest.fixture
def patch_get(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'get', get_mockreturn)
    return mp

@pytest.fixture
def patch_get_readable_fileobj(request):
    @contextmanager
    def get_readable_fileobj_mockreturn(filename, **kwargs):
        file_obj = data_path(DATA_FILES['spectra']) # TODO: add images option
        yield file_obj
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(aud, 'get_readable_fileobj', get_readable_fileobj_mockreturn)
    return mp

def get_mockreturn(url, params=None, timeout=10):
    if 'SpecObjAll' in params['cmd']:
        filename = data_path(DATA_FILES['spectra_id'])
    else:
        filename = data_path(DATA_FILES['images_id'])
    content = open(filename, 'r').read()
    return MockResponse(content)

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')

def test_alfalfa_catalog(patch_get, patch_get_readable_fileobj, coords=coords):
    cat = alfalfa.core.ALFALFA.get_catalog()

def test_alfalfa_crossID(patch_get, patch_get_readable_fileobj, coords=coords):
    agc = alfalfa.core.ALFALFA.query_region(coords, optical_counterpart=True)

def test_alfalfa_spectrum(patch_get, patch_get_readable_fileobj, coords=coords):
    AGC = alfalfa.core.ALFALFA.query_region(coords, optical_counterpart=True)
    sp = alfalfa.core.ALFALFA.get_spectrum(AGC)

if __name__ == '__main__':
    test_alfalfa_catalog()
    test_alfalfa_crossID()
    test_alfalfa_spectrum()
