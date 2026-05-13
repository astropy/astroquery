# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os
import re
import warnings
from datetime import datetime
from pathlib import Path
from shutil import copyfile
from unittest.mock import MagicMock, patch

import astropy.units as u
import numpy as np
import pytest
from astropy.coordinates import Angle, SkyCoord
from astropy.io import fits
from astropy.io.votable import parse
from astropy.table import Table, unique
from astropy.time import Time
from astropy.utils.exceptions import AstropyDeprecationWarning
from pyvo.dal import TAPResults
from pyvo.dal.exceptions import DALQueryError
from pyvo.io.vosi import parse_capabilities
from requests import HTTPError, Response

from astroquery.exceptions import (
    BlankResponseWarning,
    InputWarning,
    InvalidQueryError,
    MaxResultsWarning,
    NoResultsWarning,
    RemoteServiceError,
    ResolverError,
)
from astroquery.mast import (
    Catalogs,
    Mast,
    MastMissions,
    Observations,
    Tesscut,
    Zcut,
    auth,
    cloud,
    core,
    discovery_portal,
    services,
    utils,
)
from astroquery.mast.cloud import CloudAccess
from astroquery.utils.mocks import MockResponse

from ..catalog_collection import DEFAULT_CATALOGS, CatalogCollection, CatalogMetadata

try:
    # Optional dependency import for cloud access functionality
    from botocore.exceptions import ClientError
except ImportError:
    pass

try:
    # Optional dependency import for region handling in collections queries
    from regions import CirclePixelRegion, CircleSkyRegion, PixCoord, PolygonSkyRegion
    HAS_REGIONS = True
except ImportError:
    HAS_REGIONS = False

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
              'tap_collections': 'tap_collections.json',  # Collections available
              'tap_catalogs': 'tap_catalogs.vot',  # Catalogs for TIC
              'tap_columns': 'tap_columns.vot',  # Column metadata
              'tap_capabilities': 'tap_capabilities.xml',  # TAP service capabilities
              'tap_results': 'tap_results.vot',  # Results of a TAP query
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
    mp.setattr(
        'astroquery.mast.catalog_collection.TAPService',
        lambda *args, **kwargs: vo_tap_mock()
    )

    mp.setattr(Tesscut, '_download_file', tesscut_download_mockreturn)
    mp.setattr(Zcut, '_download_file', zcut_download_mockreturn)
    mp.setattr(core.MastQueryWithLogin, '_download_file', download_mockreturn)

    return mp


@pytest.fixture
def patch_tap(request, reset_catalogs_cache):
    mp = request.getfixturevalue("monkeypatch")

    mock_tap = vo_tap_mock()
    mp.setattr(
        'astroquery.mast.catalog_collection.TAPService',
        lambda *args, **kwargs: mock_tap
    )
    # We have to set this because CatalogsClass uses a simple request to get collections
    mp.setattr(utils, '_simple_request', request_mockreturn)

    return mock_tap


@pytest.fixture
def reset_catalogs_cache():
    Catalogs._collections_cache.clear()
    yield


def get_patch_tap_query(patch_tap):
    args, _ = patch_tap.run_sync.call_args
    query = args[0]
    return query


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
    elif 'vo-tap' in url:
        filename = data_path(DATA_FILES['tap_collections'])
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


def vo_tap_mock():
    def run_sync_mock(query, **kwargs):
        if 'invalid' in query:
            # Use this when wanting to simulate a DALQueryError
            # Where it occurs will depend on where you pass it (collection, catalog, parameter, etc.)
            raise DALQueryError('Simulated TAP query error for testing.')
        elif 'tap_schema.tables' in query:
            # Queries to get catalogs
            filename = data_path(DATA_FILES['tap_catalogs'])
        elif 'tap_schema.columns' in query:
            # Queries to get column metadata
            filename = data_path(DATA_FILES['tap_columns'])
        elif 'WHERE' in query:
            # Queries with results, keep in mind this is not meaningful and results won't match the query
            filename = data_path(DATA_FILES['tap_results'])
        votable = parse(filename)

        if 'empty' in query:
            # Simulate a query that returns no results by clearing the resources in the votable
            for resource in votable.resources:
                for table in resource.tables:
                    table.array = np.array([])  # Clear the data to simulate no results

        return TAPResults(votable)

    # Mock TAPService
    mock_tap = MagicMock()
    mock_tap.run_sync.side_effect = run_sync_mock

    # Capabilities -> Not much to do here
    filename = data_path(DATA_FILES['tap_capabilities'])
    with open(filename, "rb") as f:
        caps = parse_capabilities(f)
    mock_tap.capabilities = caps

    return mock_tap

###########################
# MissionSearchClass Test #
###########################


def test_missions_query_region_async(patch_post):
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
    # Check that metadata for search criteria is included in the result
    assert result.meta
    # Check that column metadata is included
    assert 'description' in result['sci_pep_id'].meta
    assert 'description' in result['sci_instrume'].meta

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


def test_missions_parse_multiple_targets():
    # Single coordinate object
    coord = SkyCoord(10.684, 41.269, unit='deg')
    result = MastMissions._parse_multiple_targets(coordinates=coord)
    assert result == ['10.684 41.269']

    # Single coordinate string
    result = MastMissions._parse_multiple_targets(coordinates="10.684 41.269")
    assert result == ['10.684 41.269']

    # List of coordinate objects
    coords = [SkyCoord(10.684, 41.269, unit='deg'), SkyCoord(83.6331, 22.0145, unit='deg')]
    result = MastMissions._parse_multiple_targets(coordinates=coords)
    assert result == ['10.684 41.269', '83.6331 22.0145']

    # String list of coordinates
    coords_str = "10.684 41.269, 83.6331 22.0145"
    result = MastMissions._parse_multiple_targets(coordinates=coords_str)
    assert result == ['10.684 41.269', '83.6331 22.0145']

    # Special case: one string coordinate with elements separated by a comma instead of space
    coords_str_comma = "10.684, 41.269"
    result = MastMissions._parse_multiple_targets(coordinates=coords_str_comma)
    assert result == ['10.684 41.269']

    # Vector SkyCoord input
    vector_coords = SkyCoord([10.684, 83.6324], [41.269, 22.0174], frame='icrs', unit='deg')
    result = MastMissions._parse_multiple_targets(coordinates=vector_coords)
    assert result == ['10.684 41.269', '83.6324 22.0174']

    # Single object name
    result = MastMissions._parse_multiple_targets(object_names="M101")
    assert result == ['210.802429 54.34875']

    # List of object names
    result = MastMissions._parse_multiple_targets(object_names=["M101", "M1"])
    assert result == ['210.802429 54.34875', '83.6324 22.0174']

    # Both coordinates and object names provided
    result = MastMissions._parse_multiple_targets(coordinates="10.684 41.269", object_names="M101")
    assert result == ['10.684 41.269', '210.802429 54.34875']

    # No targets provided
    with pytest.raises(InvalidQueryError, match="No targets were provided."):
        result = MastMissions._parse_multiple_targets()

    # Number of targets exceeds maximum
    with pytest.raises(InvalidQueryError, match="Too many input targets provided."):
        MastMissions._parse_multiple_targets(coordinates=["10.684 41.269"] * 101)

    # Invalid object name
    with pytest.warns(InputWarning, match='Could not resolve "invalid_object".'):
        MastMissions._parse_multiple_targets(object_names=["M1", "invalid_object"])

    # Only invalid object names
    with pytest.raises(ResolverError, match='Could not resolve "invalid_object"'):
        MastMissions._parse_multiple_targets(object_names=["invalid_object"])


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

    # Provide the mission to the method
    result = missions.download_file('mast:HLSP/ullyses/ullyses_test_file.fits', local_path=tmp_path, mission='ullyses')
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
                                                  object_name="M101")
    assert isinstance(responses, list)


