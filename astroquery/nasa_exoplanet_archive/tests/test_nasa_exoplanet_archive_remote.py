# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest

from ...exceptions import InvalidQueryError
from ..core import InvalidTableError, NasaExoplanetArchive


@pytest.mark.remote_data
def test_invalid_table():
    with pytest.raises(InvalidTableError):
        NasaExoplanetArchive.query_criteria("not_a_table")


@pytest.mark.remote_data
def test_invalid_column():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("exoplanets", select="not_a_column")
    assert "not_a_column" in str(error)


@pytest.mark.remote_data
def test_invalid_query_exoplanets():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("exoplanets", where="pl_hostname=Kepler-11")
    assert "kepler" in str(error)


@pytest.mark.remote_data
def test_missing_criterion_kepler():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("keplertimeseries", where="kepid=8561063")
    assert "Queries against the Kepler Time Series table require" in str(error)
    NasaExoplanetArchive.query_criteria("keplertimeseries", kepid=8561063, quarter=14)


@pytest.mark.remote_data
def test_missing_criterion_kelt():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("kelttimeseries")
    assert "Queries against the KELT Time Series table require" in str(error)
    NasaExoplanetArchive.query_criteria(
        "kelttimeseries", where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02"
    )


@pytest.mark.remote_data
def test_missing_criterion_super_wasp():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("superwasptimeseries")
    assert "Queries against the SuperWASP Time Series table require" in str(error)
    NasaExoplanetArchive.query_criteria(
        "superwasptimeseries", sourceid="1SWASP J191645.46+474912.3"
    )
