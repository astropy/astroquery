# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import numpy

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

        assert isinstance(result, Table)

    ## ObservationsClass tests ##

    # query functions
    def test_observations_query_region_async(self):
        responses = mast.Observations.query_region_async("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(responses, list)

    def test_observations_query_region(self):
        result = mast.Observations.query_region("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, Table)

    def test_observations_query_object_async(self):
        responses = mast.Observations.query_object_async("M8", radius=".02 deg")
        assert isinstance(responses, list)

    def test_observations_query_object(self):
        result = mast.Observations.query_object("M8", radius=".02 deg")
        assert isinstance(result, Table)

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
        result = mast.Observations.query_criteria(dataproduct_type=["image"],
                                                  proposal_pi="Ost*",
                                                  s_dec=[43.5, 45.5])
        assert isinstance(result, Table)

        # with position
        result = mast.Observations.query_criteria(filters=["NUV", "FUV"],
                                                  objectname="M101")
        assert isinstance(result, Table)

    # count functions
    def test_observations_query_region_count(self):
        result = mast.Observations.query_region_count("322.49324 12.16683", radius="0.4 deg")
        assert isinstance(result, (numpy.int64, int))

    def test_observations_query_object_count(self):
        result = mast.Observations.query_object_count("M8", radius=".02 deg")
        assert isinstance(result, (numpy.int64, int))

    def test_query_criteria_count(self):
        result = mast.Observations.query_criteria_count({"dataproduct_type": ["image"],
                                                         "proposal_pi": "Osten",
                                                         "s_dec": [43.5, 45.5]})
        assert isinstance(result, (numpy.int64, int))

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

        result = mast.Observations.get_product_list('2003738726,3000007760')
        assert isinstance(result, Table)

        observations = mast.Observations.query_object("M8", radius=".02 deg")
        result = mast.Observations.get_product_list(observations[0])
        assert isinstance(result, Table)

        result = mast.Observations.get_product_list(observations[0:4])
        assert isinstance(result, Table)

    def test_filter_products(self):
        products = mast.Observations.get_product_list('2003738726')
        result = mast.Observations.filter_products(products,
                                                   productType=["SCIENCE"],
                                                   mrp_only=False)
        assert isinstance(result, Table)

    def test_download_products(self, tmpdir):
        # actually download the products
        result = mast.Observations.download_products('2003738726',
                                                     download_dir=str(tmpdir),
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)

        # just get the curl script
        result = mast.Observations.download_products('2003738726',
                                                     download_dir=str(tmpdir),
                                                     curl_flag=True,
                                                     productType=["SCIENCE"],
                                                     mrp_only=False)
        assert isinstance(result, Table)