def test_observations_query_criteria():
    # without position
    result = Observations.query_criteria(dataproduct_type=["image"],
                                         proposal_pi="Ost*",
                                         s_dec=[43.5, 45.5])
    assert isinstance(result, Table)

    # with position
    result = Observations.query_criteria(filters=["NUV", "FUV"],
                                         object_name="M101")
    assert isinstance(result, Table)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Observations.query_criteria(object_name="M101")
    assert "least one non-positional criterion" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        Observations.query_criteria(object_name="M101", coordinates=regionCoords, intentType="science")
    assert "one of object_name and coordinates" in str(invalid_query.value)


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
        Observations.query_criteria_count(coordinates=regionCoords, object_name="M101", proposal_pi="Ost*")
    assert "one of object_name and coordinates" in str(invalid_query.value)


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
def test_observations_download_products(mock_is_file, patch_boto3, monkeypatch, tmpdir):
    mock_resource = patch_boto3[1]
    obsid = '2003738726'
    data_uri = 'mast:HST/product/u9o40504m_c3m.fits'

    # Actually download the products
    result = Observations.download_products(obsid,
                                            dataURI=data_uri,
                                            download_dir=tmpdir)
    assert isinstance(result, Table)

    # Just get the curl script
    result = Observations.download_products(obsid,
                                            curl_flag=True,
                                            productType=["SCIENCE"],
                                            mrp_only=False,
                                            download_dir=tmpdir)
    assert isinstance(result, Table)

    # Without console output, flat
    result = Observations.download_products(obsid,
                                            dataURI=data_uri,
                                            flat=True,
                                            verbose=False,
                                            download_dir=tmpdir)
    assert isinstance(result, Table)

    # Passing row product
    products = Observations.get_product_list(obsid)
    result1 = Observations.download_products(products[0], download_dir=tmpdir)
    assert isinstance(result1, Table)

    # Warn if no products to download
    with pytest.warns(NoResultsWarning, match='No products to download'):
        result = Observations.download_products(obsid, productType=["INVALID_TYPE"], download_dir=tmpdir)
        assert result is None

    # Warn if curl_flag and flags are both set
    with pytest.warns(InputWarning, match='flat=True has no effect on curl downloads.'):
        result = Observations.download_products(obsid,
                                                curl_flag=True,
                                                flat=True,
                                                download_dir=tmpdir)
        assert isinstance(result, Table)

    result = Observations.download_products(obsid,
                                            dataURI=data_uri,
                                            download_dir=tmpdir)
    assert isinstance(result, Table)
    assert result[0]['Status'] == 'COMPLETE'

    # Mock cloud download failure
    Observations.enable_cloud_dataset()  # enable cloud dataset to emit warning
    client_err = ClientError({'Error': {'Code': '500', 'Message': 'Internal Server Error'}}, 'HeadObject')
    mock_resource.Bucket.return_value.download_file.side_effect = client_err
    # Warn and fall back to on-prem download
    with pytest.warns(InputWarning, match='Falling back to MAST download'):
        result = Observations.download_products(obsid, dataURI=data_uri, download_dir=tmpdir)
    assert result[0]['Status'] == 'COMPLETE'
    # Do not fall back to on-prem download, skip instead
    with pytest.warns(NoResultsWarning, match='Skipping download.'):
        result = Observations.download_products(obsid,
                                                dataURI=data_uri,
                                                cloud_only=True,
                                                download_dir=tmpdir)
    assert result[0]['Status'] == 'SKIPPED'

    # Products not found in cloud
    monkeypatch.setattr(Observations, 'get_cloud_uris', lambda *a, **k: {})
    with pytest.warns(NoResultsWarning, match='was not found in the cloud. Skipping download.'):
        result = Observations.download_products(obsid,
                                                dataURI=data_uri,
                                                cloud_only=True,
                                                download_dir=tmpdir)
    assert result[0]['Status'] == 'SKIPPED'
    assert result[0]['Message'] == 'Product not found in cloud'
    # Warn and fall back to on-prem download if products not found in cloud and cloud_only is False
    with pytest.warns(InputWarning, match='was not found in the cloud. Falling back to MAST download'):
        result = Observations.download_products(obsid, dataURI=data_uri, download_dir=tmpdir)
    assert result[0]['Status'] == 'COMPLETE'

    # Cloud access not enabled, warn if cloud_only is True
    Observations.disable_cloud_dataset()
    with pytest.warns(InputWarning, match='cloud data access is not enabled'):
        result = Observations.download_products('2003738726',
                                                dataURI='mast:HST/product/u9o40504m_c3m.fits',
                                                cloud_only=True,
                                                download_dir=tmpdir)
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
    with pytest.raises(RemoteServiceError, match='Cloud data access is not enabled.'):
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
    with pytest.raises(RemoteServiceError, match='Cloud data access is not enabled.'):
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
    with pytest.raises(RemoteServiceError, match='Cloud data access is not enabled.'):
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
    with pytest.raises(ImportError, match='to enable cloud dataset access'):
        Observations.enable_cloud_dataset()

    # Reset cloud dataset state for other tests
    cloud.HAS_BOTO3 = True


