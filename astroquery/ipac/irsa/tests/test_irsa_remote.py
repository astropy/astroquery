# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord

from astroquery.ipac.irsa import Irsa


OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743, b=-21.5733, unit=(u.deg, u.deg),  # noqa
                     frame='galactic')]


@pytest.mark.remote_data
class TestIrsa:
    def test_query_region_cone_async(self):
        response = Irsa.query_region_async(
            'm31', catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin, cache=False)
        assert response is not None

    def test_query_region_cone(self):
        result = Irsa.query_region(
            'm31', catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin, cache=False)
        assert isinstance(result, Table)

    def test_query_region_box_async(self):
        response = Irsa.query_region_async(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box',
            width=2 * u.arcmin, cache=False)
        assert response is not None

    def test_query_region_box(self):
        result = Irsa.query_region(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box',
            width=2 * u.arcmin, cache=False)
        assert isinstance(result, Table)

    def test_query_region_async_polygon(self):
        polygon = [SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg)),
                   SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg)),
                   SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg))]
        response = Irsa.query_region_async(
            "m31", catalog="fp_psc", spatial="Polygon", polygon=polygon, cache=False)

        assert response is not None

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        result = Irsa.query_region(
            "m31", catalog="fp_psc", spatial="Polygon", polygon=polygon, cache=False)

        assert isinstance(result, Table)

    def test_list_catalogs(self):
        catalogs = Irsa.list_catalogs(cache=False)
        # Number of available catalogs may change over time, test only for significant drop.
        # (at the time of writing there are 587 catalogs in the list).
        assert len(catalogs) > 500
