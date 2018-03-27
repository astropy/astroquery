# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u

import requests
import imp

from ... import irsa

imp.reload(requests)

OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743, b=-21.5733, unit=(u.deg, u.deg),
                     frame='galactic')]


@remote_data
class TestIrsa:

    def test_query_region_cone_async(self):
        response = irsa.core.Irsa.query_region_async(
            'm31', catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin)
        assert response is not None

    def test_query_region_cone(self):
        result = irsa.core.Irsa.query_region(
            'm31', catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin)
        assert isinstance(result, Table)

    def test_query_region_box_async(self):
        response = irsa.core.Irsa.query_region_async(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box',
            width=2 * u.arcmin)
        assert response is not None

    def test_query_region_box(self):
        result = irsa.core.Irsa.query_region(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box',
            width=2 * u.arcmin)
        assert isinstance(result, Table)

    def test_query_region_async_polygon(self):
        polygon = [SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg)),
                   SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg)),
                   SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg))]
        response = irsa.core.Irsa.query_region_async(
            "m31", catalog="fp_psc", spatial="Polygon", polygon=polygon)

        assert response is not None

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        result = irsa.core.Irsa.query_region(
            "m31", catalog="fp_psc", spatial="Polygon", polygon=polygon)

        assert isinstance(result, Table)
