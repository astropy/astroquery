# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os
import re
import warnings
from shutil import copyfile
from unittest.mock import MagicMock, patch
from pathlib import Path

import astropy.units as u
import pytest
import numpy as np
from astropy.table import Table, unique
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.utils.exceptions import AstropyDeprecationWarning
from requests import HTTPError, Response

from astroquery.mast import (Catalogs, MastMissions, Observations, Tesscut, Zcut, Mast, utils, services,
                             discovery_portal, auth, core, cloud)
from astroquery.mast.cloud import CloudAccess
from astroquery.utils.mocks import MockResponse
from astroquery.exceptions import (BlankResponseWarning, InvalidQueryError, InputWarning, MaxResultsWarning,
                                   NoResultsWarning, RemoteServiceError, ResolverError, CloudAccessWarning)

try:
    from botocore.exceptions import ClientError
except ImportError:
    ClientError = BotoCoreError = ()

DATA_FILES = {'Mast.Caom.Cone': 'caom.json',
              'Mast.Name.Lookup': 'resolver.json',
              'mission_search_results': 'mission_results.json',
              'mission_columns': 'mission_columns.json',
              'mission_products': 'mission_products.json',
              'columnsconfig': 'columnsconfig.json',
              'ticcolumns': 'ticcolumns.json',
              'ticcol_filtered': 'ticcolumns_filtered.json',
              'ddcolumns': 'ddcolumns.json',
              'ddcol_filtered': 'ddcolumns_filtered.json',
              'Mast.Caom.Filtered': 'advSearch.json',
              'Mast.Caom.Filtered.Position': 'advSearchPos.json',
              'Counts': 'countsResp.json',
              'Mast.Caom.Products': 'products.json',
              'Mast.Bundle.Request': 'bundleResponse.json',
              'Mast.Caom.All': 'missions.extjs',
              'Mast.Hsc.Db.v3': 'hsc.json',
              'Mast.Hsc.Db.v2': 'hsc.json',
              'Mast.Galex.Catalog': 'hsc.json',
              'Mast.Catalogs.GaiaDR2.Cone': 'hsc.json',
              'Mast.Catalogs.GaiaDR1.Cone': 'hsc.json',
              'Mast.Catalogs.Sample.Cone': 'hsc.json',
              'Mast.Catalogs.Filtered.Tic.Rows': 'tic.json',
              'Mast.Catalogs.Filtered.Ctl.Rows': 'tic.json',
              'Mast.Catalogs.Filtered.DiskDetective.Position': 'dd.json',
              'Mast.HscMatches.Db.v3': 'matchid.json',
              'Mast.HscMatches.Db.v2': 'matchid.json',
              'Mast.HscSpectra.Db.All': 'spectra.json',
              'get_cloud_paths': 'mast_relative_path.json',
              'panstarrs': 'panstarrs.json',
              'panstarrs_columns': 'panstarrs_columns.json',
              'tess_cutout': 'astrocut_107.27_-70.0_5x5.zip',
              'tess_sector': 'tess_sector.json',
              'z_cutout_fit': 'astrocut_189.49206_62.20615_100x100px_f.zip',
              'z_cutout_jpg': 'astrocut_189.49206_62.20615_100x100px.zip',
              'z_survey': 'zcut_survey.json'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture(autouse=True)
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(utils, '_simple_request', request_mockreturn)
    mp.setattr(discovery_portal.PortalAPI, '_request', post_mockreturn)
    mp.setattr(services.ServiceAPI, '_request', service_mockreturn)
    mp.setattr(auth.MastAuth, 'session_info', session_info_mockreturn)

    mp.setattr(Tesscut, '_download_file', tesscut_download_mockreturn)
    mp.setattr(Zcut, '_download_file', zcut_download_mockreturn)
    mp.setattr(core.MastQueryWithLogin, '_download_file', download_mockreturn)

    return mp


@pytest.fixture()
def patch_boto3(monkeypatch, reset_cloud_state):
    """Fixture to patch boto3 client and resource for cloud access tests."""
    pytest.importorskip('boto3')
    mock_client = MagicMock()
    mock_client.head_object.return_value = {'ContentLength': 12345}

    mock_resource = MagicMock()
    mock_resource.Bucket.return_value.download_file.return_value = None

    monkeypatch.setattr('boto3.client', lambda *args, **kwargs: mock_client)
    monkeypatch.setattr('boto3.resource', lambda *args, **kwargs: mock_resource)

    return mock_client, mock_resource


@pytest.fixture()
def reset_cloud_state():
    """Reset the cloud dataset access state in Observations before and after each test."""
    Observations.disable_cloud_dataset()
    Observations._cloud_enabled_explicitly = None
    yield
    Observations.disable_cloud_dataset()
    Observations._cloud_enabled_explicitly = None


def post_mockreturn(self, method="POST", url=None, data=None, timeout=10, **kwargs):
    if "columnsconfig" in url:
        if "Mast.Catalogs.Tess.Cone" in data:
            service = "ticcolumns"
        elif "Mast.Catalogs.Dd.Cone" in data:
            service = "ddcolumns"
        else:
            service = 'columnsconfig'
    elif "catalogs.mast" in url:
        service = re.search(r"(\/api\/v\d*.\d*\/)(\w*)", url).group(2)
    else:
        service = re.search(r"service%22%3A%20%22([\w\.]*)%22", data).group(1)

    # Grabbing the Catalogs.all columns config calls
    if "Catalogs.All.Tic" in data or "Mast.Catalogs.Filtered.Tic.Position" in data:
        service = "ticcol_filtered"
    elif "Catalogs.All.DiskDetective" in data:
        service = "ddcol_filtered"

    # need to distiguish counts queries
    if ("Filtered" in service) and (re.search(r"COUNT_BIG%28%2A%29", data)):
        service = "Counts"
    filename = data_path(DATA_FILES[service])
    with open(filename, 'rb') as infile:
        content = infile.read()

    # returning as list because this is what the mast _request function does
    return [MockResponse(content)]


def service_mockreturn(self, method="POST", url=None, data=None, params=None, timeout=10, use_json=False, **kwargs):
    if "panstarrs" in url:
        filename = data_path(DATA_FILES["panstarrs"])
    elif "tesscut" in url:
        if "sector" in url:
            filename = data_path(DATA_FILES['tess_sector'])
        else:
            filename = data_path(DATA_FILES['tess_cutout'])
    elif "zcut" in url:
        if "survey" in url:
            filename = data_path(DATA_FILES['z_survey'])
        else:
            filename = data_path(DATA_FILES['z_cutout_fit'])
    elif use_json and 'list_products' in url:
        filename = data_path(DATA_FILES['mission_products'])
    elif use_json and data['radius'] == 300:
        filename = data_path(DATA_FILES["mission_incorrect_results"])
    elif use_json:
        filename = data_path(DATA_FILES["mission_search_results"])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content)


def request_mockreturn(url, params={}):
    if 'column_list' in url:
        filename = data_path(DATA_FILES['mission_columns'])
    elif 'mastresolver' in url:
        filename = data_path(DATA_FILES["Mast.Name.Lookup"])
    elif 'panstarrs' in url:
        filename = data_path(DATA_FILES['panstarrs_columns'])
    elif 'path_lookup' in url:
        filename = data_path(DATA_FILES['get_cloud_paths'])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content)


def download_mockreturn(*args, **kwargs):
    url = args[1]
    if 'unauthorized' in url:
        response = Response()
        response.reason = 'Unauthorized'
        response.status_code = 401
        raise HTTPError(response=response)
    return ('COMPLETE', None, None)


def session_info_mockreturn(self, silent=False):
    test_session = {'eppn': 'alice@stsci.edu',
                    'ezid': 'alice',
                    'attrib': {'uuid': '2913e6f7-e863-4f94-9416-a6af27258ba7',
                               'first_name': 'A.',
                               'last_name': 'User',
                               'display_name': 'A. User',
                               'internal': '0',
                               'email': 'alice@gmail.com',
                               'Jwstcalengdataaccess': 'false'},
                    'anon': False,
                    'scopes': ['mast:user:info', 'mast:exclusive_access'],
                    'session': None,
                    'token': '56a9cf3d...'}
    return test_session


def tesscut_get_mockreturn(method="GET", url=None, data=None, timeout=10, **kwargs):
    if "sector" in url:
        filename = data_path(DATA_FILES['tess_sector'])
    else:
        filename = data_path(DATA_FILES['tess_cutout'])

    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content)


