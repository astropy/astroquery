# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pathlib import Path
import numpy as np
import os
import pytest

from requests.models import Response

from astropy.table import Table, unique
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

from astroquery.mast import Observations, utils, Mast, Catalogs, Hapcut, Tesscut, Zcut, MastMissions

from ..utils import ResolverError
from ...exceptions import (InputWarning, InvalidQueryError, MaxResultsWarning,
                           NoResultsWarning)


@pytest.fixture(scope="module")
def msa_product_table():
    # Pull products for a JWST NIRSpec MSA observation with 6 known
    # duplicates of the MSA configuration file, propID=2736
    obs = Observations.query_criteria(proposal_id=2736,
                                      obs_collection='JWST',
                                      instrument_name='NIRSPEC/MSA',
                                      filters='F170LP;G235M',
                                      target_name='MPTCAT-0628')
    products = Observations.get_product_list(obs['obsid'][0])

    # Filter out everything but the MSA config file
    mask = np.char.find(products["dataURI"], "_msa.fits") != -1
    products = products[mask]

    return products


@pytest.mark.remote_data
class TestMast:

    ###############
    # utils tests #
    ###############

    def test_resolve_object(self):
        m101_loc = utils.resolve_object("M101")
        assert round(m101_loc.separation(SkyCoord("210.80243 54.34875", unit='deg')).value, 4) == 0

        ticobj_loc = utils.resolve_object("TIC 141914082")
        assert round(ticobj_loc.separation(SkyCoord("94.6175354 -72.04484622", unit='deg')).value, 4) == 0

    ###########################
    # MissionSearchClass Test #
    ###########################

    def test_missions_get_column_list(self):
        columns = MastMissions().get_column_list()
        assert len(columns) > 1
        assert isinstance(columns, Table)
        assert list(columns.columns.keys()) == ['name', 'data_type', 'description']

    def test_missions_query_region_async(self):
        coords = SkyCoord(83.6287, 22.0147, unit="deg")
        response = MastMissions.query_region_async(coords, radius=1)
        assert isinstance(response, Response)
        assert response.status_code == 200

    def test_missions_query_region(self):
        select_cols = ['sci_targname', 'sci_instrume']
        result = MastMissions.query_region("245.89675 -26.52575",
                                           radius=0.1,
                                           sci_instrume="WFC3, ACS",
                                           select_cols=select_cols
                                           )
        assert isinstance(result, Table)
        assert len(result) > 0
        assert (result['ang_sep'].data.data.astype('float') < 0.1).all()
        ins_strip = np.char.strip(result['sci_instrume'].data)
        assert ((ins_strip == 'WFC3') | (ins_strip == 'ACS')).all()
        assert all(c in list(result.columns.keys()) for c in select_cols)

    def test_missions_query_object_async(self):
        response = MastMissions.query_object_async("M4", radius=0.1)
        assert isinstance(response, Response)
        assert response.status_code == 200

    def test_missions_query_object(self):
        result = MastMissions.query_object("NGC6121",
                                           radius=6*u.arcsec,
                                           sci_pi_last_name='*LE*',
                                           sci_spec_1234='!F395N'
                                           )
        assert isinstance(result, Table)
        assert len(result) > 0
        assert "NGC6121" in result["sci_targname"]
        assert (result['ang_sep'].data.data.astype('float') < 0.1).all()
        assert (result['sci_pi_last_name'] == 'LEE').all()
        assert 'F395N' not in result['sci_spec_1234']

    def test_missions_query_criteria_async(self):
        response = MastMissions.query_criteria_async(sci_pep_id=12557,
                                                     sci_obs_type='SPECTRUM',
                                                     sci_aec='S')
        assert isinstance(response, Response)
        assert response.status_code == 200

    def test_missions_query_criteria(self):
        # Non-positional search
        with pytest.warns(MaxResultsWarning):
            result = MastMissions.query_criteria(sci_pep_id=12557,
                                                 sci_obs_type='SPECTRUM',
                                                 sci_aec='S',
                                                 limit=3,
                                                 select_cols=['sci_pep_id', 'sci_obs_type', 'sci_aec'])
        assert isinstance(result, Table)
        assert len(result) == 3
        assert (result['sci_pep_id'] == 12557).all()
        assert (result['sci_obs_type'] == 'SPECTRUM').all()
        assert (result['sci_aec'] == 'S').all()

        # Positional criteria search
        result = MastMissions.query_criteria(objectname='NGC6121',
                                             radius=0.1,
                                             sci_start_time='<2012',
                                             sci_actual_duration='0..200'
                                             )
        assert len(result) == 3
        assert (result['ang_sep'].data.data.astype('float') < 0.1).all()
        assert (result['sci_start_time'] < '2012').all()
        assert ((result['sci_actual_duration'] >= 0) & (result['sci_actual_duration'] <= 200)).all()

        # Raise error if a non-positional criterion is not supplied
        with pytest.raises(InvalidQueryError):
            MastMissions.query_criteria(coordinates="245.89675 -26.52575",
                                        radius=1)

    def test_missions_query_criteria_invalid_keyword(self):
        # Attempt to make a criteria query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_no_alt:
            MastMissions.query_criteria(select_cols=['sci_targname'],
                                        not_a_keyword='test')
        assert "Filter 'not_a_keyword' does not exist." in str(err_no_alt.value)

        # Attempt to make a region query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_no_alt:
            MastMissions.query_region(coordinates="245.89675 -26.52575",
                                      invalid_keyword='test')
        assert "Filter 'invalid_keyword' does not exist." in str(err_no_alt.value)

        # Keyword is close enough for difflib to offer alternative
        with pytest.raises(InvalidQueryError) as err_with_alt:
            MastMissions.query_criteria(search_position='30 30')
        assert 'search_pos' in str(err_with_alt.value)

        # Should be case sensitive
        with pytest.raises(InvalidQueryError) as err_case:
            MastMissions.query_criteria(Search_Pos='30 30')
        assert 'search_pos' in str(err_case.value)

    def test_missions_get_product_list_async(self):
        datasets = MastMissions.query_object("M4", radius=0.1)

        # Table as input
        responses = MastMissions.get_product_list_async(datasets[:3])
        assert isinstance(responses, Response)

        # Row as input
        responses = MastMissions.get_product_list_async(datasets[0])
        assert isinstance(responses, Response)

        # String as input
        responses = MastMissions.get_product_list_async(datasets[0]['sci_data_set_name'])
        assert isinstance(responses, Response)

        # Column as input
        responses = MastMissions.get_product_list_async(datasets[:3]['sci_data_set_name'])
        assert isinstance(responses, Response)

        # Unsupported data type for datasets
        with pytest.raises(TypeError) as err_type:
            MastMissions.get_product_list_async(1)
        assert 'Unsupported data type' in str(err_type.value)

        # Empty dataset list
        with pytest.raises(InvalidQueryError) as err_empty:
            MastMissions.get_product_list_async([' '])
        assert 'Dataset list is empty' in str(err_empty.value)

    def test_missions_get_product_list(self, capsys):
        datasets = MastMissions.query_object("M4", radius=0.1)
        test_dataset = datasets[0]['sci_data_set_name']
        multi_dataset = list(datasets[:2]['sci_data_set_name'])

        # Compare Row input and string input
        result_str = MastMissions.get_product_list(test_dataset)
        result_row = MastMissions.get_product_list(datasets[0])
        assert isinstance(result_str, Table)
        assert len(result_str) == len(result_row)
        assert set(result_str['filename']) == set(result_row['filename'])

        # Compare Table input and list input
        result_list = MastMissions.get_product_list(multi_dataset)
        result_table = MastMissions.get_product_list(datasets[:2])
        assert isinstance(result_list, Table)
        assert len(result_list) == len(result_table)
        assert set(result_list['filename']) == set(result_table['filename'])

        # Filter datasets based on sci_data_set_name and verify products
        filtered = datasets[datasets['sci_data_set_name'] == 'IBKH03020']
        result = MastMissions.get_product_list(filtered)
        assert isinstance(result, Table)
        assert (result['dataset'] == 'IBKH03020').all()

        # Test batching by creating a list of 1001 different strings
        # This won't return any results, but will test the batching
        dataset_list = [f'{i}' for i in range(1001)]
        result = MastMissions.get_product_list(dataset_list)
        out, _ = capsys.readouterr()
        assert isinstance(result, Table)
        assert len(result) == 0
        assert 'Fetching products for 1001 unique datasets in 2 batches' in out

    def test_missions_get_unique_product_list(self, caplog):
        # Check that no rows are filtered out when all products are unique
        dataset_ids = ['JBTAA8010']
        products = MastMissions.get_product_list(dataset_ids)
        unique_products = MastMissions.get_unique_product_list(dataset_ids)

        # Should have the same length
        assert len(products) == len(unique_products)
        # No INFO messages should be logged
        with caplog.at_level('INFO', logger='astroquery'):
            assert caplog.text == ''

        # Check that rows are filtered out when products are not unique
        dataset_ids.append('JBTAA8020')
        products = MastMissions.get_product_list(dataset_ids)
        unique_products = MastMissions.get_unique_product_list(dataset_ids)

        # Unique product list should have fewer rows
        assert len(products) > len(unique_products)
        # Rows should be unique based on filename
        assert (unique_products == unique(unique_products, keys='filename')).all()
        # Check that INFO messages were logged
        with caplog.at_level('INFO', logger='astroquery'):
            assert 'products were duplicates' in caplog.text
            assert 'To return all products' in caplog.text

    def test_missions_filter_products(self):
        # Filter by extension
        products = MastMissions.get_product_list('W0FX0301T')
        filtered = MastMissions.filter_products(products,
                                                extension='jpg')
        assert isinstance(filtered, Table)
        assert all(filename.endswith('.jpg') for filename in filtered['filename'])

        # Filter by existing column
        filtered = MastMissions.filter_products(products,
                                                category='CALIBRATED')
        assert isinstance(filtered, Table)
        assert all(filtered['category'] == 'CALIBRATED')

        # Filter by non-existing column
        with pytest.warns(InputWarning):
            filtered = MastMissions.filter_products(products,
                                                    invalid=True)

    def test_missions_download_products(self, tmp_path):
        def check_filepath(path):
            assert path.is_file()

        # Check string input
        test_dataset_id = 'Z14Z0104T'
        result = MastMissions.download_products(test_dataset_id,
                                                download_dir=tmp_path)
        for row in result:
            if row['Status'] == 'COMPLETE':
                check_filepath(row['Local Path'])

        # Check Row input
        datasets = MastMissions.query_object("M4", radius=0.1)
        prods = MastMissions.get_product_list(datasets[0])[0]
        result = MastMissions.download_products(prods,
                                                download_dir=tmp_path)
        check_filepath(result['Local Path'][0])

        # Warn about no products
        with pytest.warns(NoResultsWarning):
            result = MastMissions.download_products(test_dataset_id,
                                                    extension='jpg',
                                                    download_dir=tmp_path)

    def test_missions_download_products_flat(self, tmp_path):
        # Download products without creating subdirectories
        result = MastMissions.download_products('Z14Z0104T',
                                                flat=True,
                                                download_dir=tmp_path)
        for row in result:
            if row['Status'] == 'COMPLETE':
                assert row['Local Path'].parent == tmp_path

    def test_missions_download_file(self, tmp_path):
        def check_result(result, path):
            assert result == ('COMPLETE', None, None)
            assert path.is_file()

        # Get URI from data product
        product = MastMissions.get_product_list('Z14Z0104T')[0]
        uri = product['uri']
        filename = Path(uri).name

        # Download with unspecified local_path
        # Should download to current working directory
        result = MastMissions.download_file(uri)
        check_result(result, Path(os.getcwd(), filename))
        Path.unlink(filename)  # clean up file

        # Download with directory as local_path parameter
        local_path = Path(tmp_path, filename)
        result = MastMissions.download_file(uri, local_path=tmp_path)
        check_result(result, local_path)

        # Download with filename as local_path parameter
        local_path_file = Path(tmp_path, 'test.fits')
        result = MastMissions.download_file(uri, local_path=local_path_file)
        check_result(result, local_path_file)

    @pytest.mark.parametrize("mission, query_params", [
        ('jwst', {'fileSetName': 'jw01189001001_02101_00001'}),
        ('classy', {'Target': 'J0021+0052'}),
        ('ullyses', {'host_galaxy_name': 'WLM', 'select_cols': ['observation_id']})
    ])
    def test_missions_workflow(self, tmp_path, mission, query_params):
        # Test workflow with other missions
        m = MastMissions(mission=mission)

        # Criteria query
        datasets = m.query_criteria(**query_params)
        assert isinstance(datasets, Table)
        assert len(datasets)

        # Get products
        prods = m.get_product_list(datasets[0])
        assert isinstance(prods, Table)
        assert len(prods)

        # Download products
        result = m.download_products(prods[:3],
                                     download_dir=tmp_path)
        for row in result:
            if row['Status'] == 'COMPLETE':
                assert (row['Local Path']).is_file()

    ###################
    # MastClass tests #
    ###################

    def test_mast_service_request_async(self):
        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.001}
        responses = Mast.service_request_async(service, params)

        assert isinstance(responses, list)

    def test_mast_service_request(self):
        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.001}

        result = Mast.service_request(service, params, pagesize=10, page=2)

        # Is result in the right format
        assert isinstance(result, Table)

        # Is result limited to ten rows
        assert len(result) == 10

        # Are the GALEX observations in the results table
        assert "GALEX" in result['obs_collection']

        # Are the two GALEX observations with obs_id 6374399093149532160 in the results table
        assert len(result[np.where(result["obs_id"] == "6374399093149532160")]) == 2

    def test_mast_query(self):
        result = Mast.mast_query('Mast.Caom.Cone', ra=184.3, dec=54.5, radius=0.2)

        # Is result in the right format
        assert isinstance(result, Table)

        # Are the GALEX observations in the results table
        assert "GALEX" in result['obs_collection']

        # Are the two GALEX observations with obs_id 6374399093149532160 in the results table
        assert len(result[np.where(result["obs_id"] == "6374399093149532160")]) == 2

    def test_mast_session_info(self):
        sessionInfo = Mast.session_info(verbose=False)
        assert sessionInfo['ezid'] == 'anonymous'
        assert sessionInfo['token'] is None

    ###########################
    # ObservationsClass tests #
    ###########################

    def test_observations_list_missions(self):
        missions = Observations.list_missions()
        assert isinstance(missions, list)
        for m in ['HST', 'HLA', 'GALEX', 'Kepler']:
            assert m in missions

    def test_get_metadata(self):
        # observations
        meta_table = Observations.get_metadata("observations")
        assert isinstance(meta_table, Table)
        assert "Column Name" in meta_table.colnames
        assert "Mission" in meta_table["Column Label"]
        assert "obsid" in meta_table["Column Name"]

        # products
        meta_table = Observations.get_metadata("products")
        assert isinstance(meta_table, Table)
        assert "Column Name" in meta_table.colnames
        assert "Observation ID" in meta_table["Column Label"]
        assert "parent_obsid" in meta_table["Column Name"]

    # query functions

    def test_observations_query_region_async(self):
        responses = Observations.query_region_async("322.49324 12.16683", radius="0.005 deg")
        assert isinstance(responses, list)

    def test_observations_query_region(self):
        result = Observations.query_region("322.49324 12.16683", radius="0.005 deg")
        assert isinstance(result, Table)
        assert len(result) > 500
        assert result[np.where(result['obs_id'] == '00031992001')]

        result = Observations.query_region("322.49324 12.16683", radius="0.005 deg",
                                           pagesize=1, page=1)
        assert isinstance(result, Table)
        assert len(result) == 1

    def test_observations_query_object_async(self):
        responses = Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):
        result = Observations.query_object("M8", radius=".04 deg")
        assert isinstance(result, Table)
        assert len(result) > 150
        assert result[np.where(result['obs_id'] == 'ktwo200071160-c92_lc')]

    def test_observations_query_criteria_async(self):
        # without position
        responses = Observations.query_criteria_async(dataproduct_type=["image"],
                                                      proposal_pi="*Ost*",
                                                      s_dec=[43.5, 43.6])
        assert isinstance(responses, list)

        # with position
        responses = Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                      objectname="M10")
        assert isinstance(responses, list)

    def test_observations_query_criteria(self):
        # without position
        result = Observations.query_criteria(instrument_name="*WFPC2*",
                                             proposal_id=8169,
                                             t_min=[51361, 51362])

        assert isinstance(result, Table)
        assert len(result) == 13
        assert ((result['obs_collection'] == 'HST') | (result['obs_collection'] == 'HLA')).all()

        # with position
        result = Observations.query_criteria(objectname="M10",
                                             filters=["NUV", "FUV"],
                                             obs_collection="GALEX")
        assert isinstance(result, Table)
        assert len(result) == 7
        assert (result['obs_collection'] == 'GALEX').all()
        assert sum(result['filters'] == 'NUV') == 4

        result = Observations.query_criteria(objectname="M10",
                                             dataproduct_type="IMAGE",
                                             intentType="calibration")
        assert (result["intentType"] == "calibration").all()

        # with case-insensitive keyword arguments
        result = Observations.query_criteria(Instrument_Name="*WFPC2*",
                                             proposal_ID=8169,
                                             T_min=[51361, 51362])
        assert isinstance(result, Table)
        assert len(result) == 13

    def test_observations_query_criteria_invalid_keyword(self):
        # attempt to make a criteria query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_no_alt:
            Observations.query_criteria_count(not_a_keyword='TESS')
        assert "Filter 'not_a_keyword' does not exist." in str(err_no_alt.value)

        # keyword is close enough for difflib to offer alternative
        with pytest.raises(InvalidQueryError) as err_with_alt:
            Observations.query_criteria_count(oops_collection='TESS')
        assert 'obs_collection' in str(err_with_alt.value)

    # count functions
    def test_observations_query_region_count(self):
        maxRes = Observations.query_criteria_count()
        result = Observations.query_region_count("322.49324 12.16683",
                                                 radius=1e-10 * u.deg)
        assert isinstance(result, (np.int64, int))
        assert result > 840
        assert result < maxRes

    def test_observations_query_object_count(self):
        maxRes = Observations.query_criteria_count()
        result = Observations.query_object_count("M8", radius=".02 deg")
        assert isinstance(result, (np.int64, int))
        assert result > 150
        assert result < maxRes

    def test_observations_query_criteria_count(self):
        maxRes = Observations.query_criteria_count()
        result = Observations.query_criteria_count(proposal_id=8880)
        assert isinstance(result, (np.int64, int))
        assert result == 8
        assert result < maxRes

    # product functions
    def test_observations_get_product_list_async(self):

        test_obs = Observations.query_criteria(filters=["NUV", "FUV"], objectname="M10")

        responses = Observations.get_product_list_async(test_obs[0]["obsid"])
        assert isinstance(responses, list)

        responses = Observations.get_product_list_async(test_obs[2:3])
        assert isinstance(responses, list)

        observations = Observations.query_object("M8", radius=".02 deg")
        responses = Observations.get_product_list_async(observations[0])
        assert isinstance(responses, list)

        responses = Observations.get_product_list_async(observations[0:4])
        assert isinstance(responses, list)

    def test_observations_get_product_list(self):
        observations = Observations.query_object("M8", radius=".04 deg")
        test_obs_id = str(observations[0]['obsid'])
        mult_obs_ids = str(observations[0]['obsid']) + ',' + str(observations[1]['obsid'])

        result1 = Observations.get_product_list(test_obs_id)
        result2 = Observations.get_product_list(observations[0])
        filenames1 = list(result1['productFilename'])
        filenames2 = list(result2['productFilename'])
        assert isinstance(result1, Table)
        assert len(result1) == len(result2)
        assert set(filenames1) == set(filenames2)

        result1 = Observations.get_product_list(mult_obs_ids)
        result2 = Observations.get_product_list(observations[0:2])
        filenames1 = result1['productFilename']
        filenames2 = result2['productFilename']
        assert isinstance(result1, Table)
        assert len(result1) == len(result2)
        assert set(filenames1) == set(filenames2)

        obsLoc = np.where(observations["obs_id"] == 'ktwo200071160-c92_lc')
        result = Observations.get_product_list(observations[obsLoc])
        assert isinstance(result, Table)
        assert len(result) == 1

        obsLocs = np.where((observations['target_name'] == 'NGC6523') & (observations['obs_collection'] == "IUE"))
        result = Observations.get_product_list(observations[obsLocs])
        obs_collection = np.unique(list(result['obs_collection']))
        assert isinstance(result, Table)
        assert len(obs_collection) == 1
        assert obs_collection[0] == 'IUE'

    def test_observations_get_product_list_tess_tica(self, caplog):
        # Get observations and products with both TESS and TICA FFIs
        obs = Observations.query_criteria(target_name=['TESS FFI', 'TICA FFI', '429031146'])
        prods = Observations.get_product_list(obs)

        # Check that WARNING messages about FFIs were logged
        with caplog.at_level("WARNING", logger="astroquery"):
            assert "TESS FFI products" in caplog.text
            assert "TICA FFI products" in caplog.text

        # Should only return products corresponding to target 429031146
        assert len(prods) > 0
        assert (np.char.find(prods['obs_id'], '429031146') != -1).all()

    def test_observations_get_unique_product_list(self, caplog):
        # Check that no rows are filtered out when all products are unique
        obsids = ['24832668']
        products = Observations.get_product_list(obsids)
        unique_products = Observations.get_unique_product_list(obsids)

        # Should have the same length
        assert len(products) == len(unique_products)
        # No INFO messages should be logged
        with caplog.at_level('INFO', logger='astroquery'):
            assert caplog.text == ''

        # Check that rows are filtered out when products are not unique
        obsids.append('26421364')
        products = Observations.get_product_list(obsids)
        unique_products = Observations.get_unique_product_list(obsids)

        # Unique product list should have fewer rows
        assert len(products) > len(unique_products)
        # Rows should be unique based on dataURI
        assert (unique_products == unique(unique_products, keys='dataURI')).all()
        # Check that INFO messages were logged
        with caplog.at_level('INFO', logger='astroquery'):
            assert 'products were duplicates' in caplog.text
            assert 'To return all products' in caplog.text

    def test_observations_filter_products(self):
        observations = Observations.query_object("M8", radius=".04 deg")
        obsLoc = np.where(observations["obs_id"] == 'ktwo200071160-c92_lc')
        products = Observations.get_product_list(observations[obsLoc])
        result = Observations.filter_products(products,
                                              productType=["SCIENCE"],
                                              mrp_only=False)
        assert isinstance(result, Table)
        assert len(result) == sum(products['productType'] == "SCIENCE")

    def test_observations_download_products(self, tmp_path):
        def check_filepath(path):
            assert os.path.isfile(path)

        test_obs_id = '25119363'
        result = Observations.download_products(test_obs_id,
                                                download_dir=tmp_path,
                                                productType=["SCIENCE"],
                                                mrp_only=False)
        assert isinstance(result, Table)
        for row in result:
            if row['Status'] == 'COMPLETE':
                check_filepath(row['Local Path'])

        # just get the curl script
        result = Observations.download_products(test_obs_id,
                                                download_dir=tmp_path,
                                                curl_flag=True,
                                                productType=["SCIENCE"],
                                                mrp_only=False)
        assert isinstance(result, Table)
        check_filepath(result['Local Path'][0])

        # check for row input
        result1 = Observations.get_product_list(test_obs_id)
        result2 = Observations.download_products(result1[0],
                                                 download_dir=tmp_path)
        assert isinstance(result2, Table)
        check_filepath(result2['Local Path'][0])
        assert len(result2) == 1

    def test_observations_download_products_flat(self, tmp_path, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download with flat=True
        manifest = Observations.download_products(products, flat=True, download_dir=tmp_path)

        assert Path(manifest["Local Path"][0]).parent == tmp_path

    def test_observations_download_products_flat_curl(self, tmp_path, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download with flat=True, curl_flag=True, look for warning
        with pytest.warns(InputWarning):
            Observations.download_products(products, flat=True,
                                           curl_flag=True,
                                           download_dir=tmp_path)

    def test_observations_download_products_no_duplicates(self, tmp_path, caplog, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download the product
        manifest = Observations.download_products(products, download_dir=tmp_path)

        # Check that it downloads the MSA config file only once
        assert len(manifest) == 1

        # Check that an INFO message about duplicates was logged
        with caplog.at_level("INFO", logger="astroquery"):
            assert "products were duplicates" in caplog.text

    def test_observations_download_file(self, tmp_path):

        def check_result(result, path):
            assert result == ('COMPLETE', None, None)
            assert os.path.exists(path)

        # get observations from GALEX instrument with query_criteria
        observations = Observations.query_criteria(objectname='M10',
                                                   radius=0.001,
                                                   instrument_name='GALEX')

        assert len(observations) > 0, 'No results found for GALEX query.'

        # pull data products from a single observation
        products = Observations.get_product_list(observations['obsid'][0])

        # pull the URI of a single product
        uri = products['dataURI'][0]
        filename = Path(uri).name

        # download with unspecified local_path parameter
        # should download to current working directory
        result = Observations.download_file(uri)
        check_result(result, Path(os.getcwd(), filename))
        Path.unlink(filename)  # clean up file

        # download with directory as local_path parameter
        local_path = Path(tmp_path, filename)
        result = Observations.download_file(uri, local_path=tmp_path)
        check_result(result, local_path)

        # download with filename as local_path parameter
        local_path_file = Path(tmp_path, "test.fits")
        result = Observations.download_file(uri, local_path=local_path_file)
        check_result(result, local_path_file)

    @pytest.mark.parametrize("in_uri", [
        'mast:HLA/url/cgi-bin/getdata.cgi?download=1&filename=hst_05206_01_wfpc2_f375n_wf_daophot_trm.cat',
        'mast:HST/product/u24r0102t_c3m.fits'
    ])
    def test_observations_download_file_cloud(self, tmp_path, in_uri):
        pytest.importorskip("boto3")

        Observations.enable_cloud_dataset()

        filename = Path(in_uri).name
        result = Observations.download_file(uri=in_uri, cloud_only=True, local_path=tmp_path)
        assert result == ('COMPLETE', None, None)
        assert Path(tmp_path, filename).exists()

    def test_observations_download_file_escaped(self, tmp_path):
        # test that `download_file` correctly escapes a URI
        in_uri = 'mast:HLA/url/cgi-bin/fitscut.cgi?' \
                 'red=hst_04819_65_wfpc2_f814w_pc&blue=hst_04819_65_wfpc2_f555w_pc&size=ALL&format=fits'
        filename = Path(in_uri).name
        result = Observations.download_file(uri=in_uri, local_path=tmp_path)
        assert result == ('COMPLETE', None, None)
        assert Path(tmp_path, filename).exists()

        # check that downloaded file is a valid FITS file
        f = fits.open(Path(tmp_path, filename))
        f.close()

    @pytest.mark.parametrize("test_data_uri, expected_cloud_uri", [
        ("mast:HST/product/u24r0102t_c1f.fits",
         "s3://stpubdata/hst/public/u24r/u24r0102t/u24r0102t_c1f.fits"),
        ("mast:PS1/product/rings.v3.skycell.1334.061.stk.r.unconv.exp.fits",
         "s3://stpubdata/panstarrs/ps1/public/rings.v3.skycell/1334/061/"
         "rings.v3.skycell.1334.061.stk.r.unconv.exp.fits")
    ])
    def test_observations_get_cloud_uri(self, test_data_uri, expected_cloud_uri):
        pytest.importorskip("boto3")
        # get a product list
        product = Table()
        product['dataURI'] = [test_data_uri]
        # enable access to public AWS S3 bucket
        Observations.enable_cloud_dataset()

        # get uri
        uri = Observations.get_cloud_uri(product[0])

        assert len(uri) > 0, f'Product for dataURI {test_data_uri} was not found in the cloud.'
        assert uri == expected_cloud_uri, f'Cloud URI does not match expected. ({uri} != {expected_cloud_uri})'

        # pass the URI as a string
        uri = Observations.get_cloud_uri(test_data_uri)
        assert uri == expected_cloud_uri, f'Cloud URI does not match expected. ({uri} != {expected_cloud_uri})'

    @pytest.mark.parametrize("test_obs_id", ["25568122", "31411", "107604081"])
    def test_observations_get_cloud_uris(self, test_obs_id):
        pytest.importorskip("boto3")

        # get a product list
        index = 24 if test_obs_id == '25568122' else 0
        products = Observations.get_product_list(test_obs_id)[index:index + 2]

        assert len(products) > 0, (f'No products found for OBSID {test_obs_id}. '
                                   'Unable to move forward with getting URIs from the cloud.')

        # enable access to public AWS S3 bucket
        Observations.enable_cloud_dataset()

        # get uris
        uris = Observations.get_cloud_uris(products)

        assert len(uris) > 0, f'Products for OBSID {test_obs_id} were not found in the cloud.'

        # check for warning if no data products match filters
        with pytest.warns(NoResultsWarning):
            Observations.get_cloud_uris(products,
                                        extension='png')

    def test_observations_get_cloud_uris_list_input(self):
        pytest.importorskip("boto3")
        uri_list = ['mast:HST/product/u24r0102t_c1f.fits',
                    'mast:PS1/product/rings.v3.skycell.1334.061.stk.r.unconv.exp.fits']
        expected = ['s3://stpubdata/hst/public/u24r/u24r0102t/u24r0102t_c1f.fits',
                    's3://stpubdata/panstarrs/ps1/public/rings.v3.skycell/1334/061/rings.v3.skycell.1334.'
                    '061.stk.r.unconv.exp.fits']

        # enable access to public AWS S3 bucket
        Observations.enable_cloud_dataset()

        # list of URI strings as input
        uris = Observations.get_cloud_uris(uri_list)
        assert len(uris) > 0, f'Products for URI list {uri_list} were not found in the cloud.'
        assert uris == expected

        # check for warning if filters are provided with list input
        with pytest.warns(InputWarning, match='Filtering is not supported'):
            Observations.get_cloud_uris(uri_list,
                                        extension='png')

        # check for warning if one of the URIs is not found
        with pytest.warns(NoResultsWarning, match='Failed to retrieve MAST relative path'):
            Observations.get_cloud_uris(['mast:HST/product/does_not_exist.fits'])

    def test_observations_get_cloud_uris_query(self):
        pytest.importorskip("boto3")

        # enable access to public AWS S3 bucket
        Observations.enable_cloud_dataset()

        # get uris with other functions
        obs = Observations.query_criteria(target_name=234295610)
        prod = Observations.get_product_list(obs)
        filt = Observations.filter_products(prod, calib_level=[2])
        s3_uris = Observations.get_cloud_uris(filt)

        # get uris with streamlined function
        uris = Observations.get_cloud_uris(target_name=234295610,
                                           filter_products={'calib_level': [2]})
        assert s3_uris == uris

        # check that InvalidQueryError is thrown if neither data_products or **criteria are defined
        with pytest.raises(InvalidQueryError):
            Observations.get_cloud_uris(filter_products={'calib_level': [2]})

        # check for warning if query returns no observations
        with pytest.warns(NoResultsWarning):
            Observations.get_cloud_uris(target_name=234295611)

    def test_observations_get_cloud_uris_no_duplicates(self, msa_product_table):
        pytest.importorskip("boto3")

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # enable access to public AWS S3 bucket
        Observations.enable_cloud_dataset(provider='AWS')

        # Check that only one URI is returned
        uris = Observations.get_cloud_uris(products)
        assert len(uris) == 1

    ######################
    # CatalogClass tests #
    ######################

    # query functions
    def test_catalogs_query_region_async(self):
        in_rad = 0.001 * u.deg
        responses = Catalogs.query_region_async("158.47924 -7.30962",
                                                radius=in_rad,
                                                catalog="Galex")
        assert isinstance(responses, list)

        # Default catalog is HSC
        responses = Catalogs.query_region_async("322.49324 12.16683",
                                                radius=in_rad)
        assert isinstance(responses, list)

        responses = Catalogs.query_region_async("322.49324 12.16683",
                                                radius=in_rad,
                                                catalog="panstarrs",
                                                table="mean")
        assert isinstance(responses, Response)

    def test_catalogs_query_region(self):
        def check_result(result, row, exp_values):
            assert isinstance(result, Table)
            for k, v in exp_values.items():
                assert result[row][k] == v

        in_radius = 0.1 * u.deg
        result = Catalogs.query_region("158.47924 -7.30962",
                                       radius=in_radius,
                                       catalog="Gaia")
        row = np.where(result['source_id'] == '3774902350511581696')
        check_result(result, row, {'solution_id': '1635721458409799680'})

        result = Catalogs.query_region("322.49324 12.16683",
                                       radius=0.001*u.deg,
                                       catalog="HSC",
                                       magtype=2)
        row = np.where(result['MatchID'] == '8150896')

        with pytest.warns(MaxResultsWarning):
            result = Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2, nr=5)

        check_result(result, row, {'NumImages': 14, 'TargetName': 'M15'})

        result = Catalogs.query_region("322.49324 12.16683",
                                       radius=0.001*u.deg,
                                       catalog="HSC",
                                       version=2,
                                       magtype=2)
        row = np.where(result['MatchID'] == '82361658')
        check_result(result, row, {'NumImages': 11, 'TargetName': 'NGC7078'})

        result = Catalogs.query_region("322.49324 12.16683",
                                       radius=in_radius,
                                       catalog="Gaia",
                                       version=1)
        row = np.where(result['source_id'] == '1745948323734098688')
        check_result(result, row, {'solution_id': '1635378410781933568'})
        result = Catalogs.query_region("322.49324 12.16683",
                                       radius=0.01*u.deg,
                                       catalog="Gaia",
                                       version=2)

        row = np.where(result['source_id'] == '1745947739618544000')
        check_result(result, row, {'solution_id': '1635721458409799680'})

        result = Catalogs.query_region("322.49324 12.16683",
                                       radius=0.01*u.deg, catalog="panstarrs",
                                       table="mean")
        row = np.where((result['objName'] == 'PSO J322.4622+12.1920') & (result['yFlags'] == 16777496))
        assert isinstance(result, Table)
        np.testing.assert_allclose(result[row]['distance'], 0.039381703406789904)

        result = Catalogs.query_region("158.47924 -7.30962",
                                       radius=in_radius,
                                       catalog="Galex")
        in_radius_arcmin = 0.1*u.deg.to(u.arcmin)
        distances = list(result['distance_arcmin'])
        assert isinstance(result, Table)
        assert max(distances) <= in_radius_arcmin

        result = Catalogs.query_region("158.47924 -7.30962",
                                       radius=in_radius,
                                       catalog="tic")
        row = np.where(result['ID'] == '841736289')
        second_id = result[1]['ID']
        check_result(result, row, {'gaiaqflag': 1})
        np.testing.assert_allclose(result[row]['RA_orig'], 158.475246786483)

        result = Catalogs.query_region("158.47924 -7.30962",
                                       radius=in_radius,
                                       catalog="tic",
                                       pagesize=1,
                                       page=2)
        assert isinstance(result, Table)
        assert len(result) == 1
        assert second_id == result[0]['ID']

        result = Catalogs.query_region("158.47924 -7.30962",
                                       radius=in_radius,
                                       catalog="ctl")
        row = np.where(result['ID'] == '56662064')
        check_result(result, row, {'TYC': '4918-01335-1'})

        result = Catalogs.query_region("210.80227 54.34895",
                                       radius=1*u.deg,
                                       catalog="diskdetective")
        row = np.where(result['designation'] == 'J140544.95+535941.1')
        check_result(result, row, {'ZooniverseID': 'AWI0000r57'})

    def test_catalogs_query_object_async(self):
        responses = Catalogs.query_object_async("M10",
                                                radius=.02,
                                                catalog="TIC")
        assert isinstance(responses, list)

    def test_catalogs_query_object(self):
        def check_result(result, exp_values):
            assert isinstance(result, Table)
            for k, v in exp_values.items():
                assert v in result[k]

        result = Catalogs.query_object("M10",
                                       radius=.001,
                                       catalog="TIC")
        check_result(result, {'ID': '1305764225'})
        second_id = result[1]['ID']

        result = Catalogs.query_object("M10",
                                       radius=.001,
                                       catalog="TIC",
                                       pagesize=1,
                                       page=2)
        assert isinstance(result, Table)
        assert len(result) == 1
        assert second_id == result[0]['ID']

        result = Catalogs.query_object("M10",
                                       radius=.001,
                                       catalog="HSC",
                                       magtype=1)
        check_result(result, {'MatchID': '667727'})

        result = Catalogs.query_object("M10",
                                       radius=.001,
                                       catalog="panstarrs",
                                       table="mean")
        check_result(result, {'objName': 'PSO J254.2873-04.1006'})

        result = Catalogs.query_object("M10",
                                       radius=0.18,
                                       catalog="diskdetective")
        check_result(result, {'designation': 'J165749.79-040315.1'})

        result = Catalogs.query_object("M10",
                                       radius=0.001,
                                       catalog="Gaia",
                                       version=1)
        distances = list(result['distance'])
        radius_arcmin = 0.01 * u.deg.to(u.arcmin)
        assert isinstance(result, Table)
        assert max(distances) < radius_arcmin

        result = Catalogs.query_object("TIC 441662144",
                                       radius=0.001,
                                       catalog="ctl")
        check_result(result, {'ID': '441662144'})

        result = Catalogs.query_object('M10',
                                       radius=0.08,
                                       catalog='plato')
        assert 'PICidDR1' in result.colnames

    def test_catalogs_query_criteria_async(self):
        # without position
        responses = Catalogs.query_criteria_async(catalog="Tic",
                                                  Bmag=[30, 50],
                                                  objType="STAR")
        assert isinstance(responses, list)

        responses = Catalogs.query_criteria_async(catalog="ctl",
                                                  Bmag=[30, 50],
                                                  objType="STAR")
        assert isinstance(responses, list)

        responses = Catalogs.query_criteria_async(catalog="DiskDetective",
                                                  state=["inactive", "disabled"],
                                                  oval=[8, 10],
                                                  multi=[3, 7])
        assert isinstance(responses, list)

        # with position
        responses = Catalogs.query_criteria_async(catalog="Tic",
                                                  objectname="M10",
                                                  objType="EXTENDED")
        assert isinstance(responses, list)

        responses = Catalogs.query_criteria_async(catalog="CTL",
                                                  objectname="M10",
                                                  objType="EXTENDED")
        assert isinstance(responses, list)

        responses = Catalogs.query_criteria_async(catalog="DiskDetective",
                                                  objectname="M10",
                                                  radius=2,
                                                  state="complete")
        assert isinstance(responses, list)

        responses = Catalogs.query_criteria_async(catalog="panstarrs",
                                                  table="mean",
                                                  objectname="M10",
                                                  radius=.02,
                                                  qualityFlag=48)
        assert isinstance(responses, Response)

    def test_catalogs_query_criteria(self):
        def check_result(result, exp_vals):
            assert isinstance(result, Table)
            for k, v in exp_vals.items():
                assert v in result[k]

        # without position
        result = Catalogs.query_criteria(catalog="Tic",
                                         Bmag=[30, 50],
                                         objType="STAR")
        check_result(result, {'ID': '81609218'})
        second_id = result[1]['ID']

        result = Catalogs.query_criteria(catalog="Tic",
                                         Bmag=[30, 50],
                                         objType="STAR",
                                         pagesize=1,
                                         page=2)
        assert isinstance(result, Table)
        assert len(result) == 1
        assert second_id == result[0]['ID']

        result = Catalogs.query_criteria(catalog="ctl",
                                         Tmag=[10.5, 11],
                                         POSflag="2mass")
        check_result(result, {'ID': '291067184'})

        result = Catalogs.query_criteria(catalog="DiskDetective",
                                         state=["inactive", "disabled"],
                                         oval=[8, 10],
                                         multi=[3, 7])
        check_result(result, {'designation': 'J003920.04-300132.4'})

        # with position
        result = Catalogs.query_criteria(catalog="Tic",
                                         objectname="M10", objType="EXTENDED")
        check_result(result, {'ID': '10000732589'})

        result = Catalogs.query_criteria(objectname='TIC 291067184',
                                         catalog="ctl",
                                         Tmag=[10.5, 11],
                                         POSflag="2mass")
        check_result(result, {'Tmag': 10.893})

        result = Catalogs.query_criteria(catalog="DiskDetective",
                                         objectname="M10",
                                         radius=2,
                                         state="complete")
        check_result(result, {'designation': 'J165628.40-054630.8'})

        result = Catalogs.query_criteria(catalog="panstarrs",
                                         objectname="M10",
                                         radius=.01,
                                         qualityFlag=32,
                                         zoneID=10306)
        check_result(result, {'objName': 'PSO J254.2861-04.1091'})

        result = Catalogs.query_criteria(coordinates="158.47924 -7.30962",
                                         radius=0.01,
                                         catalog="PANSTARRS",
                                         table="mean",
                                         data_release="dr2",
                                         nStackDetections=[("gte", "1")],
                                         columns=["objName", "distance"],
                                         sort_by=[("asc", "distance")])
        assert isinstance(result, Table)
        assert result['distance'][0] <= result['distance'][1]

        # with case-insensitive keyword arguments
        result = Catalogs.query_criteria(catalog="Tic",
                                         bMAG=[30, 50],
                                         objtype="STAR")
        check_result(result, {'ID': '81609218'})

        result = Catalogs.query_criteria(catalog="DiskDetective",
                                         STATE=["inactive", "disabled"],
                                         oVaL=[8, 10],
                                         Multi=[3, 7])
        check_result(result, {'designation': 'J003920.04-300132.4'})

    def test_catalogs_query_criteria_invalid_keyword(self):
        # attempt to make a criteria query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_no_alt:
            Catalogs.query_criteria(catalog='tic', not_a_keyword='TESS')
        assert "Filter 'not_a_keyword' does not exist." in str(err_no_alt.value)

        # keyword is close enough for difflib to offer alternative
        with pytest.raises(InvalidQueryError) as err_with_alt:
            Catalogs.query_criteria(catalog='ctl', objectType="STAR")
        assert 'objType' in str(err_with_alt.value)

        # region query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_region:
            Catalogs.query_region('322.49324 12.16683',
                                  radius=0.001*u.deg,
                                  catalog='HSC',
                                  invalid=2)
        assert "Filter 'invalid' does not exist for catalog HSC." in str(err_region.value)

        # panstarrs criteria query with invalid keyword
        with pytest.raises(InvalidQueryError) as err_ps_criteria:
            Catalogs.query_criteria(coordinates="158.47924 -7.30962",
                                    catalog="PANSTARRS",
                                    table="mean",
                                    data_release="dr2",
                                    columns=["objName", "distance"],
                                    sort_by=[("asc", "distance")],
                                    obj_name='invalid')
        assert 'objName' in str(err_ps_criteria.value)

    def test_catalogs_query_hsc_matchid_async(self):
        catalogData = Catalogs.query_object("M10",
                                            radius=.001,
                                            catalog="HSC",
                                            magtype=1)

        responses = Catalogs.query_hsc_matchid_async(catalogData[0])
        assert isinstance(responses, list)

        responses = Catalogs.query_hsc_matchid_async(catalogData[0]["MatchID"])
        assert isinstance(responses, list)

    def test_catalogs_query_hsc_matchid(self):
        catalogData = Catalogs.query_object("M10",
                                            radius=.001,
                                            catalog="HSC",
                                            magtype=1)
        matchid = catalogData[0]["MatchID"]

        result = Catalogs.query_hsc_matchid(catalogData[0])
        assert isinstance(result, Table)
        assert (result['MatchID'] == matchid).all()

        result2 = Catalogs.query_hsc_matchid(matchid)
        assert isinstance(result2, Table)
        assert len(result2) == len(result)
        assert (result2['MatchID'] == matchid).all()

    def test_catalogs_get_hsc_spectra_async(self):
        responses = Catalogs.get_hsc_spectra_async()
        assert isinstance(responses, list)

    def test_catalogs_get_hsc_spectra(self):
        result = Catalogs.get_hsc_spectra()
        assert isinstance(result, Table)
        assert result[np.where(result['MatchID'] == '19657846')]
        assert result[np.where(result['DatasetName'] == 'HAG_J072657.06+691415.5_J8HPAXAEQ_V01.SPEC1D')]

    def test_catalogs_download_hsc_spectra(self, tmpdir):
        allSpectra = Catalogs.get_hsc_spectra()

        # actually download the products
        result = Catalogs.download_hsc_spectra(allSpectra[10],
                                               download_dir=str(tmpdir))
        assert isinstance(result, Table)

        for row in result:
            if row['Status'] == 'COMPLETE':
                assert os.path.isfile(row['Local Path'])

        # just get the curl script
        result = Catalogs.download_hsc_spectra(allSpectra[20:24],
                                               download_dir=str(tmpdir), curl_flag=True)
        assert isinstance(result, Table)
        assert os.path.isfile(result['Local Path'][0])

    ######################
    # TesscutClass tests #
    ######################

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_get_sectors(self, product):
        def check_sector_table(sector_table):
            assert isinstance(sector_table, Table)
            assert len(sector_table) >= 1
            assert f"{name}-s00" in sector_table['sectorName'][0]
            assert sector_table['sector'][0] > 0
            assert sector_table['camera'][0] > 0
            assert sector_table['ccd'][0] > 0

        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        name = "tess" if product == "spoc" else product
        sector_table = Tesscut.get_sectors(coordinates=coord, product=product)
        check_sector_table(sector_table)

        sector_table = Tesscut.get_sectors(objectname="M104", product=product)
        check_sector_table(sector_table)

    def test_tesscut_get_sectors_mt(self):

        # Moving target functionality testing

        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        sector_table = Tesscut.get_sectors(objectname=moving_target_name,
                                           moving_target=True)
        assert isinstance(sector_table, Table)
        assert len(sector_table) >= 1
        assert sector_table['sectorName'][0] == "tess-s0006-1-1"
        assert sector_table['sector'][0] == 6
        assert sector_table['camera'][0] == 1
        assert sector_table['ccd'][0] == 1

        error_noname = ("Please specify the object name or ID (as understood by the "
                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) "
                        "of a moving target such as an asteroid or comet.")
        error_nameresolve = f"Could not resolve {moving_target_name} to a sky position."
        error_mt_coord = "Only one of moving_target and coordinates may be specified."
        error_name_coord = "Only one of objectname and coordinates may be specified."
        error_tica_mt = "Only SPOC is available for moving targets queries."

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_sectors(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            Tesscut.get_sectors(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_sectors(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_sectors(objectname=moving_target_name, coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_sectors(objectname=moving_target_name,
                                coordinates=coord,
                                moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets
        with pytest.raises(InvalidQueryError) as error_msg:
            sector_table = Tesscut.get_sectors(objectname=moving_target_name, product='tica',
                                               moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_download_cutouts(self, tmpdir, product):

        def check_manifest(manifest, ext="fits"):
            assert isinstance(manifest, Table)
            assert len(manifest) >= 1
            assert manifest["Local Path"][0][-4:] == ext
            for row in manifest:
                assert os.path.isfile(row['Local Path'])

        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        manifest = Tesscut.download_cutouts(product=product, coordinates=coord, size=1, path=str(tmpdir))
        check_manifest(manifest)

        coord = SkyCoord(107.18696, -70.50919, unit="deg")
        manifest = Tesscut.download_cutouts(product=product, coordinates=coord, size=1, sector=27,
                                            path=str(tmpdir))
        check_manifest(manifest)

        manifest = Tesscut.download_cutouts(product=product, coordinates=coord, size=[1, 1]*u.pix, sector=33,
                                            path=str(tmpdir))
        check_manifest(manifest)

        manifest = Tesscut.download_cutouts(product=product, coordinates=coord, size=1, sector=33,
                                            path=str(tmpdir), inflate=False)
        check_manifest(manifest, ".zip")

        manifest = Tesscut.download_cutouts(product=product, objectname="TIC 32449963", size=1, path=str(tmpdir))
        check_manifest(manifest, "fits")

    def test_tesscut_download_cutouts_mt(self, tmpdir):

        # Moving target functionality testing
        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        manifest = Tesscut.download_cutouts(objectname=moving_target_name,
                                            moving_target=True,
                                            sector=6,
                                            size=1,
                                            path=str(tmpdir))
        assert isinstance(manifest, Table)
        assert len(manifest) == 1
        assert manifest["Local Path"][0][-4:] == "fits"
        for row in manifest:
            assert os.path.isfile(row['Local Path'])

        error_noname = ("Please specify the object name or ID (as understood by the "
                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) of "
                        "a moving target such as an asteroid or comet.")
        error_nameresolve = f"Could not resolve {moving_target_name} to a sky position."
        error_mt_coord = "Only one of moving_target and coordinates may be specified."
        error_name_coord = "Only one of objectname and coordinates may be specified."
        error_tica_mt = "Only SPOC is available for moving targets queries."

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.download_cutouts(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            Tesscut.download_cutouts(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.download_cutouts(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.download_cutouts(objectname=moving_target_name, coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.download_cutouts(objectname=moving_target_name,
                                     coordinates=coord,
                                     moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.download_cutouts(objectname=moving_target_name, product='tica',
                                     moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_get_cutouts(self, product):

        def check_cutout_hdu(cutout_hdus_list):
            assert isinstance(cutout_hdus_list, list)
            assert len(cutout_hdus_list) >= 1
            assert isinstance(cutout_hdus_list[0], fits.HDUList)

        coord = SkyCoord(107.18696, -70.50919, unit="deg")

        cutout_hdus_list = Tesscut.get_cutouts(product=product,
                                               coordinates=coord,
                                               size=1,
                                               sector=33)
        check_cutout_hdu(cutout_hdus_list)

        coord = SkyCoord(349.62609, -47.12424, unit="deg")

        cutout_hdus_list = Tesscut.get_cutouts(product=product,
                                               coordinates=coord,
                                               size=[1, 1]*u.arcmin,
                                               sector=[28, 68])
        check_cutout_hdu(cutout_hdus_list)

        cutout_hdus_list = Tesscut.get_cutouts(product=product,
                                               objectname="TIC 32449963",
                                               size=1,
                                               sector=37)
        check_cutout_hdu(cutout_hdus_list)

    def test_tesscut_get_cutouts_mt(self):

        # Moving target functionality testing
        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        cutout_hdus_list = Tesscut.get_cutouts(objectname=moving_target_name,
                                               moving_target=True,
                                               sector=6,
                                               size=1)
        assert isinstance(cutout_hdus_list, list)
        assert len(cutout_hdus_list) == 1
        assert isinstance(cutout_hdus_list[0], fits.HDUList)

        error_noname = ("Please specify the object name or ID (as understood by the "
                        "`JPL ephemerides service <https://ssd.jpl.nasa.gov/horizons.cgi>`__) of "
                        "a moving target such as an asteroid or comet.")
        error_nameresolve = f"Could not resolve {moving_target_name} to a sky position."
        error_mt_coord = "Only one of moving_target and coordinates may be specified."
        error_name_coord = "Only one of objectname and coordinates may be specified."
        error_tica_mt = "Only SPOC is available for moving targets queries."

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_cutouts(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            Tesscut.get_cutouts(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_cutouts(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_cutouts(objectname=moving_target_name,
                                coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_cutouts(objectname=moving_target_name,
                                coordinates=coord,
                                moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets

        with pytest.raises(InvalidQueryError) as error_msg:
            Tesscut.get_cutouts(objectname=moving_target_name, product='tica',
                                moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    ###################
    # ZcutClass tests #
    ###################
    def test_zcut_get_surveys(self):
        def check_survey_list(survery_list, no_results=True):
            assert isinstance(survery_list, list)
            assert len(survery_list) == 0 if no_results else len(survery_list) >= 1

        coord = SkyCoord(189.49206, 62.20615, unit="deg")
        survey_list = Zcut.get_surveys(coordinates=coord)
        check_survey_list(survey_list, False)
        assert survey_list[0] == 'candels_gn_60mas'
        assert survey_list[1] == 'candels_gn_30mas'
        assert survey_list[2] == 'goods_north'

        # This should always return no results
        coord = SkyCoord(57.10523, -30.08085, unit="deg")
        with pytest.warns(NoResultsWarning):
            survey_list = Zcut.get_surveys(coordinates=coord, radius=0)
            check_survey_list(survey_list)

        coord = SkyCoord(57.10523, -30.08085, unit="deg")
        with pytest.warns(NoResultsWarning):
            survey_list = Zcut.get_surveys(coordinates=coord, radius=0)
            check_survey_list(survey_list)

    def test_zcut_download_cutouts(self, tmpdir):

        def check_cutout(cutout_table, ext):
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) >= 1
            assert cutout_table["Local Path"][0][-4:] == ext
            assert os.path.isfile(cutout_table[0]['Local Path'])

        coord = SkyCoord(34.47320, -5.24271, unit="deg")
        cutout_table = Zcut.download_cutouts(coordinates=coord, size=1, path=str(tmpdir))
        check_cutout(cutout_table, "fits")

        coord = SkyCoord(189.28065571, 62.17415175, unit="deg")
        cutout_table = Zcut.download_cutouts(coordinates=coord, size=[1, 1], cutout_format="jpg", path=str(tmpdir))
        check_cutout(cutout_table, ".jpg")

        cutout_table = Zcut.download_cutouts(
            coordinates=coord, size=1, units='1*u.arcsec', cutout_format="png", path=str(tmpdir))
        check_cutout(cutout_table, ".png")

        # Intentionally returns no results
        with pytest.warns(NoResultsWarning):
            cutout_table = Zcut.download_cutouts(coordinates=coord,
                                                 survey='candels_gn_30mas',
                                                 cutout_format="jpg",
                                                 path=str(tmpdir))
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) == 0

        cutout_table = Zcut.download_cutouts(
            coordinates=coord, size=1, survey='goods_north', cutout_format="jpg", path=str(tmpdir))
        check_cutout(cutout_table, ".jpg")

        cutout_table = Zcut.download_cutouts(
            coordinates=coord, size=1, cutout_format="jpg", path=str(tmpdir), stretch='asinh', invert=True)
        check_cutout(cutout_table, ".jpg")

    def test_zcut_get_cutouts(self):
        def check_cutout_list(cutout_list, multi=True):
            assert isinstance(cutout_list, list)
            assert isinstance(cutout_list[0], fits.HDUList)
            assert len(cutout_list) >= 1 if multi else len(cutout_list) == 1

        coord = SkyCoord(189.28065571, 62.17415175, unit="deg")

        cutout_list = Zcut.get_cutouts(coordinates=coord, size=1)
        check_cutout_list(cutout_list)

        cutout_list = Zcut.get_cutouts(coordinates=coord, size=[1, 1])
        check_cutout_list(cutout_list)

        # Intentionally returns no results
        with pytest.warns(NoResultsWarning):
            cutout_list = Zcut.get_cutouts(coordinates=coord,
                                           survey='candels_gn_30mas')
            assert isinstance(cutout_list, list)
            assert len(cutout_list) == 0

        cutout_list = Zcut.get_cutouts(coordinates=coord,
                                       survey='3dhst_goods-n',
                                       size=1)
        check_cutout_list(cutout_list, multi=False)

    ###################
    # HapcutClass tests #
    ###################

    def test_hapcut_download_cutouts(self, tmpdir):
        def check_cutout_table(cutout_table, check_shape=True, data_shape=None):
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) >= 1
            for row in cutout_table:
                assert os.path.isfile(row['Local Path'])
                if check_shape and 'fits' in os.path.basename(row['Local Path']):
                    assert fits.getdata(row['Local Path']).shape == data_shape

        # Test 1: Simple API call with expected results
        coord = SkyCoord(351.347812, 28.497808, unit="deg")

        cutout_table = Hapcut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
        check_cutout_table(cutout_table, data_shape=(5, 5))

        # Test 2: Make input size a list
        cutout_table = Hapcut.download_cutouts(coordinates=coord, size=[2, 3], path=str(tmpdir))
        check_cutout_table(cutout_table, data_shape=(3, 2))

        # Test 3: Specify unit for input size
        cutout_table = Hapcut.download_cutouts(coordinates=coord, size=5*u.arcsec, path=str(tmpdir))
        check_cutout_table(cutout_table, check_shape=False)

        # Test 4: Intentional API call with no results
        bad_coord = SkyCoord(102.7, 70.50, unit="deg")
        with pytest.warns(NoResultsWarning, match='Missing HAP files for input target. Cutout not performed.'):
            cutout_table = Hapcut.download_cutouts(coordinates=bad_coord, size=5, path=str(tmpdir))
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) == 0

    def test_hapcut_get_cutouts(self):
        def check_cutout_list(cutout_list, data_shape):
            assert isinstance(cutout_list, list)
            assert len(cutout_list) >= 1
            assert isinstance(cutout_list[0], fits.HDUList)
            assert cutout_list[0][1].data.shape == data_shape

        # Test 1: Simple API call with expected results
        coord = SkyCoord(351.347812, 28.497808, unit="deg")

        cutout_list = Hapcut.get_cutouts(coordinates=coord)
        check_cutout_list(cutout_list, (5, 5))

        # Test 2: Make input size a list
        cutout_list = Hapcut.get_cutouts(coordinates=coord, size=[2, 3])
        check_cutout_list(cutout_list, (3, 2))

        # Test 3: Specify unit for input size
        cutout_list = Hapcut.get_cutouts(coordinates=coord, size=5*u.arcsec)
        check_cutout_list(cutout_list, (42, 42))

        # Test 4: Intentional API call with no results
        bad_coord = SkyCoord(102.7, 70.50, unit="deg")

        with pytest.warns(NoResultsWarning, match='Missing HAP files for input target. Cutout not performed.'):
            cutout_list = Hapcut.get_cutouts(coordinates=bad_coord)
            assert isinstance(cutout_list, list)
            assert len(cutout_list) == 0
