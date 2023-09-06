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
    def test_query_region_cone(self):
        result = Irsa.query_region(
            'm31', catalog='fp_psc', spatial='Cone', radius=2 * u.arcmin, cache=False)
        assert isinstance(result, Table)

    @pytest.mark.skip("Upstream TAP doesn't support Box geometry yet")
    def test_query_region_box(self):
        result = Irsa.query_region(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box',
            width=2 * u.arcmin, cache=False)
        assert isinstance(result, Table)

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        with pytest.warns(UserWarning, match='Polygon endpoints are being interpreted'):
            result = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
                                       polygon=polygon, cache=False)

        assert isinstance(result, Table)

    def test_list_catalogs(self):
        catalogs = Irsa.list_catalogs()
        # Number of available catalogs may change over time, test only for significant drop.
        # (at the time of writing there are 933 tables in the list).
        assert len(catalogs) > 900