def tesscut_download_mockreturn(url, file_path):
    filename = data_path(DATA_FILES['tess_cutout'])
    copyfile(filename, file_path)
    return


def zcut_download_mockreturn(url, file_path):
    if "jpg" in url:
        filename = data_path(DATA_FILES['z_cutout_jpg'])
    else:
        filename = data_path(DATA_FILES['z_cutout_fit'])
    copyfile(filename, file_path)
    return


###########################
# MissionSearchClass Test #
###########################


def test_missions_query_region_async():
    responses = MastMissions.query_region_async(regionCoords, radius=0.002, sci_pi_last_name='GORDON')
    assert isinstance(responses, MockResponse)


def test_missions_query_object_async():
    responses = MastMissions.query_object_async("M101", radius="0.002 deg")
    assert isinstance(responses, MockResponse)


def test_missions_query_object():
    result = MastMissions.query_object("M101", radius=".002 deg")
    assert isinstance(result, Table)
    assert len(result) > 0


def test_missions_query_region():
    result = MastMissions.query_region(regionCoords,
                                       sci_instrume=['ACS', 'WFPC'],
                                       radius=0.002 * u.deg,
                                       select_cols=['sci_pep_id'],
                                       sort_by=['sci_pep_id'])
    assert isinstance(result, Table)
    assert len(result) > 0


def test_missions_query_criteria_async():
    responses = MastMissions.query_criteria_async(
        coordinates=regionCoords,
        radius=3,
        sci_pep_id=12556,
        sci_obs_type='SPECTRUM',
        sci_instrume='stis,acs,wfc3,cos,fos,foc,nicmos,ghrs',
        sci_aec='S'
    )
    assert isinstance(responses, MockResponse)


def test_missions_query_criteria_async_with_missing_results():
    with pytest.raises(KeyError):
        responses = MastMissions.query_criteria_async(
            coordinates=regionCoords,
            radius=5,
            sci_pep_id=12556,
            sci_obs_type='SPECTRUM',
            sci_instrume='stis,acs,wfc3,cos,fos,foc,nicmos,ghrs',
            sci_aec='S',
            sci_aper_1234='WF3'
        )
        services._json_to_table(json.loads(responses), 'results')


def test_missions_query_criteria():
    result = MastMissions.query_criteria(
        coordinates=regionCoords,
        radius=3,
        sci_pep_id=[12556, 8794],
        sci_obs_type='SPECTRUM',
        sci_instrume='stis,acs,wfc3,cos,fos,foc,nicmos,ghrs',
        sci_aec='S',
        select_cols=['sci_pep_id', 'sci_instrume'],
        sort_by='sci_pep_id',
        sort_desc=True
    )
    assert isinstance(result, Table)
    assert len(result) > 0

    # Raise error if non-positional criteria is not supplied
    with pytest.raises(InvalidQueryError):
        MastMissions.query_criteria(
            coordinates=regionCoords,
            radius=3
        )

    # Raise error if invalid criteria is supplied
    with pytest.raises(InvalidQueryError):
        MastMissions.query_criteria(
            coordinates=regionCoords,
            invalid=True
        )

    # Maximum results warning
    with pytest.warns(MaxResultsWarning):
        MastMissions.query_criteria(
            coordinates=regionCoords,
            sci_aec='S',
            limit=1
        )


def test_missions_parse_select_cols():
    # Default columns
    cols = MastMissions._parse_select_cols(None)  # Default columns for HST
    assert cols is None

    # All columns
    all_cols = MastMissions._parse_select_cols('all')
    assert all_cols == MastMissions.get_column_list()['name'].value.tolist()

    # Comma-separated string
    string_cols = MastMissions._parse_select_cols('sci_pep_id, sci_instrume')
    for col in ['sci_pep_id', 'sci_instrume', 'sci_data_set_name']:
        assert col in string_cols

    # List of columns
    list_cols = MastMissions._parse_select_cols(['sci_pep_id', 'sci_instrume'])
    for col in ['sci_pep_id', 'sci_instrume', 'sci_data_set_name']:
        assert col in list_cols

    # Tuple of columns
    tuple_cols = MastMissions._parse_select_cols(('sci_pep_id', 'sci_instrume'))
    for col in ['sci_pep_id', 'sci_instrume', 'sci_data_set_name']:
        assert col in tuple_cols

    # Generator of columns
    gen_cols = MastMissions._parse_select_cols(col for col in ['sci_pep_id', 'sci_instrume'])
    for col in ['sci_pep_id', 'sci_instrume', 'sci_data_set_name']:
        assert col in gen_cols

    # Error if invalid type
    with pytest.raises(InvalidQueryError, match="`select_cols` must be an iterable of column names"):
        MastMissions._parse_select_cols(123)

    # Error if an individual column is not a string
    with pytest.raises(InvalidQueryError, match="`select_cols` must contain only strings"):
        MastMissions._parse_select_cols(['sci_pep_id', 123])

    # Warning for invalid column names
    with pytest.warns(InputWarning, match="Column 'invalid_column' not found."):
        valid_cols = MastMissions._parse_select_cols(['sci_pep_id', 'invalid_column'])
    assert 'sci_pep_id' in valid_cols
    assert 'invalid_column' not in valid_cols

    # Workaround for Ullyses mission default columns
    ullyses_mission = MastMissions(mission='ullyses')
    ullyses_cols = ullyses_mission._parse_select_cols(None)
    for col in MastMissions._default_ullyses_cols:
        assert col in ullyses_cols


def test_missions_get_product_list_async():
    # String input
    result = MastMissions.get_product_list_async('Z14Z0104T')
    assert isinstance(result, list)

    # List input
    in_datasets = ['Z14Z0104T', 'Z14Z0102T']
    result = MastMissions.get_product_list_async(in_datasets)
    assert isinstance(result, list)

    # Row input
    datasets = MastMissions.query_object("M101", radius=".002 deg")
    result = MastMissions.get_product_list_async(datasets[:3])
    assert isinstance(result, list)

    # Table input
    result = MastMissions.get_product_list_async(datasets[0])
    assert isinstance(result, list)

    # Unsupported data type for datasets
    with pytest.raises(TypeError) as err_type:
        MastMissions.get_product_list_async(1)
    assert 'Unsupported data type' in str(err_type.value)

    # Empty dataset list
    with pytest.raises(InvalidQueryError) as err_empty:
        MastMissions.get_product_list_async([' '])
    assert 'Dataset list is empty' in str(err_empty.value)

    # No dataset keyword
    with pytest.raises(InvalidQueryError, match='Dataset keyword not found for mission "invalid"'):
        missions = MastMissions(mission='invalid')
        missions.get_product_list_async(Table({'a': [1, 2, 3]}))


def test_missions_get_product_list():
    # String input
    result = MastMissions.get_product_list('Z14Z0104T')
    assert isinstance(result, Table)

    # List input
    in_datasets = ['Z14Z0104T', 'Z14Z0102T']
    result = MastMissions.get_product_list(in_datasets)
    assert isinstance(result, Table)

    # Row input
    datasets = MastMissions.query_object("M101", radius=".002 deg")
    result = MastMissions.get_product_list(datasets[:3])
    assert isinstance(result, Table)

    # Table input
    result = MastMissions.get_product_list(datasets[0])
    assert isinstance(result, Table)

    # Batching
    dataset_list = [f'{i}' for i in range(1001)]
    result = MastMissions.get_product_list(dataset_list)
    assert isinstance(result, Table)


def test_missions_get_unique_product_list(caplog):
    unique_products = MastMissions.get_unique_product_list('Z14Z0104T')
    assert isinstance(unique_products, Table)
    assert (len(unique_products) == len(unique(unique_products, keys='filename')))
    # No INFO messages should be logged
    with caplog.at_level('INFO', logger='astroquery'):
        assert caplog.text == ''


