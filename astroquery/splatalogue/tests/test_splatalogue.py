# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest
import requests

from astropy import units as u

from ... import splatalogue
from ...utils.testing_tools import MockResponse

SPLAT_DATA = 'CO_colons.csv'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data=None, timeout=10, files=None,
                    params=None, headers=None, **kwargs):
    if method != 'POST':
        raise ValueError("A 'post request' was made with method != POST")
    filename = data_path(SPLAT_DATA)
    content = open(filename, "rb").read()
    return MockResponse(content, **kwargs)


def test_simple(patch_post):
    splatalogue.Splatalogue.query_lines(114 * u.GHz, 116 * u.GHz,
                                        chemical_name=' CO ')


@pytest.mark.remote_data
def test_init(patch_post):
    x = splatalogue.Splatalogue.query_lines(114 * u.GHz, 116 * u.GHz,
                                            chemical_name=' CO ')
    S = splatalogue.Splatalogue(chemical_name=' CO ')
    y = S.query_lines(114 * u.GHz, 116 * u.GHz)
    # it is not currently possible to test equality between tables:
    # masked arrays fail
    # assert y == x
    assert len(x) == len(y)
    assert all(y['Species'] == x['Species'])
    assert all(x['Chemical Name'] == y['Chemical Name'])


def test_load_species_table():
    tbl = splatalogue.load_species_table.species_lookuptable()
    CO = tbl.find(' CO ')
    assert len(CO) == 4


# regression test: ConfigItems were in wrong order at one point
def test_url():
    assert 'https://' in splatalogue.core.Splatalogue.QUERY_URL
    assert 'cv.nrao.edu' in splatalogue.core.Splatalogue.QUERY_URL


# regression test: get_query_payload should work (#308)
def test_get_payload():
    q = splatalogue.core.Splatalogue.query_lines_async(1 * u.GHz, 10 * u.GHz,
                                                       get_query_payload=True)
    assert '__utma' in q


# regression test: line lists should ask for only one line list, not all
def test_line_lists():
    q = splatalogue.core.Splatalogue.query_lines_async(1 * u.GHz, 10 * u.GHz,
                                                       line_lists=['JPL'],
                                                       get_query_payload=True)
    assert q['displayJPL'] == 'displayJPL'
    assert q['displaySLAIM'] == ''


# regression test: raise an exception if a string is passed to line_lists
# uses get_query_payload to avoid having to monkeypatch
def test_linelist_type():
    with pytest.raises(TypeError) as exc:
        splatalogue.core.Splatalogue.query_lines_async(1 * u.GHz, 10 * u.GHz,
                                                       line_lists='JPL',
                                                       get_query_payload=True)
    assert exc.value.args[0] == ("Line lists should be a list of linelist "
                                 "names.  See Splatalogue.ALL_LINE_LISTS")


def test_top20_crashorno():
    splatalogue.core.Splatalogue.query_lines_async(114 * u.GHz, 116 * u.GHz,
                                                   top20='top20',
                                                   get_query_payload=True)
    with pytest.raises(ValueError) as exc:
        splatalogue.core.Splatalogue.query_lines_async(
            114 * u.GHz, 116 * u.GHz, top20='invalid', get_query_payload=True)
    assert exc.value.args[0] == "Top20 is not one of the allowed values"


def test_band_crashorno():
    splatalogue.core.Splatalogue.query_lines_async(band='alma3',
                                                   get_query_payload=True)
    with pytest.raises(ValueError) as exc:
        splatalogue.core.Splatalogue.query_lines_async(band='invalid',
                                                       get_query_payload=True)
    assert exc.value.args[0] == "Invalid frequency band."


# Upstream changed: there is no distinction between versions for this molecule
# # regression test : version selection should work
# # Unfortunately, it looks like version1 = version2 on the web page now, so this
# # may no longer be a valid test
# @pytest.mark.remote_data
# def test_version_selection():
#     results = splatalogue.Splatalogue.query_lines(
# 			    min_frequency= 703*u.GHz,
# 			    max_frequency=706*u.GHz,
# 			    chemical_name='Acetaldehyde',
# 			    version='v1.0'
# 			    )
#     assert len(results)==1

def test_exclude(patch_post):
    # regression test for issue 616
    d = splatalogue.Splatalogue.query_lines_async(114 * u.GHz, 116 * u.GHz,
                                                  chemical_name=' CO ',
                                                  exclude=None,
                                                  get_query_payload=True)

    exclusions = {'no_atmospheric': 'no_atmospheric',
                  'no_potential': 'no_potential',
                  'no_probable': 'no_probable', }

    for k, v in exclusions.items():
        assert d[k] == v

    d = splatalogue.Splatalogue.query_lines_async(114 * u.GHz, 116 * u.GHz,
                                                  chemical_name=' CO ',
                                                  exclude='none',
                                                  get_query_payload=True)

    for k, v in exclusions.items():
        assert k not in d

    for k in d:
        assert k[:3] != 'no_'


@pytest.mark.remote_data
def test_exclude_remote():
    # regression test for issue 616
    # only entry should be  "D213CO  Formaldehyde 351.96064  3.9e-06   ...."
    results = splatalogue.Splatalogue.query_lines(
        min_frequency=351.9*u.GHz,
        max_frequency=352.*u.GHz,
        chemical_name='Formaldehyde',
        exclude='none')
    assert len(results) >= 1
