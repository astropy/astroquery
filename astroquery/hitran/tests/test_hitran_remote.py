import numpy as np
import pytest
from astropy import units as u
from astropy.table import Table

from ...hitran import Hitran


@pytest.mark.remote_data
def test_query_remote():
    # 2026-07-24: returns 27 instead of 29 now?
    # there were legitimate updates to the water table,
    # so note that remote failures here may indicate database updates
    # (but may not so we should investigate if there are changes)
    tbl = Hitran.query_lines(molecule_number=1, isotopologue_number=1,
                             min_frequency=0. / u.cm, max_frequency=10. / u.cm)
    assert isinstance(tbl, Table)
    assert len(tbl) == 27
    assert set(tbl.keys()) == set(['molec_id', 'local_iso_id', 'nu', 'sw', 'a',
                                   'gamma_air', 'gamma_self', 'elower',
                                   'n_air', 'delta_air', 'global_upper_quanta',
                                   'global_lower_quanta', 'local_upper_quanta',
                                   'local_lower_quanta', 'ierr1', 'ierr2',
                                   'ierr3', 'ierr4', 'ierr5', 'ierr6', 'iref1',
                                   'iref2', 'iref3', 'iref4', 'iref5', 'iref6',
                                   'line_mixing_flag', 'gp', 'gpp'])
    assert tbl['molec_id'][0] == 1
    assert tbl['local_iso_id'][0] == 1
    np.testing.assert_almost_equal(tbl['nu'][0], 0.072052)
