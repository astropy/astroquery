# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Canadian Astronomy Data Centre
=============
"""

import pytest
import os
from datetime import datetime
from astropy.tests.helper import remote_data
from astroquery.cadc import Cadc
from astropy.coordinates import SkyCoord


@remote_data
class TestCadcClass:
    # now write tests for each method here
    def test_query_region(self):
        cadc = Cadc()
        result = cadc.query_region('08h45m07.5s +54d18m00s', collection='CFHT')
        # do some manipulation of the results. Below it's filtering out based
        # on target name but other manipulations are possible.
        assert len(result) > 0
        urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'])
        assert len(urls) > 0
        # urls are a subset of the results that match target_name==Nr3491_1
        assert len(result) >= len(urls)
        urls_data_only = len(urls)
        # now get the auxilary files too
        urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'],
                                  include_auxiliaries=True)
        assert urls_data_only <= len(urls)

        # the same result should be obtained by querying the entire region
        # and filtering out on the CFHT collection
        result2 = cadc.query_region('08h45m07.5s +54d18m00s')
        assert len(result) == len(result2[result2['collection'] == 'CFHT'])

        # search for a target
        results = cadc.query_region(SkyCoord.from_name('M31'))
        assert len(results) > 20

    def test_query_name(self):
        cadc = Cadc()
        result1 = cadc.query_name('M31')
        assert len(result1) > 20
        # test case insensitive
        result2 = cadc.query_name('m31')
        assert len(result1) == len(result2)

    def test_query(self):
        cadc = Cadc()
        result = cadc.query(
            "select count(*) from caom2.Observation where target_name='M31'")
        assert 1000 < result[0][0]

        # test that no proprietary results are returned when not logged in
        now = datetime.utcnow()
        query = "select top 1 * from caom2.Plane where " \
                "metaRelease>'{}'".format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        result = cadc.query(query)
        assert len(result) == 0

    @pytest.mark.skipif(('CADC_USER' not in os.environ or
                        'CADC_PASSWD' not in os.environ),
                        reason='Requires real CADC user/password (CADC_USER '
                               'and CADC_PASSWD environment variables)')
    def test_login(self):
        cadc = Cadc()
        now = datetime.utcnow()
        cadc.login(os.environ['CADC_USER'], os.environ['CADC_PASSWD'])
        query = "select top 1 * from caom2.Plane where " \
                "metaRelease>'{}'".format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        result = cadc.query(query)
        assert len(result) == 1
