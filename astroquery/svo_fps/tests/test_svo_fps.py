import pytest
import os
from astropy import units as u
from requests import ReadTimeout

from astroquery.exceptions import TimeoutError, InvalidQueryError
from astroquery.utils.mocks import MockResponse
from ..core import SvoFps

DATA_FILES = {'filter_index': 'svo_fps_WavelengthEff_min=12000_WavelengthEff_max=12100.xml',
              'transmission_data': 'svo_fps_ID=2MASS.2MASS.H.xml',
              'filter_list': 'svo_fps_Facility=Keck_Instrument=NIRC2.xml',
              'zeropoint': 'svo_fps_PhotCalID=2MASS.2MASS.H.Vega.xml',
              }
TEST_LAMBDA = 12000
TEST_FILTER_ID = '2MASS/2MASS.H'
TEST_FACILITY = 'Keck'
TEST_INSTRUMENT = 'NIRC2'
TEST_MAG_SYSTEM = 'Vega'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(SvoFps, '_request', get_mockreturn)
    return mp


def get_mockreturn(method, url, params=None, timeout=10, cache=None, **kwargs):
    if ('WavelengthEff_min' in params
        and (params['WavelengthEff_min'] == TEST_LAMBDA
             and params['WavelengthEff_max'] == TEST_LAMBDA+100)):
        filename = data_path(DATA_FILES['filter_index'])
    elif ('PhotCalID' in params
          and params.get('ID') == TEST_FILTER_ID
          and params['PhotCalID'] == f'{TEST_FILTER_ID}/{TEST_MAG_SYSTEM}'):
        filename = data_path(DATA_FILES['zeropoint'])
    elif 'ID' in params and params['ID'] == TEST_FILTER_ID:
        filename = data_path(DATA_FILES['filter_index'])
    elif 'Facility' in params and (params['Facility'] == TEST_FACILITY
                                   and params['Instrument'] == TEST_INSTRUMENT):
        filename = data_path(DATA_FILES['filter_list'])
    else:
        raise NotImplementedError("Test type not implemented")

    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def test_get_filter_index(patch_get, monkeypatch):
    with pytest.raises(TypeError, match="missing 2 required positional arguments"):
        SvoFps.get_filter_index()
    lambda_min = TEST_LAMBDA*u.angstrom
    lambda_max = lambda_min + 100*u.angstrom
    table = SvoFps.get_filter_index(lambda_min, lambda_max)
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.colnames
    # Results should not depend on the unit of the wavelength: #2443. If they do then
    # `get_mockreturn` raises `NotImplementedError`.
    SvoFps.get_filter_index(lambda_min.to(u.m), lambda_max)

    def get_mockreturn_timeout(*args, **kwargs):
        raise ReadTimeout

    monkeypatch.setattr(SvoFps, '_request', get_mockreturn_timeout)
    error_msg = (
        r"^Query did not finish fast enough\. A smaller wavelength range might "
        r"succeed\. Try increasing the timeout limit if a large range is needed\.$"
    )
    with pytest.raises(TimeoutError, match=error_msg):
        SvoFps.get_filter_index(lambda_min, lambda_max)


def test_get_transmission_data(patch_get):
    table = SvoFps.get_transmission_data(TEST_FILTER_ID)
    # Check if data is fetched properly, with > 0 rows
    assert len(table) > 0


def test_get_filter_list(patch_get):
    table = SvoFps.get_filter_list(TEST_FACILITY, instrument=TEST_INSTRUMENT)
    # Check if column for Filter ID (named 'filterID') exists in table
    assert 'filterID' in table.colnames


def test_get_zeropoint(patch_get):
    zp = SvoFps.get_zeropoint(TEST_FILTER_ID, mag_system=TEST_MAG_SYSTEM)
    assert 'ZeroPoint' in zp
    assert 'MagSys' in zp
    assert zp['MagSys'] == TEST_MAG_SYSTEM
    assert 'ZeroPointType' in zp
    assert zp['ZeroPointType'] == 'Pogson'
    assert 'ZeroPointUnit' in zp
    assert zp['ZeroPoint'].unit == u.Jy


def test_invalid_query(patch_get):
    msg = 'Invalid value for parameter VERB. Allowed values are {0, 1, 2}'
    with pytest.raises(InvalidQueryError, match=msg):
        SvoFps.data_from_svo(VERB=5)
    # need this wonky regex b/c {'metadata', None} is a set and the order flips every time
    msg = r"Invalid value for parameter FORMAT\. Allowed values are \{(?=.*'metadata')(?=.*None).*\}"
    with pytest.raises(InvalidQueryError, match=msg):
        SvoFps.data_from_svo(FORMAT='silly_format')

def test_invalid_get_filter_metadata(patch_get):
    msg = 'parameter flag_system is invalid. For a description of valid query parameters see the docstring for SvoFps.data_from_svo'
    with pytest.raises(InvalidQueryError, match=msg):
        SvoFps.get_filter_metadata(TEST_FILTER_ID, flag_system='no such kwd')