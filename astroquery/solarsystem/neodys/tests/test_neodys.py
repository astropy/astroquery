import pytest
import os

import numpy as np

from astroquery.utils.mocks import MockResponse
from astroquery.solarsystem.neodys import NEODySClass, NEODyS

DATA_FILE = '2018vp1_eq0.txt'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# monkeypatch replacement request function
def nonremote_request(self, request_type, url, **kwargs):
    with open(data_path(DATA_FILE), 'rb') as f:
        response = MockResponse(content=f.read(), url=url)
    return response


# use a pytest fixture to create a dummy 'requests.get' function,
# that mocks(monkeypatches) the actual 'requests.get' function:
@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(NEODySClass, '_request', nonremote_request)
    return mp


def test_neodys_query(patch_request):
    res = NEODyS.query_object(
        object_id="2018VP1", orbital_element_type='eq', epoch_near_present=0)
    np.testing.assert_allclose(res['Equinoctial State Vector'],
                               [1.5881497559198392, -0.037761493287362, 0.428349632624304, 0.018136658553998,
                                0.021742631955829, 14.9386830433394])
    assert res['Mean Julian Date'] == ['58430.299591399', 'TDT']
    assert res['Magnitude'] == [30.865, 0.15]
    np.testing.assert_allclose(
        res['Covariance Matrix'],
        [3.212371896244936e-07, -1.890888042008199e-08, 1.279370251108077e-07, 4.306149504243656e-09,
         5.180213121424896e-09, -7.806384186165599e-06, 1.113155399664521e-09, -7.5307541846631e-09,
         -2.534799484876558e-10, -3.049291243256377e-10, 4.595165457505564e-07, 5.095265031422349e-08,
         1.714984526308656e-09, 2.063091894997213e-09, -3.109000937067305e-06, 5.772527813183736e-11,
         6.944207925151111e-11, -1.04644520025806e-07, 8.353717813321847e-11, -1.258850849126041e-07,
         0.0001897040272481179])
