# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyDeprecationWarning

from pyvo.dal.exceptions import DALOverflowWarning

from astroquery.ipac.irsa import Irsa


OBJ_LIST = ["m31", "00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743, b=-21.5733, unit=(u.deg, u.deg), frame='galactic')]


@pytest.mark.remote_data
class TestIrsa:

    @pytest.mark.parametrize("coordinates", OBJ_LIST)
    def test_query_region_cone(self, coordinates):
        """
        Test multiple ways of specifying coordinates for a conesearch
        """
        result = Irsa.query_region(coordinates, catalog='fp_psc', spatial='Cone')
        assert isinstance(result, Table)
        assert len(result) == 19
        # assert all columns are returned
        assert len(result.colnames) == 64

    def test_query_selcols_deprecated(self):
        """
        Test renamed selcols
        """
        with pytest.warns(AstropyDeprecationWarning, match='"selcols" was deprecated in version'):
            result = Irsa.query_region("m31", catalog='fp_psc', selcols='ra,dec,j_m')

        assert result.colnames == ['ra', 'dec', 'j_m']

    def test_query_columns_radius(self):
        """
        Test selection of only a few columns, and using a bigger radius
        """
        result = Irsa.query_region("m31", catalog='fp_psc', columns='ra,dec,j_m', radius=0.5 * u.arcmin)
        assert len(result) == 84
        # assert only selected columns are returned
        assert result.colnames == ['ra', 'dec', 'j_m']

    def test_query_region_box(self):
        result = Irsa.query_region(
            "00h42m44.330s +41d16m07.50s", catalog='fp_psc', spatial='Box', width=0.5 * u.arcmin)
        assert isinstance(result, Table)
        assert len(result) == 24

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        with pytest.warns(UserWarning, match='Polygon endpoints are being interpreted'):
            result = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon", polygon=polygon)

        assert isinstance(result, Table)
        assert len(result) == 7

    def test_list_columns(self):
        columns = Irsa.list_columns('slphotdr4')
        assert len(columns) == 203
        assert isinstance(columns, dict)

        full_columns = Irsa.list_columns('slphotdr4', full=True)
        assert isinstance(full_columns, Table)

    def test_list_catalogs(self):
        catalogs = Irsa.list_catalogs()
        # Number of available catalogs may change over time, test only for significant drop.
        # (at the time of writing there are 933 tables in the list).
        assert len(catalogs) > 900
        assert isinstance(catalogs, dict)

    def test_list_catalogs_filter(self):
        spitzer_catalogs = Irsa.list_catalogs(filter='spitzer')

        assert len(spitzer_catalogs) == 142

    @pytest.mark.parametrize('servicetype', (None, 'sia', 'ssa'))
    def test_list_collections(self, servicetype):
        collections = Irsa.list_collections(servicetype=servicetype)
        # Number of available collections may change over time, test only for significant drop.
        # (at the time of writing there are 104 SIA and 35 SSA collections in the list).
        assert isinstance(collections, Table)
        if servicetype == 'ssa':
            assert len(collections) > 30
            assert 'sofia_exes' in collections['collection']
        else:
            assert len(collections) > 100
            assert 'spitzer_seip' in collections['collection']
            assert 'wise_allwise' in collections['collection']

    def test_list_collections_filter(self):
        spitzer_collections = Irsa.list_collections(filter='spitzer')

        assert len(spitzer_collections) == 47

    def test_tap(self):
        query = "SELECT TOP 5 ra,dec FROM cosmos2015"
        with pytest.warns(expected_warning=DALOverflowWarning,
                          match="Partial result set. Potential causes MAXREC, async storage space, etc."):
            result = Irsa.query_tap(query=query)
        assert len(result) == 5
        assert result.to_table().colnames == ['ra', 'dec']

    def test_ssa(self):
        coord = SkyCoord.from_name("Eta Carina")
        result = Irsa.query_ssa(pos=coord)
        assert len(result) > 260
        collections = set(result['dataid_collection'])
        assert {'champ', 'iso_sws', 'sofia_forcast', 'sofia_great', 'spitzer_sha'}.issubset(collections)
