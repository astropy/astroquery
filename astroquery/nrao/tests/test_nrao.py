# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os

import pytest
from unittest.mock import patch, Mock

from astropy import units as u
from astropy import coordinates as coord
from astropy.table import Table
from astropy.coordinates import SkyCoord

from astroquery.nrao import Nrao
from astroquery.nrao.core import _gen_sql


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


# NRAO TAP table is tap_schema.obscore (not ivoa.obscore as on the ALMA TAP).
# Position queries use CONTAINS(POINT, CIRCLE) because the NRAO TAP server
# stores s_region as text rather than as a geometry type, so INTERSECTS(...,
# s_region) raises "operator does not exist: scircle && text".  Range
# (RANGE_S2D) queries are not supported by the server either.
COMMON_SELECT = 'select * from tap_schema.obscore'
COMMON_SELECT_WHERE = COMMON_SELECT + ' WHERE '


def test_gen_pos_sql():
    # circle, radius defaults to 10 arcmin
    assert _gen_sql({'ra_dec': '1 2'}) == COMMON_SELECT_WHERE + \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,2.0,0.16666666666666666))=1"
    assert _gen_sql({'ra_dec': '1 2, 3'}) == COMMON_SELECT_WHERE + \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,2.0,3.0))=1"
    assert _gen_sql({'ra_dec': '12:13:14.0 -00:01:02.1, 3'}) == \
        COMMON_SELECT_WHERE + \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',12.220555555555556,-0.01725,3.0))=1"

    # multiple circles via "|"
    assert _gen_sql({'ra_dec': '1 20|40, 3'}) == COMMON_SELECT_WHERE + \
        "(CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,20.0,3.0))=1 OR " \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,40.0,3.0))=1)"
    assert _gen_sql({'ra_dec': '1|10 20|40, 1'}) == COMMON_SELECT_WHERE + \
        "(CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,20.0,1.0))=1 OR " \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,40.0,1.0))=1 OR " \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',10.0,20.0,1.0))=1 OR " \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',10.0,40.0,1.0))=1)"

    # galactic frame, single circle
    center = coord.SkyCoord(1, 2, unit=u.deg, frame='galactic')
    assert _gen_sql({'galactic': '1 2, 3'}) == COMMON_SELECT_WHERE + \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{},{},3.0))=1".format(
            center.icrs.ra.to(u.deg).value, center.icrs.dec.to(u.deg).value)

    # combination of frames (ICRS and galactic) ANDed together
    assert _gen_sql({'ra_dec': '1 2, 3', 'galactic': '1 2, 3'}) == \
        COMMON_SELECT_WHERE + \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,2.0,3.0))=1 AND " \
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',{},{},3.0))=1".format(
            center.icrs.ra.to(u.deg).value, center.icrs.dec.to(u.deg).value)


def test_gen_numeric_sql():
    assert _gen_sql({'bandwidth': '23'}) == COMMON_SELECT_WHERE + \
        'aggregate_bandwidth=23.0'
    assert _gen_sql({'bandwidth': '22 .. 23'}) == COMMON_SELECT_WHERE + \
        '(22.0<=aggregate_bandwidth AND aggregate_bandwidth<=23.0)'
    assert _gen_sql({'bandwidth': '<100'}) == COMMON_SELECT_WHERE + \
        'aggregate_bandwidth<=100.0'
    assert _gen_sql({'bandwidth': '>100'}) == COMMON_SELECT_WHERE + \
        'aggregate_bandwidth>=100.0'
    assert _gen_sql({'bandwidth': '!(20 .. 30)'}) == COMMON_SELECT_WHERE + \
        '(aggregate_bandwidth<=20.0 OR aggregate_bandwidth>=30.0)'
    assert _gen_sql({'bandwidth': '<10 | >20'}) == COMMON_SELECT_WHERE + \
        '(aggregate_bandwidth<=10.0 OR aggregate_bandwidth>=20.0)'
    assert _gen_sql({'bandwidth': 100, 'freq_min': '>3'}) == \
        COMMON_SELECT_WHERE + "aggregate_bandwidth=100 AND freq_min>=3.0"


def test_gen_str_sql():
    assert _gen_sql({'project_code': '2012.* | 2013.?3*'}) == \
        COMMON_SELECT_WHERE + \
        "(project_code LIKE '2012.%' OR project_code LIKE '2013._3%')"
    # with brackets like the form example
    assert _gen_sql({'project_code': '(2012.* | 2013.?3*)'}) == \
        COMMON_SELECT_WHERE + \
        "(project_code LIKE '2012.%' OR project_code LIKE '2013._3%')"
    # exact match
    assert _gen_sql({'project_code': '12A-001'}) == COMMON_SELECT_WHERE + \
        "project_code='12A-001'"


def test_gen_datetime_sql():
    assert _gen_sql({'start_date': '01-01-2020'}) == COMMON_SELECT_WHERE + \
        "t_min=58849.0"
    assert _gen_sql({'start_date': '>01-01-2020'}) == COMMON_SELECT_WHERE + \
        "t_min>=58849.0"
    assert _gen_sql({'start_date': '<01-01-2020'}) == COMMON_SELECT_WHERE + \
        "t_min<=58849.0"
    assert _gen_sql({'start_date': '(01-01-2020 .. 01-02-2020)'}) == \
        COMMON_SELECT_WHERE + "(58849.0<=t_min AND t_min<=58880.0)"


