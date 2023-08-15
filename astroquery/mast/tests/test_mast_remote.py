# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pathlib import Path
import numpy as np
import os
import pytest

from requests.models import Response

from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u

from astroquery import mast

from ..utils import ResolverError
from ...exceptions import (InputWarning, InvalidQueryError, MaxResultsWarning,
                           NoResultsWarning)


OBSID = '1647157'


@pytest.fixture(scope="module")
def msa_product_table():
    # Pull products for a JWST NIRSpec MSA observation with 6 known
    # duplicates of the MSA configuration file, propID=2736
    products = mast.Observations.get_product_list("87602009")

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
        m101_loc = mast.utils.resolve_object("M101")
        assert round(m101_loc.separation(SkyCoord("210.80227 54.34895", unit='deg')).value, 4) == 0

        ticobj_loc = mast.utils.resolve_object("TIC 141914082")
        assert round(ticobj_loc.separation(SkyCoord("94.6175354 -72.04484622", unit='deg')).value, 4) == 0

    ###################
    # MastClass tests #
    ###################

    def test_mast_service_request_async(self):
        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.2}
        responses = mast.Mast.service_request_async(service, params)

        assert isinstance(responses, list)

    def test_mast_service_request(self):

        # clear columns config
        mast.Mast._column_configs = dict()

        service = 'Mast.Caom.Cone'
        params = {'ra': 184.3,
                  'dec': 54.5,
                  'radius': 0.2}

        result = mast.Mast.service_request(service, params)

        # Is result in the right format
        assert isinstance(result, Table)

        # Are the GALEX observations in the results table
        assert "GALEX" in result['obs_collection']

        # Are the two GALEX observations with obs_id 6374399093149532160 in the results table
        assert len(result[np.where(result["obs_id"] == "6374399093149532160")]) == 2

    def test_mast_query(self):
        # clear columns config
        mast.Mast._column_configs = dict()

        result = mast.Mast.mast_query('Mast.Caom.Cone', ra=184.3, dec=54.5, radius=0.2)

        # Is result in the right format
        assert isinstance(result, Table)

        # Are the GALEX observations in the results table
        assert "GALEX" in result['obs_collection']

        # Are the two GALEX observations with obs_id 6374399093149532160 in the results table
        assert len(result[np.where(result["obs_id"] == "6374399093149532160")]) == 2

    def test_mast_session_info(self):
        sessionInfo = mast.Mast.session_info(verbose=False)
        assert sessionInfo['ezid'] == 'anonymous'
        assert sessionInfo['token'] is None

    ###########################
    # ObservationsClass tests #
    ###########################

    def test_observations_list_missions(self):
        missions = mast.Observations.list_missions()
        assert isinstance(missions, list)
        for m in ['HST', 'HLA', 'GALEX', 'Kepler']:
            assert m in missions

    def test_get_metadata(self):
        # observations
        meta_table = mast.Observations.get_metadata("observations")
        assert isinstance(meta_table, Table)
        assert "Column Name" in meta_table.colnames
        assert "Mission" in meta_table["Column Label"]
        assert "obsid" in meta_table["Column Name"]

        # products
        meta_table = mast.Observations.get_metadata("products")
        assert isinstance(meta_table, Table)
        assert "Column Name" in meta_table.colnames
        assert "Observation ID" in meta_table["Column Label"]
        assert "parent_obsid" in meta_table["Column Name"]

    # query functions

    def test_observations_query_region_async(self):
        responses = mast.Observations.query_region_async("322.49324 12.16683", radius="0.005 deg")
        assert isinstance(responses, list)

    def test_observations_query_region(self):

        # clear columns config
        mast.Observations._column_configs = dict()

        result = mast.Observations.query_region("322.49324 12.16683", radius="0.005 deg")
        assert isinstance(result, Table)
        assert len(result) > 500
        assert result[np.where(result['obs_id'] == '00031992001')]

        result = mast.Observations.query_region("322.49324 12.16683", radius="0.005 deg",
                                                pagesize=1, page=1)
        assert isinstance(result, Table)
        assert len(result) == 1

    def test_observations_query_object_async(self):
        responses = mast.Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):

        # clear columns config
        mast.Observations._column_configs = dict()

        result = mast.Observations.query_object("M8", radius=".04 deg")
        assert isinstance(result, Table)
        assert len(result) > 150
        assert result[np.where(result['obs_id'] == 'ktwo200071160-c92_lc')]

    def test_observations_query_criteria_async(self):
        # without position
        responses = mast.Observations.query_criteria_async(dataproduct_type=["image"],
                                                           proposal_pi="*Ost*",
                                                           s_dec=[43.5, 45.5])
        assert isinstance(responses, list)

        # with position
        responses = mast.Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                           objectname="M101")
        assert isinstance(responses, list)

    def test_observations_query_criteria(self):

        # clear columns config
        mast.Observations._column_configs = dict()

        # without position
        result = mast.Observations.query_criteria(instrument_name="*WFPC2*",
                                                  proposal_id=8169,
                                                  t_min=[49335, 51499])

        assert isinstance(result, Table)
        assert len(result) == 57
        assert ((result['obs_collection'] == 'HST') | (result['obs_collection'] == 'HLA')).all()

        # with position
        result = mast.Observations.query_criteria(filters=["NUV", "FUV"],
                                                  obs_collection="GALEX",
                                                  objectname="M101")
        assert isinstance(result, Table)
        assert len(result) == 12
        assert (result['obs_collection'] == 'GALEX').all()
        assert sum(result['filters'] == 'NUV') == 6

        result = mast.Observations.query_criteria(objectname="M101",
                                                  dataproduct_type="IMAGE", intentType="calibration")
        assert (result["intentType"] == "calibration").all()

    # count functions
    def test_observations_query_region_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_region_count("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, (np.int64, int))
        assert result > 1800
        assert result < maxRes

    def test_observations_query_object_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_object_count("M8", radius=".02 deg")
        assert isinstance(result, (np.int64, int))
        assert result > 150
        assert result < maxRes

    def test_observations_query_criteria_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_criteria_count(proposal_pi="*Osten*",
                                                        proposal_id=8880)
        assert isinstance(result, (np.int64, int))
        assert result == 7
        assert result < maxRes

    # product functions
    def test_observations_get_product_list_async(self):

        test_obs = mast.Observations.query_criteria(filters=["NUV", "FUV"], objectname="M101")

        responses = mast.Observations.get_product_list_async(test_obs[0]["obsid"])
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async(test_obs[2:3])
        assert isinstance(responses, list)

        observations = mast.Observations.query_object("M8", radius=".02 deg")
        responses = mast.Observations.get_product_list_async(observations[0])
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async(observations[0:4])
        assert isinstance(responses, list)

    def test_observations_get_product_list(self):

        # clear columns config
        mast.Observations._column_configs = dict()

        observations = mast.Observations.query_object("M8", radius=".04 deg")
        test_obs_id = str(observations[0]['obsid'])
        mult_obs_ids = str(observations[0]['obsid']) + ',' + str(observations[1]['obsid'])

        result1 = mast.Observations.get_product_list(test_obs_id)
        result2 = mast.Observations.get_product_list(observations[0])
        filenames1 = list(result1['productFilename'])
        filenames2 = list(result2['productFilename'])
        assert isinstance(result1, Table)
        assert len(result1) == len(result2)
        assert set(filenames1) == set(filenames2)

        result1 = mast.Observations.get_product_list(mult_obs_ids)
        result2 = mast.Observations.get_product_list(observations[0:2])
        filenames1 = result1['productFilename']
        filenames2 = result2['productFilename']
        assert isinstance(result1, Table)
        assert len(result1) == len(result2)
        assert set(filenames1) == set(filenames2)

        obsLoc = np.where(observations["obs_id"] == 'ktwo200071160-c92_lc')
        result = mast.Observations.get_product_list(observations[obsLoc])
        assert isinstance(result, Table)
        assert len(result) == 1

        obsLocs = np.where((observations['target_name'] == 'NGC6523') & (observations['obs_collection'] == "IUE"))
        result = mast.Observations.get_product_list(observations[obsLocs])
        obs_collection = np.unique(list(result['obs_collection']))
        assert isinstance(result, Table)
        assert len(obs_collection) == 1
        assert obs_collection[0] == 'IUE'

    def test_observations_filter_products(self):
        observations = mast.Observations.query_object("M8", radius=".04 deg")
        obsLoc = np.where(observations["obs_id"] == 'ktwo200071160-c92_lc')
        products = mast.Observations.get_product_list(observations[obsLoc])
        result = mast.Observations.filter_products(products,
                                                   productType=["SCIENCE"],
                                                   mrp_only=False)
        assert isinstance(result, Table)
        assert len(result) == sum(products['productType'] == "SCIENCE")

    # test downloads 150+ files, 50MB+, TODO: revise OBSID to query only a few, small files for download
    @pytest.mark.skip("Tests should not download this much data. Skipping until revised.")
    def test_observations_download_products(self, tmpdir):
        test_obs_id = OBSID
        result = mast.Observations.download_products(test_obs_id,
                                                     download_dir=str(tmpdir),
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)
        for row in result:
            if row['Status'] == 'COMPLETE':
                assert os.path.isfile(row['Local Path'])

        # just get the curl script
        result = mast.Observations.download_products(test_obs_id[0]["obsid"],
                                                     download_dir=str(tmpdir),
                                                     curl_flag=True,
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)
        assert os.path.isfile(result['Local Path'][0])

        # check for row input
        result1 = mast.Observations.get_product_list(test_obs_id[0]["obsid"])
        result2 = mast.Observations.download_products(result1[0])
        assert isinstance(result2, Table)
        assert os.path.isfile(result2['Local Path'][0])
        assert len(result2) == 1

    def test_observations_download_products_flat(self, tmp_path, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download with flat=True
        manifest = mast.Observations.download_products(products, flat=True,
                                                       download_dir=tmp_path)

        assert Path(manifest["Local Path"][0]).parent == tmp_path

    def test_observations_download_products_flat_curl(self, tmp_path, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download with flat=True, curl_flag=True, look for warning
        with pytest.warns(InputWarning):
            mast.Observations.download_products(products, flat=True,
                                                curl_flag=True,
                                                download_dir=tmp_path)

    def test_observations_download_products_no_duplicates(self, tmp_path, caplog, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # Download the product
        manifest = mast.Observations.download_products(products,
                                                       download_dir=tmp_path)

        # Check that it downloads the MSA config file only once
        assert len(manifest) == 1

        # Check that an INFO message about duplicates was logged
        with caplog.at_level("INFO", logger="astroquery"):
            assert "products were duplicates" in caplog.text

    def test_observations_get_cloud_uris_no_duplicates(self, msa_product_table):

        # Get a product list with 6 duplicate JWST MSA config files
        products = msa_product_table

        assert len(products) == 6

        # enable access to public AWS S3 bucket
        mast.Observations.enable_cloud_dataset(provider='AWS')

        # Check for cloud URIs.  Accept a NoResultsWarning if AWS S3
        # doesn't have the file.  It doesn't matter as we're only checking
        # that the duplicate products have been culled to a single one.
        with pytest.warns(NoResultsWarning):
            uris = mast.Observations.get_cloud_uris(products)
        assert len(uris) == 1

    def test_observations_download_file(self, tmp_path):

        # get observations from GALEX instrument with query_criteria
        observations = mast.Observations.query_criteria(objectname='M1',
                                                        radius=0.2,
                                                        instrument_name='GALEX')

        assert len(observations) > 0, 'No results found for GALEX query.'

        # pull data products from a single observation
        products = mast.Observations.get_product_list(observations['obsid'][0])

        # pull the URI of a single product
        uri = products['dataURI'][0]
        local_path = Path(tmp_path, Path(uri).name)

        # download it
        result = mast.Observations.download_file(uri, local_path=local_path)
        assert result == ('COMPLETE', None, None)

    @pytest.mark.parametrize("test_data_uri, expected_cloud_uri", [
        ("mast:HST/product/u24r0102t_c1f.fits",
         "s3://stpubdata/hst/public/u24r/u24r0102t/u24r0102t_c1f.fits"),
        ("mast:PS1/product/rings.v3.skycell.1334.061.stk.r.unconv.exp.fits",
         "s3://stpubdata/panstarrs/ps1/public/rings.v3.skycell/1334/061/"
         "rings.v3.skycell.1334.061.stk.r.unconv.exp.fits")
    ])
    def test_get_cloud_uri(self, test_data_uri, expected_cloud_uri):
        pytest.importorskip("boto3")
        # get a product list
        product = Table()
        product['dataURI'] = [test_data_uri]
        # enable access to public AWS S3 bucket
        mast.Observations.enable_cloud_dataset()

        # get uri
        uri = mast.Observations.get_cloud_uri(product[0])

        assert len(uri) > 0, f'Product for dataURI {test_data_uri} was not found in the cloud.'
        assert uri == expected_cloud_uri, f'Cloud URI does not match expected. ({uri} != {expected_cloud_uri})'

    def test_get_cloud_uris(self):
        pytest.importorskip("boto3")
        test_obs_id = '25568122'

        # get a product list
        products = mast.Observations.get_product_list(test_obs_id)[24:]

        assert len(products) > 0, (f'No products found for OBSID {test_obs_id}. '
                                   'Unable to move forward with getting URIs from the cloud.')

        # enable access to public AWS S3 bucket
        mast.Observations.enable_cloud_dataset()

        # get uris
        uris = mast.Observations.get_cloud_uris(products)

        assert len(uris) > 0, f'Products for OBSID {test_obs_id} were not found in the cloud.'

    ######################
    # CatalogClass tests #
    ######################

    # query functions
    def test_catalogs_query_region_async(self):
        responses = mast.Catalogs.query_region_async("158.47924 -7.30962", catalog="Galex")
        assert isinstance(responses, list)

        # Default catalog is HSC
        responses = mast.Catalogs.query_region_async("322.49324 12.16683",
                                                     radius="0.02 deg")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_region_async("322.49324 12.16683",
                                                     radius="0.02 deg",
                                                     catalog="panstarrs", table="mean")
        assert isinstance(responses, Response)

    def test_catalogs_query_region(self):

        # clear columns config
        mast.Catalogs._column_configs = dict()
        in_radius = 0.1 * u.deg

        result = mast.Catalogs.query_region("158.47924 -7.30962",
                                            radius=in_radius,
                                            catalog="Gaia")
        row = np.where(result['source_id'] == '3774902350511581696')
        assert isinstance(result, Table)
        assert result[row]['solution_id'] == '1635721458409799680'

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=0.01*u.deg,
                                            catalog="HSC",
                                            magtype=2)
        row = np.where(result['MatchID'] == '78095437')

        with pytest.warns(MaxResultsWarning):
            result = mast.Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2)

        assert isinstance(result, Table)
        assert result[row]['NumImages'] == 1
        assert result[row]['TargetName'] == 'M15'

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=0.01*u.deg,
                                            catalog="HSC",
                                            version=2,
                                            magtype=2)
        row = np.where(result['MatchID'] == '82368728')

        with pytest.warns(MaxResultsWarning):
            result = mast.Catalogs.query_region("322.49324 12.16683", catalog="HSC",
                                                version=2, magtype=2)
        assert isinstance(result, Table)
        assert result[row]['NumImages'] == 11
        assert result[row]['TargetName'] == 'NGC7078'

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=in_radius,
                                            catalog="Gaia",
                                            version=1)
        row = np.where(result['source_id'] == '1745948323734098688')
        assert isinstance(result, Table)
        assert result[row]['solution_id'] == '1635378410781933568'

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=in_radius,
                                            catalog="Gaia",
                                            version=2)

        row = np.where(result['source_id'] == '1745973204477191424')
        assert isinstance(result, Table)
        assert result[row]['solution_id'] == '1635721458409799680'

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=in_radius, catalog="panstarrs",
                                            table="mean")
        row = np.where((result['objName'] == 'PSO J322.4622+12.1920') & (result['yFlags'] == 16777496))
        assert isinstance(result, Table)
        np.testing.assert_allclose(result[row]['distance'], 0.039381703406789904)

        result = mast.Catalogs.query_region("322.49324 12.16683",
                                            radius=in_radius, catalog="panstarrs",
                                            table="mean",
                                            pagesize=3)
        assert isinstance(result, Table)
        assert len(result) == 3

        result = mast.Catalogs.query_region("158.47924 -7.30962",
                                            radius=in_radius,
                                            catalog="Galex")
        in_radius_arcmin = 0.1*u.deg.to(u.arcmin)
        distances = list(result['distance_arcmin'])
        assert isinstance(result, Table)
        assert max(distances) <= in_radius_arcmin

        result = mast.Catalogs.query_region("158.47924 -7.30962",
                                            radius=in_radius,
                                            catalog="tic")
        row = np.where(result['ID'] == '841736289')
        assert isinstance(result, Table)
        np.testing.assert_allclose(result[row]['RA_orig'], 158.475246786483)
        assert result[row]['gaiaqflag'] == 1

        result = mast.Catalogs.query_region("158.47924 -7.30962",
                                            radius=in_radius,
                                            catalog="ctl")
        row = np.where(result['ID'] == '56662064')
        assert isinstance(result, Table)
        assert result[row]['TYC'] == '4918-01335-1'

        result = mast.Catalogs.query_region("210.80227 54.34895",
                                            radius=1*u.deg,
                                            catalog="diskdetective")
        row = np.where(result['designation'] == 'J140544.95+535941.1')
        assert isinstance(result, Table)
        assert result[row]['ZooniverseID'] == 'AWI0000r57'

    def test_catalogs_query_object_async(self):
        responses = mast.Catalogs.query_object_async("M10",
                                                     radius=.02,
                                                     catalog="TIC")
        assert isinstance(responses, list)

    def test_catalogs_query_object(self):

        # clear columns config
        mast.Catalogs._column_configs = dict()

        result = mast.Catalogs.query_object("M10",
                                            radius=".02 deg",
                                            catalog="TIC")
        assert isinstance(result, Table)
        assert '189844449' in result['ID']

        result = mast.Catalogs.query_object("M10",
                                            radius=.001,
                                            catalog="HSC",
                                            magtype=1)
        assert isinstance(result, Table)
        assert '60112519' in result['MatchID']

        result = mast.Catalogs.query_object("M10",
                                            radius=.001,
                                            catalog="panstarrs",
                                            table="mean")
        assert isinstance(result, Table)
        assert 'PSO J254.2872-04.0991' in result['objName']

        result = mast.Catalogs.query_object("M101",
                                            radius=1,
                                            catalog="diskdetective")
        assert isinstance(result, Table)
        assert 'J140758.82+534902.4' in result['designation']

        result = mast.Catalogs.query_object("M10",
                                            radius=0.01,
                                            catalog="Gaia",
                                            version=1)
        distances = list(result['distance'])
        radius_arcmin = 0.01 * u.deg.to(u.arcmin)
        assert isinstance(result, Table)
        assert max(distances) < radius_arcmin

        result = mast.Catalogs.query_object("TIC 441662144",
                                            radius=0.01,
                                            catalog="ctl")
        assert isinstance(result, Table)
        assert '441662144' in result['ID']

        result = mast.Catalogs.query_object('M1',
                                            radius=0.2,
                                            catalog='plato')
        assert 'PICidDR1' in result.colnames

    def test_catalogs_query_criteria_async(self):
        # without position
        responses = mast.Catalogs.query_criteria_async(catalog="Tic",
                                                       Bmag=[30, 50],
                                                       objType="STAR")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_criteria_async(catalog="ctl",
                                                       Bmag=[30, 50],
                                                       objType="STAR")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_criteria_async(catalog="DiskDetective",
                                                       state=["inactive", "disabled"],
                                                       oval=[8, 10],
                                                       multi=[3, 7])
        assert isinstance(responses, list)

        # with position
        responses = mast.Catalogs.query_criteria_async(catalog="Tic",
                                                       objectname="M10",
                                                       objType="EXTENDED")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_criteria_async(catalog="CTL",
                                                       objectname="M10",
                                                       objType="EXTENDED")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_criteria_async(catalog="DiskDetective",
                                                       objectname="M10",
                                                       radius=2,
                                                       state="complete")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_criteria_async(catalog="panstarrs",
                                                       table="mean",
                                                       objectname="M10",
                                                       radius=.02,
                                                       qualityFlag=48)
        assert isinstance(responses, Response)

    def test_catalogs_query_criteria(self):

        # clear columns config
        mast.Catalogs._column_configs = dict()

        # without position
        result = mast.Catalogs.query_criteria(catalog="Tic",
                                              Bmag=[30, 50],
                                              objType="STAR")
        assert isinstance(result, Table)
        assert '81609218' in result['ID']

        result = mast.Catalogs.query_criteria(catalog="ctl",
                                              Tmag=[10.5, 11],
                                              POSflag="2mass")
        assert isinstance(result, Table)
        assert '291067184' in result['ID']

        result = mast.Catalogs.query_criteria(catalog="DiskDetective",
                                              state=["inactive", "disabled"],
                                              oval=[8, 10],
                                              multi=[3, 7])
        assert isinstance(result, Table)
        assert 'J003920.04-300132.4' in result['designation']

        # with position
        result = mast.Catalogs.query_criteria(catalog="Tic",
                                              objectname="M10", objType="EXTENDED")
        assert isinstance(result, Table)
        assert '10000732589' in result['ID']

        result = mast.Catalogs.query_criteria(objectname='TIC 291067184',
                                              catalog="ctl",
                                              Tmag=[10.5, 11],
                                              POSflag="2mass")
        assert isinstance(result, Table)
        assert 10.893 in result['Tmag']

        result = mast.Catalogs.query_criteria(catalog="DiskDetective",
                                              objectname="M10",
                                              radius=2,
                                              state="complete")
        assert isinstance(result, Table)
        assert 'J165628.40-054630.8' in result['designation']

        result = mast.Catalogs.query_criteria(catalog="panstarrs",
                                              objectname="M10",
                                              radius=.01,
                                              qualityFlag=32,
                                              zoneID=10306)
        assert isinstance(result, Table)
        assert 'PSO J254.2861-04.1091' in result['objName']

        result = mast.Catalogs.query_criteria(coordinates="158.47924 -7.30962",
                                              radius=0.01,
                                              catalog="PANSTARRS",
                                              table="mean",
                                              data_release="dr2",
                                              nStackDetections=[("gte", "1")],
                                              columns=["objName", "distance"],
                                              sort_by=[("asc", "distance")])
        assert isinstance(result, Table)
        assert result['distance'][0] <= result['distance'][1]

    def test_catalogs_query_hsc_matchid_async(self):
        catalogData = mast.Catalogs.query_object("M10",
                                                 radius=.001,
                                                 catalog="HSC",
                                                 magtype=1)

        responses = mast.Catalogs.query_hsc_matchid_async(catalogData[0])
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_hsc_matchid_async(catalogData[0]["MatchID"])
        assert isinstance(responses, list)

    def test_catalogs_query_hsc_matchid(self):

        # clear columns config
        mast.Catalogs._column_configs = dict()

        catalogData = mast.Catalogs.query_object("M10",
                                                 radius=.001,
                                                 catalog="HSC",
                                                 magtype=1)
        matchid = catalogData[0]["MatchID"]

        result = mast.Catalogs.query_hsc_matchid(catalogData[0])
        assert isinstance(result, Table)
        assert (result['MatchID'] == matchid).all()

        result2 = mast.Catalogs.query_hsc_matchid(matchid)
        assert isinstance(result2, Table)
        assert len(result2) == len(result)
        assert (result2['MatchID'] == matchid).all()

    def test_catalogs_get_hsc_spectra_async(self):
        responses = mast.Catalogs.get_hsc_spectra_async()
        assert isinstance(responses, list)

    def test_catalogs_get_hsc_spectra(self):

        # clear columns config
        mast.Catalogs._column_configs = dict()

        result = mast.Catalogs.get_hsc_spectra()
        assert isinstance(result, Table)
        assert result[np.where(result['MatchID'] == '19657846')]
        assert result[np.where(result['DatasetName'] == 'HAG_J072657.06+691415.5_J8HPAXAEQ_V01.SPEC1D')]

    def test_catalogs_download_hsc_spectra(self, tmpdir):
        allSpectra = mast.Catalogs.get_hsc_spectra()

        # actually download the products
        result = mast.Catalogs.download_hsc_spectra(allSpectra[10],
                                                    download_dir=str(tmpdir))
        assert isinstance(result, Table)

        for row in result:
            if row['Status'] == 'COMPLETE':
                assert os.path.isfile(row['Local Path'])

        # just get the curl script
        result = mast.Catalogs.download_hsc_spectra(allSpectra[20:24],
                                                    download_dir=str(tmpdir), curl_flag=True)
        assert isinstance(result, Table)
        assert os.path.isfile(result['Local Path'][0])

    ######################
    # TesscutClass tests #
    ######################

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_get_sectors(self, product):

        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        sector_table = mast.Tesscut.get_sectors(coordinates=coord, product=product)
        assert isinstance(sector_table, Table)
        assert len(sector_table) >= 1

        name = "tess" if product == "spoc" else product
        assert f"{name}-s00" in sector_table['sectorName'][0]

        assert sector_table['sector'][0] > 0
        assert sector_table['camera'][0] > 0
        assert sector_table['ccd'][0] > 0

        sector_table = mast.Tesscut.get_sectors(objectname="M104", product=product)
        assert isinstance(sector_table, Table)
        assert len(sector_table) >= 1

        name = "tess" if product == "spoc" else product
        assert f"{name}-s00" in sector_table['sectorName'][0]

        assert sector_table['sector'][0] > 0
        assert sector_table['camera'][0] > 0
        assert sector_table['ccd'][0] > 0

    def test_tesscut_get_sectors_mt(self):

        # Moving target functionality testing

        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        sector_table = mast.Tesscut.get_sectors(objectname=moving_target_name,
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
            mast.Tesscut.get_sectors(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            mast.Tesscut.get_sectors(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_sectors(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_sectors(objectname=moving_target_name,
                                     coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_sectors(objectname=moving_target_name,
                                     coordinates=coord,
                                     moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets

        with pytest.raises(InvalidQueryError) as error_msg:
            sector_table = mast.Tesscut.get_sectors(objectname=moving_target_name, product='tica',
                                                    moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_download_cutouts(self, tmpdir, product):

        coord = SkyCoord(349.62609, -47.12424, unit="deg")

        manifest = mast.Tesscut.download_cutouts(product=product, coordinates=coord, size=5, path=str(tmpdir))
        assert isinstance(manifest, Table)
        assert len(manifest) >= 1
        assert manifest["Local Path"][0][-4:] == "fits"
        for row in manifest:
            assert os.path.isfile(row['Local Path'])

        coord = SkyCoord(107.18696, -70.50919, unit="deg")

        manifest = mast.Tesscut.download_cutouts(product=product, coordinates=coord, size=5, sector=27,
                                                 path=str(tmpdir))
        assert isinstance(manifest, Table)
        assert len(manifest) == 1
        assert manifest["Local Path"][0][-4:] == "fits"
        assert os.path.isfile(manifest[0]['Local Path'])

        manifest = mast.Tesscut.download_cutouts(product=product, coordinates=coord, size=[5, 7]*u.pix, sector=33,
                                                 path=str(tmpdir))
        assert isinstance(manifest, Table)
        assert len(manifest) >= 1
        assert manifest["Local Path"][0][-4:] == "fits"
        for row in manifest:
            assert os.path.isfile(row['Local Path'])

        manifest = mast.Tesscut.download_cutouts(product=product, coordinates=coord, size=5, sector=33,
                                                 path=str(tmpdir), inflate=False)
        assert isinstance(manifest, Table)
        assert len(manifest) == 1
        assert manifest["Local Path"][0][-3:] == "zip"
        assert os.path.isfile(manifest[0]['Local Path'])

        manifest = mast.Tesscut.download_cutouts(product=product, objectname="TIC 32449963", size=5, path=str(tmpdir))
        assert isinstance(manifest, Table)
        assert len(manifest) >= 1
        assert manifest["Local Path"][0][-4:] == "fits"
        for row in manifest:
            assert os.path.isfile(row['Local Path'])

    def test_tesscut_download_cutouts_mt(self, tmpdir):

        # Moving target functionality testing
        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        manifest = mast.Tesscut.download_cutouts(objectname=moving_target_name,
                                                 moving_target=True,
                                                 sector=6,
                                                 size=5,
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
            mast.Tesscut.download_cutouts(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            mast.Tesscut.download_cutouts(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.download_cutouts(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.download_cutouts(objectname=moving_target_name,
                                          coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.download_cutouts(objectname=moving_target_name,
                                          coordinates=coord,
                                          moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.download_cutouts(objectname=moving_target_name, product='tica',
                                          moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    @pytest.mark.parametrize("product", ["tica", "spoc"])
    def test_tesscut_get_cutouts(self, product):

        coord = SkyCoord(107.18696, -70.50919, unit="deg")

        cutout_hdus_list = mast.Tesscut.get_cutouts(product=product, coordinates=coord, size=5, sector=33)
        assert isinstance(cutout_hdus_list, list)
        assert len(cutout_hdus_list) >= 1
        assert isinstance(cutout_hdus_list[0], fits.HDUList)

        cutout_hdus_list = mast.Tesscut.get_cutouts(product=product, coordinates=coord, size=5, sector=27)
        assert isinstance(cutout_hdus_list, list)
        assert len(cutout_hdus_list) == 1
        assert isinstance(cutout_hdus_list[0], fits.HDUList)

        coord = SkyCoord(349.62609, -47.12424, unit="deg")

        cutout_hdus_list = mast.Tesscut.get_cutouts(product=product, coordinates=coord, size=[2, 4]*u.arcmin)
        assert isinstance(cutout_hdus_list, list)
        assert len(cutout_hdus_list) >= 1
        assert isinstance(cutout_hdus_list[0], fits.HDUList)

        cutout_hdus_list = mast.Tesscut.get_cutouts(product=product, objectname="TIC 32449963", size=5)
        assert isinstance(cutout_hdus_list, list)
        assert len(cutout_hdus_list) >= 1
        assert isinstance(cutout_hdus_list[0], fits.HDUList)

    def test_tesscut_get_cutouts_mt(self):

        # Moving target functionality testing
        coord = SkyCoord(349.62609, -47.12424, unit="deg")
        moving_target_name = 'Eleonora'

        cutout_hdus_list = mast.Tesscut.get_cutouts(objectname=moving_target_name,
                                                    moving_target=True,
                                                    sector=6,
                                                    size=5)
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
            mast.Tesscut.get_cutouts(moving_target=True)
        assert error_noname in str(error_msg.value)

        with pytest.raises(ResolverError) as error_msg:
            mast.Tesscut.get_cutouts(objectname=moving_target_name)
        assert error_nameresolve in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_cutouts(coordinates=coord, moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_cutouts(objectname=moving_target_name,
                                     coordinates=coord)
        assert error_name_coord in str(error_msg.value)

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_cutouts(objectname=moving_target_name,
                                     coordinates=coord,
                                     moving_target=True)
        assert error_mt_coord in str(error_msg.value)

        # The TICA product option is not available for moving targets

        with pytest.raises(InvalidQueryError) as error_msg:
            mast.Tesscut.get_cutouts(objectname=moving_target_name, product='tica',
                                     moving_target=True)
            assert error_tica_mt in str(error_msg.value)

    ###################
    # ZcutClass tests #
    ###################
    def test_zcut_get_surveys(self):

        coord = SkyCoord(189.49206, 62.20615, unit="deg")
        survey_list = mast.Zcut.get_surveys(coordinates=coord)
        assert isinstance(survey_list, list)
        assert len(survey_list) >= 1
        assert survey_list[0] == 'candels_gn_60mas'
        assert survey_list[1] == 'candels_gn_30mas'
        assert survey_list[2] == 'goods_north'

        # This should always return no results
        with pytest.warns(NoResultsWarning):
            coord = SkyCoord(57.10523, -30.08085, unit="deg")
            survey_list = mast.Zcut.get_surveys(coordinates=coord, radius=0)
            assert isinstance(survey_list, list)
            assert len(survey_list) == 0

        coord = SkyCoord(57.10523, -30.08085, unit="deg")
        with pytest.warns(NoResultsWarning):
            survey_list = mast.Zcut.get_surveys(coordinates=coord, radius=0)
        assert isinstance(survey_list, list)
        assert len(survey_list) == 0

    def test_zcut_download_cutouts(self, tmpdir):

        coord = SkyCoord(34.47320, -5.24271, unit="deg")

        cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        assert cutout_table["Local Path"][0][-4:] == "fits"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

        coord = SkyCoord(189.28065571, 62.17415175, unit="deg")

        cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=[200, 300], path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        assert cutout_table["Local Path"][0][-4:] == "fits"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

        cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=5, cutout_format="jpg", path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        assert cutout_table["Local Path"][0][-4:] == ".jpg"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

        cutout_table = mast.Zcut.download_cutouts(
            coordinates=coord, size=5, units='5*u.arcsec', cutout_format="png", path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        assert cutout_table["Local Path"][0][-4:] == ".png"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

        # Intetionally returns no results
        with pytest.warns(NoResultsWarning):
            cutout_table = mast.Zcut.download_cutouts(coordinates=coord,
                                                      survey='candels_gn_30mas',
                                                      cutout_format="jpg",
                                                      path=str(tmpdir))
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) == 0

        cutout_table = mast.Zcut.download_cutouts(
            coordinates=coord, survey='goods_north', cutout_format="jpg", path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) == 4
        assert cutout_table["Local Path"][0][-4:] == ".jpg"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

        cutout_table = mast.Zcut.download_cutouts(
            coordinates=coord, cutout_format="jpg", path=str(tmpdir), stretch='asinh', invert=True)
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        assert cutout_table["Local Path"][0][-4:] == ".jpg"
        for row in cutout_table:
            assert os.path.isfile(cutout_table[0]['Local Path'])

    def test_zcut_get_cutouts(self):

        coord = SkyCoord(189.28065571, 62.17415175, unit="deg")

        cutout_list = mast.Zcut.get_cutouts(coordinates=coord)
        assert isinstance(cutout_list, list)
        assert len(cutout_list) >= 1
        assert isinstance(cutout_list[0], fits.HDUList)

        cutout_list = mast.Zcut.get_cutouts(coordinates=coord, size=[200, 300])
        assert isinstance(cutout_list, list)
        assert len(cutout_list) >= 1
        assert isinstance(cutout_list[0], fits.HDUList)

        # Intentionally returns no results
        with pytest.warns(NoResultsWarning):
            cutout_list = mast.Zcut.get_cutouts(coordinates=coord,
                                                survey='candels_gn_30mas')
            assert isinstance(cutout_list, list)
            assert len(cutout_list) == 0

        cutout_list = mast.Zcut.get_cutouts(coordinates=coord, survey='3dhst_goods-n')
        assert isinstance(cutout_list, list)
        assert len(cutout_list) == 1
        assert isinstance(cutout_list[0], fits.HDUList)

    ###################
    # HapcutClass tests #
    ###################

    def test_hapcut_download_cutouts(self, tmpdir):

        # Test 1: Simple API call with expected results
        coord = SkyCoord(351.347812, 28.497808, unit="deg")

        cutout_table = mast.Hapcut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        for row in cutout_table:
            assert os.path.isfile(row['Local Path'])
            if 'fits' in os.path.basename(row['Local Path']):
                assert fits.getdata(row['Local Path']).shape == (5, 5)

        # Test 2: Make input size a list
        cutout_table = mast.Hapcut.download_cutouts(coordinates=coord, size=[2, 3], path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        for row in cutout_table:
            assert os.path.isfile(row['Local Path'])
            if 'fits' in os.path.basename(row['Local Path']):
                assert fits.getdata(row['Local Path']).shape == (3, 2)

        # Test 3: Specify unit for input size
        cutout_table = mast.Hapcut.download_cutouts(coordinates=coord, size=5*u.arcsec, path=str(tmpdir))
        assert isinstance(cutout_table, Table)
        assert len(cutout_table) >= 1
        for row in cutout_table:
            assert os.path.isfile(row['Local Path'])

        # Test 4: Intentional API call with no results
        bad_coord = SkyCoord(102.7, 70.50, unit="deg")
        with pytest.warns(NoResultsWarning, match='Missing HAP files for input target. Cutout not performed.'):
            cutout_table = mast.Hapcut.download_cutouts(coordinates=bad_coord, size=5, path=str(tmpdir))
            assert isinstance(cutout_table, Table)
            assert len(cutout_table) == 0

    def test_hapcut_get_cutouts(self):

        # Test 1: Simple API call with expected results
        coord = SkyCoord(351.347812, 28.497808, unit="deg")

        cutout_list = mast.Hapcut.get_cutouts(coordinates=coord)
        assert isinstance(cutout_list, list)
        assert len(cutout_list) >= 1
        assert isinstance(cutout_list[0], fits.HDUList)
        assert cutout_list[0][1].data.shape == (5, 5)

        # Test 2: Make input size a list
        cutout_list = mast.Hapcut.get_cutouts(coordinates=coord, size=[2, 3])
        assert isinstance(cutout_list, list)
        assert len(cutout_list) >= 1
        assert isinstance(cutout_list[0], fits.HDUList)
        assert cutout_list[0][1].data.shape == (3, 2)

        # Test 3: Specify unit for input size
        cutout_list = mast.Hapcut.get_cutouts(coordinates=coord, size=5*u.arcsec)
        assert isinstance(cutout_list, list)
        assert len(cutout_list) >= 1
        assert isinstance(cutout_list[0], fits.HDUList)
        assert cutout_list[0][1].data.shape == (42, 42)

        # Test 4: Intentional API call with no results
        bad_coord = SkyCoord(102.7, 70.50, unit="deg")

        with pytest.warns(NoResultsWarning, match='Missing HAP files for input target. Cutout not performed.'):
            cutout_list = mast.Hapcut.get_cutouts(coordinates=bad_coord)
            assert isinstance(cutout_list, list)
            assert len(cutout_list) == 0
