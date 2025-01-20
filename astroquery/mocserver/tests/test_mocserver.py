# Licensed under a 3-clause BSD style license - see LICENSE.rst
import json
from pathlib import Path

import pytest
import requests

from astropy import coordinates
from astropy.io.votable import parse_single_table
from astropy.table import Table
from astropy.utils.exceptions import AstropyDeprecationWarning

try:
    from mocpy import MOC, STMOC, TimeMOC, FrequencyMOC
    HAS_MOCPY = True
except ImportError:
    HAS_MOCPY = False
try:
    from regions import CircleSkyRegion, PolygonSkyRegion  # noqa: E402
    HAS_REGIONS = True
except ImportError:
    HAS_REGIONS = False

from ... import mocserver
from ..core import MOCServer, _parse_result, _cast_to_float


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
def test_polygon_spatial_request():
    polygon_region = PolygonSkyRegion(
        coordinates.SkyCoord(
            [57.376, 56.391, 56.025, 56.616],
            [24.053, 24.622, 24.049, 24.291],
            frame="icrs",
            unit="deg",
        )
    )
    request_payload = MOCServer.query_region(
        region=polygon_region, intersect="overlaps", get_query_payload=True
    )
    print(request_payload)
    assert request_payload["stc"] == (
        "Polygon 57.376 24.053 56.391 24.622 56.025 24.049 56.616 24.291"
    )


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
def test_cone_search_spatial_request():
    ra = 10.8
    dec = 6.5
    radius = 0.5
    center = coordinates.SkyCoord(ra, dec, unit="deg")
    cone_region = CircleSkyRegion(
        center=center, radius=coordinates.Angle(radius, unit="deg")
    )
    request_payload = MOCServer.query_region(
        region=cone_region, get_query_payload=True, intersect="overlaps"
    )
    assert request_payload["DEC"] == str(dec)
    assert request_payload["RA"] == str(ra)
    assert request_payload["SR"] == str(radius)


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
def test_regions_provided_as_mocs(monkeypatch):
    # FrequencyMOCs are not supported yet, they should raise an error, along with
    # any other unsupported type
    with pytest.raises(ValueError, match="'region' should be of type: *"):
        MOCServer.query_region(region=FrequencyMOC.from_str("5/0"),
                               get_query_payload=True)
    # patching _request

    def mockreturn(**kwargs):
        return kwargs

    monkeypatch.setattr(MOCServer, "_request", mockreturn)
    # looping on accepted MOC flavors
    for moc in [
        MOC.from_str("0/0-11"),
        TimeMOC.from_str("0/0-1"),
        STMOC.from_str("t0/0-1 s0/0-11"),
    ]:
        tempfile_moc = MOCServer.query_async(region=moc)["files"]["moc"]
        assert tempfile_moc.startswith(b"SIMPLE  =                    T")


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
def test_query_hips():
    # no meta
    payload = MOCServer.query_hips(get_query_payload=True)
    assert payload["expr"] == "hips_frame=*"
    # with meta
    payload = MOCServer.query_hips(criteria="TEST", get_query_payload=True)
    assert payload["expr"] == "(TEST)&&hips_frame=*"


# -----------
# List fields
# -----------


@pytest.fixture
def _mock_list_fields(monkeypatch):
    """Avoid a request to get the list of fields in the mocserver."""

    # This response changes with time. To regenerate it, do:
    # >>> from astroquery.mocserver import MOCServer
    # >>> import json
    # >>> response = MOCServer._request(method="GET", url=self.URL,
    # ...                               timeout=self.TIMEOUT, cache=cache,
    # ...                               params={"get": "example", "fmt": "json"}).json()[0]
    # >>> with open("list_fields.json", "w") as f:
    # ...     json.dump(dict(response.json()[0]))
    class MockedListFields:
        def json(self):
            with open(Path(__file__).parent / "data" / "list_fields.json", "r") as f:
                return [json.load(f)]

    monkeypatch.setattr(requests.Session, 'send',
                        lambda *args, **kwargs: MockedListFields())


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
@pytest.mark.usefixtures("_mock_list_fields")
def test_list_fields():
    fields = MOCServer.list_fields("id", cache=False)
    assert "ID" in fields["field_name"]


# -----------------------
# List coordinate systems
# -----------------------


