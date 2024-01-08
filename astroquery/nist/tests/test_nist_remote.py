# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.table import Table
import astropy.units as u

import pytest

from astroquery.nist import Nist


@pytest.mark.remote_data
class TestNist:

    def test_query_async(self):
        response = Nist.query_async(4000 * u.AA, 7000 * u.AA)
        assert response is not None
        assert response.status_code == 200

    def test_query(self):
        result = Nist.query(4000 * u.AA, 7000 * u.AA)
        assert isinstance(result, Table)

        # check that no javascript was left in the table
        # (regression test for 1355)

        assert set(result['TP'].filled()) == set(['T8637', 'T7771', 'N/A'])

    def test_unescape_html(self):
        response = Nist.query_async(4333 * u.AA, 4334 * u.AA, linename="V I")
        assert '&dagger;' in response.text
        # check that Unicode characters have been properly unescaped from their
        # raw HTML code equivalents during parsing
        response = Nist._parse_result(response)
        assert any('†' in s for s in response['Ei           Ek'])

    def test_query_limits(self):
        result = Nist.query(4101 * u.AA, 4103 * u.AA)
        # check that min, max wavelengths are appropriately set
        assert result['Ritz'].min() >= 4101
        assert result['Ritz'].max() <= 4103

        # check that the units are respected
        result = Nist.query(410.1 * u.nm, 410.3 * u.nm)
        assert result['Ritz'].min() >= 410.1
        assert result['Ritz'].max() <= 410.3

        result = Nist.query(0.4101 * u.um, 0.4103 * u.um)
        assert result['Ritz'].min() >= 0.4101
        assert result['Ritz'].max() <= 0.4103

        # check that non-supported units default to angstroms
        result = Nist.query(4101 * 1e-10 * u.m, 4103 * 1e-10 * u.m)
        assert result['Ritz'].min() >= 4101
        assert result['Ritz'].max() <= 4103
