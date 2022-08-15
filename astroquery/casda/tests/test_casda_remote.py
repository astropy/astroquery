# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

import keyring
import math
import os
import pytest

from astropy.table import Table, Column
import astropy.units as u
from astropy.coordinates import SkyCoord

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

    @pytest.fixture
    def cached_credentials(self):
        if 'CASDA_USER' in os.environ and 'CASDA_PASSWD' not in os.environ:
            keyring.set_password("astroquery:casda.csiro.au", os.environ['CASDA_USER'], os.environ['CASDA_PASSWD'])
            yield
            keyring.delete_password("astroquery:casda.csiro.au", os.environ['CASDA_USER'])
        else:
            yield

    @pytest.mark.skipif(('CASDA_USER' not in os.environ),
                        reason='Requires real CASDA user/password (CASDA_USER '
                               'and CASDA_PASSWD environment variables or password in keyring)')
    def test_stage_data(self, cached_credentials):
        prefix = 'https://data.csiro.au/casda_vo_proxy/vo/datalink/links?ID='
        access_urls = [prefix + 'cube-1262']
        table = Table([Column(data=access_urls, name='access_url')])
        casda = Casda()
        casda.login(username=os.environ['CASDA_USER'])
        casda.POLL_INTERVAL = 3
        urls = casda.stage_data(table)

        assert 'g300to310.q.fits' in str(urls[0])
        assert str(urls[1]).endswith('image_cube_g300to310.q.fits.checksum')
        assert len(urls) == 2

    @pytest.mark.skipif(('CASDA_USER' not in os.environ),
                        reason='Requires real CASDA user/password (CASDA_USER '
                               'and CASDA_PASSWD environment variables or password in keyring)')
    def test_cutout(self, cached_credentials):
        prefix = 'https://data.csiro.au/casda_vo_proxy/vo/datalink/links?ID='
        access_urls = [prefix + 'cube-44705']
        table = Table([Column(data=access_urls, name='access_url')])
        casda = Casda()
        casda.login(username=os.environ['CASDA_USER'])
        casda.POLL_INTERVAL = 3
        pos = SkyCoord(196.49583333*u.deg, -62.7*u.deg)
        urls = casda.cutout(table, coordinates=pos, radius=15*u.arcmin)

        # URLs may come back in any order
        for url in urls:
            if url.endswith('.checksum'):
                checksum_url = str(url)
            else:
                cutout_url = str(url)

        assert cutout_url.endswith('-imagecube-44705.fits')
        assert 'cutout-' in cutout_url
        assert checksum_url.endswith('-imagecube-44705.fits.checksum')
        assert len(urls) == 2
