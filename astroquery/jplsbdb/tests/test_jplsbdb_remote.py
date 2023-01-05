# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import astropy.units as u

from .. import SBDB


@pytest.mark.remote_data
class TestSBDBClass:

    def test_id_types(self):
        sbdb1 = SBDB.query('Mommert', id_type='search')
        sbdb2 = SBDB.query('1998 QS55', id_type='desig')
        sbdb3 = SBDB.query('2012893', id_type='spk')

        assert sbdb1['object']['fullname'] == '12893 Mommert (1998 QS55)'
        assert sbdb2['object']['fullname'] == '12893 Mommert (1998 QS55)'
        assert sbdb3['object']['fullname'] == '12893 Mommert (1998 QS55)'

    def test_name_search(self):
        sbdb = SBDB.query('2014 AA1*', id_type='search',
                          neo_only=True)
        assert sbdb['list']['pdes'] == ['2006 AN', '2014 AA17']

    def test_uri(self):
        sbdb = SBDB.query('Mommert', id_type='search',
                          get_uri=True)
        assert sbdb['query_uri'] == ('https://ssd-api.jpl.nasa.gov/sbdb.api'
                                     '?sstr=Mommert')

    def test_array_creation(self):
        sbdb = SBDB.query('Apophis', id_type='search',
                          close_approach=True)

        assert (sbdb['ca_data']['jd'].shape[0] > 0
                and len(sbdb['ca_data']['jd'].shape) == 1)

    def test_units(self):
        sbdb = SBDB.query('Apophis', id_type='search',
                          close_approach=True)

        assert sbdb['orbit']['moid_jup'].unit.bases[0] == u.au
        assert sbdb['orbit']['model_pars']['A2'].unit.bases == [u.au, u.d]
        assert sbdb['orbit']['model_pars']['A2'].unit.is_equivalent(u.au / u.d**2)
        assert sbdb['orbit']['elements']['tp'].unit.bases[0] == u.d

        sbdb = SBDB.query('Bennu', id_type='search', phys=True)
        assert sbdb['phys_par']['I'].unit == u.Unit('J / (K m2 s(1/2))')
