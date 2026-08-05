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

catalog_list_test = ["KiDS_DR4_1_ugriZYJHKs_cat_fits"]  # test catalog


@pytest.mark.remote_data
class TestEso:
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_list_catalogs(self):
        eso = Eso()
        t = eso.list_catalogs(all_versions=False)
        t_all = eso.list_catalogs(all_versions=True)

        assert isinstance(t, list), f"Expected type {type(list)}; Obtained {type(t)}"
        assert len(t) > 0, "Expected non-empty list of catalogs"
        assert len(t_all) > 0, "Expected non-empty list of catalogs"
        assert len(t) >= len(catalog_list), "Expected more catalogs than the test list"
        assert len(t_all) >= len(catalog_list_all), "Expected more catalogs than the test list of all versions"
        assert len(t_all) > len(t), "Expected all_versions=True to return more catalogs than all_versions=False"

    @pytest.mark.filterwarnings("ignore::astroquery.exceptions.MaxResultsWarning")
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    @pytest.mark.parametrize("catalog", catalog_list_test)
    def test_query_catalog(self, catalog):
        eso = Eso()
        eso.ROW_LIMIT = 5
        t = eso.query_catalog(catalog)

        assert isinstance(t, Table), f"Expected type {type(Table)}; Obtained {type(t)}"
        assert len(t) <= 5, f"Expected max 5 records; Obtained {len(t)}"
        assert len(t) > 0, "Expected non-empty table"

    @pytest.mark.parametrize("catalog", catalog_list_test)
    def test_query_catalog_help(self, catalog):
        eso = Eso()
        eso.query_catalog(catalog, help=True)
