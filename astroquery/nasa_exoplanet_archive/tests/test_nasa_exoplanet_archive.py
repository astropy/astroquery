# Licensed under a 3-clause BSD style license - see LICENSE.rst


import json
import os
import sys
from urllib.parse import urlencode

import astropy.units as u
from astropy.io.ascii import write as ap_write
import numpy as np
import pkg_resources
import pytest
import requests
from astropy.coordinates import SkyCoord
from astropy.tests.helper import assert_quantity_allclose
from astropy.utils.exceptions import AstropyDeprecationWarning

from ...exceptions import InputWarning, InvalidQueryError, NoResultsWarning
from ...utils.testing_tools import MockResponse
from ..core import NasaExoplanetArchive, conf, InvalidTableError, request_to_sql

MAIN_DATA = pkg_resources.resource_filename("astroquery.nasa_exoplanet_archive", "data")
TEST_DATA = pkg_resources.resource_filename(__name__, "data")
RESPONSE_FILE = os.path.join(TEST_DATA, "responses.json")
os.environ["NASA_EXOPLANET_ARCHIVE_GENERATE_RESPONSES"] = '1' # Activate for generating responses 

# TAP supported: ps, pscomppars, keplernames, k2names. API support: all others
# TODO: add tables transitspec and emissionspec
# TODO: these tests might have to be split between TAP and API accessed tables
ALL_TABLES = [
    # ("ps", dict(where="hostname='Kepler-11'")),
    # ("pscomppars", dict(where="hostname='WASP-166'")),
    # ("ml", dict(where="pl_name='MOA-2010-BLG-353L b'")), # new microlensing table not ready for the wild yet
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
    # ("keplernames", dict(where="kepid=10601284")),
    ("kelttimeseries", dict(where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02")),
    ("kelt", dict(where="kelt_sourceid='KELT_N02_lc_012738_V01_east'", kelt_field="N02")),
    ("superwasptimeseries", dict(sourceid="1SWASP J191645.46+474912.3")),
    ("k2targets", dict(where="epic_number=206027655")),
    ("k2candidates", dict(where="epic_name='EPIC 206027655'")),
    # ("k2names", dict(where="epic_host='EPIC 206027655'")),
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

    # Read request parameters
    params = kwargs.get("params", None)
    assert params is not None

    try:
        # Read request (URL substring for API or SQL query for TAP) from json file as dict
        with open(RESPONSE_FILE, "r") as f:
            responses = json.load(f)
    except FileNotFoundError:
        responses = {}


    table = params["table"]
    # Set base URL depending on whether TAP or API for access
    if table in ["ps", "pscomppars", "k2names", "keplernames"]:
        assert url == conf.url_tap
        service_type = "tap"
    else:
        assert url == conf.url_api
        service_type = "api"

    # Work out where the expected response is saved  
    if service_type == "api":
        key = urlencode(sorted(params.items())) # construct URL query string from params
    else:
        key = request_to_sql(sorted(params.items())) # construct SQL query string from params
    try:
        # Find index of query string in list of queries for specific table.
        # Set to empty list if table isn't in dictionary, which will return ValueError
        index = responses.get(table, []).index(key)
    except ValueError:
        index = -1


    # If the NASA_EXOPLANET_ARCHIVE_GENERATE_RESPONSES environment variable is set, we make a
    # remote request if necessary. Otherwise we throw a ValueError.
    if index < 0: # Request wasn't already in responses.json
        if "NASA_EXOPLANET_ARCHIVE_GENERATE_RESPONSES" not in os.environ:
            raise ValueError("unexpected request")
        responses[table] = responses.get(table, [])
        responses[table].append(key) # add query string to dict of table entries
        index = len(responses[table]) - 1 # set index to write new entry
        if table in ["ps", "pscomppars", "k2names", "keplernames"]:
            tap = pyvo.dal.tap.TAPService(baseurl=url)
            resp = tap.run_async(query=key, language="ADQL")
            ap_write(resp.to_table(), output=os.path.join(TEST_DATA, "{0}_expect_{1}.txt".format(table, index)))
        else: # use basic http request of URL
            with requests.Session() as session:
                resp = session.old_request(method, url, params=params)
        with open(os.path.join(TEST_DATA, "{0}_expect_{1}.txt".format(table, index)), "w") as f:
            f.write(resp.text) # writing response text (actual response from server) to data files
        with open(RESPONSE_FILE, "w") as f:
            json.dump(responses, f, sort_keys=True, indent=2) # write updated dict to responses.json

    with open(os.path.join(TEST_DATA, "{0}_expect_{1}.txt".format(table, index)), "r") as f:
        data = f.read() # Read saved response from data file

    return MockResponse(data.encode("utf-8")) # Return as MockResponse


@pytest.fixture
def patch_get(request):  # pragma: nocover
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:
        mp = request.getfuncargvalue("monkeypatch")

    # Keep track of the original function so that we can use it to generate the expected responses
    # TODO: Need to add similar for TAP here ...
    requests.Session.old_request = requests.Session.request
    mp.setattr(requests.Session, "request", mock_get)
    return mp


def test_regularize_object_name(patch_get):
    # aliastable temporarily inacessible, so no regularization possible
    assert NasaExoplanetArchive._regularize_object_name("kepler 2") == "HAT-P-7"
    assert NasaExoplanetArchive._regularize_object_name("kepler 1 b") == "TrES-2 b"

    with pytest.warns(NoResultsWarning) as warning:
        NasaExoplanetArchive._regularize_object_name("not a planet") # 
    assert "No aliases found for name: 'not a planet'" == str(warning[0].message)


def test_backwards_compat(patch_get):
    """
    These are the tests from the previous version of this interface.
    They query old tables by default and should return InvalidTableError.
    """

    # test_hd209458b_exoplanets_archive
    with pytest.warns(AstropyDeprecationWarning):
        with pytest.raises(InvalidTableError) as error:
            params = NasaExoplanetArchive.query_planet("HD 209458 b ")
        assert "replaced" in str(error)


    # test_hd209458b_exoplanet_archive_coords
    with pytest.warns(AstropyDeprecationWarning):
        with pytest.raises(InvalidTableError) as error:
            params = NasaExoplanetArchive.query_planet("HD 209458 b ")
        assert "replaced" in str(error)


    # test_hd209458_stellar_exoplanet
    with pytest.warns(AstropyDeprecationWarning):
        with pytest.raises(InvalidTableError) as error:
            params = NasaExoplanetArchive.query_star("HD 209458")
        assert "replaced" in str(error)


    # test_hd136352_stellar_exoplanet_archive
    with pytest.warns(AstropyDeprecationWarning):
        with pytest.raises(InvalidTableError) as error:
            params = NasaExoplanetArchive.query_star("HD 136352")
        assert "replaced" in str(error)

    # test_exoplanet_archive_query_all_columns
    with pytest.warns(AstropyDeprecationWarning):
        with pytest.raises(InvalidTableError) as error:
            params = NasaExoplanetArchive.query_planet("HD 209458 b ", all_columns=True)
        assert "replaced" in str(error)


@pytest.mark.filterwarnings("error")
@pytest.mark.parametrize("table,query", ALL_TABLES)
def test_all_tables(patch_get, table, query):
    data = NasaExoplanetArchive.query_criteria(table, select="*", **query)
    assert len(data) > 0

    # Check that the units were fixed properly
    for col in data.columns:
        assert isinstance(data[col], SkyCoord) or not isinstance(data[col].unit, u.UnrecognizedUnit)


def test_select(): # removed patch_get for now
    payload = NasaExoplanetArchive.query_criteria(
        "ps",
        select=["hostname", "pl_name"],
        where="hostname='Kepler-11'",
        get_query_payload=True,
    )
    assert payload["select"] == "hostname,pl_name"

    table1 = NasaExoplanetArchive.query_criteria(
        "ps", select=["hostname", "pl_name"], where="hostname='Kepler-11'"
    )
    table2 = NasaExoplanetArchive.query_criteria(
        "ps", select="hostname,pl_name", where="hostname='Kepler-11'"
    )
    _compare_tables(table1, table2)


def test_warnings(): # removed patch_get for now
    with pytest.warns(NoResultsWarning):
        NasaExoplanetArchive.query_criteria("ps", where="hostname='not a host'")

    with pytest.warns(InputWarning):
        NasaExoplanetArchive.query_object("HAT-P-11 b", where="nothing")

    with pytest.raises(InvalidQueryError) as error:
        NasaExoplanetArchive.query_object("HAT-P-11 b", table="cumulative")
    assert "Invalid table 'cumulative'" in str(error)


def test_query_region(): # removed patch_get for now
    coords = SkyCoord(ra=330.79488 * u.deg, dec=18.8843 * u.deg)
    radius = 0.001
    table1 = NasaExoplanetArchive.query_region("pscomppars", coords, radius * u.deg)
    assert len(table1) == 1
    assert table1["hostname"] == "HD 209458"

    table2 = NasaExoplanetArchive.query_region("pscomppars", coords, radius)
    _compare_tables(table1, table2)


def test_format(): # removed patch_get for now
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
