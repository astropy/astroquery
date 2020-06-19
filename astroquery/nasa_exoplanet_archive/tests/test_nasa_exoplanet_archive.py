# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import json
import os
import sys
from urllib.parse import urlencode

import astropy.units as u
import numpy as np
import pkg_resources
import pytest
import requests
from astropy.coordinates import SkyCoord
from astropy.tests.helper import assert_quantity_allclose
from astropy.utils.exceptions import AstropyDeprecationWarning

from ...exceptions import InputWarning, InvalidQueryError, NoResultsWarning
from ...utils.testing_tools import MockResponse
from ..core import NasaExoplanetArchive, conf

MAIN_DATA = pkg_resources.resource_filename("astroquery.nasa_exoplanet_archive", "data")
TEST_DATA = pkg_resources.resource_filename(__name__, "data")
RESPONSE_FILE = os.path.join(TEST_DATA, "responses.json")
ALL_TABLES = [
    ("exoplanets", dict(where="pl_hostname='Kepler-11'")),
    ("compositepars", dict(where="fpl_hostname='WASP-166'")),
    ("exomultpars", dict(where="mpl_hostname='TrES-2'")),
    ("microlensing", dict(where="plntname='MOA-2010-BLG-353L b'")),
    ("cumulative", dict(where="kepid=10601284")),
    ("koi", dict(where="kepid=10601284")),
    ("q1_q17_dr25_sup_koi", dict(where="kepid=10601284")),
    ("q1_q17_dr25_koi", dict(where="kepid=10601284")),
    ("q1_q17_dr24_koi", dict(where="kepid=10601284")),
    ("q1_q16_koi", dict(where="kepid=10601284")),
    ("q1_q12_koi", dict(where="kepid=10601284")),
    ("q1_q8_koi", dict(where="kepid=10601284")),
    ("q1_q6_koi", dict(where="kepid=10601284")),
    ("tce", dict(where="kepid=10601284")),
    ("q1_q17_dr25_tce", dict(where="kepid=10601284")),
    ("q1_q17_dr24_tce", dict(where="kepid=10601284")),
    ("q1_q16_tce", dict(where="kepid=10601284")),
    ("q1_q12_tce", dict(where="kepid=10601284")),
    ("keplerstellar", dict(where="kepid=10601284")),
    ("q1_q17_dr25_supp_stellar", dict(where="kepid=10601284")),
    ("q1_q17_dr25_stellar", dict(where="kepid=10601284")),
    ("q1_q17_dr24_stellar", dict(where="kepid=10601284")),
    ("q1_q16_stellar", dict(where="kepid=10601284")),
    ("q1_q12_stellar", dict(where="kepid=10601284")),
    ("keplertimeseries", dict(kepid=8561063, quarter=14)),
    ("keplernames", dict(where="kepid=10601284")),
    ("kelttimeseries", dict(where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02")),
    ("kelt", dict(where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02")),
    ("superwasptimeseries", dict(sourceid="1SWASP J191645.46+474912.3")),
    ("k2targets", dict(where="epic_number=206027655")),
    ("k2candidates", dict(where="epic_name='EPIC 206027655'")),
    ("k2names", dict(where="epic_host='EPIC 206027655'")),
    ("missionstars", dict(where="star_name='tau Cet'")),
    ("mission_exocat", dict(where="star_name='HIP 5110 A'")),
    pytest.param(
        "toi",
        dict(where="toi=256.01"),
        marks=pytest.mark.skipif(
            sys.platform.startswith("win"), reason="TOI table cannot be loaded on Windows"
        ),
    ),
]


def mock_get(self, method, url, *args, **kwargs):  # pragma: nocover
    assert url == conf.url

    params = kwargs.get("params", None)
    assert params is not None

    try:
        with open(RESPONSE_FILE, "r") as f:
            responses = json.load(f)
    except FileNotFoundError:
        responses = {}

    # Work out where the expected response is saved
    table = params["table"]
    key = urlencode(sorted(params.items()))
    try:
        index = responses.get(table, []).index(key)
    except ValueError:
        index = -1

    # If the NASA_EXOPLANET_ARCHIVE_GENERATE_RESPONSES environment variable is set, we make a
    # remote request if necessary. Otherwise we throw a ValueError.
    if index < 0:
        if "NASA_EXOPLANET_ARCHIVE_GENERATE_RESPONSES" not in os.environ:
            raise ValueError("unexpected request")
        with requests.Session() as session:
            resp = session.old_request(method, url, params=params)
        responses[table] = responses.get(table, [])
        responses[table].append(key)
        index = len(responses[table]) - 1
        with open(os.path.join(TEST_DATA, "{0}_expect_{1}.txt".format(table, index)), "w") as f:
            f.write(resp.text)
        with open(RESPONSE_FILE, "w") as f:
            json.dump(responses, f, sort_keys=True, indent=2)

    with open(os.path.join(TEST_DATA, "{0}_expect_{1}.txt".format(table, index)), "r") as f:
        data = f.read()

    return MockResponse(data.encode("utf-8"))


@pytest.fixture
def patch_get(request):  # pragma: nocover
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:
        mp = request.getfuncargvalue("monkeypatch")

    # Keep track of the original function so that we can use it to generate the expected responses
    requests.Session.old_request = requests.Session.request
    mp.setattr(requests.Session, "request", mock_get)
    return mp


def test_regularize_object_name(patch_get):
    assert NasaExoplanetArchive._regularize_object_name("kepler 2") == "HAT-P-7"
    assert NasaExoplanetArchive._regularize_object_name("kepler 1 b") == "TrES-2 b"

    with pytest.warns(NoResultsWarning) as warning:
        NasaExoplanetArchive._regularize_object_name("not a planet")
    assert "No aliases found for name: 'not a planet'" == str(warning[0].message)


def test_backwards_compat(patch_get):
    """These are the tests from the previous version of this interface"""

    # test_hd209458b_exoplanets_archive
    with pytest.warns(AstropyDeprecationWarning):
        params = NasaExoplanetArchive.query_planet("HD 209458 b ")
    assert_quantity_allclose(params["pl_radj"], 1.320 * u.R_jup, atol=0.1 * u.R_jup)

    # test_hd209458b_exoplanet_archive_coords
    with pytest.warns(AstropyDeprecationWarning):
        params = NasaExoplanetArchive.query_planet("HD 209458 b ")
    simbad_coords = SkyCoord(ra="22h03m10.77207s", dec="+18d53m03.5430s")
    sep = params["sky_coord"][0].separation(simbad_coords)
    assert abs(sep) < 5 * u.arcsec

    # test_hd209458_stellar_exoplanet
    with pytest.warns(AstropyDeprecationWarning):
        params = NasaExoplanetArchive.query_star("HD 209458")
    assert len(params) == 1
    assert str(params["pl_name"][0]) == "HD 209458 b"
    assert_quantity_allclose(params["pl_orbper"], 3.52474859 * u.day, atol=1e-5 * u.day)
    assert not params["pl_kepflag"]
    assert not params["pl_ttvflag"]

    # test_hd136352_stellar_exoplanet_archive
    with pytest.warns(AstropyDeprecationWarning):
        params = NasaExoplanetArchive.query_star("HD 136352")
    assert len(params) == 3
    expected_planets = ["HD 136352 b", "HD 136352 c", "HD 136352 d"]
    for planet in expected_planets:
        assert planet in params["pl_name"]
    assert "pl_trandep" not in params.colnames

    # test_exoplanet_archive_query_all_columns
    with pytest.warns(AstropyDeprecationWarning):
        params = NasaExoplanetArchive.query_planet("HD 209458 b ", all_columns=True)
    assert "pl_tranflag" in params.columns


def test_query_object_compat(patch_get):
    """Make sure that query_object is compatible with query_planet and query_star"""
    with pytest.warns(AstropyDeprecationWarning):
        table1 = NasaExoplanetArchive.query_planet("HD 209458 b ")
    table2 = NasaExoplanetArchive.query_object("HD 209458 b ")
    _compare_tables(table1, table2)

    with pytest.warns(AstropyDeprecationWarning):
        table1 = NasaExoplanetArchive.query_star(" Kepler 2")
    table2 = NasaExoplanetArchive.query_object("HAT-P-7 ")
    _compare_tables(table1, table2)


@pytest.mark.filterwarnings("error")
@pytest.mark.parametrize("table,query", ALL_TABLES)
def test_all_tables(patch_get, table, query):
    data = NasaExoplanetArchive.query_criteria(table, select="*", **query)
    assert len(data) > 0

    # Check that the units were fixed properly
    for col in data.columns:
        assert isinstance(data[col], SkyCoord) or not isinstance(data[col].unit, u.UnrecognizedUnit)


def test_select(patch_get):
    payload = NasaExoplanetArchive.query_criteria(
        "exoplanets",
        select=["pl_hostname", "pl_name"],
        where="pl_hostname='Kepler-11'",
        get_query_payload=True,
    )
    assert payload["select"] == "pl_hostname,pl_name"

    table1 = NasaExoplanetArchive.query_criteria(
        "exoplanets", select=["pl_hostname", "pl_name"], where="pl_hostname='Kepler-11'"
    )
    table2 = NasaExoplanetArchive.query_criteria(
        "exoplanets", select="pl_hostname,pl_name", where="pl_hostname='Kepler-11'"
    )
    _compare_tables(table1, table2)


def test_warnings(patch_get):
    with pytest.warns(NoResultsWarning):
        NasaExoplanetArchive.query_criteria("exoplanets", where="pl_hostname='not a host'")

    with pytest.warns(InputWarning):
        NasaExoplanetArchive.query_object("HAT-P-11 b", where="nothing")

    with pytest.warns(AstropyDeprecationWarning) as warning:
        NasaExoplanetArchive.query_planet(
            "HAT-P-11 b", all_columns=False, show_progress=True, table_path="nothing"
        )
    assert len(warning) == 3

    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_object("HAT-P-11 b", table="cumulative")
    assert "Invalid table 'cumulative'" in str(error)


def test_query_region(patch_get):
    coords = SkyCoord(ra=330.79488 * u.deg, dec=18.8843 * u.deg)
    radius = 0.001
    table1 = NasaExoplanetArchive.query_region("exoplanets", coords, radius * u.deg)
    assert len(table1) == 1
    assert table1["pl_hostname"] == "HD 209458"

    table2 = NasaExoplanetArchive.query_region("exoplanets", coords, radius)
    _compare_tables(table1, table2)


def test_format(patch_get):
    table1 = NasaExoplanetArchive.query_object("HAT-P-11 b")
    table2 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="votable")
    _compare_tables(table1, table2)

    table1 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="csv")
    table2 = NasaExoplanetArchive.query_object("HAT-P-11 b", format="bar")
    _compare_tables(table1, table2)


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
