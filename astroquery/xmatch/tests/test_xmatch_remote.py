# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os.path
import os
import pytest

from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.units import arcsec
from astropy.io import ascii

from ...xmatch import XMatch


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


# fixture only used here to save creating XMatch instances in each
# of the following test functions
@pytest.fixture
def xmatch():
    return XMatch()


@remote_data
def test_xmatch_avail_tables(xmatch):
    tables = xmatch.get_available_tables()
    assert tables
    # those example tables are from
    # http://cdsxmatch.u-strasbg.fr/xmatch/doc/API-calls.html
    assert 'II/311/wise' in tables
    assert 'II/246/out' in tables


@remote_data
def test_xmatch_is_avail_table(xmatch):
    assert xmatch.is_table_available('II/311/wise')
    assert xmatch.is_table_available('II/246/out')
    assert xmatch.is_table_available('vizier:II/311/wise')
    assert not xmatch.is_table_available('blablabla')


@remote_data
def test_xmatch_query(xmatch):
    with open(os.path.join(DATA_DIR, 'posList.csv'), 'r') as pos_list:
        table = xmatch.query(
            cat1=pos_list, cat2='vizier:II/246/out', max_distance=5 * arcsec,
            colRA1='ra', colDec1='dec')
    assert isinstance(table, Table)
    assert table.colnames == [
        'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
        'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
        'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
    assert len(table) == 11

    http_test_table = http_test()
    assert all(table == http_test_table)


@remote_data
def test_xmatch_query_astropy_table(xmatch):
    datapath = os.path.join(DATA_DIR, 'posList.csv')
    input_table = Table.read(datapath, format='ascii.csv')
    table = xmatch.query(
        cat1=input_table, cat2='vizier:II/246/out', max_distance=5 * arcsec,
        colRA1='ra', colDec1='dec')
    assert isinstance(table, Table)
    assert table.colnames == [
        'angDist', 'ra', 'dec', 'my_id', '2MASS', 'RAJ2000', 'DEJ2000',
        'errHalfMaj', 'errHalfMin', 'errPosAng', 'Jmag', 'Hmag', 'Kmag',
        'e_Jmag', 'e_Hmag', 'e_Kmag', 'Qfl', 'Rfl', 'X', 'MeasureJD']
    assert len(table) == 11

    http_test_table = http_test()
    assert all(table == http_test_table)


@remote_data
def http_test():
    # this can be used to check that the API is still functional & doing as expected
    infile = os.path.join(DATA_DIR, 'posList.csv')
    outfile = os.path.join(DATA_DIR, 'http_result.csv')
    os.system('curl -X POST -F request=xmatch -F distMaxArcsec=5 -F RESPONSEFORMAT=csv '
              '-F cat1=@{1} -F colRA1=ra -F colDec1=dec -F cat2=vizier:II/246/out  '
              'http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync > {0}'.
              format(outfile, infile))
    table = ascii.read(outfile, format='csv')
    return table
