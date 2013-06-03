# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import lamda

def test_query():
    lamda.print_mols()
    lamda.query(mol='co', query_type='erg_levels')
    lamda.query(mol='co', query_type='rad_trans')
    lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)