def test_observations_disable_cloud_dataset(patch_boto3):
    # Explicitly disable cloud dataset
    Observations.disable_cloud_dataset()
    assert Observations._cloud_connection is None
    assert Observations._cloud_enabled_explicitly is False


#######################
# CatalogsClass tests #
#######################


def test_catalogs_attributes(patch_tap):
    Catalogs.query_criteria(
        collection="tic",
        region="Circle ICRS 202.4656816 +47.1999842 0.04",
        radius=0.002 * u.deg,
        offset=1,
        sort_by="ra",
    )
    # Should not change after query
    assert Catalogs.collection == "hsc"
    assert Catalogs.catalog == "dbo.SumMagAper2CatView"


def test_catalogs_get_catalogs(patch_tap):
    catalogs = Catalogs.get_catalogs("tic")
    assert isinstance(catalogs, Table)


def test_catalogs_get_column_metadata(patch_tap):
    metadata = Catalogs.get_column_metadata(collection="tic")
    assert isinstance(metadata, Table)


def test_catalogs_query_criteria(patch_tap):
    # Coordinates
    result = Catalogs.query_criteria(
        collection="tic",
        coordinates=regionCoords,
        radius=0.002 * u.deg,
        limit=2,
    )

    assert isinstance(result, Table)
    assert len(result) > 0
    assert "dec" in result.colnames
    query = get_patch_tap_query(patch_tap)
    assert "FROM dbo.catalogrecord" in query
    assert "CONTAINS" in query
    assert "CIRCLE" in query
    assert "TOP 2" in query

    # Region query
    result = Catalogs.query_criteria(
        collection="tic",
        region="Circle ICRS 202.4656816 +47.1999842 0.04",
        radius=0.002 * u.deg,
        offset=1,
        sort_by="ra",
    )

    assert isinstance(result, Table)
    assert len(result) > 0
    assert "dec" in result.colnames
    query = get_patch_tap_query(patch_tap)
    assert "FROM dbo.catalogrecord" in query
    assert "CONTAINS" in query
    assert "CIRCLE" in query
    assert "OFFSET" in query
    assert "ORDER BY" in query

    # Non-positional query
    result = Catalogs.query_criteria(
        collection="tic",
        filters={"pmra": [">-10", "<10"]},
    )
    assert isinstance(result, Table)
    assert len(result) > 0
    assert "dec" in result.colnames
    query = get_patch_tap_query(patch_tap)
    assert "FROM dbo.catalogrecord" in query
    assert "WHERE" in query
    assert "pmra > -10" in query
    assert "pmra < 10" in query


def test_catalogs_invalid_query_criteria(patch_tap):
    # Specifying both region and coordinates
    with pytest.raises(InvalidQueryError, match="Specify either `region` or `coordinates`"):
        Catalogs.query_criteria(
            collection="tic",
            coordinates=regionCoords,
            region="Circle ICRS 202.4656816 +47.1999842 0.04"
        )

    # Specifying both region and object_name
    with pytest.raises(InvalidQueryError, match="Specify either `region` or `object_name`"):
        Catalogs.query_criteria(
            collection="tic",
            object_name="M31",
            region="Circle ICRS 202.4656816 +47.1999842 0.04"
        )

    # Named parameters and filters dict specifying criteria
    with pytest.raises(InvalidQueryError, match="Criteria specified both"):
        Catalogs.query_criteria(
            collection="tic",
            object_name="M31",
            file_suffix=['A', 'B', '!C'],
            filters={"file_suffix": ['A', 'B', '!C']}
        )

    # sort_by cols and sort_desc different lengths
    with pytest.raises(InvalidQueryError, match="must be 1 or equal to length of 'sort_by'"):
        Catalogs.query_criteria(
            collection="tic",
            coordinates=regionCoords,
            sort_by=["ra", "dec"],
            sort_desc=[True, False, True]
        )

    # Invalid sort col
    with pytest.raises(InvalidQueryError, match="Filter 'fake' is not recognized"):
        Catalogs.query_criteria(
            collection="tic",
            coordinates=regionCoords,
            sort_by="fake",
        )

    # Invalid filter
    with pytest.raises(InvalidQueryError, match="Filter 'fake' is not recognized"):
        Catalogs.query_criteria(
            collection="tic",
            fake=1
        )

    # Collection is not a string
    with pytest.raises(InvalidQueryError, match="Collection name must be a string."):
        Catalogs.query_criteria(
            collection=123,
            objtype="star"
        )

    # Warn if result table is empty
    with pytest.warns(NoResultsWarning, match="The query returned no results."):
        Catalogs.query_criteria(
            collection="tic",
            objtype="empty"
        )


def test_catalogs_query_region(patch_tap):
    # Passing region coords and radius
    result = Catalogs.query_region(
        regionCoords,
        radius=0.002 * u.deg,
        collection="tic"
    )

    assert isinstance(result, Table)
    assert len(result) > 0
    assert "ra" in result.colnames
    query = get_patch_tap_query(patch_tap)
    assert "FROM dbo.catalogrecord" in query
    assert "CONTAINS" in query
    assert "CIRCLE" in query
    assert "POINT" in query


def test_catalogs_invalid_query_region():
    # Query without region or coordinates
    with pytest.raises(InvalidQueryError, match="Must specify either `region` or `coordinates`"):
        Catalogs.query_region(
            collection="tic",
        )

    # Query with unsupported region type
    with pytest.raises(InvalidQueryError, match="does not support ADQL region type 'POLYGON'"):
        Catalogs.query_region(
            region="Polygon ICRS 202.4656816 +47.1999842 202.5656816 +47.2999842 202.3656816 +47.0999842",
            collection="tic"
        )


def test_catalogs_query_object(patch_tap):
    # Object and radius query
    radius = .001
    result = Catalogs.query_object(
        "M10",
        radius=radius,
        collection="TIC"
    )

    assert isinstance(result, Table)
    assert len(result) > 0
    assert "ra" in result.colnames
    query = get_patch_tap_query(patch_tap)
    assert "FROM dbo.catalogrecord" in query
    assert "CONTAINS" in query
    assert "POINT" in query
    assert str(radius) in query


def test_catalogs_init_with_catalog(patch_tap):
    catalog = Catalogs(
        collection="tic",
        catalog="tap_schema.schemas"
    )
    assert catalog.catalog == "tap_schema.schemas"


