# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

import math
import pytest

import astropy.units as u
from astropy.table import Table

from astroquery.casda import Casda


@pytest.mark.remote_data
class TestCasda:

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
        print(responses[0])
        for key in ('dataproduct_type', 'obs_id', 'access_url', 'access_format', 'obs_release_date'):
            assert key in responses.keys()
