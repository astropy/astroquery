# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import numpy as np
import os

from astropy.tests.helper import remote_data
from astropy.table import Table

from ... import mast


@remote_data
class TestMast(object):

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

    def test_mast_sesion_info(self):
        sessionInfo = mast.Mast.session_info(True)
        assert sessionInfo['Username'] == 'anonymous'
        assert sessionInfo['Session Expiration'] is None

    ###########################
    # ObservationsClass tests #
    ###########################

    def test_observations_list_missions(self):
        missions = mast.Observations.list_missions()
        assert isinstance(missions, list)
        for m in ['HST', 'HLA', 'GALEX', 'Kepler']:
            assert m in missions

    # query functions
    def test_observations_query_region_async(self):
        responses = mast.Observations.query_region_async("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(responses, list)

    def test_observations_query_region(self):
        result = mast.Observations.query_region("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, Table)
        assert len(result) >= 1710
        assert result[np.where(result['obs_id'] == '00031992001')]

        result = mast.Observations.query_region("322.49324 12.16683", radius="0.1 deg",
                                                pagesize=1, page=1)
        assert isinstance(result, Table)
        assert len(result) == 1

    def test_observations_query_object_async(self):
        responses = mast.Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):
        result = mast.Observations.query_object("M8", radius=".02 deg")
        assert isinstance(result, Table)
        assert len(result) >= 196
        assert result[np.where(result['obs_id'] == 'ktwo200071160-c92_lc')]

    def test_observations_query_criteria_async(self):
        # without position
        responses = mast.Observations.query_criteria_async(dataproduct_type=["image"],
                                                           proposal_pi="Ost*",
                                                           s_dec=[43.5, 45.5])
        assert isinstance(responses, list)

        # with position
        responses = mast.Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                           objectname="M101")
        assert isinstance(responses, list)

    def test_observations_query_criteria(self):
        # without position
        result = mast.Observations.query_criteria(target_classification="*Europa*",
                                                  proposal_id=8169,
                                                  t_min=[51179, 51910])
        assert isinstance(result, Table)
        assert len(result) == 4
        assert (result['obs_collection'] == 'HST').all()

        # with position
        result = mast.Observations.query_criteria(filters=["NUV", "FUV"],
                                                  obs_collection="GALEX",
                                                  objectname="M101")
        assert isinstance(result, Table)
        assert len(result) == 12
        assert (result['obs_collection'] == 'GALEX').all()
        assert sum(result['filters'] == 'NUV') == 6

    # count functions
    def test_observations_query_region_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_region_count("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, (np.int64, int))
        assert result >= 1710
        assert result < maxRes

    def test_observations_query_object_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_object_count("M8", radius=".02 deg")
        assert isinstance(result, (np.int64, int))
        assert result >= 196
        assert result < maxRes

    def test_observations_query_criteria_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_criteria_count(proposal_pi="Osten",
                                                        proposal_id=8880)
        assert isinstance(result, (np.int64, int))
        # Temporarily commented out (May 9, 2018) due to upstream issue
        # assert result == 7
        assert result < maxRes

    # product functions
    def test_observations_get_product_list_async(self):
        responses = mast.Observations.get_product_list_async('2003738726')
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async('2003738726,3000007760')
        assert isinstance(responses, list)

        observations = mast.Observations.query_object("M8", radius=".02 deg")
        responses = mast.Observations.get_product_list_async(observations[0])
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async(observations[0:4])
        assert isinstance(responses, list)

    def test_observations_get_product_list(self):
        result = mast.Observations.get_product_list('2003738726')
        assert isinstance(result, Table)
        assert len(result) == 22
        assert (result['obs_id'] == 'U9O40504M').all()

        result = mast.Observations.get_product_list('2003738726,3000007760')
        assert isinstance(result, Table)
        assert len(result) == 34
        assert "HST" in result['obs_collection']
        assert "IUE" in result['obs_collection']

        observations = mast.Observations.query_object("M8", radius=".02 deg")
        obsLoc = np.where(observations["obs_id"] == 'ktwo200071160-c92_lc')
        result = mast.Observations.get_product_list(observations[obsLoc])
        assert isinstance(result, Table)
        assert len(result) == 4

        obsLocs = np.where((observations['target_name'] == 'NGC6523') & (observations['obs_collection'] == "IUE"))
        result = mast.Observations.get_product_list(observations[obsLocs])
        assert isinstance(result, Table)
        assert len(result) == 30

    def test_observations_filter_products(self):
        products = mast.Observations.get_product_list('2003738726')
        result = mast.Observations.filter_products(products,
                                                   productType=["SCIENCE"],
                                                   mrp_only=False)
        assert isinstance(result, Table)
        assert len(result) == sum(products['productType'] == "SCIENCE")

    def test_observations_download_products(self, tmpdir):
        # actually download the products
        result = mast.Observations.download_products('2003738726',
                                                     download_dir=str(tmpdir),
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)
        for row in result:
            if row['Status'] == 'COMPLETE':
                assert os.path.isfile(row['Local Path'])

        # just get the curl script
        result = mast.Observations.download_products('2003738726',
                                                     download_dir=str(tmpdir),
                                                     curl_flag=True,
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)
        assert os.path.isfile(result['Local Path'][0])

    ######################
    # CatalogClass tests #
    ######################

        # query functions
    def test_catalogs_query_region_async(self):
        responses = mast.Catalogs.query_region_async("158.47924 -7.30962", catalog="Galex")
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_region_async("322.49324 12.16683", radius="0.02 deg")
        assert isinstance(responses, list)

    def test_catalogs_query_region(self):
        result = mast.Catalogs.query_region("158.47924 -7.30962", radius=0.1, catalog="Gaia")
        assert isinstance(result, Table)
        assert len(result) >= 82
        assert result[np.where(result['source_id'] == '3774902350511581696')]

        result = mast.Catalogs.query_region("322.49324 12.16683", catalog="HSC", magtype=2)
        assert isinstance(result, Table)
        assert len(result) == 50000

    def test_catalogs_query_object_async(self):
        responses = mast.Catalogs.query_object_async("M10", radius=.02, catalog="TIC")
        assert isinstance(responses, list)

    def test_catalogs_query_object(self):
        result = mast.Catalogs.query_object("M10", radius=".02 deg", catalog="TIC")
        assert isinstance(result, Table)
        assert len(result) >= 305
        assert result[np.where(result['ID'] == '189844449')]

        result = mast.Catalogs.query_object("M10", radius=.001, catalog="HSC", magtype=1)
        assert isinstance(result, Table)
        assert len(result) >= 97
        assert result[np.where(result['MatchID'] == 17306539)]

    def test_catalogs_query_criteria_async(self):
        # without position
        responses = mast.Catalogs.query_criteria_async(catalog="Tic",
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

        responses = mast.Catalogs.query_criteria_async(catalog="DiskDetective",
                                                       objectname="M10",
                                                       radius=2,
                                                       state="complete")
        assert isinstance(responses, list)

    def test_catalogs_query_criteria(self):
        # without position
        result = mast.Catalogs.query_criteria(catalog="Tic", Bmag=[30, 50], objType="STAR")
        assert isinstance(result, Table)
        assert len(result) >= 3
        assert result[np.where(result['ID'] == '81609218')]

        result = mast.Catalogs.query_criteria(catalog="DiskDetective",
                                              state=["inactive", "disabled"],
                                              oval=[8, 10], multi=[3, 7])
        assert isinstance(result, Table)
        assert len(result) >= 39
        assert result[np.where(result['designation'] == 'J043401.21-372522.1')]

        # with position
        result = mast.Catalogs.query_criteria(catalog="Tic", objectname="M10", objType="EXTENDED")
        assert isinstance(result, Table)
        assert len(result) >= 7
        assert result[np.where(result['ID'] == '10000732589')]

        result = mast.Catalogs.query_criteria(catalog="DiskDetective", objectname="M10", radius=2,
                                              state="complete")
        assert isinstance(result, Table)
        assert len(result) >= 7
        assert result[np.where(result['designation'] == 'J165628.40-054630.8')]

    def test_catalogs_query_hsc_matchid_async(self):
        catalogData = mast.Catalogs.query_object("M10", radius=.001, catalog="HSC", magtype=1)

        responses = mast.Catalogs.query_hsc_matchid_async(catalogData[0])
        assert isinstance(responses, list)

        responses = mast.Catalogs.query_hsc_matchid_async(catalogData[0]["MatchID"])
        assert isinstance(responses, list)

    def test_catalogs_query_hsc_matchid(self):
        catalogData = mast.Catalogs.query_object("M10", radius=.001, catalog="HSC", magtype=1)
        matchid = catalogData[0]["MatchID"]

        result = mast.Catalogs.query_hsc_matchid(catalogData[0])
        assert isinstance(result, Table)
        assert len(result) >= 8
        assert (result['MatchID'] == matchid).all()

        result = mast.Catalogs.query_hsc_matchid(matchid)
        assert isinstance(result, Table)
        assert len(result) >= 8
        assert (result['MatchID'] == matchid).all()

    def test_catalogs_get_hsc_spectra_async(self):
        responses = mast.Catalogs.get_hsc_spectra_async()
        assert isinstance(responses, list)

    def test_catalogs_get_hsc_spectra(self):
        result = mast.Catalogs.get_hsc_spectra()
        assert isinstance(result, Table)
        assert len(result) >= 45762
        assert result[np.where(result['MatchID'] == '19657846')]

    def test_catalogs_download_hsc_spectra(self, tmpdir):
        allSpectra = mast.Catalogs.get_hsc_spectra()

        # actually download the products
        result = mast.Catalogs.download_hsc_spectra(allSpectra[10], download_dir=str(tmpdir))
        assert isinstance(result, Table)
        for row in result:
            if row['Status'] == 'COMPLETE':
                assert os.path.isfile(row['Local Path'])

        # just get the curl script
        result = mast.Catalogs.download_hsc_spectra(allSpectra[20:24],
                                                    download_dir=str(tmpdir), curl_flag=True)
        assert isinstance(result, Table)
        assert os.path.isfile(result['Local Path'][0])
