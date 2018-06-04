

import numpy as np
from astropy import units as u
from astropy.table import Table
from astropy.tests.helper import remote_data

from ...jpl_spectral_catalog import JPLSpec

@remote_data
def test_remote():
    tbl = JPLSpec.query_lines(min_frequency = 500 * u.GHz, max_frequency = 1000 * u.GHz, min_strength = -500,\
    molecule = "18003 H20")
    assert isinstance(tbl,Table)
    assert len(tbl) == 36
    assert set(tbl.keys()) == set(['FREQ', 'ERR', 'LGINT', 'DR', 'ELO', 'GUP',
           'TAG', 'QNFMT', 'QN\'', 'QN"'])

    assert tbl['FREQ'][0] == 503568.5200
    assert tbl['ERR'][0] == 0.0200
    assert tbl['LGINT'][0] == -4.9916
    assert tbl['ERR'][7] == 12.4193
    assert tbl['FREQ'][35] == 987926.7590