def test_catalogs_setting_catalog(patch_tap):
    catalog = Catalogs(
        collection="tic",
        catalog="tap_schema.schemas"
    )
    catalog.catalog = "tap_schema.key_columns"
    assert catalog.catalog == "tap_schema.key_columns"


def test_catalogs_get_collections_cached(patch_tap):
    catalog = Catalogs("tic")
    collections = catalog.get_collections()

    assert isinstance(collections, Table)
    assert len(collections) > 0
    assert "collection_name" in collections.colnames


def test_catalogs_collection_cache_is_shared(patch_tap):
    collection = "gaiadr3"
    catalog_one = Catalogs(collection)
    catalog_two = Catalogs(collection)

    collection_one = catalog_one._get_collection_obj(collection)
    collection_two = catalog_two._get_collection_obj(collection)

    assert collection_one is collection_two


def test_catalogs_supports_spatial_queries(patch_tap):
    catalog = Catalogs()
    result = catalog.supports_spatial_queries(
        collection="tic",
        catalog="tap_schema.schemas"
    )

    assert isinstance(result, bool)
    assert result


def test_catalogs_verify_collection(patch_tap):
    valid = Catalogs._verify_collection("tic")
    assert valid.lower() == "tic"

    # Renamed collection
    renamed = list(Catalogs._renamed_collections.keys())[0]
    new_name = Catalogs._renamed_collections[renamed]
    with pytest.warns(InputWarning, match="has been renamed"):
        result = Catalogs._verify_collection(renamed)
        assert result == new_name

    # Invalid collection
    with pytest.raises(InvalidQueryError, match="is not recognized"):
        Catalogs._verify_collection("FAKE")

    # No longer supported collection
    if Catalogs._no_longer_supported_collections:
        unsupported = list(Catalogs._no_longer_supported_collections)[0]
        with pytest.raises(InvalidQueryError) as exc:
            Catalogs._verify_collection(unsupported)
        assert "no longer supported" in str(exc.value)


def test_catalogs_parse_inputs(patch_tap):
    collection_name = Catalogs.available_collections[0]
    collection_obj, catalog = Catalogs._parse_inputs(collection=collection_name, catalog=None)
    assert isinstance(collection_obj, CatalogCollection)
    assert collection_obj.name == collection_name
    assert catalog == collection_obj.default_catalog

    # Catalog parameter warning
    with pytest.warns(DeprecationWarning, match="via the `catalog` parameter is deprecated."):
        collection_name = Catalogs.available_collections[0]
        collection_obj, catalog = Catalogs._parse_inputs(collection=None, catalog=collection_name)
        assert isinstance(collection_obj, CatalogCollection)
        assert catalog == collection_obj.default_catalog

    # Use catalog attribute if valid for collection
    Catalogs.catalog = "dbo.catalogrecord"
    collection_obj, catalog = Catalogs._parse_inputs(collection="tic")
    assert collection_obj.name == "tic"
    assert catalog == "dbo.catalogrecord"


def test_catalogs_parse_select_cols(patch_tap):
    catalog = Catalogs("tic")
    column_metadata = catalog.get_column_metadata()
    result = Catalogs._parse_select_cols(
        ["ra", "dec"],
        column_metadata)
    assert result == "ra, dec"

    # Close match suggestion
    close_match_col = "gaiagaiabp"
    with pytest.warns(InputWarning, match=" not found in catalog. Did you mean"):
        result = Catalogs._parse_select_cols(
            ["ra", close_match_col],
            column_metadata
        )

    # Empty columns
    with pytest.raises(InvalidQueryError, match="No valid columns specified in `select_cols`"):
        result = Catalogs._parse_select_cols(
            [],
            column_metadata
        )


def test_catalogs_parse_legacy_pagination(patch_tap):
    catalog = Catalogs("tic")
    limit, offset = catalog._parse_legacy_pagination(
        limit=5000,
        offset=0,
        pagesize=10,
        page=None,
    )
    assert limit == 10
    assert offset == 0

    # Missing pagesize
    with pytest.warns(InputWarning, match="The 'page' parameter is ignored without 'pagesize'."):
        catalog._parse_legacy_pagination(
            limit=5000,
            offset=0,
            pagesize=None,
            page=2,
        )


def test_catalogs_create_adql_region(patch_tap):
    # String regions
    adql_region = Catalogs._create_adql_region(
        region="Circle 202.4656816 +47.1999842 0.2"
    )
    assert adql_region == "CIRCLE('ICRS',202.4656816,+47.1999842,0.2)"

    adql_region = Catalogs._create_adql_region(
        region="Polygon ICRS 202.4656816 +47.1999842 202.5656816 +47.2999842 202.3656816 +47.0999842"
    )
    assert adql_region == "POLYGON('ICRS',202.4656816,+47.1999842,202.5656816,+47.2999842,202.3656816,+47.0999842)"

    adql_region = Catalogs._create_adql_region(
        region="Polygon 202.4656816 +47.1999842 202.5656816 +47.2999842 202.3656816 +47.0999842"
    )
    assert adql_region == "POLYGON('ICRS',202.4656816,+47.1999842,202.5656816,+47.2999842,202.3656816,+47.0999842)"

    # Iterable coord pairs
    adql_region = Catalogs._create_adql_region(
        region=[
            (57.376, 24.053),
            (56.391, 24.622),
            (56.025, 24.049),
            (56.616, 24.291)
        ]
    )
    assert adql_region == "POLYGON('ICRS',57.376,24.053,56.391,24.622,56.025,24.049,56.616,24.291)"

    if HAS_REGIONS:
        # Astropy region objects
        cone_region = CircleSkyRegion(
            center=SkyCoord(10.8, 6.5, unit="deg"),
            radius=Angle(0.5, unit="deg")
        )
        adql_region = Catalogs._create_adql_region(region=cone_region)
        assert adql_region == "CIRCLE('ICRS',10.8,6.5,0.5)"

        polygon_region = PolygonSkyRegion(
            SkyCoord(
                [57.376, 56.391, 56.025, 56.616],
                [24.053, 24.622, 24.049, 24.291],
                frame="icrs",
                unit="deg",
            )
        )
        adql_region = Catalogs._create_adql_region(region=polygon_region)
        assert adql_region == "POLYGON('ICRS',57.376,24.053,56.391,24.622,56.025,24.049,56.616,24.291)"


