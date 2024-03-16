# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest
import json

from astropy import units as u

from ... import splatalogue


SPLAT_DATA = 'CO.json'


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_simple(patch_post):
    splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                        max_frequency=116 * u.GHz,
                                        chemical_name=' CO ')


@pytest.mark.remote_data
def test_init(patch_post):
    x = splatalogue.Splatalogue.query_lines(min_frequency=114 * u.GHz,
                                            max_frequency=116 * u.GHz,
                                            chemical_name=' CO ')
    S = splatalogue.Splatalogue(chemical_name=' CO ')
    y = S.query_lines(min_frequency=114 * u.GHz, max_frequency=116 * u.GHz)
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


# regression test: get_query_payload should work (#308)
def test_get_payload():
    q = splatalogue.core.Splatalogue.query_lines_async(min_frequency=1 * u.GHz,
                                                       max_frequency=10 * u.GHz,
                                                       get_query_payload=True)
    assert q['body']["userInputFrequenciesFrom"] == [1.0]
    assert q['body']["userInputFrequenciesTo"] == [10.0]


# regression test: line lists should ask for only one line list, not all
def test_line_lists():
    q = splatalogue.core.Splatalogue.query_lines_async(min_frequency=1 * u.GHz,
                                                       max_frequency=10 * u.GHz,
                                                       line_lists=['JPL'],
                                                       get_query_payload=True)
    assert q['body']['lineListDisplayCDMSJPL']
    assert not q['body']['lineListDisplaySLAIM']


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