def test_missions_filter_products():
    # Filter products list by column
    products = MastMissions.get_product_list('Z14Z0104T')
    filtered = MastMissions.filter_products(products, category='CALIBRATED')
    assert isinstance(filtered, Table)
    assert all(filtered['category'] == 'CALIBRATED')

    # Filter by extension
    filtered = MastMissions.filter_products(products, extension='fits')
    assert len(filtered) > 0

    # -------- Numeric filtering tests --------
    # Single integer value
    filtered = MastMissions.filter_products(products, size=11520)
    assert all(filtered['size'] == 11520)

    # Single string value
    filtered = MastMissions.filter_products(products, size='11520')
    assert all(filtered['size'] == 11520)

    # Comparison operators
    filtered = MastMissions.filter_products(products, size='<15000')
    assert all(filtered['size'] < 15000)

    filtered = MastMissions.filter_products(products, size='>15000')
    assert all(filtered['size'] > 15000)

    filtered = MastMissions.filter_products(products, size='>=14400')
    assert all(filtered['size'] >= 14400)

    filtered = MastMissions.filter_products(products, size='<=14400')
    assert all(filtered['size'] <= 14400)

    # Range operator
    filtered = MastMissions.filter_products(products, size='14400..17280')
    assert all((filtered['size'] >= 14400) & (filtered['size'] <= 17280))

    # List of expressions
    filtered = MastMissions.filter_products(products, size=[14400, '>20000'])
    assert all((filtered['size'] == 14400) | (filtered['size'] > 20000))

    # -------- Negative operator tests --------
    # Negate a single numeric value
    filtered = MastMissions.filter_products(products, size='!11520')
    assert all(filtered['size'] != 11520)

    # Negate a comparison
    filtered = MastMissions.filter_products(products, size='!<15000')
    assert all(filtered['size'] >= 15000)

    # Negate one element in a list with one other condition
    filtered = MastMissions.filter_products(products, size=['!14400', '>20000'])
    assert all((filtered['size'] != 14400) & (filtered['size'] > 20000))

    # Negate one element in a list with two other conditions
    filtered = MastMissions.filter_products(products, size=['!14400', '<20000', '>30000'])
    assert all((filtered['size'] != 14400) & (filtered['size'] < 20000) | (filtered['size'] > 30000))

    # Negate a range
    filtered = MastMissions.filter_products(products, size='!14400..17280')
    assert all(~((filtered['size'] >= 14400) & (filtered['size'] <= 17280)))

    # Negate a string match
    filtered = MastMissions.filter_products(products, category='!calibrated')
    assert all(filtered['category'] != 'CALIBRATED')

    # Negate one string in a list
    filtered = MastMissions.filter_products(products, category=['!CALIBRATED', 'UNCALIBRATED'])
    assert all((filtered['category'] != 'CALIBRATED') & (filtered['category'] == 'UNCALIBRATED'))

    # Negate two strings in a list
    filtered = MastMissions.filter_products(products, category=['!CALIBRATED', '!UNCALIBRATED'])
    assert all((filtered['category'] != 'CALIBRATED') & (filtered['category'] != 'UNCALIBRATED'))
    # ------------------------------------------

    with pytest.raises(InvalidQueryError, match="Could not parse numeric filter 'invalid' for column 'size'"):
        # Invalid filter value
        MastMissions.filter_products(products, size='invalid')

    # Error when filtering by non-existing column
    with pytest.raises(InvalidQueryError, match="Column 'non_existing' not found in product table."):
        MastMissions.filter_products(products, non_existing='value')


def test_missions_download_products(tmp_path):
    # Check string input
    test_dataset_id = 'Z14Z0104T'
    result = MastMissions.download_products(test_dataset_id, download_dir=tmp_path)
    assert isinstance(result, Table)

    # Check Row input
    prods = MastMissions.get_product_list('Z14Z0104T')
    result = MastMissions.download_products(prods[0], download_dir=tmp_path)
    assert isinstance(result, Table)

    # JSON data input
    json_data = [{'fileset': 'r0022201004001004001_0001_wfi09_f129',
                  'filename': 'r0022201004001004001_0001_wfi09_f129_wcs.asdf'}]
    result = MastMissions.download_products(json_data, download_dir=tmp_path)
    assert isinstance(result, Table)

    # JSON file input
    json_file = tmp_path / 'products.json'
    json_file.write_text(json.dumps(json_data))
    result = MastMissions.download_products(json_file,
                                            download_dir=tmp_path)
    assert isinstance(result, Table)

    # No products to download
    with pytest.raises(InvalidQueryError, match='No products specified for download.'):
        MastMissions.download_products([], download_dir=tmp_path)

    # Product does not have proper keywords
    missing_data = [{'filename': 'r0022201004001004001_0001_wfi09_f129_wcs.asdf'}]
    with pytest.raises(InvalidQueryError, match='Data product is missing "dataset" or "fileset" field'):
        MastMissions.download_products(missing_data, download_dir=tmp_path)

    # Filters resulting in no products to download
    with pytest.warns(NoResultsWarning, match='No products to download after applying filters.'):
        MastMissions.download_products(test_dataset_id,
                                       download_dir=tmp_path,
                                       category='NON_EXISTING_CATEGORY')

    # JSON file with invalid JSON
    json_file = tmp_path / 'invalid.json'
    json_file.write_text('{ this is not valid json')
    with pytest.raises(InvalidQueryError, match="Failed to decode JSON"):
        MastMissions.download_products(json_file, download_dir=tmp_path)

    # JSON in the wrong format
    json_file = tmp_path / 'wrong_format.json'
    json_file.write_text(json.dumps({'obsid': '1', 'ra': 10.0}))
    with pytest.raises(InvalidQueryError, match="Expected a list of product rows"):
        MastMissions.download_products(json_file, download_dir=tmp_path)


@patch.object(Path, 'is_file', return_value=True)
def test_missions_download_file(mock_is_file, tmp_path):
    # JWST download
    missions = MastMissions()
    missions.mission = 'JWST'
    result = missions.download_file('jwst_test_file.fits', local_path=tmp_path)
    assert result[0] == 'COMPLETE'

    # Classy HLSP download
    missions.mission = 'Classy'
    result = missions.download_file('mast:HLSP/classy/classy_test_file.fits', local_path=tmp_path)
    assert result[0] == 'COMPLETE'

    # HLSP downloads should fail without URI
    with pytest.raises(InvalidQueryError, match='For mission "classy", a full MAST URI is required'):
        missions.download_file('classy_test_file.fits', local_path=tmp_path)


def test_missions_download_no_auth(caplog):
    # Exclusive access products should not be downloaded if user is not authenticated
    # User is not authenticated
    uri = 'unauthorized.fits'
    result = MastMissions.download_file(uri)
    assert result[0] == 'ERROR'
    assert 'HTTPError' in result[1]
    with caplog.at_level('WARNING', logger='astroquery'):
        assert 'You are not authorized to download' in caplog.text
        assert 'Please authenticate yourself' in caplog.text
    caplog.clear()

    # User is authenticated, but doesn't have proper permissions
    test_token = "56a9cf3df4c04052atest43feb87f282"
    MastMissions.login(token=test_token)
    result = MastMissions.download_file(uri)
    assert result[0] == 'ERROR'
    assert 'HTTPError' in result[1]
    with caplog.at_level('WARNING', logger='astroquery'):
        assert 'You are not authorized to download' in caplog.text
        assert 'You do not have access to download this data' in caplog.text


def test_missions_get_dataset_kwd(caplog):
    m = MastMissions()

    # Default is HST
    assert m.mission == 'hst'
    assert m.get_dataset_kwd() == 'sci_data_set_name'

    # Switch to JWST
    m.mission = 'JWST'  # case-insensitive
    assert m.mission == 'jwst'
    assert m.get_dataset_kwd() == 'fileSetName'

    # Switch to an HLSP
    m.mission = 'Classy'
    assert m.mission == 'classy'
    assert m.get_dataset_kwd() == 'Target'

    # Switch to an unknown
    m.mission = 'Unknown'
    assert m.mission == 'unknown'
    assert m.get_dataset_kwd() is None
    with caplog.at_level('WARNING', logger='astroquery'):
        assert 'The mission "unknown" does not have a known dataset ID keyword' in caplog.text


@pytest.mark.parametrize(
    'method, kwargs,',
    [['query_region', dict()],
     ['query_criteria', dict(ang_sep=0.6)]]
)
def test_missions_radius_too_large(method, kwargs):
    m = MastMissions(mission='jwst')
    coordinates = SkyCoord(0, 0, unit=u.deg)
    radius = m._max_query_radius + 0.1 * u.deg
    with pytest.raises(
        InvalidQueryError, match='Query radius too large. Must be*'
    ):
        getattr(m, method)(coordinates=coordinates, radius=radius, **kwargs)


###################
# MastClass tests #
###################


