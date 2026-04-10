# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===========================
ESO Astroquery Module tests
===========================

European Southern Observatory (ESO)

"""

import pytest

from astropy.table import Table
from astroquery.eso import Eso

from .test_eso_catalogs import catalog_list, catalog_list_all


@pytest.mark.remote_data
class TestEso:
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_list_catalogs(self):
        eso = Eso()
        t = eso.list_catalogs(all_versions=False)
        t_all = eso.list_catalogs(all_versions=True)
        lt = len(t)
        lt_all = len(t_all)

        assert isinstance(t, list), f"Expected type {type(list)}; Obtained {type(t)}"
        assert lt > 0, "Expected non-empty list of catalogs"
        assert set(t) <= set(catalog_list), "Expected different list of catalogs"
        assert set(t_all) <= set(catalog_list_all), "Expected different list of catalogs"
        assert (
            lt_all >= lt
        ), "Expected all_versions=True to return equal or more catalogs than all_versions=False"

    @pytest.mark.filterwarnings("ignore::astroquery.exceptions.MaxResultsWarning")
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    @pytest.mark.parametrize("catalog", catalog_list)
    def test_query_catalog(self, catalog):
        eso = Eso()
        t = eso.query_catalog(catalog, ROW_LIMIT=5)

        assert isinstance(t, Table), f"Expected type {type(Table)}; Obtained {type(t)}"
        assert len(t) <= 5, f"Expected max 5 records; Obtained {len(t)}"
        assert len(t) > 0, "Expected non-empty table"

    @pytest.mark.parametrize("catalog", catalog_list)
    def test_query_catalog_help(self, catalog):
        eso = Eso()
        eso.query_catalog(catalog, help=True)
