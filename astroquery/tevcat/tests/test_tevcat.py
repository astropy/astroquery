# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
from ..core import get_tevcat, _TeVCat


def _test_tevcat_local():
    """Check that table extraction for HTML works"""
    t = _TeVCat()
    # TODO: I'm not sure how to create the test HTML data file
    # with only a few of data present.
    t._html = 'TODO'
    t._extract_version()
    t._extract_data()
    t._make_table()
    table = t.table

    assert len(table) == 2
    assert 'TeV J0534+220' in table['catalog_name']


@remote_data
def test_tevcat_remote():
    table = get_tevcat()
    assert len(table) > 100

    assert 'TeV J0534+220' in table['catalog_name']