def test_list_missions():
    missions = Observations.list_missions()
    assert isinstance(missions, list)
    for m in ['HST', 'HLA', 'GALEX', 'Kepler']:
        assert m in missions


def test_mast_service_request_async():
    service = 'Mast.Name.Lookup'
    params = {'input': "M103",
              'format': 'json'}
    responses = Mast.service_request_async(service, params)

    output = responses[0].json()

    assert isinstance(responses, list)
    assert output


def test_mast_service_request():
    service = 'Mast.Caom.Cone'
    params = {'ra': 23.34086,
              'dec': 60.658,
              'radius': 0.2}
    result = Mast.service_request(service, params)

    assert isinstance(result, Table)


def test_mast_query():
    # cone search
    result = Mast.mast_query('Mast.Caom.Cone', ra=23.34086, dec=60.658, radius=0.2)
    assert isinstance(result, Table)

    # filtered search
    result = Mast.mast_query('Mast.Caom.Filtered',
                             dataproduct_type=['image', 'spectrum'],
                             proposal_pi={'Osten, Rachel A.'},
                             calib_level=np.asarray(3),
                             s_dec={'min': 43.5, 'max': 45.5},
                             columns=['proposal_pi', 's_dec', 'obs_id'])
    pp_list = result['proposal_pi']
    sd_list = result['s_dec']
    assert isinstance(result, Table)
    assert len(set(pp_list)) == 1
    assert max(sd_list) < 45.5
    assert min(sd_list) > 43.5

    # warn if columns provided for non-filtered query
    with pytest.warns(InputWarning, match="'columns' parameter is ignored"):
        Mast.mast_query('Mast.Caom.Cone', ra=23.34086, dec=60.658, radius=0.2, columns=['obs_id', 's_ra'])

    # error if no filters provided for filtered query
    with pytest.raises(InvalidQueryError, match="Please provide at least one filter."):
        Mast.mast_query('Mast.Caom.Filtered')

    # error if a full range if not provided for range filter
    with pytest.raises(InvalidQueryError,
                       match='Range filter for "s_ra" must be a dictionary with "min" and "max" keys.'):
        Mast.mast_query('Mast.Caom.Filtered', s_ra={'min': 10.0})


def test_resolve_object_single():
    obj = "TIC 307210830"
    tic_coord = SkyCoord(124.531756290083, -68.3129998725044, unit="deg")
    simbad_coord = SkyCoord(124.5317560026638, -68.3130014904408, unit="deg")

    # Resolve without a specific resolver
    obj_loc = Mast.resolve_object(obj)
    assert isinstance(obj_loc, SkyCoord)
    assert round(obj_loc.separation(tic_coord).value, 10) == 0

    # Resolve using a specific resolver and an object that belongs to a MAST catalog
    obj_loc_simbad = Mast.resolve_object(obj, resolver="SIMBAD")
    assert round(obj_loc_simbad.separation(simbad_coord).value, 10) == 0

    # Resolve using a specific resolver and an object that does not belong to a MAST catalog
    m1_coord = SkyCoord(83.6324, 22.0174, unit="deg")
    obj_loc_simbad = Mast.resolve_object("M1", resolver="SIMBAD")
    assert isinstance(obj_loc_simbad, SkyCoord)
    assert round(obj_loc_simbad.separation(m1_coord).value, 10) == 0

    # Resolve using all resolvers
    obj_loc_dict = Mast.resolve_object(obj, resolve_all=True)
    assert isinstance(obj_loc_dict, dict)
    assert round(obj_loc_dict["SIMBAD"].separation(simbad_coord).value, 10) == 0
    assert round(obj_loc_dict["TIC"].separation(tic_coord).value, 10) == 0

    # Error with invalid resolver
    with pytest.raises(ResolverError, match="Invalid resolver"):
        Mast.resolve_object(obj, resolver="invalid")

    # Error if single object cannot be resolved
    with pytest.raises(ResolverError, match='Could not resolve "nonexisting" to a sky position.'):
        Mast.resolve_object("nonexisting")

    # Error if object is not a string
    with pytest.raises(InvalidQueryError, match='All object names must be strings.'):
        Mast.resolve_object(1)

    # Error if single object cannot be resolved with given resolver
    with pytest.raises(ResolverError, match='Could not resolve "Barnard\'s Star" to a sky position using '
                       'resolver "NED".'):
        Mast.resolve_object("Barnard's Star", resolver="NED")

    # Warn if specifying both resolver and resolve_all
    with pytest.warns(InputWarning, match="The resolver parameter is ignored when resolve_all is True"):
        loc = Mast.resolve_object(obj, resolver="NED", resolve_all=True)
        assert isinstance(loc, dict)


def test_resolve_object_multi():
    objects = ["TIC 307210830", "M1", "Barnard's Star"]

    # No resolver specified
    coord_dict = Mast.resolve_object(objects)
    assert isinstance(coord_dict, dict)
    for obj in objects:
        assert obj in coord_dict
        assert isinstance(coord_dict[obj], SkyCoord)

    # Resolver specified
    coord_dict = Mast.resolve_object(objects, resolver="SIMBAD")
    assert isinstance(coord_dict, dict)
    for obj in objects:
        assert obj in coord_dict
        assert isinstance(coord_dict[obj], SkyCoord)

    # Resolve all
    coord_dict = Mast.resolve_object(objects, resolve_all=True)
    assert isinstance(coord_dict, dict)
    for obj in objects:
        assert obj in coord_dict
        obj_dict = coord_dict[obj]
        assert isinstance(obj_dict, dict)
        assert isinstance(obj_dict["SIMBAD"], SkyCoord)

    # Warn if one of the objects cannot be resolved
    with pytest.warns(InputWarning, match='Could not resolve "nonexisting" to a sky position.'):
        coord_dict = Mast.resolve_object(["M1", "nonexisting"])

    # Warn if one of the objects can't be resolved with given resolver
    with pytest.warns(InputWarning, match='Could not resolve "TIC 307210830" to a sky position using resolver "NED"'):
        Mast.resolve_object(objects[:2], resolver="NED")

    # Error if none of the objects can be resolved
    warnings.simplefilter("ignore", category=InputWarning)  # ignore warnings
    with pytest.raises(ResolverError, match='Could not resolve any of the given object names to sky positions.'):
        Mast.resolve_object(["nonexisting1", "nonexisting2"])


def test_login_logout():
    test_token = "56a9cf3df4c04052atest43feb87f282"

    Mast.login(token=test_token)
    assert Mast._authenticated is True
    assert Mast._session.cookies.get("mast_token") == test_token

    Mast.logout()
    assert Mast._authenticated is False
    assert not Mast._session.cookies.get("mast_token")


def test_session_info():
    info = Mast.session_info(verbose=False)
    assert isinstance(info, dict)
    assert info['ezid'] == 'alice'


###########################
# ObservationsClass tests #
###########################


regionCoords = SkyCoord(23.34086, 60.658, unit=('deg', 'deg'))


# query functions
def test_observations_query_region_async():
    responses = Observations.query_region_async(regionCoords, radius=0.2)
    assert isinstance(responses, list)


def test_observations_query_region():
    result = Observations.query_region(regionCoords, radius=0.2 * u.deg)
    assert isinstance(result, Table)


def test_observations_query_object_async():
    responses = Observations.query_object_async("M103", radius="0.2 deg")
    assert isinstance(responses, list)


def test_observations_query_object():
    result = Observations.query_object("M103", radius=".02 deg")
    assert isinstance(result, Table)


def test_query_observations_criteria_async():
    # without position
    responses = Observations.query_criteria_async(dataproduct_type=["image"],
                                                  proposal_pi="Ost*",
                                                  s_dec=[43.5, 45.5])
    assert isinstance(responses, list)

    # with position
    responses = Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                  objectname="M101")
    assert isinstance(responses, list)


def test_observations_query_criteria():
    # without position
    result = Observations.query_criteria(dataproduct_type=["image"],
                                         proposal_pi="Ost*",
                                         s_dec=[43.5, 45.5])
    assert isinstance(result, Table)

    # with position
    result = Observations.query_criteria(filters=["NUV", "FUV"],
                                         objectname="M101")
    assert isinstance(result, Table)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Observations.query_criteria(objectname="M101")
    assert "least one non-positional criterion" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Observations.query_criteria(objectname="M101", coordinates=regionCoords, intentType="science")
    assert "one of objectname and coordinates" in str(invalid_query.value)