@pytest.fixture
def _mock_list_coordinate_systems(monkeypatch):
    # This list changes upstream. To regenerate it, do:
    # >>> from astroquery.mocserver import MOCServer
    # >>> hips_frames = MOCServer.query_region(criteria="hips_frame=*",
    # ...                                       fields=["hips_frame"],
    # ...                                       coordinate_system=None, max_rec=100)
    # >>> hips_frames.remove_column("ID")
    # >>> hips_frames.write("hips_frames.vot", format="votable", overwrite=True)
    with open(Path(__file__).parent / "data" / "hips_frames.vot", "rb") as f:
        table = parse_single_table(f).to_table()
    monkeypatch.setattr(
        mocserver.MOCServerClass, "query_region", lambda self, **kwargs: table
    )


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
@pytest.mark.usefixtures("_mock_list_coordinate_systems")
def test_list_coordinate_systems():
    list_coordinate_system = MOCServer.list_coordinate_systems()
    assert "sky" in list_coordinate_system and "equatorial" in list_coordinate_system


# ---------------------
# Special case keywords
# ---------------------


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
@pytest.mark.skipif(not HAS_REGIONS, reason="regions is required")
@pytest.mark.parametrize("intersect", ["encloses", "overlaps", "covers"])
def test_intersect_param(intersect):
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")
    cone_region = CircleSkyRegion(center, radius)
    request_payload = MOCServer.query_region(
        region=cone_region, intersect=intersect, get_query_payload=True
    )
    if intersect == "encloses":
        assert request_payload["intersect"] == "enclosed"
    else:
        assert request_payload["intersect"] == intersect


def test_fields():
    # check that it works for a single field
    payload = MOCServer.query_region(criteria="", fields="ID", get_query_payload=True)
    assert payload["fields"] == "ID"
    # as well as more fields
    payload = MOCServer.query_region(
        criteria="", fields=["ID", "hips_properties"], get_query_payload=True
    )
    # cannot test the order, due to the use of set
    assert "hips_properties" in payload["fields"] and "ID" in payload["fields"]
    # ID has to be in fields
    payload = MOCServer.query_region(
        criteria="", fields="hips_body", get_query_payload=True
    )
    assert "ID" in payload["fields"]


def test_caseinsensitive():
    # casesensitive was hardcoded to true until astroquery 0.4.8. It is now an option
    payload = MOCServer.query_region(criteria="", fields="ID", get_query_payload=True)
    assert payload["casesensitive"] == "false"
    payload = MOCServer.query_region(
        criteria="", fields="ID", get_query_payload=True, casesensitive=True
    )
    assert payload["casesensitive"] == "true"


def test_maxrec():
    payload = MOCServer.query_region(criteria="", max_rec=100, get_query_payload=True)
    assert payload["MAXREC"] == "100"


def test_return_moc():
    # legacy compatibility, return_moc=True means a space-MOC
    payload = MOCServer.query_region(
        criteria="", return_moc=True, max_norder=5, get_query_payload=True
    )
    assert payload["get"] == "moc"
    assert payload["fmt"] == "ascii"
    assert payload["order"] == 5
    # no max_norder means maximum order available
    payload = MOCServer.query_region(
        criteria="", return_moc=True, get_query_payload=True
    )
    assert payload["order"] == "max"


def test_coordinate_system():
    payload = MOCServer.query_region(
        coordinate_system="sky", criteria="", return_moc=True,
        max_norder=5, get_query_payload=True
    )
    assert payload["spacesys"] == "C"


# ----------------
# Helper functions
# ----------------


@pytest.mark.skipif(not HAS_MOCPY, reason="mocpy is required")
def test_parse_result():
    class MockResult:
        def __init__(self, text):
            self.text = text

        def json(self):
            return self.text

    # all MOC types
    assert isinstance(_parse_result(MockResult("0/0-11"), return_moc="moc"), MOC)
    assert isinstance(_parse_result(MockResult("0/0-1"), return_moc="tmoc"), TimeMOC)
    assert isinstance(_parse_result(MockResult("t3/ s5/"), return_moc="stmoc"), STMOC)
    # fmoc not yet accepted
    with pytest.raises(ValueError, match="'return_moc' can only take the values*"):
        _parse_result(MockResult("test"), return_moc="fmoc")
    # non-MOC response
    assert isinstance(
        _parse_result(MockResult([{"a": 0, "b": 1}]), return_moc=None), Table
    )


def test_cast_to_float():
    assert _cast_to_float("3") == 3
    assert _cast_to_float("test") == "test"

# ------------
# Deprecations
# ------------


def test_find_datasets():
    # find datasets is useless as it does the same than query region
    # and 'meta_data' is replaced byt the new argument 'criteria' in query_region
    with pytest.warns(AstropyDeprecationWarning, match="'find_datasets' is replaced "
                                                       "by 'query_region' *"):
        old = MOCServer.find_datasets(meta_data="ID=*Euclid*", get_query_payload=True)
    assert old == MOCServer.query_region(criteria="ID=*Euclid*", get_query_payload=True)