def test_catalogs_invalid_create_adql_region(patch_tap):
    # Polygon without points
    with pytest.raises(InvalidQueryError, match="Invalid POLYGON region string"):
        Catalogs._create_adql_region(region="Polygon ICRS")

    # Polygon without sufficient points
    with pytest.raises(InvalidQueryError, match="Invalid POLYGON region string"):
        Catalogs._create_adql_region(region="Polygon ICRS 202.4656816 +47.1999842 202.5656816 +47.2999842")

    # Missing circle spec, frame not specified
    with pytest.raises(InvalidQueryError, match="Invalid CIRCLE region string"):
        Catalogs._create_adql_region(region="CIRCLE 202.4656816 +47.1999842")

    # Missing circle spec, frame specified
    with pytest.raises(InvalidQueryError, match="Invalid CIRCLE region string"):
        Catalogs._create_adql_region(region="CIRCLE ICRS 202.4656816 +47.1999842")

    # Invalid region str
    with pytest.raises(InvalidQueryError, match="Unrecognized region string"):
        Catalogs._create_adql_region(region="Badshape ICRS 202.4656816 +47.1999842 0.04")

    # Invalid list of coord pairs
    with pytest.raises(InvalidQueryError, match="Invalid iterable region format"):
        Catalogs._create_adql_region(
            region=[57.376, 24.053, 56.391, 24.622, 56.025, 24.049, 56.616, 24.291]
        )

    if HAS_REGIONS:
        # Invalid astropy region
        with pytest.raises(TypeError, match="Unsupported region type"):
            Catalogs._create_adql_region(
                region=CirclePixelRegion(PixCoord(x=42, y=43), 4.2)
            )


def test_catalogs_parse_numeric_expression(patch_tap):
    # Handling between
    predicate = Catalogs._parse_numeric_expr("dec", "5..10")
    assert predicate == "dec BETWEEN 5 AND 10"

    # Handling inequalities
    predicate = Catalogs._parse_numeric_expr("teff", "<1")
    assert predicate == "teff < 1"

    # Handling specific values
    predicate = Catalogs._parse_numeric_expr("gaiabp", "1")
    assert predicate == "gaiabp = 1.0"

    # Passing not numeric str
    with pytest.raises(InvalidQueryError, match="is numeric; unsupported value"):
        Catalogs._parse_numeric_expr("dec", "notnumeric")


def test_catalogs_parse_temporal_expression(patch_tap):
    # Handling between
    predicate = Catalogs._parse_temporal_expr("time", "2024-01-01..2024-12-31")
    assert predicate == "time BETWEEN '2024-01-01 00:00:00' AND '2024-12-31 00:00:00'"

    # Handling inequalities
    predicate = Catalogs._parse_temporal_expr("datetime", ">=2020-06-01")
    assert predicate == "datetime >= '2020-06-01 00:00:00'"

    # Handling specific values
    predicate = Catalogs._parse_temporal_expr("obs_time", "2025-04-01 12:00:00")
    assert predicate == "obs_time BETWEEN '2025-04-01 12:00:00' AND '2025-04-01 12:00:01'"

    # Passing not datetime str
    predicate = Catalogs._parse_temporal_expr("dec", "notdatetime")
    assert predicate == "dec = 'notdatetime'"

    # Handling microseconds
    predicate = Catalogs._parse_temporal_expr("datetime", ">=2020-06-01 10:00:00.0001")
    assert predicate == "datetime >= '2020-06-01 10:00:00'"

    # Handling year-only str
    predicate = Catalogs._parse_temporal_expr("time", "2025")
    assert predicate == "time = '2025'"

    # Handling date str
    predicate = Catalogs._parse_temporal_expr("time", "2020-08-01")
    assert predicate == "time BETWEEN '2020-08-01 00:00:00' AND '2020-08-01 00:00:01'"

    # Handling astropy Time
    predicate = Catalogs._parse_temporal_expr("obs_time", Time('2000-01-01 12:30:00'))
    assert predicate == "obs_time BETWEEN '2000-01-01 12:30:00' AND '2000-01-01 12:30:01'"

    # Handling datetime
    predicate = Catalogs._parse_temporal_expr("obs_time", datetime(2024, 6, 1, 8, 0, 1))
    assert predicate == "obs_time BETWEEN '2024-06-01 08:00:01' AND '2024-06-01 08:00:02'"


def test_catalogs_format_scalar_predicate(patch_tap):
    # Handling bool
    predicate = Catalogs._format_scalar_predicate(
        "var", True
    )
    assert predicate == 'var = 1'

    # Handling num
    predicate = Catalogs._format_scalar_predicate(
        "e_lum", 1, is_numeric=True
    )
    assert predicate == 'e_lum = 1'

    # Handling str(num)
    predicate = Catalogs._format_scalar_predicate(
        "e_lum", "1", is_numeric=True
    )
    assert predicate == 'e_lum = 1.0'

    # Handling ! nots
    predicate = Catalogs._format_scalar_predicate(
        "e_lum", "!1", is_numeric=True
    )
    assert predicate == 'NOT (e_lum = 1.0)'

    # Handling wildcard *
    predicate = Catalogs._format_scalar_predicate(
        "var", "WILDCARD*"
    )
    assert predicate == "var LIKE 'WILDCARD%'"

    # Handling wildcard * and nots
    predicate = Catalogs._format_scalar_predicate(
        "var", "!WILDCARD*"
    )
    assert predicate == "NOT (var LIKE 'WILDCARD%')"

    # Handling wildcard %
    predicate = Catalogs._format_scalar_predicate(
        "var", "WILDCARD%"
    )
    assert predicate == "var LIKE 'WILDCARD%'"

    # Handling wildcard % and nots
    predicate = Catalogs._format_scalar_predicate(
        "var", "!WILDCARD%"
    )
    assert predicate == "NOT (var LIKE 'WILDCARD%')"

    # Handling temporal
    predicate = Catalogs._format_scalar_predicate(
        "time", "!1", is_temporal=True
    )
    assert predicate == "NOT (time = '1')"


def test_catalogs_combine_predicates(patch_tap):
    # No predicates
    result = Catalogs._combine_predicates([], [])
    assert result == ""

    # One positive predicate
    result = Catalogs._combine_predicates(["ra > 5"], [])
    assert result == "ra > 5"

    # Multiple positive predicate
    result = Catalogs._combine_predicates(
        ["ra > 5", "dec < 0"],
        []
    )
    assert result == "(ra > 5 OR dec < 0)"

    # Multiple negative predicates
    result = Catalogs._combine_predicates(
        [],
        ["ra != 5", "dec != 0"]
    )
    assert result == "ra != 5 AND dec != 0"

    # Multiple positive and negative predicates
    result = Catalogs._combine_predicates(
        ["ra > 5", "dec < 0"],
        ["ra != 10"]
    )
    assert result == "(ra != 10) AND (ra > 5 OR dec < 0)"


