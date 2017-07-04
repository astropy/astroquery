# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import numpy as np
import os

from astropy.tests.helper import remote_data
from astropy.table import Table

from ... import mast


@remote_data
class TestMast(object):

    # MastClass tests
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

    ## ObservationsClass tests ##

    def test_list_missions(self):
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
        assert len(result) >= 1826
        assert result[np.where(result['obs_id'] == '00031992001')]

    def test_observations_query_object_async(self):
        responses = mast.Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):
        result = mast.Observations.query_object("M8", radius=".02 deg")
        assert isinstance(result, Table)
        assert len(result) >= 196
        assert result[np.where(result['obs_id'] == 'ktwo200071160-c92_lc')]

    def test_query_criteria_async(self):
        # without position
        responses = mast.Observations.query_criteria_async(dataproduct_type=["image"],
                                                           proposal_pi="Ost*",
                                                           s_dec=[43.5, 45.5])
        assert isinstance(responses, list)

        # with position
        responses = mast.Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                           objectname="M101")
        assert isinstance(responses, list)

    def test_query_criteria(self):
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
        assert result >= 1826
        assert result < maxRes

    def test_observations_query_object_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_object_count("M8", radius=".02 deg")
        assert isinstance(result, (np.int64, int))
        assert result >= 196
        assert result < maxRes

    def test_query_criteria_count(self):
        maxRes = mast.Observations.query_criteria_count()
        result = mast.Observations.query_criteria_count(proposal_pi="Osten",
                                                        proposal_id=8880)
        assert isinstance(result, (np.int64, int))
        assert result == 7
        assert result < maxRes

    # product functions
    def test_get_product_list_async(self):
        responses = mast.Observations.get_product_list_async('2003738726')
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async('2003738726,3000007760')
        assert isinstance(responses, list)

        observations = mast.Observations.query_object("M8", radius=".02 deg")
        responses = mast.Observations.get_product_list_async(observations[0])
        assert isinstance(responses, list)

        responses = mast.Observations.get_product_list_async(observations[0:4])
        assert isinstance(responses, list)

    def test_get_product_list(self):
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

    def test_filter_products(self):
        products = mast.Observations.get_product_list('2003738726')
        result = mast.Observations.filter_products(products,
                                                   productType=["SCIENCE"],
                                                   mrp_only=False)
        assert isinstance(result, Table)
        assert len(result) == sum(products['productType'] == "SCIENCE")

    def test_download_products(self, tmpdir):
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
