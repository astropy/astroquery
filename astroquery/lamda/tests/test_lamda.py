# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import lamda

def test_query():
    Q = lamda.core.LAMDAQuery()
    Q.lamda_query(mol='co', query_type='erg_levels')
    Q.lamda_query(mol='co', query_type='rad_trans')
    Q.lamda_query(mol='co', query_type='coll_rates')