def test_catalogs_build_numeric_list_predicate(patch_tap):
    # Multiple positive nums
    result = Catalogs._build_numeric_list_predicate(
        "ra",
        pos_items=[1, 2, 3],
        neg_items=[]
    )
    assert result == "ra IN (1, 2, 3)"

    # Multiple positive bools
    result = Catalogs._build_numeric_list_predicate(
        "tessflag",
        pos_items=[True, False],
        neg_items=[]
    )
    assert result == "tessflag IN (1, 0)"

    # Multiple positive inequalities and ranges
    result = Catalogs._build_numeric_list_predicate(
        "dec",
        pos_items=["<5", "10..20"],
        neg_items=[]
    )
    assert "< 5" in result
    assert "BETWEEN 10 AND 20" in result

    # Single positive num
    result = Catalogs._build_numeric_list_predicate(
        "ra",
        pos_items=[np.int64(7)],
        neg_items=[]
    )
    assert "ra IN (7.0)" in result

    # Positive and negative nums
    result = Catalogs._build_numeric_list_predicate(
        "ra",
        pos_items=[1, 2],
        neg_items=[">5"]
    )
    assert "ra IN (1, 2)" in result
    assert "ra > 5" in result
    assert "AND" in result

    # Unsupported numeric value type
    with pytest.raises(InvalidQueryError, match="Unsupported numeric value type"):
        Catalogs._build_numeric_list_predicate(
            "ra",
            pos_items=[{"not": "a number"}],
            neg_items=[]
        )


def test_catalogs_build_string_list_predicate(patch_tap):
    # Multiple positive strs
    result = Catalogs._build_string_list_predicate(
        "var",
        pos_items=["str", "str"],
        neg_items=[]
    )
    assert result == "var IN ('str', 'str')"

    # Multiple positive bools
    result = Catalogs._build_string_list_predicate(
        "var",
        pos_items=[True, False],
        neg_items=[]
    )
    assert result == "var IN (1, 0)"

    # Multiple positive strs with wildcard
    result = Catalogs._build_string_list_predicate(
        "var",
        pos_items=["WILDCARD%", "str"],
        neg_items=[]
    )
    assert "var IN ('str')" in result
    assert "LIKE 'WILDCARD%" in result
    assert "OR" in result

    # Multiple positive nums
    result = Catalogs._build_string_list_predicate(
        "var",
        pos_items=[1, 0],
        neg_items=[]
    )
    assert result == "var IN (1, 0)"


def test_catalogs_build_temporal_list_predicate(patch_tap):
    # Multiple positive temps
    result = Catalogs._build_temporal_list_predicate(
        "var",
        pos_items=["<2020-06-01", ">2025-06-01"],
        neg_items=[]
    )
    assert result == "(var < '2020-06-01 00:00:00' OR var > '2025-06-01 00:00:00')"

    # Multiple positive inequalities and ranges
    result = Catalogs._build_temporal_list_predicate(
        "var",
        pos_items=[">2025-06-01", "2020-06-01..2020-12-31"],
        neg_items=[]
    )
    assert "var > '2025-06-01 00:00:00'" in result
    assert "BETWEEN '2020-06-01 00:00:00' AND '2020-12-31 00:00:00'" in result


def test_catalogs_format_criteria_conditions(patch_tap):
    # Multiple numeric cols and singular criteria
    criteria = {"ra": 5, "dec": 10}
    result = Catalogs._format_criteria_conditions(
        CatalogCollection("tic"),
        "dbo.catalogrecord",
        criteria
    )
    assert result == ["ra = 5", "dec = 10"]

    # Str cols and singular criteria
    criteria = {"obj_type": "STAR"}
    result = Catalogs._format_criteria_conditions(
        CatalogCollection("tic"),
        "dbo.catalogrecord",
        criteria
    )
    assert result == ["obj_type = 'STAR'"]

    # Multiple cols and multiple criteria
    criteria = {"ra": [1, 2, 3], "dec": [">5", "<10"]}
    result = Catalogs._format_criteria_conditions(
        CatalogCollection("tic"),
        "dbo.catalogrecord",
        criteria
    )
    assert any("ra IN" in r or "ra >" in r for r in result)
    assert any("dec <" in r or "dec >" in r for r in result)

    # Str cols and multiple criteria
    criteria = {"obj_type": ["STAR", "!GALAXY"]}
    result = Catalogs._format_criteria_conditions(
        CatalogCollection("tic"),
        "dbo.catalogrecord",
        criteria
    )
    assert any("NOT" in r for r in result)
    assert any("STAR" in r for r in result)

    # Empty criteria
    criteria = {"ra": []}
    result = Catalogs._format_criteria_conditions(
        CatalogCollection("tic"),
        "dbo.catalogrecord",
        criteria
    )
    assert result == ["1=0"]


def test_catalogs_invalid_tap_query(patch_tap):
    # This will trigger a DALQueryError in the mock TAP service
    # when 'invalid' is found in the query string
    with pytest.raises(InvalidQueryError, match="Simulated TAP query error"):
        Catalogs.query_criteria(
            collection="tic",
            coordinates=regionCoords,
            radius=0.002 * u.deg,
            allwise='invalid'
        )

    with pytest.raises(InvalidQueryError, match="Simulated TAP query error"):
        Catalogs.query_region(
            regionCoords,
            radius=0.002 * u.deg,
            collection="tic",
            allwise='invalid'
        )

    with pytest.raises(InvalidQueryError, match="Simulated TAP query error"):
        Catalogs.query_object(
            "M10",
            radius=.001,
            collection="TIC",
            allwise='invalid'
        )


def test_catalogs_invalid_spatial_query(patch_tap):
    # Force spatial query to fail
    patch_tap.search = MagicMock(side_effect=DALQueryError("spatial failed"))
    with pytest.raises(InvalidQueryError, match="does not support spatial queries"):
        Catalogs.query_criteria(
            collection="tic",
            coordinates=regionCoords,
            radius=0.002 * u.deg,
        )


