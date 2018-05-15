# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import imp
import pytest
import requests

from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

from ... import lcogt

imp.reload(requests)

OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743, b=-21.5733, unit=(u.deg, u.deg),
                     frame='galactic')]


@remote_data
@pytest.mark.skip(reason="Changed remote API, xfailing until fixing"
                  "https://github.com/astropy/astroquery/issues/725")
class TestLcogt:

    def test_query_object_meta(self):
        response = lcogt.core.Lcogt.query_object_async('M1', catalog='lco_img')
        assert response is not None

    def test_query_object_phot(self):
        response = lcogt.core.Lcogt.query_object_async('M1', catalog='lco_cat')
        assert response is not None

    def test_query_region_cone_async(self):
        response = lcogt.core.Lcogt.query_region_async(
            'm31', catalog='lco_img', spatial='Cone', radius=2 * u.arcmin)

        assert response is not None

    def test_query_region_cone(self):
        result = lcogt.core.Lcogt.query_region(
            'm31', catalog='lco_img', spatial='Cone', radius=2 * u.arcmin)
        assert isinstance(result, Table)

    def test_query_region_box_async(self):
        response = lcogt.core.Lcogt.query_region_async(
            "00h42m44.330s +41d16m07.50s", catalog='lco_img', spatial='Box',
            width=2 * u.arcmin)
        assert response is not None

    def test_query_region_box(self):
        result = lcogt.core.Lcogt.query_region(
            "00h42m44.330s +41d16m07.50s", catalog='lco_img', spatial='Box',
            width=2 * u.arcmin)
        assert isinstance(result, Table)

    def test_query_region_async_polygon(self):
        polygon = [SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg),
                            frame='icrs'),
                   SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg),
                            frame='icrs'),
                   SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg),
                            frame='icrs')]
        response = lcogt.core.Lcogt.query_region_async(
            "m31", catalog="lco_img", spatial="Polygon", polygon=polygon)
        assert response is not None

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        result = lcogt.core.Lcogt.query_region(
            "m31", catalog="lco_img", spatial="Polygon", polygon=polygon)

        assert isinstance(result, Table)
