# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os.path
import os
import sys
import pytest
import requests
from requests import ReadTimeout

from astropy.table import Table
from astropy.units import arcsec, arcmin
from astropy.io import ascii

from astropy.coordinates import SkyCoord

try:
    from regions import CircleSkyRegion
except ImportError:
    pass

from ...xmatch import XMatch


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


@pytest.mark.remote_data
@pytest.mark.dependency(name='xmatch_up')
def test_is_xmatch_up():
    try:
        requests.get("http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync")
    except Exception as ex:
        pytest.xfail("XMATCH appears to be down.  Exception was: {0}".format(ex))


@pytest.mark.remote_data
@pytest.mark.dependency(depends=["xmatch_up"])
class TestXMatch:
    # fixture only used here to save creating XMatch instances in each
    # of the following test functions
    @pytest.fixture
    def xmatch(self):
        return XMatch()

    def test_xmatch_avail_tables(self, xmatch):
        tables = xmatch.get_available_tables()
        assert tables
        # those example tables are from
        # http://cdsxmatch.u-strasbg.fr/xmatch/doc/API-calls.html
        assert 'II/311/wise' in tables
        assert 'II/246/out' in tables

    def test_xmatch_is_avail_table(self, xmatch):
        assert xmatch.is_table_available('II/311/wise')
        assert xmatch.is_table_available('II/246/out')
        assert xmatch.is_table_available('vizier:II/311/wise')
        assert not xmatch.is_table_available('blablabla')

    def test_xmatch_query(self, xmatch):
        with open(os.path.join(DATA_DIR, 'posList.csv'), 'r') as pos_list:
            try:
                table = xmatch.query(
                    cat1=pos_list, cat2='vizier:II/246/out', max_distance=5 * arcsec,
                    colRA1='ra', colDec1='dec')
            except ReadTimeout:
                pytest.xfail("xmatch query timed out.")
        assert isinstance(table, Table)
        assert table.colnames == [
            'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
            'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
            'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
        assert len(table) == 11

        http_test_table = self.http_test()
        assert all(table == http_test_table)

    def test_xmatch_query_astropy_table(self, xmatch):
        datapath = os.path.join(DATA_DIR, 'posList.csv')
        input_table = Table.read(datapath, format='ascii.csv')
        try:
            table = xmatch.query(
                cat1=input_table, cat2='vizier:II/246/out', max_distance=5 * arcsec,
                colRA1='ra', colDec1='dec')
        except ReadTimeout:
            pytest.xfail("xmatch query timed out.")
        assert isinstance(table, Table)
        assert table.colnames == [
            'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
            'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
            'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
        assert len(table) == 11

        http_test_table = self.http_test()
        assert all(table == http_test_table)

    @pytest.mark.skipif('regions' not in sys.modules,
                        reason="requires astropy-regions")
    def test_xmatch_query_with_cone_area(self, xmatch):
        try:
            table = xmatch.query(
                cat1='vizier:II/311/wise', cat2='vizier:II/246/out', max_distance=5 * arcsec,
                area=CircleSkyRegion(center=SkyCoord(10, 10, unit='deg', frame='icrs'), radius=12 * arcmin))
        except ReadTimeout:
            pytest.xfail("xmatch query timed out.")
        assert len(table) == 185

    def http_test(self):
        # this can be used to check that the API is still functional & doing as expected
        infile = os.path.join(DATA_DIR, 'posList.csv')
        outfile = os.path.join(DATA_DIR, 'http_result.csv')
        os.system('curl -X POST -F request=xmatch -F distMaxArcsec=5 -F RESPONSEFORMAT=csv '
                  '-F cat1=@{1} -F colRA1=ra -F colDec1=dec -F cat2=vizier:II/246/out  '
                  'http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync > {0}'.
                  format(outfile, infile))
        table = ascii.read(outfile, format='csv', fast_reader=False)
        return table
