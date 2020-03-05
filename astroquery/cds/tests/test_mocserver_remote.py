# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import pytest

from astropy import coordinates
from astropy.table import Table

try:
    from mocpy import MOC
except ImportError:
    pass

try:
    from regions import CircleSkyRegion
except ImportError:
    pass

from ..core import cds


@pytest.mark.remote_data
class TestMOCServerRemote(object):
    """
    Tests requiring regions
    """

    # test of MAXREC payload
    @pytest.mark.skipif('regions' not in sys.modules,
                        reason="requires astropy-regions")
    @pytest.mark.parametrize('max_rec', [3, 10, 25, 100])
    def test_max_rec_param(self, max_rec):
        center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
        radius = coordinates.Angle(1.5, unit="deg")

        cone_region = CircleSkyRegion(center, radius)
        result = cds.query_region(region=cone_region,
                                  max_rec=max_rec,
                                  get_query_payload=False)

        assert max_rec == len(result)

    # test of field_l when retrieving dataset records
    @pytest.mark.skipif('regions' not in sys.modules,
                        reason="requires astropy-regions")
    @pytest.mark.parametrize('field_l', [['ID'],
                                         ['ID', 'moc_sky_fraction'],
                                         ['data_ucd', 'vizier_popularity', 'ID'],
                                         ['publisher_id', 'ID']])
    def test_field_l_param(self, field_l):
        center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
        radius = coordinates.Angle(1.5, unit="deg")

        cone_region = CircleSkyRegion(center, radius)

        table = cds.query_region(region=cone_region,
                                 fields=field_l,
                                 get_query_payload=False)
        assert isinstance(table, Table)
        assert set(table.colnames).issubset(set(field_l))

    """
    Tests requiring mocpy
    """

    # test of moc_order payload
    @pytest.mark.skipif('mocpy' not in sys.modules,
                        reason="requires MOCPy")
    @pytest.mark.parametrize('moc_order', [5, 10])
    def test_moc_order_param(self, moc_order):
        moc_region = MOC.from_json({'0': [1]})

        result = cds.query_region(region=moc_region,
                                  # return a mocpy obj
                                  return_moc=True,
                                  max_norder=moc_order,
                                  get_query_payload=False)

        assert isinstance(result, MOC)

    @pytest.mark.parametrize('meta_data_expr', ["ID=*HST*",
                                                "moc_sky_fraction>0.5",
                                                "(ID=*DSS*)&&(moc_sky_fraction>0.1)"])
    def test_find_data_sets(self, meta_data_expr):
        result = cds.find_datasets(meta_data=meta_data_expr,
                                   fields=['ID', 'moc_sky_fraction'],
                                   get_query_payload=False)

        assert isinstance(result, Table)
