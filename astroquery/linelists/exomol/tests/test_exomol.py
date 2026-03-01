# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import numpy as np
from astropy import units as u
from astropy.table import Table
from astroquery.linelists.exomol import ExoMol

try:
    import radis  # noqa: F401
    RADEX_NOT_AVAILABLE = False
except ImportError:
    RADEX_NOT_AVAILABLE = True


@pytest.fixture
def fake_linelist_df():
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
    return Table(
        {
            "T": np.arange(100, 3100, 100, dtype=float),
            "Q": np.linspace(10.0, 5000.0, 30),
        }
    )


@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_returns_table(monkeypatch, fake_linelist_df):
    monkeypatch.setattr(
        "radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_linelist_df
    )
    result = ExoMol.query_lines(
        "CO", wavenum_min=2000 * u.cm**-1, wavenum_max=2100 * u.cm**-1
    )
    assert isinstance(result, Table)
    assert len(result) == 50


@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_columns(monkeypatch, fake_linelist_df):
    monkeypatch.setattr(
        "radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_linelist_df
    )
    result = ExoMol.query_lines(
        "CO", wavenum_min=2000 * u.cm**-1, wavenum_max=2100 * u.cm**-1
    )
    for col in ["wav", "int", "A", "El", "Eu"]:
        assert col in result.colnames, f"Missing column: {col}"


@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_broadening_str(monkeypatch, fake_linelist_df):
    captured = {}

    def mock_fetch(*a, **kw):
        captured["broadening_species"] = kw.get("broadening_species")
        return fake_linelist_df

    monkeypatch.setattr("radis.io.exomol.fetch_exomol", mock_fetch)
    result = ExoMol.query_lines(
        "CO",
        wavenum_min=2000 * u.cm**-1,
        wavenum_max=2100 * u.cm**-1,
        broadening_species="H2",
    )
    assert isinstance(result, Table)
    assert captured["broadening_species"] == "H2"


@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_query_lines_broadening_list(monkeypatch, fake_linelist_df):
    captured = {}

    def mock_fetch(*a, **kw):
        captured["broadening_species"] = kw.get("broadening_species")
        return fake_linelist_df

    monkeypatch.setattr("radis.io.exomol.fetch_exomol", mock_fetch)
    result = ExoMol.query_lines(
        "H2O",
        database="POKAZATEL",
        wavenum_min=1000 * u.cm**-1,
        wavenum_max=1100 * u.cm**-1,
        broadening_species=["H2", "He"],
    )
    assert isinstance(result, Table)
    assert captured["broadening_species"] == ["H2", "He"]


@pytest.mark.skipif(RADEX_NOT_AVAILABLE, reason="radis is required for this test")
def test_get_partition_function_returns_table(monkeypatch, fake_pf_df):
    monkeypatch.setattr(
        "radis.io.exomol.fetch_exomol", lambda *a, **kw: fake_pf_df
    )
    result = ExoMol.get_partition_function("CO")
    assert isinstance(result, Table)
    assert "T" in result.colnames
    assert "Q" in result.colnames


def test_get_databases_returns_list(monkeypatch):
    fake_html = (
        "<html><body>"
        '<a href="/data/molecules/H2O/POKAZATEL/">POKAZATEL</a>'
        '<a href="/data/molecules/H2O/BT2/">BT2</a>'
        "</body></html>"
    )

    class FakeResponse:
        text = fake_html

        def raise_for_status(self):
            pass

    monkeypatch.setattr(
        ExoMol.__class__, "_request", lambda self, *a, **kw: FakeResponse()
    )
    dbs = ExoMol.get_databases("H2O")
    assert isinstance(dbs, list)
    assert "POKAZATEL" in dbs
    assert "BT2" in dbs
