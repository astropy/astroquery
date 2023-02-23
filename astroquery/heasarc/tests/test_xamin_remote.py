# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord

from pyvo.dal.exceptions import DALOverflowWarning

from astroquery.heasarc import Xamin


OBJ_LIST = ["NGC 4151", "182d38m08.64s 39d24m21.06s",
            SkyCoord(l=155.0771, b=75.0631, unit=(u.deg, u.deg), frame='galactic')]

@pytest.mark.remote_data
class TestXamin:

    @pytest.mark.parametrize("coordinates", OBJ_LIST)
    def test_query_region_cone(self, coordinates):
        """
        Test multiple ways of specifying coordinates for a conesearch
        """
        result = Xamin.query_region(coordinates, table='suzamaster', spatial='cone', radius=1*u.arcmin)
        assert isinstance(result, Table)
        assert len(result) == 3
        # assert all columns are returned
        assert len(result.colnames) == 52


    def test_query_columns_radius(self):
        """
        Test selection of only a few columns, and using a bigger radius
        """
        result = Xamin.query_region("NGC 4151", table='suzamaster', columns='ra,dec,obsid', radius=10*u.arcmin)
        assert len(result) == 4
        # assert only selected columns are returned
        assert result.colnames == ['ra', 'dec', 'obsid']

    def test_query_region_box(self):
        result = Xamin.query_region(
            "182d38m08.64s 39d24m21.06s", table='suzamaster', spatial='box',
            width=2 * u.arcmin)
        assert isinstance(result, Table)
        assert len(result) == 3

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        with pytest.warns(UserWarning, match='Polygon endpoints are being interpreted'):
            result = Xamin.query_region("NGC 4151", table="suzamaster", spatial="polygon", polygon=polygon)

        assert isinstance(result, Table)

    def test_list_tables(self):
        tables = Xamin.tables()
        # Number of available tables may change over time, test only for significant drop.
        # (at the time of writing there are 1020 tables in the list).
        assert len(tables) > 1000

    def test_tap(self):
        query = "SELECT TOP 10 ra,dec FROM xray"
        with pytest.warns(expected_warning=DALOverflowWarning,
                          match="Partial result set. Potential causes MAXREC, async storage space, etc."):
            result = Xamin.query_tap(query=query, maxrec=5)
        assert len(result) == 5
        assert result.to_table().colnames == ['ra', 'dec']


    def test_data_links(self):
        with pytest.raises(ValueError, match='Unknown table name:'):
            Xamin.get_links(Table({'__row':[1,2,3.]}), tablename='wrongtable')
