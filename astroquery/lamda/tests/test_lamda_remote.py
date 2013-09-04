# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import lamda

def test_query_levels(patch_get):
    result = lamda.query(mol='co', query_type='erg_levels')
    assert len(result) == 41


def test_query_radtrans(patch_get):
    result = lamda.query(mol='co', query_type='rad_trans')
    assert len(result) == 40


def test_query_collrates(patch_get):
    result = lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)
    assert len(result) == 820
