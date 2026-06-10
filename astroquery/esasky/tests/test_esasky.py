# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyDeprecationWarning

from astroquery.esasky import ESASky

# Fake mission descriptors so that no network access is needed to build the query payload.
FAKE_DESCRIPTORS = {"XMM": {"mission": "XMM",
                            "table_name": "observations.mv_v_esasky_xmm_om_optical_fdw",
                            "ra": "ra_deg", "dec": "dec_deg",
                            "intersect_polygon_query": True}}


@pytest.mark.parametrize("method_name, descriptor_getter",
                         [("query_region_maps", "_get_observation_info"),
                          ("query_region_catalogs", "_get_catalogs_info"),
                          ("query_region_spectra", "_get_spectra_info")])
def test_query_region_deprecated_position(monkeypatch, method_name, descriptor_getter):
    # The 'position' keyword was renamed to 'coordinates'; the old keyword
    # should still work but emit an AstropyDeprecationWarning.
    monkeypatch.setattr(ESASky, descriptor_getter, lambda: FAKE_DESCRIPTORS)
    coordinates = SkyCoord(ra=202.469, dec=47.195, unit="deg")
    method = getattr(ESASky, method_name)
    kwargs = {("catalogs" if method_name == "query_region_catalogs" else "missions"): ["XMM"]}

    expected = method(coordinates=coordinates, radius="5 arcmin",
                      get_query_payload=True, **kwargs)

    with pytest.warns(AstropyDeprecationWarning):
        result = method(position=coordinates, radius="5 arcmin",
                        get_query_payload=True, **kwargs)

    assert result == expected
    assert "QUERY" in result["XMM"]
