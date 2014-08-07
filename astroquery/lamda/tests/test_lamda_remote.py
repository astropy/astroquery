# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
from ... import lamda
import requests
import imp
imp.reload(requests)


@remote_data
def test_query_levels():
    result = lamda.query(mol='co', query_type='erg_levels')
    assert len(result) == 41


@remote_data
def test_query_radtrans():
    result = lamda.query(mol='co', query_type='rad_trans')
    assert len(result) == 40


@remote_data
def test_query_collrates():
    result = lamda.query(mol='co', query_type='coll_rates', coll_partner_index=1)
    assert len(result) == 820
