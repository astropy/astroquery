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

from .test_eso_catalogues import catalogue_list, catalogue_list_all


@pytest.mark.remote_data
class TestEso:
    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    def test_list_catalogues(self):
        eso = Eso()
        t = eso.list_catalogues(all_versions=False)
        t_all = eso.list_catalogues(all_versions=True)
        lt = len(t)
        lt_all = len(t_all)

        assert isinstance(t, list), f"Expected type {type(list)}; Obtained {type(t)}"
        assert lt > 0, "Expected non-empty list of catalogues"
        assert set(t) <= set(catalogue_list), "Expected different list of catalogues"
        assert set(t_all) <= set(catalogue_list_all), "Expected different list of catalogues"
        assert (
            lt_all >= lt
        ), "Expected all_versions=True to return equal or more catalogues than all_versions=False"

    @pytest.mark.filterwarnings("ignore::pyvo.dal.exceptions.DALOverflowWarning")
    @pytest.mark.parametrize("catalogue", catalogue_list)
    def test_query_catalogue(self, catalogue):
        eso = Eso()
        t = eso.query_catalogue(catalogue, ROW_LIMIT=5)

        assert isinstance(t, Table), f"Expected type {type(Table)}; Obtained {type(t)}"
        assert len(t) <= 5, f"Expected max 5 records; Obtained {len(t)}"
        assert len(t) > 0, "Expected non-empty table"

    @pytest.mark.parametrize("catalogue", catalogue_list)
    def test_query_catalogue_help(self, catalogue):
        eso = Eso()
        eso.query_catalogue(catalogue, help=True)
