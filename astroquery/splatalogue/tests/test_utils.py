# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import splatalogue
from astropy import units as u
import numpy as np
from .test_splatalogue import patch_post
from .. import utils


def test_clean(patch_post):
    x = splatalogue.Splatalogue.query_lines(114 * u.GHz, 116 * u.GHz,
                                            chemical_name=' CO ')
    c = utils.clean_column_headings(x)
    assert 'Resolved QNs' not in c.colnames
    assert 'QNs' in c.colnames


def test_merge(patch_post):
    x = splatalogue.Splatalogue.query_lines(114 * u.GHz, 116 * u.GHz,
                                            chemical_name=' CO ')
    c = utils.merge_frequencies(x)
    assert 'Freq' in c.colnames
    assert np.all(c['Freq'] > 0)


def test_minimize(patch_post):
    x = splatalogue.Splatalogue.query_lines(114 * u.GHz, 116 * u.GHz,
                                            chemical_name=' CO ')
    c = utils.minimize_table(x)

    assert 'Freq' in c.colnames
    assert np.all(c['Freq'] > 0)
    assert 'Resolved QNs' not in c.colnames
    assert 'QNs' in c.colnames