# count functions
def test_observations_query_region_count():
    result = Observations.query_region_count(regionCoords, radius="0.2 deg")
    assert result == 599


def test_observations_query_object_count():
    result = Observations.query_object_count("M8", radius=0.2*u.deg)
    assert result == 599


def test_observations_query_criteria_count():
    result = Observations.query_criteria_count(dataproduct_type=["image"],
                                               proposal_pi="Ost*",
                                               s_dec=[43.5, 45.5])
    assert result == 599

    result = Observations.query_criteria_count(dataproduct_type=["image"],
                                               proposal_pi="Ost*",
                                               s_dec=[43.5, 45.5], coordinates=regionCoords)
    assert result == 599

    with pytest.raises(InvalidQueryError) as invalid_query:
        Observations.query_criteria_count(coordinates=regionCoords, objectname="M101", proposal_pi="Ost*")
    assert "one of objectname and coordinates" in str(invalid_query.value)


# product functions
def test_observations_get_product_list_async():
    responses = Observations.get_product_list_async('2003738726')
    assert isinstance(responses, list)

    responses = Observations.get_product_list_async('2003738726,3000007760')
    assert isinstance(responses, list)

    observations = Observations.query_object("M8", radius=".02 deg")
    responses = Observations.get_product_list_async(observations[0])
    assert isinstance(responses, list)

    responses = Observations.get_product_list_async(observations[0:4])
    assert isinstance(responses, list)


def test_observations_get_product_list():
    result = Observations.get_product_list('2003738726')
    assert isinstance(result, Table)

    result = Observations.get_product_list('2003738726,3000007760')
    assert isinstance(result, Table)

    observations = Observations.query_object("M8", radius=".02 deg")
    result = Observations.get_product_list(observations[0])
    assert isinstance(result, Table)

    result = Observations.get_product_list(observations[0:4])
    assert isinstance(result, Table)

    in_obsids = ['83229830', '1829332', '26074149', '24556715']
    result = Observations.get_product_list(in_obsids)
    assert isinstance(result, Table)

    # Error if no valid obsids are found
    with pytest.raises(InvalidQueryError, match='Observation list is empty'):
        Observations.get_product_list([' '])


def test_observations_filter_products():
    products = Observations.get_product_list('2003738726')
    filtered = Observations.filter_products(products,
                                            productType=["sCiEnCE"],
                                            mrp_only=False)
    assert isinstance(filtered, Table)
    assert len(filtered) == 7

    # Filter for minimum recommended products
    filtered = Observations.filter_products(products, mrp_only=True)
    assert all(filtered['productGroupDescription'] == 'Minimum Recommended Products')

    # Filter by extension
    filtered = Observations.filter_products(products, extension='FITS')
    assert len(filtered) > 0
    filtered = Observations.filter_products(products, extension=['png'])
    assert len(filtered) == 0

    # Numeric filtering
    filtered = Observations.filter_products(products, size='<50000')
    assert all(filtered['size'] < 50000)

    # Numeric filter that cannot be parsed
    with pytest.raises(InvalidQueryError, match="Could not parse numeric filter 'invalid' for column 'size'"):
        filtered = Observations.filter_products(products, size='invalid')

    # Filter by non-existing column
    with pytest.raises(InvalidQueryError, match="Column 'invalid' not found in product table."):
        Observations.filter_products(products, invalid=True)


@patch.object(Path, "is_file", return_value=True)
def test_observations_download_products(mock_is_file, patch_boto3, monkeypatch):
    mock_resource = patch_boto3[1]
    obsid = '2003738726'
    data_uri = 'mast:HST/product/u9o40504m_c3m.fits'

    # Actually download the products
    result = Observations.download_products(obsid,
                                            dataURI=data_uri)
    assert isinstance(result, Table)

    # Just get the curl script
    result = Observations.download_products(obsid,
                                            curl_flag=True,
                                            productType=["SCIENCE"],
                                            mrp_only=False)
    assert isinstance(result, Table)

    # Without console output, flat
    result = Observations.download_products(obsid,
                                            dataURI=data_uri,
                                            flat=True,
                                            verbose=False)
    assert isinstance(result, Table)

    # Passing row product
    products = Observations.get_product_list(obsid)
    result1 = Observations.download_products(products[0])
    assert isinstance(result1, Table)

    # Warn if no products to download
    with pytest.warns(NoResultsWarning, match='No products to download'):
        result = Observations.download_products(obsid, productType=["INVALID_TYPE"])
        assert result is None

    # Warn if curl_flag and flags are both set
    with pytest.warns(InputWarning, match='flat=True has no effect on curl downloads.'):
        result = Observations.download_products(obsid,
                                                curl_flag=True,
                                                flat=True)
        assert isinstance(result, Table)

    result = Observations.download_products(obsid,
                                            dataURI=data_uri)
    assert isinstance(result, Table)
    assert result[0]['Status'] == 'COMPLETE'

    # Mock cloud download failure
    Observations.enable_cloud_dataset()  # enable cloud dataset to emit warning
    client_err = ClientError({'Error': {'Code': '500', 'Message': 'Internal Server Error'}}, 'HeadObject')
    mock_resource.Bucket.return_value.download_file.side_effect = client_err
    # Warn and fall back to on-prem download
    with pytest.warns(InputWarning, match='Falling back to MAST download'):
        result = Observations.download_products(obsid, dataURI=data_uri)
    assert result[0]['Status'] == 'COMPLETE'
    # Do not fall back to on-prem download, skip instead
    with pytest.warns(NoResultsWarning, match='Skipping download.'):
        result = Observations.download_products(obsid,
                                                dataURI=data_uri,
                                                cloud_only=True)
    assert result[0]['Status'] == 'SKIPPED'

    # Products not found in cloud
    monkeypatch.setattr(Observations, 'get_cloud_uris', lambda *a, **k: {})
    with pytest.warns(NoResultsWarning, match='was not found in the cloud. Skipping download.'):
        result = Observations.download_products(obsid,
                                                dataURI=data_uri,
                                                cloud_only=True)
    assert result[0]['Status'] == 'SKIPPED'
    assert result[0]['Message'] == 'Product not found in cloud'
    # Warn and fall back to on-prem download if products not found in cloud and cloud_only is False
    with pytest.warns(InputWarning, match='was not found in the cloud. Falling back to MAST download'):
        result = Observations.download_products(obsid, dataURI=data_uri)
    assert result[0]['Status'] == 'COMPLETE'

    # Cloud access not enabled, warn if cloud_only is True
    Observations.disable_cloud_dataset()
    with pytest.warns(InputWarning, match='cloud data access is not enabled'):
        result = Observations.download_products('2003738726',
                                                dataURI='mast:HST/product/u9o40504m_c3m.fits',
                                                cloud_only=True)
    assert result[0]['Status'] == 'COMPLETE'


@patch.object(Path, "is_file", return_value=True)
def test_observations_download_file(mock_is_file, patch_boto3, tmpdir):
    mock_client, mock_resource = patch_boto3
    mock_client.head_object.return_value = {'ContentLength': 12345}
    mock_resource.Bucket.return_value.download_file.return_value = None
    mast_uri = 'mast:HST/product/u9o40504m_c3m.fits'

    result = Observations.download_file(mast_uri, local_path=tmpdir)
    assert result == ('COMPLETE', None, None)

    # Warn if both cloud_only and force_on_prem are True
    with pytest.raises(InvalidQueryError, match='Invalid argument combination'):
        result = Observations.download_file(mast_uri, cloud_only=True, force_on_prem=True)

    # Skip file if cloud_only is True but file is not in cloud
    nonexistent_uri = 'mast:HST/product/does_not_exist.fits'
    with pytest.warns(NoResultsWarning, match=f'The product {nonexistent_uri} was not found in the cloud'):
        result = Observations.download_file(nonexistent_uri, cloud_only=True)
        assert result == ('SKIPPED', None, None)

    # Use on-prem download if cloud_only is False and file is not in cloud
    Observations.enable_cloud_dataset()  # enable cloud dataset to emit warning
    with pytest.warns(InputWarning, match=f'The product {nonexistent_uri} was not found in the cloud'):
        result = Observations.download_file(nonexistent_uri, cloud_only=False)
        assert result == ('COMPLETE', None, None)

    # Error if data product is not a string
    with pytest.raises(InvalidQueryError, match='A valid data product URI'):
        Observations.download_file(12345, cloud_only=True)

    # Mock cloud download failure, fallback to on-prem
    client_err = ClientError({'Error': {'Code': '500', 'Message': 'Internal Server Error'}}, 'HeadObject')
    mock_resource.Bucket.return_value.download_file.side_effect = client_err
    with pytest.warns(InputWarning, match='Falling back to MAST download'):
        result = Observations.download_file(mast_uri)
    assert result == ('COMPLETE', None, None)

    # Skip if cloud download fails and cloud_only is True
    with pytest.warns(NoResultsWarning, match='Skipping download.'):
        result = Observations.download_file(mast_uri, cloud_only=True)
    assert result == ('SKIPPED', None, None)

    # Warning if cloud dataset is not enabled
    Observations.disable_cloud_dataset()
    with pytest.warns(InputWarning, match='cloud data access is not enabled'):
        result = Observations.download_file(mast_uri, cloud_only=True)
        assert result == ('COMPLETE', None, None)