def test_gen_public_sql():
    # _gen_pub_sql emits NRAO's PUBLIC/LOCKED literals against proprietary_status
    assert _gen_sql({'public_data': None}) == COMMON_SELECT
    assert _gen_sql({'public_data': True}) == COMMON_SELECT + \
        " WHERE proprietary_status='PUBLIC'"
    assert _gen_sql({'public_data': False}) == COMMON_SELECT + \
        " WHERE proprietary_status='LOCKED'"


def test_pol_sql():
    # NRAO splits Single/Dual/Full into circular and linear variants and
    # emits the per-feed receiver labels (RR, XX, ...).
    assert _gen_sql({'polarization_type': 'Stokes I'}) == COMMON_SELECT + \
        " WHERE pol_states LIKE '%I%'"
    assert _gen_sql({'polarization_type': 'Single-circular'}) == \
        COMMON_SELECT + " WHERE pol_states='RR'"
    assert _gen_sql({'polarization_type': 'Dual-circular'}) == \
        COMMON_SELECT + " WHERE pol_states='RR, LL'"
    assert _gen_sql({'polarization_type': 'Full-circular'}) == \
        COMMON_SELECT + " WHERE pol_states='RR, RL, LR, LL'"
    assert _gen_sql({'polarization_type': 'Single-linear'}) == \
        COMMON_SELECT + " WHERE pol_states='XX'"
    assert _gen_sql({'polarization_type': 'Dual-linear'}) == \
        COMMON_SELECT + " WHERE pol_states='XX, YY'"
    assert _gen_sql({'polarization_type': 'Full-linear'}) == \
        COMMON_SELECT + " WHERE pol_states='XX, XY, YX, YY'"
    assert _gen_sql({'polarization_type': ['Single-linear', 'Dual-linear']}) \
        == COMMON_SELECT + " WHERE (pol_states='XX' OR pol_states='XX, YY')"


def test_gen_band_sql():
    # band names map to (freq_min, freq_max) ranges in Hz
    assert _gen_sql({'band_list': ['L']}) == COMMON_SELECT_WHERE + \
        '((freq_min >= 950000000.0 AND freq_max <= 2000000000.0))'
    assert _gen_sql({'band_list': ['3']}) == COMMON_SELECT_WHERE + \
        '((freq_min >= 84000000000.0 AND freq_max <= 116000000000.0))'


def test_query():
    # query_region: mocked TAP returns the empty-result fixture and we verify
    # the ADQL that was sent.
    tap_mock = Mock()
    empty_result = Table.read(os.path.join(DATA_DIR, 'nrao-empty.txt'),
                              format='ascii')
    mock_result = Mock()
    mock_result.to_table.return_value = empty_result
    tap_mock.search.return_value = mock_result
    nrao = Nrao()
    nrao._get_dataarchive_url = Mock()
    nrao._tap = tap_mock
    result = nrao.query_region(SkyCoord(1*u.deg, 2*u.deg, frame='icrs'),
                               radius=0.001*u.deg)
    assert len(result) == 0
    # NRAO's TAP column for project identifier is 'project_code'
    assert 'project_code' in result.columns
    tap_mock.search.assert_called_once_with(
        "select * from tap_schema.obscore WHERE "
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,2.0,0.001))=1",
        language='ADQL', maxrec=None)

    # query_object: SkyCoord.from_name is mocked to (1, 2) so the resolved
    # coordinates appear in the SQL.  query_object uses the default 10-arcmin
    # radius from _gen_pos_sql.
    tap_mock = Mock()
    mock_result = Mock()
    mock_result.to_table.return_value = empty_result
    tap_mock.search.return_value = mock_result
    nrao = Nrao()
    nrao._tap = tap_mock
    with patch('astroquery.nrao.tapsql.coord.SkyCoord.from_name') as name_mock:
        name_mock.return_value = SkyCoord(1, 2, unit='deg')
        result = nrao.query_object('M83')
    assert len(result) == 0

    tap_mock.search.assert_called_once_with(
        "select * from tap_schema.obscore WHERE "
        "CONTAINS(POINT('ICRS',s_ra,s_dec),CIRCLE('ICRS',1.0,2.0,0.16666666666666666))=1",
        language='ADQL', maxrec=None)


def test_tap():
    tap_mock = Mock()
    empty_result = Table.read(os.path.join(DATA_DIR, 'nrao-empty.txt'),
                              format='ascii')
    tap_mock.search.return_value = Mock(table=empty_result)
    nrao = Nrao()
    nrao._get_dataarchive_url = Mock()
    nrao._tap = tap_mock
    result = nrao.query_tap('select * from tap_schema.obscore')
    assert len(result.table) == 0

    tap_mock.search.assert_called_once_with('select * from tap_schema.obscore',
                                            language='ADQL', maxrec=None)


def test_galactic_query():
    """
    Regression test for the galactic-to-icrs conversion in query_region.
    query_region(..., get_query_payload=True) returns the prepared payload
    dict (not the SQL string); the SQL form is exposed by query().
    """
    nrao = Nrao()
    nrao._get_dataarchive_url = Mock()
    result = nrao.query_region(SkyCoord(0*u.deg, 0*u.deg, frame='galactic'),
                               radius=1*u.deg, get_query_payload=True)

    assert isinstance(result, dict)
    assert 'ra_dec' in result
    # galactic (0, 0) -> icrs (266.405..., -28.9362...)
    assert '266.405' in result['ra_dec']
    assert '-28.9362' in result['ra_dec']
    assert result['ra_dec'].endswith(', 1.0')
