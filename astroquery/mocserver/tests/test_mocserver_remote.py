# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy import coordinates
from astropy.table import Table

try:
    from mocpy import MOC

    HAS_MOCPY = True
except ImportError:
    HAS_MOCPY = False

try:
    from regions import CircleSkyRegion

    HAS_REGIONS = True
except ImportError:
    HAS_REGIONS = False

from ..core import MOCServer


@pytest.mark.remote_data
@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
class TestMOCServerRemote:
    """
    Tests requiring regions
    """

    # test of MAXREC payload
    @pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
    @pytest.mark.parametrize("max_rec", [3, 10, 25, 100])
    def test_max_rec_param(self, max_rec):
        center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
        radius = coordinates.Angle(1.5, unit="deg")

        cone_region = CircleSkyRegion(center, radius)
        result = MOCServer.query_region(
            region=cone_region, max_rec=max_rec, get_query_payload=False
        )

        assert max_rec == len(result)

    # test of field_l when retrieving dataset records
    @pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
    @pytest.mark.parametrize(
        "field_l",
        [
            ["ID"],
            ["ID", "moc_sky_fraction"],
            ["data_ucd", "vizier_popularity", "ID"],
            ["publisher_id", "ID"],
        ],
    )
    def test_field_l_param(self, field_l):
        center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
        radius = coordinates.Angle(1.5, unit="deg")

        cone_region = CircleSkyRegion(center, radius)

        table = MOCServer.query_region(
            region=cone_region, fields=field_l, get_query_payload=False
        )
        assert isinstance(table, Table)
        assert set(table.colnames).issubset(set(field_l))

    """
    Tests requiring mocpy
    """

    # test of moc_order payload
    @pytest.mark.parametrize("moc_order", [5, 10])
    def test_moc_order_param(self, moc_order, tmp_cwd):
        # We need a long timeout for this
        MOCServer.TIMEOUT = 300

        moc_region = MOC.from_json({"0": [1]})

        result = MOCServer.query_region(
            region=moc_region,
            # return a mocpy obj
            return_moc=True,
            max_norder=moc_order,
            get_query_payload=False,
        )

        assert isinstance(result, MOC)

    @pytest.mark.parametrize(
        "meta_data_expr",
        ["ID=*HST*", "moc_sky_fraction>0.5", "(ID=*DSS*)&&(moc_sky_fraction>0.1)"],
    )
    def test_find_data_sets(self, meta_data_expr):
        result = MOCServer.find_datasets(
            meta_data=meta_data_expr,
            fields=["ID", "moc_sky_fraction"],
            get_query_payload=False,
        )

        assert isinstance(result, Table)
