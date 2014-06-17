import os.path

import pytest
from astropy.tests.helper import remote_data

from ...xmatch import XMatch


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


@pytest.fixture
def xmatch():
    return XMatch()


@remote_data
def test_xmatch_avail_tables(xmatch):
    tables = xmatch.get_available_tables('txt').splitlines()
    assert tables
    # those example tables are from
    # http://cdsxmatch.u-strasbg.fr/xmatch/doc/API-calls.html
    assert 'II/311/wise' in tables
    assert 'II/246/out' in tables


@remote_data
def test_xmatch_is_avail_table(xmatch):
    assert xmatch.is_available_table('II/311/wise')
    assert xmatch.is_available_table('II/246/out')
    assert not xmatch.is_available_table('vizier:II/311/wise')


@remote_data
def test_xmatch_query(xmatch):
    with open(os.path.join(DATA_DIR, 'expected_output.csv')) as csv:
        expected_csv_output = csv.read()
    with open(os.path.join(DATA_DIR, 'posList.csv')) as pos_list:
        csv = xmatch.query(
            pos_list, 'vizier:II/246/out', 5, 'csv', 'ra', 'dec')
        assert csv == expected_csv_output