def test_catalogs_query_hsc_matchid_async(patch_post):
    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        responses = Catalogs.query_hsc_matchid_async(82371983)
        assert isinstance(responses, list)

    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        responses = Catalogs.query_hsc_matchid_async(82371983, version=2)
        assert isinstance(responses, list)

    with pytest.warns((AstropyDeprecationWarning, InputWarning)) as record:
        Catalogs.query_hsc_matchid_async(82371983, version=5)
        messages = [str(w.message) for w in record]
        assert any("This function is deprecated" in m for m in messages)
        assert any("Invalid HSC version number" in m for m in messages)


def test_catalogs_query_hsc_matchid(patch_post):
    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        result = Catalogs.query_hsc_matchid(82371983)
        assert isinstance(result, Table)


def test_catalogs_get_hsc_spectra_async(patch_post):
    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        responses = Catalogs.get_hsc_spectra_async()
        assert isinstance(responses, list)


def test_catalogs_get_hsc_spectra(patch_post):
    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        result = Catalogs.get_hsc_spectra()
        assert isinstance(result, Table)


def test_catalogs_download_hsc_spectra(patch_post, tmpdir):
    with pytest.warns(AstropyDeprecationWarning, match="This function is deprecated"):
        allSpectra = Catalogs.get_hsc_spectra()

        # Actually download the products
        result = Catalogs.download_hsc_spectra(allSpectra[10], download_dir=str(tmpdir))
        assert isinstance(result, Table)

        # Just get the curl script
        result = Catalogs.download_hsc_spectra(allSpectra[20:24],
                                               download_dir=str(tmpdir), curl_flag=True)
        assert isinstance(result, Table)


###########################
# CatalogCollection tests #
###########################


def test_catalog_collection_discover_collections(patch_tap):
    collections = CatalogCollection.discover_collections()
    assert isinstance(collections, Table)
    assert len(collections) > 0
    assert "collection_name" in collections.colnames
    assert "parent_collection" in collections.colnames


def test_catalog_collection_get_parent_collection(patch_tap):
    parent = CatalogCollection.get_parent_collection("tic")
    assert parent == "tic"

    # Error if collection not a string
    with pytest.raises(InvalidQueryError):
        CatalogCollection.get_parent_collection(123)

    # Error if collection not found
    with pytest.raises(InvalidQueryError, match="Collection 'fake' not found"):
        CatalogCollection.get_parent_collection("fake")


def test_catalog_collection_tap_get_catalog_metadata(patch_tap):
    cc = CatalogCollection("tic")
    default_catalog = cc.get_default_catalog()
    default_metadata = cc.get_catalog_metadata(default_catalog)
    assert isinstance(default_metadata, CatalogMetadata)
    assert isinstance(default_metadata.column_metadata, Table)
    assert isinstance(default_metadata.ra_column, str)
    assert isinstance(default_metadata.dec_column, str)
    assert isinstance(default_metadata.supports_spatial_queries, bool)

    assert len(default_metadata.column_metadata) > 0
    assert default_metadata.ra_column in default_metadata.column_metadata["column_name"]
    assert default_metadata.dec_column in default_metadata.column_metadata["column_name"]

    metadata_cached = cc.get_catalog_metadata(default_catalog)
    assert default_metadata is metadata_cached


def test_catalog_collection_get_default_catalog(patch_tap):
    cc = CatalogCollection("tic")
    catalogs = cc._fetch_catalogs()
    default = cc.get_default_catalog()

    assert isinstance(catalogs, Table)
    assert len(catalogs) > 0
    assert catalogs.colnames == ['catalog_name', 'description']

    assert not default.startswith("tap_schema")
    assert default.casefold() in [name.casefold() for name in catalogs["catalog_name"]]
    assert DEFAULT_CATALOGS["tic"] == default

    # First non-tap_schema
    cc = CatalogCollection("tic")
    cc.name = "fake"
    fake_catalogs = Table({
        "catalog_name": [
            "tap_schema.tables",
            "tap_schema.columns",
            "real_catalog",
            "real_catalog_2",
        ],
        "description": ["", "", "", ""],
    })
    cc._fetch_catalogs = MagicMock(return_value=fake_catalogs)
    assert isinstance(catalogs, Table)
    assert len(catalogs) > 0

    default = cc.get_default_catalog()
    assert default == "real_catalog"

    # All are tap_schema
    cc = CatalogCollection("tic")
    cc.name = "fake"
    fake_catalogs = Table({
        "catalog_name": [
            "tap_schema.tables",
            "tap_schema.columns",
        ],
        "description": ["", ""],
    })
    cc._fetch_catalogs = MagicMock(return_value=fake_catalogs)
    assert isinstance(catalogs, Table)
    assert len(catalogs) > 0

    default = cc.get_default_catalog()
    assert default == "tap_schema.tables"


def test_catalog_collection_run_tap_query(patch_tap):
    cc = CatalogCollection("tic")

    adql_str = (
        "SELECT TOP 10 solution_id, designation, source_id, ra, dec "
        "FROM gaia_source WHERE "
        "ra BETWEEN 10 AND 11 AND dec BETWEEN 12 AND 13"
    )
    result = cc.run_tap_query(adql_str)

    assert isinstance(result, Table)
    assert len(result) > 0

    query = get_patch_tap_query(patch_tap)
    assert adql_str in query


def test_catalog_collection_invalid_run_tap_query(patch_tap):
    cc = CatalogCollection("tic")
    with pytest.raises(InvalidQueryError, match="TAP query failed for collection 'tic'"):
        adql_str = "invalid"
        cc.run_tap_query(adql_str)


def test_catalog_collection_grouped_fetch_catalogs(patch_tap):
    name = "dbo"
    cc = CatalogCollection(name)
    _ = cc._fetch_catalogs()
    query = get_patch_tap_query(patch_tap)
    assert f"WHERE table_name LIKE '{name}" in query


def test_catalog_collection_verify_catalog(patch_tap):
    cc = CatalogCollection("tic")
    default_catalog = cc.get_default_catalog()

    # Valid catalog
    assert isinstance(cc._verify_catalog(default_catalog), str)
    assert cc._verify_catalog(default_catalog) == 'dbo.catalogrecord'


def test_catalog_collection_invalid_verify_catalog(patch_tap):
    cc = CatalogCollection("tic")

    # Ambiguous
    fake_catalogs = Table({
        "catalog_name": [
            "mission1.catalogA",
            "mission2.catalogA",
        ],
        "description": ["", ""],
    })
    cc._fetch_catalogs = MagicMock(return_value=fake_catalogs)

    with pytest.raises(InvalidQueryError, match="is ambiguous for collection"):
        cc._verify_catalog("catalogA")

    # Invalid catalog
    with pytest.raises(InvalidQueryError, match="Catalog 'fake' is not recognized for collection 'tic'"):
        cc._verify_catalog("fake")


