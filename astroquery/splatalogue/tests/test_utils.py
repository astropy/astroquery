# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import units as u
import numpy as np
import pytest

from ... import splatalogue
from .. import utils


def test_clean(patch_post):
    x = splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                            max_frequency=116 * u.GHz,
                                            chemical_name=' CO ')
    c = utils.clean_column_headings(x)
    assert 'Resolved QNs' not in c.colnames
    assert 'resolved_QNs' in c.colnames


def test_minimize(patch_post):
    x = splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                            max_frequency=116 * u.GHz,
                                            chemical_name=' CO ')
    c = utils.minimize_table(x)

    assert 'Freq' in c.colnames
    assert np.all(c['Freq'] > 0)
    assert 'Resolved QNs' not in c.colnames
    assert 'resolved_QNs' in c.colnames


@pytest.mark.remote_data
def test_minimize_issue2135():
    """
    This was a regression test for 2135, but is now just a basic test for the
    new (March 2024) keywords
    """
    rslt = splatalogue.Splatalogue.query_lines(min_frequency=100*u.GHz,
                                               max_frequency=200*u.GHz,
                                               chemical_name=' SiO ',
                                               energy_max=1840,
                                               energy_type='eu_k',
                                               line_lists=['JPL', 'CDMS', 'SLAIM'],
                                               show_upper_degeneracy=True)

    minimized = utils.minimize_table(rslt)

    np.testing.assert_allclose(minimized['Freq'], rslt['orderedfreq'])
