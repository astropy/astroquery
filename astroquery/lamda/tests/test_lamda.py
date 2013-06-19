# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import lamda


def test_print_query():
    lamda.print_mols()

def test_query_levels():
    lamda.query(mol='co', query_type='erg_levels')

def test_query_radtrans():
    lamda.query(mol='co', query_type='rad_trans')

def test_query_collrates():
    lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)
