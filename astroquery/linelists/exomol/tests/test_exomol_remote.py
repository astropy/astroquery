# Licensed under a 3-clause BSD style license - see LICENSE.rst
import gc
import warnings

import pytest
from astropy import units as u
from astropy.table import Table
from astroquery.linelists.exomol import ExoMol

try:
    import radis  # noqa: F401
    RADEX_NOT_AVAILABLE = False
except ImportError:
    RADEX_NOT_AVAILABLE = True


@pytest.mark.remote_data
def test_get_molecule_list_remote():
    molecules = ExoMol.get_molecule_list()
    assert isinstance(molecules, list)
    assert len(molecules) > 50
    assert any("CO" in m for m in molecules)


@pytest.mark.remote_data
def test_get_databases_H2O_remote():
    dbs = ExoMol.get_databases("H2O")
    assert isinstance(dbs, list)
    assert len(dbs) > 0


@pytest.mark.remote_data
@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_CO_remote():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ExoMol.query_lines(
            molecule="CO",
            wavenum_min=2000 * u.cm**-1,
            wavenum_max=2100 * u.cm**-1,
        )
        gc.collect()
    assert isinstance(result, Table)
    assert len(result) > 0


@pytest.mark.remote_data
@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_CO_with_H2_broadening_remote():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ExoMol.query_lines(
            molecule="CO",
            wavenum_min=2000 * u.cm**-1,
            wavenum_max=2050 * u.cm**-1,
            broadening_species="H2",
        )
        gc.collect()
    assert isinstance(result, Table)
    assert len(result) > 0
