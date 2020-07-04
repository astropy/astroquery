import pytest
import os
from astropy import units as u

from ...utils.testing_tools import MockResponse
from ..core import SvoFps

DATA_FILES = {'filter_index': 'svo_fps_WavelengthEff_min=12000_WavelengthEff_max=12100.xml',
              'transmission_data': 'svo_fps_ID=2MASS.2MASS.H.xml',
              'filter_list': 'svo_fps_Facility=Keck_Instrument=NIRC2.xml'
              }
TEST_LAMBDA = 12000
TEST_FILTER_ID = '2MASS/2MASS.H'
TEST_FACILITY = 'Keck'
TEST_INSTRUMENT = 'NIRC2'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(SvoFps, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=None, **kwargs):
    if ('WavelengthEff_min' in params and
        (params['WavelengthEff_min'] == TEST_LAMBDA and
         params['WavelengthEff_max'] == TEST_LAMBDA+100)):
        filename = data_path(DATA_FILES['filter_index'])
    elif 'ID' in params and params['ID'] == TEST_FILTER_ID:
        filename = data_path(DATA_FILES['filter_index'])
    elif 'Facility' in params and (params['Facility'] == TEST_FACILITY and
                                   params['Instrument'] == TEST_INSTRUMENT):
        filename = data_path(DATA_FILES['filter_list'])
    else:
        raise NotImplementedError("Test type not implemented")

    content = open(filename, 'rb').read()
    return MockResponse(content, **kwargs)


def test_get_filter_index(patch_get):
    table = SvoFps.get_filter_index(TEST_LAMBDA*u.angstrom, (TEST_LAMBDA+100)*u.angstrom)
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.colnames


def test_get_transmission_data(patch_get):
    table = SvoFps.get_transmission_data(TEST_FILTER_ID)
    # Check if data is fetched properly, with > 0 rows
    assert len(table) > 0


def test_get_filter_list(patch_get):
    table = SvoFps.get_filter_list(TEST_FACILITY, TEST_INSTRUMENT)
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.colnames
