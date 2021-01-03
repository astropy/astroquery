# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

import math
import os
import pytest

from astropy.table import Table, Column
import astropy.units as u

from astroquery.casda import Casda


@pytest.mark.remote_data
class TestCasdaRemote:

    def test_query_region_text_radius(self):
        ra = 333.9092
        dec = -45.8418
        radius = 0.5
        query_payload = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=radius * u.deg, cache=False,
                                           get_query_payload=True)
        assert isinstance(query_payload, dict)
        assert 'POS' in query_payload
        assert query_payload['POS'].startswith('CIRCLE 333')
        pos_parts = query_payload['POS'].split(' ')
        assert pos_parts[0] == 'CIRCLE'
        assert math.isclose(float(pos_parts[1]), ra, abs_tol=1e-4)
        assert math.isclose(float(pos_parts[2]), dec, abs_tol=1e-4)
        assert math.isclose(float(pos_parts[3]), radius)
        assert len(pos_parts) == 4

        responses = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.arcmin, cache=False)
        assert isinstance(responses, Table)
        assert len(responses) > 1

        for key in ('dataproduct_type', 'obs_id', 'access_url', 'access_format', 'obs_release_date'):
            assert key in responses.keys()

    @pytest.mark.skipif(('CASDA_USER' not in os.environ or
                        'CASDA_PASSWD' not in os.environ),
                        reason='Requires real CASDA user/password (CASDA_USER '
                               'and CASDA_PASSWD environment variables)')
    def test_stage_data(self):
        prefix = 'https://data.csiro.au/casda_vo_proxy/vo/datalink/links?ID='
        access_urls = [prefix + 'cube-1262']
        table = Table([Column(data=access_urls, name='access_url')])
        casda = Casda(os.environ['CASDA_USER'], os.environ['CASDA_PASSWD'])
        casda.POLL_INTERVAL = 3
        urls = casda.stage_data(table)

        assert str(urls[0]).endswith('image_cube_g300to310.q.fits')
        assert str(urls[1]).endswith('image_cube_g300to310.q.fits.checksum')
        assert len(urls) == 2