def test_observations_download_file_not_found(patch_boto3):
    mast_uri = 'mast:HST/product/u9o40504m_c3m.fits'
    result = Observations.download_file(mast_uri)
    assert result[0] == 'ERROR'
    assert result[1] == 'File was not downloaded'

    mast_uri = 'mast:HST/product/u9o40504m_c3m.fits'
    result = Observations.download_file(mast_uri)
    assert result[0] == 'ERROR'
    assert result[1] == 'File was not downloaded'


def test_observations_list_cloud_missions(patch_boto3):
    mock_client = patch_boto3[0]
    mock_client.list_objects_v2.return_value = {
        'CommonPrefixes': [{'Prefix': 'hst/'}, {'Prefix': 'jwst/'}, {'Prefix': 'mast/'}]
    }

    supported = Observations.list_cloud_datasets()
    assert isinstance(supported, list)
    assert 'hst' in supported
    assert 'jwst' in supported
    assert 'mast' in supported


def test_observations_list_cloud_missions_error(patch_boto3):
    # Mock an error when listing objects
    mock_client = patch_boto3[0]
    client_error = ClientError({'Error': {'Code': 'AWS error'}}, 'ListObjectsV2')
    mock_client.list_objects_v2.side_effect = client_error

    supported = Observations.list_cloud_datasets()
    assert supported == []

    # Cloud access not enabled
    Observations.disable_cloud_dataset()
    with pytest.raises(RemoteServiceError, match='Please enable anonymous cloud access'):
        Observations.list_cloud_datasets()


def test_observations_get_cloud_uri(patch_boto3):
    mast_uri = 'mast:HST/product/u9o40504m_c3m.fits'
    expected = 's3://stpubdata/hst/public/u9o4/u9o40504m/u9o40504m_c3m.fits'

    # Row input
    product = Table()
    product['dataURI'] = [mast_uri]
    uri = Observations.get_cloud_uri(product[0])
    assert isinstance(uri, str)
    assert uri == expected

    # String input
    uri = Observations.get_cloud_uri(mast_uri)
    assert uri == expected

    # Warn if not found
    with pytest.warns(NoResultsWarning, match='Failed to retrieve cloud path'):
        Observations.get_cloud_uri('mast:HST/product/does_not_exist.fits')

    # Cloud access not enabled
    Observations.disable_cloud_dataset()
    with pytest.raises(RemoteServiceError, match='Please enable anonymous cloud access'):
        Observations.get_cloud_uri(mast_uri)


def test_observations_get_cloud_uris(patch_boto3):
    mast_uri = 'mast:HST/product/u9o40504m_c3m.fits'
    expected = 's3://stpubdata/hst/public/u9o4/u9o40504m/u9o40504m_c3m.fits'

    # Get the cloud URIs
    # Table input
    product = Table()
    product['dataURI'] = [mast_uri]
    uris = Observations.get_cloud_uris([mast_uri])
    assert isinstance(uris, list)
    assert len(uris) == 1
    assert uris[0] == expected

    # List input
    uris = Observations.get_cloud_uris([mast_uri])
    assert isinstance(uris, list)
    assert len(uris) == 1
    assert uris[0] == expected

    # Return full URLs
    uris = Observations.get_cloud_uris([mast_uri], include_bucket=False, full_url=True)
    assert isinstance(uris, list)
    assert uris[0].startswith('http://s3.amazonaws.com/')

    # Return a map of URIs
    uri_map = Observations.get_cloud_uris([mast_uri], return_uri_map=True)
    assert isinstance(uri_map, dict)
    assert len(uri_map) == 1
    assert uri_map[mast_uri] == expected

    # Warn if attempting to filter with list input
    with pytest.warns(InputWarning, match='Filtering is not supported'):
        Observations.get_cloud_uris([mast_uri],
                                    extension='png')

    # Warn if not found
    with pytest.warns(NoResultsWarning, match='Failed to retrieve cloud path'):
        Observations.get_cloud_uris(['mast:HST/product/does_not_exist.fits'])

    # Cloud access not enabled
    Observations.disable_cloud_dataset()
    with pytest.raises(RemoteServiceError, match='Please enable anonymous cloud access'):
        Observations.get_cloud_uris([mast_uri])


def test_observations_get_cloud_uris_error(patch_boto3):
    mock_client = patch_boto3[0]

    # Mock head_object to raise an exception
    # Raise the error if not a 404
    exc = ClientError({'Error': {'Code': '500', 'Message': 'Internal Server Error'}}, 'HeadObject')
    mock_client.head_object.side_effect = exc

    with pytest.raises(ClientError):
        Observations.get_cloud_uris(['mast:HST/product/u9o40504m_c3m.fits'])

    # Only warn if the error is a 404
    exc = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'HeadObject')
    mock_client.head_object.side_effect = exc

    with pytest.warns(NoResultsWarning, match='Failed to retrieve cloud path'):
        uris = Observations.get_cloud_uris(['mast:HST/product/u9o40504m_c3m.fits'])
    assert uris == []


def test_observations_get_cloud_uris_query(patch_boto3):
    # get uris with streamlined function
    uris = Observations.get_cloud_uris(target_name=234295610,
                                       filter_products={'productSubGroupDescription': 'C3M'})
    assert isinstance(uris, list)

    # check that InvalidQueryError is thrown if neither data_products or **criteria are defined
    with pytest.raises(InvalidQueryError):
        Observations.get_cloud_uris(filter_products={'productSubGroupDescription': 'C3M'})

    # warn if no data products match filters
    with pytest.warns(NoResultsWarning, match='No matching products'):
        Observations.get_cloud_uris(target_name=234295610,
                                    filter_products={'productSubGroupDescription': 'LC'})


def test_observations_enable_cloud_dataset(patch_boto3):
    # Enable cloud dataset
    Observations.enable_cloud_dataset()
    assert Observations._cloud_connection is not None
    assert Observations._cloud_enabled_explicitly is True

    # Force an import error when connecting to cloud dataset
    cloud.HAS_BOTO3 = False
    Observations.disable_cloud_dataset()  # reset state
    with pytest.warns(CloudAccessWarning):
        Observations.enable_cloud_dataset()

    # Reset cloud dataset state for other tests
    cloud.HAS_BOTO3 = True


def test_observations_disable_cloud_dataset(patch_boto3):
    # Explicitly disable cloud dataset
    Observations.disable_cloud_dataset()
    assert Observations._cloud_connection is None
    assert Observations._cloud_enabled_explicitly is False


######################
# CatalogClass tests #
######################


def test_catalogs_query_region_async():
    responses = Catalogs.query_region_async(regionCoords, radius=0.002)
    assert isinstance(responses, list)


def test_catalogs_fabric_query_region_async():
    responses = Catalogs.query_region_async(regionCoords, radius=0.002, catalog="panstarrs", table="mean")
    assert isinstance(responses, MockResponse)


def test_catalogs_query_region():
    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg)
    assert isinstance(result, Table)

    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="hsc", version=2)
    assert isinstance(result, Table)

    with pytest.warns(InputWarning) as i_w:
        Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="hsc", version=5)
    assert "Invalid HSC version number" in str(i_w[0].message)

    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="galex")
    assert isinstance(result, Table)

    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=2)
    assert isinstance(result, Table)

    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=1)
    assert isinstance(result, Table)

    with pytest.warns(InputWarning) as i_w:
        Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=5)
    assert "Invalid Gaia version number" in str(i_w[0].message)

    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="Sample")
    assert isinstance(result, Table)


