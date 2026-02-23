# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Tests for astroquery.linelists.exomol
Implements RADIS issue #925 - astroquery ExoMol module

Run offline tests:  pytest tests/test_exomol.py -v
Run remote tests:   pytest tests/test_exomol.py -v --remote-data
"""

import pytest
import numpy as np
from astropy.table import Table
from astroquery.linelists.exomol import ExoMol

try:
    import radis
except ImportError as e:
    pytest.skip(f"radis required for exomol tests: {e}")

# ===========================================================
# FIXTURES
# ===========================================================


@pytest.fixture
def fake_linelist_df():
    """Fake ExoMol line list Table for mocking."""
    rng = np.random.default_rng(42)
    return Table(
        {
            "wav": np.linspace(2000, 2100, 50),
            "int": rng.random(50),
            "A": rng.random(50),
            "El": rng.random(50) * 1000,
            "Eu": rng.random(50) * 1000 + 100,
        }
    )


@pytest.fixture
def fake_pf_df():
    """Fake partition function Table for mocking."""
    return Table(
        {
            "T": np.arange(100, 3100, 100, dtype=float),
            "Q": np.linspace(10.0, 5000.0, 30),
        }
    )


# ===========================================================
# MOCKED TESTS - always run in CI (no network needed)
# ===========================================================


def test_query_lines_returns_table(monkeypatch, fake_linelist_df):
    """query_lines must return astropy Table."""
    monkeypatch.setattr(
        "radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_linelist_df
    )
    result = ExoMol.query_lines("CO", load_wavenum_min=2000, load_wavenum_max=2100)
    assert isinstance(result, Table)
    assert len(result) == 50


def test_query_lines_columns(monkeypatch, fake_linelist_df):
    """Table must contain expected ExoMol line list columns."""
    monkeypatch.setattr(
        "radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_linelist_df
    )
    result = ExoMol.query_lines("CO", load_wavenum_min=2000, load_wavenum_max=2100)
    for col in ["wav", "int", "A", "El", "Eu"]:
        assert col in result.colnames, f"Missing column: {col}"


def test_query_lines_broadening_str(monkeypatch, fake_linelist_df):
    """broadening_species as string must work."""
    captured = {}

    def mock_fetch(*a, **kw):
        captured["broadening_species"] = kw.get("broadening_species")
        return fake_linelist_df

    monkeypatch.setattr("radis.io.exomol.fetch_exomol", mock_fetch)
    result = ExoMol.query_lines(
        "CO", load_wavenum_min=2000, load_wavenum_max=2100, broadening_species="H2"
    )
    assert isinstance(result, Table)
    assert captured["broadening_species"] == "H2"


def test_query_lines_broadening_list(monkeypatch, fake_linelist_df):
    """broadening_species as list must be passed through correctly."""
    captured = {}

    def mock_fetch(*a, **kw):
        captured["broadening_species"] = kw.get("broadening_species")
        return fake_linelist_df

    monkeypatch.setattr("radis.io.exomol.fetch_exomol", mock_fetch)
    result = ExoMol.query_lines(
        "H2O",
        database="POKAZATEL",
        load_wavenum_min=1000,
        load_wavenum_max=1100,
        broadening_species=["H2", "He"],
    )
    assert isinstance(result, Table)
    assert captured["broadening_species"] == ["H2", "He"]


def test_get_partition_function_returns_table(monkeypatch, fake_pf_df):
    """get_partition_function must return astropy Table."""
    monkeypatch.setattr("radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_pf_df)
    result = ExoMol.get_partition_function("CO")
    assert isinstance(result, Table)
    assert "T" in result.colnames
    assert "Q" in result.colnames


# ===========================================================
# REMOTE TESTS - actual ExoMol network calls
# Run with: pytest --remote-data
# ===========================================================


@pytest.mark.remote_data
def test_get_molecule_list_remote():
    """ExoMol must return 50+ molecules."""
    molecules = ExoMol.get_molecule_list()
    assert isinstance(molecules, list)
    assert len(molecules) > 50
    assert any("CO" in m for m in molecules)


@pytest.mark.remote_data
def test_get_databases_H2O_remote():
    """H2O must have multiple databases."""
    dbs = ExoMol.get_databases("H2O")
    assert isinstance(dbs, list)
    assert len(dbs) > 0


@pytest.mark.remote_data
def test_query_lines_CO_remote():
    """CO line list fetch must succeed and return Table."""
    import warnings
    import gc

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ExoMol.query_lines(
            molecule="CO",
            load_wavenum_min=2000,
            load_wavenum_max=2100,
        )
        gc.collect()
    assert isinstance(result, Table)
    assert len(result) > 0


@pytest.mark.remote_data
def test_query_lines_CO_with_H2_broadening_remote():
    """CO line list with H2 broadening must succeed (falls back to air if unavailable)."""
    import warnings
    import gc

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = ExoMol.query_lines(
            molecule="CO",
            load_wavenum_min=2000,
            load_wavenum_max=2050,
            broadening_species="H2",
        )
        gc.collect()
    assert isinstance(result, Table)
    assert len(result) > 0
