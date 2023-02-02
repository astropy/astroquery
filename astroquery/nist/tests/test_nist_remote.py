# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.table import Table
import astropy.units as u

import pytest

from ... import nist


@pytest.mark.remote_data
class TestNist:

    def test_query_async(self):
        response = nist.core.Nist.query_async(4000 * u.nm, 7000 * u.nm)
        assert response is not None

    def test_query(self):
        result = nist.core.Nist.query(4000 * u.nm, 7000 * u.nm)
        assert isinstance(result, Table)

        # check that no javascript was left in the table
        # (regression test for 1355)
        assert set(result['TP']) == set(['T8637', 'T7771'])

    def test_unescape_html(self):
        response = nist.core.Nist.query_async(4333 * u.AA, 4334 * u.AA, linename="V I")
        assert '&dagger;' in response.text
        # check that Unicode characters have been properly unescaped from their
        # raw HTML code equivalents during parsing
        response = nist.core.Nist._parse_result(response)
        assert any('†' in s for s in response['Ei           Ek'])