def test_catalogs_fabric_query_region():
    result = Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="panstarrs", table="mean")
    assert isinstance(result, Table)


def test_catalogs_query_object_async():
    responses = Catalogs.query_object_async("M101", radius="0.002 deg")
    assert isinstance(responses, list)


def test_catalogs_fabric_query_object_async():
    responses = Catalogs.query_object_async("M101", radius="0.002 deg", catalog="panstarrs", table="mean")
    assert isinstance(responses, MockResponse)


def test_catalogs_query_object():
    result = Catalogs.query_object("M101", radius=".002 deg")
    assert isinstance(result, Table)


def test_catalogs_fabric_query_object():
    result = Catalogs.query_object("M101", radius=".002 deg", catalog="panstarrs", table="mean")
    assert isinstance(result, Table)


def test_catalogs_query_criteria_async():
    responses = Catalogs.query_criteria_async(catalog="Tic",
                                              Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = Catalogs.query_criteria_async(catalog="Ctl",
                                              Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = Catalogs.query_criteria_async(catalog="Tic", objectname="M10",
                                              Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = Catalogs.query_criteria_async(catalog="DiskDetective",
                                              objectname="M10", radius=2,
                                              state="complete")
    assert isinstance(responses, list)

    responses = Catalogs.query_criteria_async(catalog="panstarrs", objectname="M10", radius=2,
                                              table="mean", qualityFlag=48)
    assert isinstance(responses, MockResponse)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Catalogs.query_criteria_async(catalog="Tic")
    assert "non-positional" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Catalogs.query_criteria_async(catalog="SampleFail")
    assert "query not available" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Catalogs.query_criteria_async(catalog="panstarrs", objectname="M10", coordinates=regionCoords,
                                      objType="STAR")
    assert "one of objectname and coordinates" in str(invalid_query.value)


def test_catalogs_query_criteria():
    # without position
    result = Catalogs.query_criteria(catalog="Tic",
                                     Bmag=[30, 50], objType="STAR")

    assert isinstance(result, Table)

    result = Catalogs.query_criteria(catalog="Ctl",
                                     Bmag=[30, 50], objType="STAR")

    assert isinstance(result, Table)

    # with position
    result = Catalogs.query_criteria(catalog="DiskDetective",
                                     objectname="M10", radius=2,
                                     state="complete")
    assert isinstance(result, Table)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Catalogs.query_criteria(catalog="Tic", objectname="M10")
    assert "non-positional" in str(invalid_query.value)


def test_catalogs_query_hsc_matchid_async():
    responses = Catalogs.query_hsc_matchid_async(82371983)
    assert isinstance(responses, list)

    responses = Catalogs.query_hsc_matchid_async(82371983, version=2)
    assert isinstance(responses, list)

    with pytest.warns(InputWarning) as i_w:
        Catalogs.query_hsc_matchid_async(82371983, version=5)
    assert "Invalid HSC version number" in str(i_w[0].message)


def test_catalogs_query_hsc_matchid():
    result = Catalogs.query_hsc_matchid(82371983)
    assert isinstance(result, Table)


def test_catalogs_get_hsc_spectra_async():
    responses = Catalogs.get_hsc_spectra_async()
    assert isinstance(responses, list)


def test_catalogs_get_hsc_spectra():
    result = Catalogs.get_hsc_spectra()
    assert isinstance(result, Table)


def test_catalogs_download_hsc_spectra(tmpdir):
    allSpectra = Catalogs.get_hsc_spectra()

    # actually download the products
    result = Catalogs.download_hsc_spectra(allSpectra[10], download_dir=str(tmpdir))
    assert isinstance(result, Table)

    # just get the curl script
    result = Catalogs.download_hsc_spectra(allSpectra[20:24],
                                           download_dir=str(tmpdir), curl_flag=True)
    assert isinstance(result, Table)


######################
# TesscutClass tests #
######################

def test_tesscut_get_sector():
    coord = SkyCoord(324.24368, -27.01029, unit="deg")
    sector_table = Tesscut.get_sectors(coordinates=coord)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    sector_table = Tesscut.get_sectors(coordinates=coord, radius=0.2)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    # Exercising the search by object name
    sector_table = Tesscut.get_sectors(objectname="M103")
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    # Exercising the search by moving target
    sector_table = Tesscut.get_sectors(objectname="Ceres",
                                       moving_target=True,
                                       mt_type='small_body')
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    # Invalid queries
    # Testing catch for multiple designators'
    error_str = ("Only one of moving_target and coordinates may be specified. "
                 "Please remove coordinates if using moving_target and objectname.")
    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.get_sectors(objectname='Ceres', moving_target=True, coordinates=coord)
    assert error_str in str(invalid_query.value)

    # Error when no object name with moving target
    with pytest.raises(InvalidQueryError, match='Please specify the object name or ID'):
        Tesscut.get_sectors(moving_target=True)

    # Error when both object name and coordinates are specified
    with pytest.raises(InvalidQueryError, match='Please remove objectname if using coordinates'):
        Tesscut.get_sectors(objectname='Ceres', coordinates=coord)

    # Testing invalid queries
    # Invalid product type
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.get_sectors(objectname="M101", product="spooc")
    assert "Input product must be SPOC." in str(invalid_query.value)


def test_tesscut_download_cutouts(tmpdir):
    coord = SkyCoord(107.27, -70.0, unit="deg")

    # Testing with inflate
    manifest = Tesscut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Testing without inflate
    manifest = Tesscut.download_cutouts(coordinates=coord, size=5,
                                        path=str(tmpdir), inflate=False)
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-3:] == "zip"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Exercising the search by object name
    manifest = Tesscut.download_cutouts(objectname="M103", size=5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Exercising the search by moving target
    manifest = Tesscut.download_cutouts(objectname="Eleonora",
                                        moving_target=True,
                                        mt_type='small_body',
                                        sector=1,
                                        size=5,
                                        path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Testing catch for multiple designators'
    error_str = ("Only one of moving_target and coordinates may be specified. "
                 "Please remove coordinates if using moving_target and objectname.")

    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.download_cutouts(objectname="Eleonora",
                                 moving_target=True,
                                 coordinates=coord,
                                 size=5,
                                 path=str(tmpdir))
    assert error_str in str(invalid_query.value)

    # Testing invalid queries
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.download_cutouts(objectname="M101", product="spooc")
    assert "Input product must be SPOC." in str(invalid_query.value)


def test_tesscut_get_cutouts(tmpdir):
    coord = SkyCoord(107.27, -70.0, unit="deg")
    cutout_hdus_list = Tesscut.get_cutouts(coordinates=coord, size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Exercising the search by object name
    cutout_hdus_list = Tesscut.get_cutouts(objectname="M103", size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Exercising the search by object name
    cutout_hdus_list = Tesscut.get_cutouts(objectname='Eleonora',
                                           moving_target=True,
                                           mt_type='small_body',
                                           sector=1,
                                           size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Testing catch for multiple designators'
    error_str = ("Only one of moving_target and coordinates may be specified. "
                 "Please remove coordinates if using moving_target and objectname.")

    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.get_cutouts(objectname="Eleonora",
                            moving_target=True,
                            coordinates=coord,
                            size=5)
    assert error_str in str(invalid_query.value)

    # Testing invalid queries
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.get_cutouts(objectname="M101", product="spooc")
    assert "Input product must be SPOC." in str(invalid_query.value)


def test_tesscut_get_cutouts_mt_no_sector():
    """Test get_cutouts with moving target but no sector specified.

    When sector is not specified for moving targets, the method should
    automatically fetch available sectors and make individual requests per sector.
    """
    # Moving target without specifying sector - should automatically fetch sectors
    cutout_hdus_list = Tesscut.get_cutouts(objectname="Eleonora", moving_target=True, mt_type="small_body", size=5)
    assert isinstance(cutout_hdus_list, list)
    # Mock returns 1 sector, so we expect 1 cutout
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)


def test_tesscut_download_cutouts_mt_no_sector(tmpdir):
    """Test download_cutouts with moving target but no sector specified.

    When sector is not specified for moving targets, the method should
    automatically fetch available sectors and make individual requests per sector.
    """
    # Moving target without specifying sector - should automatically fetch sectors
    manifest = Tesscut.download_cutouts(
        objectname="Eleonora", moving_target=True, mt_type="small_body", size=5, path=str(tmpdir)
    )
    assert isinstance(manifest, Table)
    # Mock returns 1 sector, so we expect 1 file
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]["Local Path"])


def test_tesscut_get_cutouts_mt_no_sector_empty_results(monkeypatch):
    """Test get_cutouts with moving target when no sectors are available.

    When get_sectors returns an empty table, the method should warn and return an empty list.
    """
    # Mock get_sectors to return an empty Table
    empty_sector_table = Table(names=["sectorName", "sector", "camera", "ccd"], dtype=[str, int, int, int])
    monkeypatch.setattr(Tesscut, "get_sectors", lambda *args, **kwargs: empty_sector_table)

    with pytest.warns(NoResultsWarning, match="Coordinates are not in any TESS sector"):
        cutout_hdus_list = Tesscut.get_cutouts(objectname="NonExistentObject", moving_target=True, size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 0


def test_tesscut_download_cutouts_mt_no_sector_empty_results(tmpdir, monkeypatch):
    """Test download_cutouts with moving target when no sectors are available.

    When get_sectors returns an empty table, the method should warn and return an empty Table.
    """
    # Mock get_sectors to return an empty Table
    empty_sector_table = Table(names=["sectorName", "sector", "camera", "ccd"], dtype=[str, int, int, int])
    monkeypatch.setattr(Tesscut, "get_sectors", lambda *args, **kwargs: empty_sector_table)

    with pytest.warns(NoResultsWarning, match="Coordinates are not in any TESS sector"):
        manifest = Tesscut.download_cutouts(
            objectname="NonExistentObject", moving_target=True, size=5, path=str(tmpdir)
        )
    assert isinstance(manifest, Table)
    assert len(manifest) == 0


######################
# ZcutClass tests #
######################


def test_zcut_get_survey():

    coord = SkyCoord(189.49206, 62.20615, unit="deg")
    survey_list = Zcut.get_surveys(coordinates=coord)
    assert isinstance(survey_list, list)
    assert len(survey_list) == 3
    assert survey_list[0] == 'candels_gn_60mas'
    assert survey_list[1] == 'candels_gn_30mas'
    assert survey_list[2] == 'goods_north'

    survey_list = Zcut.get_surveys(coordinates=coord, radius=0.2)
    assert isinstance(survey_list, list)
    assert len(survey_list) == 3
    assert survey_list[0] == 'candels_gn_60mas'
    assert survey_list[1] == 'candels_gn_30mas'
    assert survey_list[2] == 'goods_north'


def test_zcut_download_cutouts(tmpdir):

    coord = SkyCoord(189.49206, 62.20615, unit="deg")

    # Testing with fits
    cutout_table = Zcut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 1
    assert cutout_table["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(cutout_table[0]['Local Path'])

    # Testing with png
    cutout_table = Zcut.download_cutouts(coordinates=coord, size=5,
                                         cutout_format="jpg", path=str(tmpdir))
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 3
    assert cutout_table["Local Path"][0][-4:] == ".jpg"
    assert os.path.isfile(cutout_table[0]['Local Path'])

    # Testing with img_param
    cutout_table = Zcut.download_cutouts(coordinates=coord, size=5,
                                         cutout_format="jpg", path=str(tmpdir), invert=True)
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 3
    assert cutout_table["Local Path"][0][-4:] == ".jpg"
    assert os.path.isfile(cutout_table[0]['Local Path'])


def test_zcut_get_cutouts(tmpdir):

    coord = SkyCoord(189.49206, 62.20615, unit="deg")
    cutout_list = Zcut.get_cutouts(coordinates=coord, size=5)
    assert isinstance(cutout_list, list)
    assert len(cutout_list) == 1
    assert isinstance(cutout_list[0], fits.HDUList)


################
# Utils tests #
################


def test_parse_input_location():
    # Test with coordinates
    coord = SkyCoord(23.34086, 60.658, unit="deg")
    loc = utils.parse_input_location(coordinates=coord)
    assert isinstance(loc, SkyCoord)
    assert loc.ra == coord.ra
    assert loc.dec == coord.dec

    # Test with object name
    obj_coord = SkyCoord(124.531756290083, -68.3129998725044, unit="deg")
    loc = utils.parse_input_location(objectname="TIC 307210830")
    assert isinstance(loc, SkyCoord)
    assert loc.ra == obj_coord.ra
    assert loc.dec == obj_coord.dec

    # Error if both coordinates and object name are provided
    with pytest.raises(InvalidQueryError, match="Only one of objectname and coordinates may be specified"):
        utils.parse_input_location(coordinates=coord, objectname="M101")

    # Error if neither coordinates nor object name is provided
    with pytest.raises(InvalidQueryError, match="One of objectname and coordinates must be specified"):
        utils.parse_input_location()

    # Warn if resolver is specified without an object name
    with pytest.warns(InputWarning, match="Resolver is only used when resolving object names"):
        loc = utils.parse_input_location(coordinates=coord, resolver="SIMBAD")
        assert isinstance(loc, SkyCoord)


def test_json_to_table_fallback_type_coercion():
    json_obj = {'info': [{'name': 'test_int', 'type': 'int'}],
                'data': [['1'], ['2'], ['not_an_int'], ['3'], [-999]]}

    with pytest.warns(BlankResponseWarning):
        table = services._json_to_table(json_obj)

    # Column exists
    assert 'test_int' in table.colnames
    col = table['test_int']
    assert col.dtype == np.int64

    # Good values survived
    assert col[0] == 1
    assert col[1] == 2
    assert col[3] == 3

    # Bad + ignored values are masked
    assert col.mask[2]  # 'not_an_int'
    assert col.mask[4]  # ignore_value


################
# Cloud tests #
################

def test_cloud_access_init():
    cloud.HAS_BOTO3 = False
    with pytest.raises(ImportError, match='Please install the `boto3` and `botocore` packages'):
        CloudAccess()

    # Restore the original state for other tests
    cloud.HAS_BOTO3 = True


def test_download_file_from_cloud(patch_boto3):
    mock_client, mock_resource = patch_boto3
    cloud = CloudAccess()

    mock_client.head_object.return_value = {'ContentLength': 123}
    mock_resource.Bucket.return_value.download_file.return_value = None

    cloud.download_file_from_cloud(
        "s3://stpubdata/hst/public/u9o4/u9o40504m/u9o40504m_c3m.fits",
        "local.fits",
        verbose=False
    )
    mock_resource.Bucket.return_value.download_file.assert_called_once()


def test_download_file_from_cloud_not_found(patch_boto3):
    cloud = CloudAccess()

    # Force get_cloud_uri_list to return [None]
    cloud.get_cloud_uri_list = lambda *a, **k: [None]

    with pytest.raises(RemoteServiceError, match='was not found in the cloud'):
        cloud.download_file_from_cloud("mast:HST/product/missing.fits", "local.fits")


@patch('os.path.exists', return_value=True)
@patch('os.path.getsize', return_value=123)
def test_download_file_from_cloud_existing(mock_getsize, mock_exists, patch_boto3):
    mock_client, mock_resource = patch_boto3
    mock_client.head_object.return_value = {'ContentLength': 123}
    cloud = CloudAccess()

    # File exists locally with same size
    cloud.download_file_from_cloud(
        "mast:HST/product/u9o40504m_c3m.fits",
        "local.fits",
        verbose=False
    )
    # No download should be attempted
    mock_resource.Bucket.return_value.download_file.assert_not_called()

    # File exists locally with different size
    mock_getsize.return_value = 456
    cloud.download_file_from_cloud(
        "mast:HST/product/u9o40504m_c3m.fits",
        "local.fits",
        verbose=False
    )
    # Download should be attempted
    mock_resource.Bucket.return_value.download_file.assert_called_once()


def test_download_file_from_cloud_verbose(patch_boto3):
    mock_client, mock_resource = patch_boto3
    cloud = CloudAccess()

    mock_client.head_object.return_value = {'ContentLength': 123}
    mock_resource.Bucket.return_value.download_file.return_value = None

    cloud.download_file_from_cloud(
        "s3://stpubdata/hst/public/u9o4/u9o40504m/u9o40504m_c3m.fits",
        "local.fits",
        verbose=True
    )
    # Ensure callback was supplied
    _, kwargs = mock_resource.Bucket.return_value.download_file.call_args
    assert "Callback" in kwargs