def test_catalog_collection_invalid_get_column_metadata(patch_tap):
    cc = CatalogCollection("tic")

    empty_result = Table(
        names=["column_name", "datatype", "unit", "ucd", "description"]
    )
    cc.tap_service.run_sync = MagicMock(return_value=empty_result)

    with pytest.raises(
        InvalidQueryError,
        match="Catalog 'fake_catalog' not found in collection 'tic'"
    ):
        cc._get_column_metadata("fake_catalog")


def test_catalog_collection_verify_criteria(patch_tap):
    cc = CatalogCollection("tic")
    default_catalog = cc.get_default_catalog()

    # Valid filters
    assert cc._verify_criteria(default_catalog) is None
    assert cc._verify_criteria(default_catalog, gaiabp=1) is None
    assert cc._verify_criteria(default_catalog, gaiabp=1, teff=1) is None


def test_catalog_collection_invalid_verify_criteria(patch_tap):
    cc = CatalogCollection("tic")
    default_catalog = cc.get_default_catalog()

    close_match_col = "gaiagaiabp"
    with pytest.raises(InvalidQueryError, match=f"Filter '{close_match_col}' is not recognized for collection "
                       f"'{cc.name}' and catalog '{default_catalog}'. Did you mean 'gaiabp'?"):
        cc._verify_criteria(default_catalog, gaiagaiabp=1)

    invalid_col = "fake_column"
    with pytest.raises(InvalidQueryError, match=f"Filter '{invalid_col}' is not recognized for collection "
                       f"'{cc.name}' and catalog '{default_catalog}'."):
        cc._verify_criteria(default_catalog, fake_column=1)


def test_catalog_collection_invalid_spatial_query(patch_tap):
    cc = CatalogCollection("tic")

    # Force only spatial query to fail
    patch_tap.search = MagicMock(side_effect=DALQueryError("spatial failed"))
    default_catalog = cc.get_default_catalog()
    metadata = cc.get_catalog_metadata(default_catalog)

    assert metadata.supports_spatial_queries is False
    assert patch_tap.search.called


def test_catalog_collection_invalid_collection_type(patch_tap):
    # Error if collection name is not a string
    with pytest.raises(ValueError, match="Collection name must be a string, got <class 'int'>"):
        CatalogCollection(123)


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
    sector_table = Tesscut.get_sectors(object_name="M103")
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    # Exercising the search by moving target
    sector_table = Tesscut.get_sectors(object_name="Ceres",
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
                 "Please remove coordinates if using moving_target and object_name.")
    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.get_sectors(object_name='Ceres', moving_target=True, coordinates=coord)
    assert error_str in str(invalid_query.value)

    # Error when no object name with moving target
    with pytest.raises(InvalidQueryError, match='Please specify the object name or ID'):
        Tesscut.get_sectors(moving_target=True)

    # Error when both object name and coordinates are specified
    with pytest.raises(InvalidQueryError, match='Please remove object_name if using coordinates'):
        Tesscut.get_sectors(object_name='Ceres', coordinates=coord)

    # Testing invalid queries
    # Invalid product type
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.get_sectors(object_name="M101", product="spooc")
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
    manifest = Tesscut.download_cutouts(object_name="M103", size=5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Exercising the search by moving target
    manifest = Tesscut.download_cutouts(object_name="Eleonora",
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
                 "Please remove coordinates if using moving_target and object_name.")

    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.download_cutouts(object_name="Eleonora",
                                 moving_target=True,
                                 coordinates=coord,
                                 size=5,
                                 path=str(tmpdir))
    assert error_str in str(invalid_query.value)

    # Testing invalid queries
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.download_cutouts(object_name="M101", product="spooc")
    assert "Input product must be SPOC." in str(invalid_query.value)


def test_tesscut_get_cutouts(tmpdir):
    coord = SkyCoord(107.27, -70.0, unit="deg")
    cutout_hdus_list = Tesscut.get_cutouts(coordinates=coord, size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Exercising the search by object name
    cutout_hdus_list = Tesscut.get_cutouts(object_name="M103", size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Exercising the search by object name
    cutout_hdus_list = Tesscut.get_cutouts(object_name='Eleonora',
                                           moving_target=True,
                                           mt_type='small_body',
                                           sector=1,
                                           size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Testing catch for multiple designators'
    error_str = ("Only one of moving_target and coordinates may be specified. "
                 "Please remove coordinates if using moving_target and object_name.")

    with pytest.raises(InvalidQueryError) as invalid_query:
        Tesscut.get_cutouts(object_name="Eleonora",
                            moving_target=True,
                            coordinates=coord,
                            size=5)
    assert error_str in str(invalid_query.value)

    # Testing invalid queries
    with pytest.raises(InvalidQueryError) as invalid_query:
        with pytest.warns(AstropyDeprecationWarning, match="Tesscut no longer supports"):
            Tesscut.get_cutouts(object_name="M101", product="spooc")
    assert "Input product must be SPOC." in str(invalid_query.value)


def test_tesscut_get_cutouts_mt_no_sector():
    """Test get_cutouts with moving target but no sector specified.

    When sector is not specified for moving targets, the method should
    automatically fetch available sectors and make individual requests per sector.
    """
    # Moving target without specifying sector - should automatically fetch sectors
    cutout_hdus_list = Tesscut.get_cutouts(object_name="Eleonora", moving_target=True, mt_type="small_body", size=5)
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
        object_name="Eleonora", moving_target=True, mt_type="small_body", size=5, path=str(tmpdir)
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
        cutout_hdus_list = Tesscut.get_cutouts(object_name="NonExistentObject", moving_target=True, size=5)
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
            object_name="NonExistentObject", moving_target=True, size=5, path=str(tmpdir)
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
    loc = utils.parse_input_location(object_name="TIC 307210830")
    assert isinstance(loc, SkyCoord)
    assert loc.ra == obj_coord.ra
    assert loc.dec == obj_coord.dec

    # Error if both coordinates and object name are provided
    with pytest.raises(InvalidQueryError, match="Only one of object_name and coordinates may be specified"):
        utils.parse_input_location(coordinates=coord, object_name="M101")

    # Error if neither coordinates nor object name is provided
    with pytest.raises(InvalidQueryError, match="One of object_name and coordinates must be specified"):
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
