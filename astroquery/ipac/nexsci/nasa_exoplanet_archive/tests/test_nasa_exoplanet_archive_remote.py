# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest

import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord

from astropy.tests.helper import assert_quantity_allclose
from astroquery.exceptions import InputWarning, InvalidQueryError, NoResultsWarning
from astroquery.ipac.nexsci.nasa_exoplanet_archive.core import InvalidTableError, NasaExoplanetArchive


@pytest.mark.remote_data
def test_invalid_table():
    with pytest.raises(InvalidTableError) as error:
        NasaExoplanetArchive.query_criteria("not_a_table")
    assert "not_a_table" in str(error)


@pytest.mark.remote_data
def test_invalid_column():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("ps", select="not_a_column")
    assert "not_a_column" in str(error).lower()


@pytest.mark.remote_data
def test_invalid_query_exoplanets():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("ps", where="hostname=Kepler-11")
    assert "kepler" in str(error).lower()


@pytest.mark.remote_data
def test_invalid_query_kepler():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("keplertimeseries", where="kepid=8561063")
    assert "'KEPID': invalid identifier" in str(error)
    NasaExoplanetArchive.query_criteria("keplertimeseries", where="star_id=8561063")


@pytest.mark.skip('TMP skip, server stuck with query')
@pytest.mark.remote_data
def test_missing_criterion_kelt():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("kelttimeseries")
    assert "Queries against the KELT Time Series table require" in str(error)
    NasaExoplanetArchive.query_criteria(
        "kelttimeseries", where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02"
    )


@pytest.mark.skip('TMP skip, server stuck with query')
@pytest.mark.remote_data
def test_missing_criterion_super_wasp():
    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_criteria("superwasptimeseries")
    assert "Queries against the SuperWASP Time Series table require" in str(error)
    NasaExoplanetArchive.query_criteria(
        "superwasptimeseries", sourceid="1SWASP J191645.46+474912.3"
    )


@pytest.mark.remote_data
def _compare_tables(table1, table2):
    assert len(table1) == len(table2)
    for col in sorted(set(table1.columns) | set(table2.columns)):
        assert col in table1.columns
        assert col in table2.columns
        try:
            m = np.isfinite(table1[col]) & np.isfinite(table2[col])
            assert_quantity_allclose(table1[col][m], table2[col][m])
        except TypeError:
            try:
                # SkyCoords
                assert np.all(table1[col].separation(table2[col]) < 0.1 * u.arcsec)
            except AttributeError:
                assert np.all(table1[col] == table2[col])


@pytest.mark.remote_data
def test_select():
    payload_sql = NasaExoplanetArchive.query_criteria("ps", select=["hostname", "pl_name"],
                                                      where="hostname='Kepler-11'", get_query_payload=True)
    assert "hostname,pl_name" in payload_sql

    table1 = NasaExoplanetArchive.query_criteria("ps", select=["hostname", "pl_name"], where="hostname='Kepler-11'")

    table2 = NasaExoplanetArchive.query_criteria("ps", select="hostname,pl_name", where="hostname='Kepler-11'")
    _compare_tables(table1, table2)


@pytest.mark.remote_data
def test_warnings():
    with pytest.warns(NoResultsWarning):
        NasaExoplanetArchive.query_criteria("ps", where="hostname='not a host'")

    with pytest.warns(InputWarning):
        NasaExoplanetArchive.query_object("HAT-P-11 b", where="nothing")

    with pytest.warns(InputWarning):
        NasaExoplanetArchive.query_object(object_name="K2-18 b", table="pscomppars", where="nothing")

    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_object("HAT-P-11 b", table="cumulative")
    assert "Invalid table 'cumulative'" in str(error)


@pytest.mark.remote_data
def test_table_errors():
    with pytest.raises(InvalidTableError) as error:
        NasaExoplanetArchive.query_object("K2-18 b", table="exoplanets")
    assert "exoplanets" in str(error)

    with pytest.raises(InvalidTableError) as error:
        NasaExoplanetArchive.query_object("K2-18 b", table="exomultpars")
    assert "exomultpars" in str(error)

    with pytest.raises(InvalidTableError) as error:
        NasaExoplanetArchive.query_object("K2-18 b", table="compositepars")
    assert "compositepars" in str(error)


@pytest.mark.remote_data
def test_request_to_sql():
    payload = NasaExoplanetArchive.query_region("ps", coordinates=SkyCoord(ra=172.56 * u.deg, dec=7.59 * u.deg),
                                                radius=1.0 * u.deg, get_query_payload=True)

    assert payload == "select * from ps where contains(point('icrs',ra,dec),circle('icrs',172.56,7.59,1.0 degree))=1"

    payload_sql = NasaExoplanetArchive.query_criteria(table="ps", where="hostname like 'Kepler%'",
                                                      order="hostname", get_query_payload=True)

    assert payload_sql == "select * from ps where hostname like 'Kepler%' order by hostname"

    # "cumulative" table is now in TAP_TABLES
    payload_dict = NasaExoplanetArchive.query_criteria(table="cumulative", where="pl_hostname like 'Kepler%'",
                                                       order="pl_hostname", get_query_payload=True)
    assert isinstance(payload_dict, str)


@pytest.mark.remote_data
def test_query_region():
    coords = SkyCoord(ra=330.79488 * u.deg, dec=18.8843 * u.deg)
    radius = 0.001
    table1 = NasaExoplanetArchive.query_region("pscomppars", coords, radius * u.deg)
    assert len(table1) == 1
    assert table1["hostname"] == "HD 209458"

    table2 = NasaExoplanetArchive.query_region("pscomppars", coords, radius)
    _compare_tables(table1, table2)


@pytest.mark.remote_data
def test_query_aliases():
    name = "bet Pic"
    aliases = NasaExoplanetArchive.query_aliases(name)
    assert len(aliases) > 10
    assert "HD 39060" in aliases


@pytest.mark.remote_data
def test_query_aliases_multi():
    aliases = NasaExoplanetArchive.query_aliases("LTT1445A")
    assert len(aliases) > 10
    assert "BD-17 588 A" in aliases


@pytest.mark.remote_data
def test_format():
    table1 = NasaExoplanetArchive.query_object("HAT-P-11 b")
    table2 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="votable")
    _compare_tables(table1, table2)

    table1 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="csv")
    table2 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="bar")
    _compare_tables(table1, table2)

    table1 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="xml")
    table2 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="table")
    _compare_tables(table1, table2)

    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_object("HAT-P-11 b", format="json")
    assert "json" in str(error)


@pytest.mark.remote_data
def test_table_case_sensivity():
    # Regression test from #3090
    table = NasaExoplanetArchive.query_criteria(table='DI_STARS_EXEP', select='tic_id')
    assert len(table) > 0
