# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest
import json

from astropy import units as u

from astroquery.utils.mocks import MockResponse
from astroquery import splatalogue


SPLAT_DATA = 'CO.json'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_simple(patch_post):
    splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                        max_frequency=116 * u.GHz,
                                        chemical_name=' CO ')


def mockreturn(*args, method='POST', data={}, url='', **kwargs):
    with open(data_path("CO.json"), 'rb') as fh:
        jdata = fh.read()
    return MockResponse(content=jdata)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(splatalogue.Splatalogue, '_request', mockreturn)
    return mp


@pytest.mark.remote_data
def test_init_remote():
    x = splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                            max_frequency=116 * u.GHz,
                                            chemical_name=' CO ')
    S = splatalogue.Splatalogue(chemical_name=' CO ')
    y = S.query_lines(min_frequency=114 * u.GHz, max_frequency=116 * u.GHz)
    # it is not currently possible to test equality between tables:
    # masked arrays fail
    # assert y == x
    assert len(x) == len(y)
    assert all(y['species_id'] == x['species_id'])
    assert all(y['name'] == x['name'])
    assert all(y['chemical_name'] == x['chemical_name'])


def test_init():
    splat = splatalogue.Splatalogue(chemical_name=' CO ')
    assert splat.data['speciesSelectBox'] == ['204', '990', '991', '1343']
    payload = splat.query_lines(min_frequency=114 * u.GHz, max_frequency=116 * u.GHz,
                                get_query_payload=True)
    payload = json.loads(payload['body'])
    assert payload['speciesSelectBox'] == ['204', '990', '991', '1343']
    assert payload['userInputFrequenciesFrom'] == [114.0]
    assert payload['userInputFrequenciesTo'] == [116.0]


def test_load_species_table():
    tbl = splatalogue.load_species_table.species_lookuptable()
    CO = tbl.find(' CO ')
    assert len(CO) == 4


# regression test: get_query_payload should work (#308)
def test_get_payload():
    payload = splatalogue.core.Splatalogue.query_lines_async(min_frequency=1 * u.GHz,
                                                             max_frequency=10 * u.GHz,
                                                             get_query_payload=True)
    payload = json.loads(payload['body'])
    assert payload["userInputFrequenciesFrom"] == [1.0]
    assert payload["userInputFrequenciesTo"] == [10.0]


# regression test: line lists should ask for only one line list, not all
def test_line_lists():
    payload = splatalogue.core.Splatalogue.query_lines_async(min_frequency=1 * u.GHz,
                                                             max_frequency=10 * u.GHz,
                                                             line_lists=['JPL'],
                                                             get_query_payload=True)
    payload = json.loads(payload['body'])
    assert payload['lineListDisplayJPL']
    assert not payload['lineListDisplaySLAIM']
    assert not payload['lineListDisplayCDMS']


# regression test: raise an exception if a string is passed to line_lists
# uses get_query_payload to avoid having to monkeypatch
def test_linelist_type():
    with pytest.raises(TypeError) as exc:
        splatalogue.core.Splatalogue.query_lines_async(min_frequency=1 * u.GHz,
                                                       max_frequency=10 * u.GHz,
                                                       line_lists='JPL',
                                                       get_query_payload=True)
    assert exc.value.args[0] == ("Line lists should be a list of linelist "
                                 "names.  See Splatalogue.ALL_LINE_LISTS")


def test_exclude(patch_post):
    # regression test for issue 616
    payload = splatalogue.Splatalogue.query_lines_async(min_frequency=114 * u.GHz,
                                                        max_frequency=116 * u.GHz,
                                                        chemical_name=' CO ',
                                                        exclude=None,
                                                        get_query_payload=True)

    payload = json.loads(payload['body'])
    exclusions = {'excludePotentialInterstellarSpecies': False,
                  'excludeAtmosSpecies': False,
                  'excludeProbableInterstellarSpecies': False,
                  'excludeKnownASTSpecies': False}

    for k, v in exclusions.items():
        assert payload[k] == v

    # 'none' doesn't mean None, but it should have the same effect
    payload = splatalogue.Splatalogue.query_lines_async(min_frequency=114 * u.GHz,
                                                        max_frequency=116 * u.GHz,
                                                        chemical_name=' CO ',
                                                        exclude='none',
                                                        get_query_payload=True)
    payload = json.loads(payload['body'])

    for key in exclusions:
        assert not payload[key]


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
