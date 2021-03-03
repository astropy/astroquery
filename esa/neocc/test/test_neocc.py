# -*- coding: utf-8 -*-
"""
This module contains all the monkeypatch tests. The data for these
tests is gathered in data folder and contains the information
of different lists and object information from ESA NEOCC portal.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Date: 02-11-2021

© Copyright [European Space Agency][2021]
All rights reserved
"""

import os
import io
import re
import pytest

import requests
import pandas as pd
from pandas._testing import assert_frame_equal, assert_series_equal
import pandas.api.types as ptypes

from astroquery.utils.testing_tools import MockResponse

from astroquery.esa.neocc.__init__ import conf
from astroquery.esa.neocc import lists
from astroquery.esa.neocc.core import neocc

# Import BASE URL and TIMEOUT
API_URL = conf.API_URL
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TIMEOUT = conf.TIMEOUT
VERIFICATION = conf.SSL_CERT_VERIFICATION

# Disable warning in pylint related to monkeypath functions
# pylint: disable=W0613, W0621
class MockResponseESANEOCC(MockResponse):
    """MockResponse is an object intended to have any of the attributes
    that a normal requests.Response object would have. However, it
    only needs to implement the methods that are actually used within
    the tests.
    """
    def __init__(self, content):
        super().__init__(content)


def data_path(filename):
    """Look for the data directory local to the test_module.py file.
    """
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

@pytest.fixture
def patch_get(request):
    """This function, when called, changes the requests.Session’s
    request method to call the get_mockreturn function, defined below.
    """
    try:
        monkey_p = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        monkey_p = request.getfuncargvalue("monkeypatch")
    monkey_p.setattr(requests, 'get', get_mockreturn)
    return monkey_p


def get_mockreturn(name, timeout=TIMEOUT, verify=VERIFICATION):
    """Define a function to return the appropriate data stored in the
    data/ directory as a readable object within the MockResponse class.
    """
    # Split name (the requested url) to obtain the name of the file
    # loation stored in \data
    fileloc = name.split(r'=')[1]
    # Exception for ephemerides
    if '&oc' in fileloc:
        fileloc = fileloc.split(r'&')[0] + '.eph'
    filename = data_path(fileloc)
    content = open(filename, 'rb').read()
    return MockResponse(content)


def test_bad_list_names():
    """Check errores from invalid names
    """
    # Invalid inputs
    bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
    foo_data = []
    # Assert for invalid names
    for elements in bad_names:
        with pytest.raises(KeyError):
            lists.get_list_url(elements)
        with pytest.raises(KeyError):
            lists.parse_list(elements, foo_data)


def test_parse_nea(patch_get):
    """Check data: nea_list, updated_nea and monthly_update
    """
    # NEA list, Updated NEA list and monthly update
    nea_list = neocc.query_list('nea_list')
    updated_nea = neocc.query_list('updated_nea')
    monthly_update = neocc.query_list('monthly_update')
    # Assert is a pandas Series
    assert isinstance(nea_list, pd.Series) and\
           isinstance(updated_nea, pd.Series) and\
           isinstance(monthly_update, pd.Series)
    # Assert is not empty
    assert not nea_list.empty and\
           not updated_nea.empty and\
           not monthly_update.empty
    # Check size of the files
    assert nea_list.size == 26844 and\
           updated_nea.size == 3366 and\
           monthly_update.size == 1
    # Check some elements of the lists
    # NEA list
    first_neas = pd.Series(['433 Eros', '719 Albert', '887 Alinda',
                            '1036 Ganymed', '1221 Amor', '1566 Icarus',
                            '1580 Betulia', '1620 Geographos',
                            '1627 Ivar', '1685 Toro', '1862 Apollo',
                            '1863 Antinous', '1864 Daedalus',
                            '1865 Cerberus', '1866 Sisyphus',
                            '1915 Quetzalcoatl', '1916 Boreas',
                            '1917 Cuyo', '1943 Anteros',
                            '1980 Tezcatlipoca', '1981 Midas',
                            '2059 Baboquivari', '2061 Anza',
                            '2062 Aten', '2063 Bacchus',
                            '2100 Ra-Shalom', '2101 Adonis',
                            '2102 Tantalus', '2135 Aristaeus',
                            '2201 Oljato', '2202 Pele',
                            '2212 Hephaistos', '2329 Orthos',
                            '2340 Hathor', '2368 Beltrovata',
                            '2608 Seneca', '3102 Krok', '3103 Eger',
                            '3122 Florence', '3199 Nefertiti'])
    first_neas = first_neas.rename(0)
    assert_series_equal(first_neas, nea_list.iloc[0:40])
    assert nea_list.iloc[-1] == '6344P-L'
    # Updated NEA
    first_update = pd.Series(['Mon Oct 04 06:30:08 UTC 2021',
                              '2021SF4', '2021SK4', '2021SL4',
                              '2021TK', '2021TL', '2021TM', '2021TN',
                              '2021TO', '2021TQ',])
    first_update = first_update.rename(0)
    assert_series_equal(first_update, updated_nea.iloc[0:10])
    assert updated_nea.iloc[-1] == '2019UE2'
    # Monthly update
    assert monthly_update.iloc[0] == 'Tue Aug 24 06:21:13 UTC 2021'
    # Check date format DDD MMM DD HH:MM:SS UTC YYYY
    assert re.match(r'\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} '
                        r'\w{3} \d{4}', monthly_update.iloc[0])


def test_parse_risk(patch_get):
    """Check data: risk_list, risk_list_special
    """
    # Risk and risk special lists
    risk_list = neocc.query_list("risk_list")
    risk_list_special = neocc.query_list("risk_list_special")
    # Assert is a pandas Series
    assert isinstance(risk_list, pd.DataFrame) and\
           isinstance(risk_list_special, pd.DataFrame)
    # Assert is not empty
    assert not risk_list.empty and\
           risk_list_special.empty
    # Check size of the list (rows, columns)
    assert risk_list.shape == (1216, 12)
    # Assert columns
    risk_columns = ['Object Name', 'Diameter in m', '*=Y',
                    'Date/Time', 'IP max', 'PS max', 'TS',
                    'Vel in km/s', 'First year', 'Last year',
                    'IP cum', 'PS cum']
    risk_special_columns = risk_columns[0:8]
    assert (risk_list.columns == risk_columns).all() and\
           (risk_list_special.columns == risk_special_columns).all()
    # Assert columns data types
    # Floats
    float_cols = ['Diameter in m', 'IP max', 'PS max',
                  'Vel in km/s', 'IP cum', 'PS cum']
    assert all(ptypes.is_float_dtype(risk_list[cols1])\
        for cols1 in float_cols)
    # int64
    int_cols = ['TS', 'First year', 'Last year']
    assert all(ptypes.is_int64_dtype(risk_list[cols2])\
        for cols2 in int_cols)
    # Object
    object_cols = ['Object Name', '*=Y']
    assert all(ptypes.is_object_dtype(risk_list[cols3])\
        for cols3 in object_cols)
    # Datetime
    assert ptypes.is_datetime64_ns_dtype(
            risk_list['Date/Time'])
    # Check first, last and random mid element
    risk_first = pd.DataFrame(data=[['2021QM1', 50.0, '*',
                                     '2052-04-02 01:36:00', 0.000298,
                                     -2.72, 0, 23.72, 2050, 2054,
                                     0.000298, -2.72]],
                              columns=risk_columns)
    risk_first['Date/Time'] = pd.to_datetime(risk_first['Date/Time'])
    risk_last = pd.DataFrame(data=[['2021KQ2', 4.0, '*',
                                    '2097-05-21 03:05:00', 1.26e-11,
                                    -13.71, 0, 11.42, 2097, 2097,
                                    1.26e-11, -13.71]],
                             columns=risk_columns, index=[1215])
    risk_last['Date/Time'] = pd.to_datetime(risk_last['Date/Time'])
    risk_mid = pd.DataFrame(data=[['2013BR15', 30.0, '*',
                                   '2100-01-02 18:03:00', 1.21e-07,
                                   -7.15, 0, 17.98, 2100, 2100,
                                   1.6e-07, -7.03]],
                            columns=risk_columns, index=[608])
    risk_mid['Date/Time'] = pd.to_datetime(risk_mid['Date/Time'])
    assert_frame_equal(risk_first, risk_list.iloc[[0]])
    assert_frame_equal(risk_last, risk_list.iloc[[-1]])
    assert_frame_equal(risk_mid, risk_list.iloc[[608]])


def test_parse_clo(patch_get):
    """Check data: close_approaches_upcoming, close_approaches_recent
    """
    # Close approaches upcoming and recent lists
    close_appr_upcoming = neocc.query_list("close_approaches_upcoming")
    close_appr_recent = neocc.query_list("close_approaches_recent")
    # Assert is a pandas DataFrame
    assert isinstance(close_appr_upcoming, pd.DataFrame) and\
           isinstance(close_appr_recent, pd.DataFrame)
    # Assert dataframe is not empty, columns names and length
    assert not close_appr_upcoming.empty and\
           not close_appr_recent.empty
    # Check size of the list
    assert close_appr_upcoming.shape == (162, 10) and\
           close_appr_recent.shape == (139, 10)
    # Assert columns of close approaches lists
    close_columns = ['Object Name', 'Date',
                     'Miss Distance in km', 'Miss Distance in au',
                     'Miss Distance in LD', 'Diameter in m',
                     '*=Yes', 'H', 'Max Bright',
                     'Rel. vel in km/s']
    assert (close_appr_upcoming.columns == close_columns).all() and\
           (close_appr_recent.columns == close_columns).all()
    # Assert columns data types
    # Floats
    float_cols = ['Miss Distance in au',
                  'Miss Distance in LD', 'Diameter in m', 'H',
                  'Max Bright', 'Rel. vel in km/s']
    assert all(ptypes.is_float_dtype(close_appr_upcoming[cols1])\
        for cols1 in float_cols) and\
           all(ptypes.is_float_dtype(close_appr_recent[cols1])\
        for cols1 in float_cols)
    # int64
    int_cols = 'Miss Distance in km'
    assert ptypes.is_int64_dtype(close_appr_upcoming[int_cols])\
        and ptypes.is_int64_dtype(close_appr_recent[int_cols])
    # Object
    object_cols = ['Object Name', '*=Yes']
    assert all(ptypes.is_object_dtype(close_appr_upcoming[cols3])\
        for cols3 in object_cols) and\
           all(ptypes.is_object_dtype(close_appr_recent[cols3])\
        for cols3 in object_cols)
    # Datetime
    assert ptypes.is_datetime64_ns_dtype(close_appr_upcoming['Date'])\
        and ptypes.is_datetime64_ns_dtype(close_appr_recent['Date'])
    # Check first, last and random mid element
    # Close approaches upcoming
    closeup_first = pd.DataFrame(data=[['2021SV1',
                                        '2021-10-04 00:00:00', 2610993,
                                        0.017453, 6.792, 18.0, '*',
                                        26.5, 120.5, 8.9]],
                                 columns=close_columns)
    closeup_first['Date'] = pd.to_datetime(closeup_first['Date'])
    closeup_last = pd.DataFrame(data=[['2018ER1',
                                       '2022-10-02 00:00:00', 5639345,
                                       0.037697, 14.671, 25.0, '*',
                                       25.7, 122.7, 4.0]],
                                columns=close_columns, index=[161])
    closeup_last['Date'] = pd.to_datetime(closeup_last['Date'])
    closeup_mid = pd.DataFrame(data=[['455176 1999VF22',
                                      '2022-02-22 00:00:00', 5366108,
                                      0.03587, 13.96, 250.0, '*',
                                      20.7, 16.0, 25.1]],
                               columns=close_columns, index=[80])
    closeup_mid['Date'] = pd.to_datetime(closeup_mid['Date'])
    assert_frame_equal(closeup_first, close_appr_upcoming.iloc[[0]])
    assert_frame_equal(closeup_last, close_appr_upcoming.iloc[[-1]])
    assert_frame_equal(closeup_mid, close_appr_upcoming.iloc[[80]])
    # Close approaches recent
    closere_first = pd.DataFrame(data=[['2021SZ1',
                                        '2021-10-03 00:00:00', 874866,
                                        0.005848, 2.276, 17.0, '*',
                                        26.6, 17.6, 13.7]],
                                 columns=close_columns)
    closere_first['Date'] = pd.to_datetime(closere_first['Date'])
    closere_last = pd.DataFrame(data=[['2021RT1',
                                       '2021-09-04 00:00:00', 2223152,
                                       0.014861, 5.783, 30.0, '*',
                                       25.2, 18.6, 20.6]],
                                columns=close_columns, index=[138])
    closere_last['Date'] = pd.to_datetime(closere_last['Date'])
    closere_mid = pd.DataFrame(data=[['2008CD6',
                                      '2021-09-13 00:00:00', 1544099,
                                      0.010322, 4.017, 60.0, '*',
                                      23.9, 16.1, 14.4]],
                               columns=close_columns, index=[68])
    closere_mid['Date'] = pd.to_datetime(closere_mid['Date'])
    assert_frame_equal(closere_first, close_appr_recent.iloc[[0]])
    assert_frame_equal(closere_last, close_appr_recent.iloc[[-1]])
    assert_frame_equal(closere_mid, close_appr_recent.iloc[[68]])
    # Assert Connection Error. In case of internal server error
    # the request provided an empty file
    foo_error = io.StringIO('This site cant be reached\n'
                            'domain.com regused to connect\n'
                            'Search Google for domain\n'
                            'ERR_CONNECTION_REFUSED')
    with pytest.raises(ConnectionError):
        lists.parse_clo(foo_error)


def test_parse_pri(patch_get):
    """Check data: priority_list, priority_list_faint
    """
    # Priority list and priority faint list
    priority_list = neocc.query_list("priority_list")
    faint_list = neocc.query_list("priority_list_faint")
    # Assert is a pandas DataFrame
    assert isinstance(priority_list, pd.DataFrame) and\
           isinstance(faint_list, pd.DataFrame)
    # Assert dataframe is not empty, columns names and length
    assert not priority_list.empty and\
           not faint_list.empty
    # Check size of the list
    assert priority_list.shape == (176, 8) and\
           faint_list.shape == (734, 8)
    # Assert columns of close approaches lists
    priority_columns = ['Priority', 'Object',
                        'R.A. in arcsec', 'Decl. in deg',
                        'Elong. in deg', 'V in mag', 'Sky uncert.',
                        'End of Visibility']
    assert (priority_list.columns == priority_columns).all() and\
           (faint_list.columns == priority_columns).all()
    # Assert columns data types
    # Floats
    float_cols = ['R.A. in arcsec', 'Decl. in deg',
                  'V in mag']
    assert all(ptypes.is_float_dtype(priority_list[cols1])\
        for cols1 in float_cols) and\
           all(ptypes.is_float_dtype(faint_list[cols1])\
        for cols1 in float_cols)
    # int64
    int_cols = ['Priority', 'Elong. in deg', 'Sky uncert.']
    assert all(ptypes.is_int64_dtype(priority_list[cols2])\
        for cols2 in int_cols) and\
           all(ptypes.is_int64_dtype(faint_list[cols2])\
        for cols2 in int_cols)
    # Object
    assert ptypes.is_object_dtype(priority_list['Object']) and\
           ptypes.is_object_dtype(faint_list['Object'])
    # Datetime
    assert ptypes.is_datetime64_ns_dtype(
               priority_list['End of Visibility']) and\
           ptypes.is_datetime64_ns_dtype(
               faint_list['End of Visibility'])

    # Check first, last and random mid element
    # Priority list
    priority_first = pd.DataFrame(data=[[0, '2013GM8', 5880.0, 35.7,
                                         146, 21.3, 62144,
                                         '2021-11-16 00:00:00']],
                                 columns=priority_columns)
    priority_first['End of Visibility'] =\
        pd.to_datetime(priority_first['End of Visibility'])
    priority_last = pd.DataFrame(data=[[3, '2021NN50', 71880.0, -11.8,
                                        108, 21.2, 0,
                                        '2021-11-20 00:00:00']],
                                columns=priority_columns, index=[175])
    priority_last['End of Visibility'] =\
         pd.to_datetime(priority_last['End of Visibility'])
    priority_mid = pd.DataFrame(data=[[1, '2021SY2', 10560.0, 6.0,
                                       146, 20.1, 3,
                                       '2021-10-22 00:00:00']],
                                columns=priority_columns, index=[87])
    priority_mid['End of Visibility'] =\
          pd.to_datetime(priority_mid['End of Visibility'])
    assert_frame_equal(priority_first, priority_list.iloc[[0]])
    assert_frame_equal(priority_last, priority_list.iloc[[-1]])
    assert_frame_equal(priority_mid, priority_list.iloc[[87]])

    # Priority faint list
    faint_first = pd.DataFrame(data=[[0, '2012BD77', 13800.0, -36.0,
                                      120, 24.7, 1251,
                                      '2021-12-26 00:00:00']],
                                 columns=priority_columns)
    faint_first['End of Visibility'] =\
        pd.to_datetime(faint_first['End of Visibility'])
    faint_last = pd.DataFrame(data=[[1, '2021SX3', 83340.0, -6.3,
                                     155, 22.2, 1,
                                     '2021-12-12 00:00:00']],
                                columns=priority_columns, index=[733])
    faint_last['End of Visibility'] =\
         pd.to_datetime(faint_last['End of Visibility'])
    faint_mid = pd.DataFrame(data=[[0, '2019UO10', 84960.0, -37.9,
                                    135, 24.9, 9185,
                                    '2021-10-13 00:00:00']],
                                columns=priority_columns, index=[338])
    faint_mid['End of Visibility'] =\
          pd.to_datetime(faint_mid['End of Visibility'])
    assert_frame_equal(faint_first, faint_list.iloc[[0]])
    assert_frame_equal(faint_last, faint_list.iloc[[-1]])
    assert_frame_equal(faint_mid, faint_list.iloc[[338]])


def test_parse_encounter(patch_get):
    """Check data: encounter_list
    """
    encounter_list = neocc.query_list("close_encounter")
    # Assert is a pandas DataFrame
    assert isinstance(encounter_list, pd.DataFrame)
    # Assert dataframe is not empty, columns names and length
    assert not encounter_list.empty
    # Check size of the list
    assert encounter_list.shape == (4770, 13)
    # Assert columns of close approaches lists
    encounter_columns = ['Name/desig', 'Planet', 'Date',
                         'Time approach', 'Time uncert',
                         'Distance', 'Minimum distance',
                         'Distance uncertainty', 'Width',
                         'Stretch', 'Probability', 'Velocity',
                         'Max Mag']
    assert (encounter_list.columns == encounter_columns).all()
    # Assert columns data types
    # Floats
    float_cols = encounter_columns[3:]
    assert all(ptypes.is_float_dtype(encounter_list[cols1])\
        for cols1 in float_cols)
    # Object
    object_cols = ['Name/desig', 'Planet']
    assert all(ptypes.is_object_dtype(encounter_list[cols2])\
        for cols2 in object_cols)
    # Datetime
    assert ptypes.is_datetime64_ns_dtype(encounter_list['Date'])
    # Check first, last and random mid element
    encounter_first = pd.DataFrame(data=[['433', 'EARTH',
                                          '1975-01-23 07:39:27.648000',
                                          42435.3, 1.15121e-05,
                                          0.151134, 0.151134,
                                          1.67494e-08, 1.314e-08,
                                          4.091e-08, 1.0, 5.82531,
                                          7.399]],
                                 columns=encounter_columns)
    encounter_first['Date'] = pd.to_datetime(encounter_first['Date'])
    encounter_last = pd.DataFrame(data=[['585428', 'EARTH',
                                         '2080-01-16 09:16:19.776000',
                                         80779.4, 0.00227633, 0.196848,
                                         0.196847, 3.65604e-07,
                                         7.5e-08, 1.795e-05, 1.0,
                                         17.5023, 166.366]],
                                columns=encounter_columns,
                                index=[4769])
    encounter_last['Date'] = pd.to_datetime(encounter_last['Date'])
    encounter_mid = pd.DataFrame(data=[['506074', 'EARTH',
                                        '1980-10-11 15:44:13.344000',
                                        44523.655710240,
                                        1.990310993e-04,
                                        1.614067301329673e-01,
                                        1.613990552029752e-01,
                                        3.120379042532057e-06,
                                        6.589e-08, 3.719e-06,
                                        1.00e+00, 18.51895001,
                                        18.013]],
                                columns=encounter_columns,
                                index=[2000])
    encounter_mid['Date'] = pd.to_datetime(encounter_mid['Date'])
    assert_frame_equal(encounter_first, encounter_list.iloc[[0]])
    assert_frame_equal(encounter_last, encounter_list.iloc[[-1]])
    assert_frame_equal(encounter_mid, encounter_list.iloc[[2000]])
    # Assert Connection Error. In case of internal server error
    # the request provided an empty file
    foo_error = io.StringIO('This site cant be reached\n'
                            'domain.com regused to connect\n'
                            'Search Google for domain\n'
                            'ERR_CONNECTION_REFUSED')
    with pytest.raises(ConnectionError):
        lists.parse_encounter(foo_error)


def test_parse_impacts(patch_get):
    """Check data: impacted objects list
    """
    impact_list = neocc.query_list("impacted_objects")
    # Assert is a pandas DataFrame
    assert isinstance(impact_list, pd.DataFrame)
    # Assert dataframe is not empty, columns names and length
    assert not impact_list.empty
    # Check size of the list
    assert impact_list.shape == (4, 2)
    # Assert columns data types
    # Object
    assert ptypes.is_object_dtype(impact_list[0])
    # Datetime
    assert ptypes.is_datetime64_ns_dtype(impact_list[1])
    # Assert Data frame
    impacts_data = pd.DataFrame(data=[['2008TC3', '2008-10-07 00:00:00'],
                                      ['2018LA', '2018-06-02 00:00:00'],
                                      ['2014AA', '2014-01-02 00:00:00'],
                                      ['2019MO', '2019-06-22 00:00:00']])
    impacts_data[1] = pd.to_datetime(impacts_data[1])
    assert_frame_equal(impacts_data, impact_list)


def test_parse_catalogues(patch_get):
    """Check data: encounter_list
    """
    catalogues = ['neo_catalogue_current',
                  'neo_catalogue_middle']
    for catalogue in catalogues:
        cat_list = neocc.query_list(list_name=catalogue)
        # Assert is a pandas DataFrame
        assert isinstance(cat_list, pd.DataFrame)
        # Assert dataframe is not empty, columns names and length
        assert not cat_list.empty
        # Check size of the list
        assert cat_list.shape == (27104, 11)
        # Assert columns of close approaches lists
        cat_columns = ['Name', 'Epoch (MJD)', 'a', 'e', 'i',
                       'long. node', 'arg. peric.', 'mean anomaly',
                       'absolute magnitude', 'slope param.',
                       'non-grav param.']
        assert (cat_list.columns == cat_columns).all()
        # Assert columns data types
        # Floats
        float_cols = ['Epoch (MJD)', 'a', 'e', 'i',
                    'long. node', 'arg. peric.', 'mean anomaly',
                    'absolute magnitude', 'slope param.']
        assert all(ptypes.is_float_dtype(cat_list[cols1])\
            for cols1 in float_cols)
        # Object
        assert ptypes.is_object_dtype(cat_list['Name'])
        # Int
        assert ptypes.is_int64_dtype(cat_list['non-grav param.'])
    # Check first, last and random mid element
    cat_list = neocc.query_list(list_name='neo_catalogue_current')
    cat_first = pd.DataFrame(data=[['433', 59600.0, 1.458273,
                                    0.222727, 10.828461, 304.296355,
                                    178.897169, 246.904188, 10.85,
                                    0.46, 0]], columns=cat_columns)
    cat_last = pd.DataFrame(data=[['6344P-L', 59400.0, 2.820228,
                                   0.66156, 4.678611, 182.823002,
                                   234.946602, 323.861524, 20.4,
                                   0.15, 0]], columns=cat_columns,
                                   index=[27103])
    cat_mid = pd.DataFrame(data=[['2015GZ', 59400.0, 2.805925,
                                  0.717771, 13.504485, 19.799757,
                                  114.569305, 128.28982, 26.06,
                                  0.15, 0]], columns=cat_columns,
                                  index=[12488])
    assert_frame_equal(cat_first, cat_list.iloc[[0]])
    assert_frame_equal(cat_last, cat_list.iloc[[-1]])
    assert_frame_equal(cat_mid, cat_list.iloc[[12488]])


def test_tabs_impacts(patch_get):
    """Check data: asteroid impacts tab
    """
    # Check asteroids
    # Exceptions: 433 Eros has not tab "impacts"
    #             99942 Apophis currently has not tab "impacts"
    #             however, it had a special additional_note case
    list_neas = {
        '1979XB'  : ['There is no additional note for this object',
                     '20190808 162907.255 CET', '1979-12-15T10:19:12',
                     '1979-12-11T12:15:50.400000', 18, 0,
                     'Coordinates are given on the Target '
                     'Plane\n\nUnit is one Earth radius, but impact '
                     'cross section\nhas radius between  1.12 and  '
                     '1.12 Earth radii\n\nCoordinates for LOV = EQU '
                     'scaled= 1 second= F'],
        '433'     : [],
        '99942'   : ['ADDITIONAL NOTE\nThe results contained in this '
                     'impactor table are based on the Line Of '
                     'Variations method generalised\nto the 7-dimensional'
                     ' space of the orbital elements and the Yarkovsky '
                     'parameter. The Yarkovsky parameter\nhas been '
                     'estimated from the fit to the astrometry as '
                     '(-2.65+/- 0.23) 10^-14 au/d^2.\nThe results are '
                     'compatible with the ones obtained at JPL and '
                     'NEODyS.', '20210119 112012.088 UTC.',
                     '2021-01-17T13:39:21.600000',
                     '2004-03-15T02:35:31.200000', 4711, 3,
                     'Coordinates are given on the Target '
                     'Plane.\n\nUnit is one Earth radius, but impact '
                     'cross section\nhas radius between  2.15 and  '
                     '2.16 Earth radii.\n\nCoordinates for LOV = KEP '
                     'scaled= 2 second= F.']
        }
    for asteroid in list_neas:
        # Check ValueError for not file
        if asteroid == '433':
            with pytest.raises(ValueError):
                neocc.query_object(name=asteroid, tab='impacts')
        else:
            ast_impact = neocc.query_object(name=asteroid,
                                            tab='impacts')
            dict_attributes = {
                'impacts'               : pd.DataFrame,
                'arc_start'             : str,
                'arc_end'               : str,
                'observation_accepted'  : int,
                'observation_rejected'  : int,
                'computation'           : str,
                'info'                  : str,
                'additional_note'       : str
                }
            for attribute in dict_attributes:
                # Check attributes exist and their type
                assert hasattr(ast_impact, attribute)
                assert isinstance(getattr(ast_impact, attribute),
                                dict_attributes[attribute])
                # Check values are the same from stored data
                assert ast_impact.additional_note ==\
                     list_neas[asteroid][0]
                assert ast_impact.computation == list_neas[asteroid][1]
                assert ast_impact.arc_end == list_neas[asteroid][2]
                assert ast_impact.arc_start == list_neas[asteroid][3]
                assert ast_impact.observation_accepted ==\
                     list_neas[asteroid][4]
                assert ast_impact.observation_rejected ==\
                     list_neas[asteroid][5]
                assert ast_impact.info == list_neas[asteroid][6]
                # Assert dataframe is not empty, columns names
                # and length
                assert not ast_impact.impacts.empty
                # Check size of the list
                assert ast_impact.impacts.shape == (8, 11)
                # Assert columns of close approaches lists
                impacts_columns = ['date', 'MJD', 'sigma', 'sigimp',
                                   'dist', 'width', 'stretch', 'p_RE',
                                   'Exp. Energy in MT', 'PS', 'TS']
                assert (ast_impact.impacts.columns == \
                        impacts_columns).all()
                # Assert columns data types
                # Floats
                float_cols = ast_impact.impacts.columns[1:10]
                assert all(ptypes.is_float_dtype(ast_impact.\
                    impacts[cols1]) for cols1 in float_cols)
                # Int
                assert ptypes.is_int64_dtype(ast_impact.impacts['TS'])
                # Datetime
                assert ptypes.is_datetime64_ns_dtype(ast_impact.\
                                                     impacts['date'])
                # Check specific elements of the impacts Data Frame
                df_test = pd.DataFrame([['2101-12-14 04:52:19.200000',
                                         88781.204, -0.384, 0.0, 0.61,
                                         0.089, 194000000.0, 3.48e-09,
                                         0.000131, -5.36, 0],
                                        ['2074-04-13 08:36:57.600000',
                                          78675.359, 2.396, 0.0, 1.35,
                                          0.008, 3280000.0, 2.91e-08,
                                          0.0000221, -5.48, 0]],
                                        columns=impacts_columns)
                df_test['date'] = pd.to_datetime(df_test['date'])
                if asteroid == '1979XB':
                    assert_series_equal(ast_impact.impacts.iloc[3],
                                    df_test.iloc[0], check_names=False)
                else:
                    assert_series_equal(ast_impact.impacts.iloc[3],
                                    df_test.iloc[1], check_names=False)


def test_tabs_close_approach(patch_get):
    """Check data: asteroid close approaches tab
    """
    list_neas = {'433'      : (5, 10),
                 '99942'    : (26, 10),
                 '594938 2021GE13' : ()}
    for asteroid in list_neas:
        ast_close = neocc.query_object(name=asteroid,
                                       tab='close_approaches')
        if asteroid == '594938 2021GE13':
            assert ast_close.empty
        else:
            # Assert is a pandas DataFrame
            assert isinstance(ast_close, pd.DataFrame)
            # Assert dataframe is not empty, columns names and length
            assert not ast_close.empty
            # Check size of the list
            assert ast_close.shape == list_neas[asteroid]
            # Assert columns of close approaches lists
            close_columns = ['BODY', 'CALENDAR-TIME', 'MJD-TIME',
                                 'TIME-UNCERT.', 'NOM.-DISTANCE',
                                 'MIN.-POSS.-DIST.', 'DIST.-UNCERT.',
                                 'STRETCH', 'WIDTH', 'PROBABILITY']
            assert (ast_close.columns == close_columns).all()
            # Assert columns data types
            # Floats
            float_cols = close_columns[2:]
            assert all(ptypes.is_float_dtype(ast_close[cols1])\
                for cols1 in float_cols)
            # Object
            assert ptypes.is_object_dtype(ast_close['BODY'])
            # Datetime
            assert ptypes.is_datetime64_ns_dtype(
                ast_close['CALENDAR-TIME'])
            # Check specific elements of the impacts Data Frame
            df_test = pd.DataFrame([['EARTH',
                                     '2093-01-31 15:46:48',
                                     85543.657499489, 1.572619005e-05,
                                     0.1824638321371326,
                                     0.1824638180864916,
                                     4.954403653193194e-08,
                                     9.921e-08, 1.612e-08, 1.0],
                                    ['EARTH',
                                     '1972-12-24 11:52:22.080000',
                                     41675.494697571, 0.004521177247,
                                     0.07923789245024694,
                                     0.07920056098848807,
                                     1.244155168249903e-05,
                                     1.584e-05, 4.645e-09, 1.0]],
                                     columns=close_columns)
            df_test['CALENDAR-TIME'] = pd.to_datetime(
                df_test['CALENDAR-TIME'])
            if asteroid == '433':
                assert_series_equal(ast_close.iloc[3],
                                    df_test.iloc[0], check_names=False)
            else:
                assert_series_equal(ast_close.iloc[3],
                                    df_test.iloc[1], check_names=False)


def test_tabs_physical_properties(patch_get):
    """Check data: physical properties tab
    """
    list_neas = {
    '99942'       : [['Rotation Period', 30.56, 'h', '[4]'],
                     ['Quality', 3.0, '-', '[4]'],
                     ['Amplitude', 1.0, 'mag', '[4]'],
                     ['Rotation Direction', 'RETRO', '-', '[1]'],
                     ['Spinvector L', 250, 'deg', '[1]'],
                     ['Spinvector B', -7.50e1, 'deg', '[1]'],
                     ['Taxonomy', 'S/Sq', '-', '[2]'],
                     ['Taxonomy (all)', 'Sq,Scomp', '-', '[3]'],
                     ['Absolute Magnitude (H)', [18.937, 19.09],
                        ['mag','mag'], ['[5]', '[6]']],
                     ['Slope Parameter (G)', ['0.15**', 0.24, '0.15**'],
                        ['mag', 'mag', 'mag'], ['[7]', '[1]', '[5]']],
                     ['Albedo', 0.285, '-', '[8]'],
                     ['Diameter', 375, 'm' , '[9]'],
                     ['Color Index Information', [0.846, 0.451, 0.362],
                        ['B-V', 'V-R', 'R-I'], ['[10]', '[10]', '[10]']],
                     ['Sightings', ['Radar R', 'Visual S'],
                        ['-', '-'], ['[11]', '[12]']]],
    '1994CJ1'      : [['Rotation Period', 30.0, 'h', '[2]'],
                     ['Quality', ['1', 'B', 'R'], '-', '[2]'],
                     ['Amplitude', 0.8, 'mag', '[2]'],
                     ['Rotation Direction', '-', '-', '[-]'],
                     ['Spinvector L', '-', 'deg', '[-]'],
                     ['Spinvector B', '-', 'deg', '[-]'],
                     ['Taxonomy', 'A', '-', '[1]'],
                     ['Taxonomy (all)', 'A', '-', '[1]'],
                     ['Absolute Magnitude (H)', 21.539, 'mag', '[3]'],
                     ['Slope Parameter (G)', ['0.15**', '0.15**'],
                        ['mag', 'mag'], ['[4]', '[3]']],
                     ['Albedo', '-', '-', '[-]'],
                     ['Diameter', '170*', 'm' , '[5]'],
                     ['Color Index Information', '-', 'mag', '[-]'],
                     ['Sightings', 'Radar R', '-', '[6]']]
    }
    # Check value error if empty
    with pytest.raises(ValueError):
        neocc.query_object(name='frfre', tab='physical_properties')
    for asteroid in list_neas:
        phys_props = neocc.query_object(name=asteroid,
                                        tab='physical_properties')
        dict_attributes = {
            'physical_properties'   : pd.DataFrame,
            'sources'               : pd.DataFrame,

            }
        for attribute in dict_attributes:
            # Check attributes exist and their type
            assert hasattr(phys_props, attribute)
            # Add type stre in tuple for those objects whose
            # observations are strings
            assert isinstance(getattr(phys_props, attribute),
                            dict_attributes[attribute])
            # Check values are the same from stored data
            assert phys_props.physical_properties.shape == (14, 4)
            phys_prop_columns = ['Property', 'Value(s)', 'Units',
                                'Reference(s)']
            assert (phys_props.physical_properties.columns == \
                        phys_prop_columns).all()
            sources_columns = ['No.', 'Name', 'Additional']
            assert (phys_props.sources.columns == \
                        sources_columns).all()
            assert all(ptypes.is_object_dtype(phys_props.\
                    physical_properties[cols1])
                    for cols1 in phys_prop_columns) and\
                all(ptypes.is_object_dtype(phys_props.\
                    sources[cols1]) for cols1 in sources_columns)
            properties = pd.DataFrame(list_neas[asteroid],
                                      columns=phys_prop_columns)

            for item1, item2 in zip(phys_props.physical_properties,
                                    properties):
                assert item1 == item2


def test_tabs_observations(patch_get):
    """Check data: asteroid observations tab
    """
    list_neas = {
        '433'       : [3.99763e-01, 5.19998e-01, (9888, 31), (6, 14),
                       (98 ,10)],
        '1685'      : [3.75402e-01, 4.33873e-01, (3670, 31), (9, 14),
                       (119, 10)],
        '2016YC8'   : [4.91025e-01, 3.64713e-01, (86, 31), (2, 14),
                       (2, 10)],
        '2020BX12'  : [6.09087e-01, 3.80688e-01, (153, 31), (2, 14),
                       ()],
        '1979XB'    : [4.49806E-01, 'No data for RMSmag', (18, 31), (),
                       ()],
        }
    with pytest.raises(ValueError):
        neocc.query_object(name='FOO', tab='observations')
    for asteroid in list_neas:
        ast_observations = neocc.query_object(name=asteroid,
                                              tab='observations')
        dict_attributes = {
            'version'               : float,
            'errmod'                : str,
            'rmsast'                : float,
            'rmsmag'                : float,
            'optical_observations'  : pd.DataFrame,
            'radar_observations'    : pd.DataFrame,
            'roving_observations'   : pd.DataFrame,
            'sat_observations'      : pd.DataFrame
            }
        for attribute in dict_attributes:
            # Check attributes exist and their type
            assert hasattr(ast_observations, attribute)
            # Add type stre in tuple for those objects whose
            # observations are strings
            assert isinstance(getattr(ast_observations, attribute),
                            (dict_attributes[attribute], str))
            # Check values are the same from stored data
            assert ast_observations.version == 2.0
            assert ast_observations.errmod == 'vfcc17'
            assert ast_observations.rmsast == list_neas[asteroid][0]
            assert ast_observations.rmsmag == list_neas[asteroid][1]
            # Assert there are always optical observations and its size
            assert not ast_observations.optical_observations.empty
            assert ast_observations.optical_observations.shape ==\
                list_neas[asteroid][2]
            opt_obs_columns = ['Design.', 'K', 'T', 'N', 'Date',
                               'Date Accuracy', 'RA HH', 'RA MM',
                               'RA SS.sss', 'RA Accuracy', 'RA RMS',
                               'RA F', 'RA Bias', 'RA Resid',
                               'DEC sDD', 'DEC MM', 'DEC SS.ss',
                               'DEC Accuracy', 'DEC RMS', 'DEC F',
                               'DEC Bias', 'DEC Resid', 'MAG Val',
                               'MAG B', 'MAG RMS', 'MAG Resid',
                               'Ast Cat', 'Obs Code', 'Chi', 'A', 'M']
            assert (ast_observations.optical_observations.columns == \
                     opt_obs_columns).all()
            # Assert columns data types
            # Floats
            float_cols = ['Date Accuracy', 'RA SS.sss', 'RA Accuracy',
                          'RA RMS', 'RA Bias', 'RA Resid', 'DEC SS.ss',
                          'DEC Accuracy', 'DEC RMS', 'DEC Bias',
                          'DEC Resid', 'Chi']
            assert all(ptypes.is_float_dtype(ast_observations.\
                optical_observations[cols1]) for cols1 in float_cols)
            # Int, Object
            object_cols = ['Design.', 'K', 'T', 'N', 'DEC sDD',
                           'DEC MM', 'DEC F', 'MAG Val', 'MAG B',
                           'MAG RMS', 'MAG Resid', 'Ast Cat',
                           'Obs Code', 'A', 'M']
            assert all(ptypes.is_object_dtype(ast_observations.\
                optical_observations[cols1]) for cols1 in object_cols) or\
                   all(ptypes.is_float_dtype(ast_observations.\
                optical_observations[cols1]) for cols1 in float_cols)
            # Datetime
            assert ptypes.is_datetime64_ns_dtype(ast_observations.\
                optical_observations['Date'])
            # Assert radar observations
            if asteroid == '1979XB':
                assert ast_observations.radar_observations ==\
                    'There is no relevant radar information'
            else:
                assert not ast_observations.radar_observations.empty
                assert ast_observations.radar_observations.shape ==\
                list_neas[asteroid][3]
                radar_obs_columns = ['Design', 'K', 'T', 'Datetime',
                                     'Measure', 'Accuracy', 'rms', 'F',
                                     'Bias', 'Resid', 'TRX', 'RCX',
                                     'Chi', 'S']
                assert (ast_observations.radar_observations.columns ==\
                     radar_obs_columns).all()
                # Assert columns data types
                # Floats
                float_cols = ['Measure', 'Resid', 'Bias', 'Chi']
                assert all(ptypes.is_float_dtype(ast_observations.\
                    radar_observations[cols1]) for cols1 in float_cols)
                # Int, Object
                object_cols = ['Design', 'K', 'T', 'Accuracy',
                               'rms', 'F', 'TRX', 'RCX', 'S']
                assert all(ptypes.is_object_dtype(ast_observations.\
                    radar_observations[cols1]) for cols1 in object_cols) or\
                       all(ptypes.is_float_dtype(ast_observations.\
                    radar_observations[cols1]) for cols1 in float_cols)
                # Datetime
                assert ptypes.is_datetime64_ns_dtype(ast_observations.\
                    radar_observations['Datetime'])
            if asteroid in ['1979XB', '2020BX12']:
                assert ast_observations.sat_observations ==\
                    'There are no Satellite observations for this object'
            else:
                assert not ast_observations.radar_observations.empty
                assert ast_observations.sat_observations.shape ==\
                list_neas[asteroid][4]
                sat_obs_columns = ['Design.', 'K', 'T', 'N', 'Date',
                                   'Parallax info.', 'X', 'Y', 'Z',
                                   'Obs Code']
                assert (ast_observations.sat_observations.columns ==\
                     sat_obs_columns).all()
                # Assert columns data types
                # Floats
                float_cols = ast_observations.\
                             sat_observations.columns[6:9]
                assert all(ptypes.is_float_dtype(ast_observations.\
                    sat_observations[cols1]) for cols1 in float_cols)
                # Int, Object
                object_cols = ['Design.', 'Obs Code', 'Parallax info.',
                               'K', 'T', 'N']
                assert all(ptypes.is_object_dtype(ast_observations.\
                    sat_observations[cols1]) for cols1 in object_cols) or\
                       all(ptypes.is_float_dtype(ast_observations.\
                    sat_observations[cols1]) for cols1 in float_cols)
                # Datetime
                assert ptypes.is_datetime64_ns_dtype(ast_observations.\
                    sat_observations['Date'])
            if asteroid == '1685':
                assert not ast_observations.radar_observations.empty
                assert ast_observations.roving_observations.shape ==\
                    (5, 9)
                rov_obs_columns = ['Design.', 'K', 'T', 'N', 'Date',
                                   'E longitude', 'Latitude',
                                   'Altitude', 'Obs Code']
                assert (ast_observations.roving_observations.columns ==\
                     rov_obs_columns).all()
                # Assert columns data types
                # Floats
                float_cols = ast_observations.\
                             roving_observations.columns[5:8]
                assert all(ptypes.is_float_dtype(ast_observations.\
                    roving_observations[cols1]) for cols1 in float_cols)
                # Int, Object
                object_cols = ['Design.', 'Obs Code']
                assert all(ptypes.is_object_dtype(ast_observations.\
                    roving_observations[cols1]) for cols1 in object_cols) or\
                       all(ptypes.is_float_dtype(ast_observations.\
                    roving_observations[cols1]) for cols1 in float_cols)
                # Datetime
                assert ptypes.is_datetime64_ns_dtype(ast_observations.\
                    roving_observations['Date'])
            else:
                assert ast_observations.roving_observations ==\
                    'There are no "Roving Observer" observations'\
                    ' for this object'
    # Object 1685 contains a complete set of information
    ast_observations = neocc.query_object(name='1685',
                                          tab='observations')
    opt_test = {'Design.': 1685, 'K': 'O', 'T': 'C', 'N': '2',
                'Date': '1999-04-20 11:00:32.198400',
                'Date Accuracy': 1e-06, 'RA HH': 17,
                'RA MM': 25,'RA SS.sss': 59.714,
                'RA Accuracy': 0.01261, 'RA RMS': 0.5,
                'RA F': 'F', 'RA Bias': 0.0, 'RA Resid': -0.293,
                'DEC sDD': -32, 'DEC MM': 45, 'DEC SS.ss': 54.61,
                'DEC Accuracy': 0.01, 'DEC RMS': 0.5,
                'DEC F': 'F', 'DEC Bias': 0.0, 'DEC Resid': -0.06,
                'MAG Val': 17.05, 'MAG B': 'V', 'MAG RMS': 0.5,
                'MAG Resid': -0.1, 'Ast Cat': 'l',
                'Obs Code': '689', 'Chi': 0.6, 'A': 1, 'M': 1}
    df_opt_test = pd.DataFrame(opt_test, index=[0])
    df_opt_test['Date'] = pd.to_datetime(df_opt_test['Date'])
    assert_series_equal(ast_observations.optical_observations.iloc[290],
                        df_opt_test.iloc[0], check_names=False)
    rad_test = {'Design': 1685, 'K': 'R', 'T': 's',
                'Datetime': '1988-07-24 07:35:00',
                'Measure': 31263444.2679, 'Accuracy': '2.99792',
                'rms': '  2.99792', 'F': 'F', 'Bias': 0.0,
                'Resid': 0.11676, 'TRX': '251', 'RCX': '251',
                'Chi': 0.04, 'S': 1}
    df_rad_test = pd.DataFrame(rad_test, index=[0])
    df_rad_test['Datetime'] = pd.to_datetime(df_rad_test['Datetime'])
    assert_series_equal(ast_observations.radar_observations.iloc[4],
                        df_rad_test.iloc[0], check_names=False)
    sat_test = {'Design.': 1685, 'K': 'S', 'T': 's', 'N': ' ',
                'Date': '2010-02-11 22:52:40.800000',
                'Parallax info.': 1, 'X': -4304.3019,
                'Y': -4326.899999999999, 'Z': -3247.9272,
                'Obs Code': 'C51'}
    df_sat_test = pd.DataFrame(sat_test, index=[0])
    df_sat_test['Date'] = pd.to_datetime(df_sat_test['Date'])
    assert_series_equal(ast_observations.sat_observations.iloc[4],
                        df_sat_test.iloc[0], check_names=False)
    rov_test = {'Design.': 1685, 'K': 'O', 'T': ' v', 'N': ' ',
                'Date': '2008-02-14 07:21:30.240000',
                'E longitude': 237.818, 'Latitude': 37.8191,
                'Altitude': 470.0, 'Obs Code': 247}
    df_rov_test = pd.DataFrame(rov_test, index=[0])
    df_rov_test['Date'] = pd.to_datetime(df_rov_test['Date'])
    assert_series_equal(ast_observations.roving_observations.iloc[4],
                        df_rov_test.iloc[0], check_names=False)


def test_tabs_orbit_properties(patch_get):
    """Check data: asteroid orbit properties tab
    """
    list_neas = {
        '433'               : ['middle', (1,3), (1,6), (6, 6)],
        '99942'             : ['present', (1,4), (1,7), (7 ,7)],
        '99942 modif'       : ['present', (1,4), (1,7), (7 ,7)],
        '2009BD'            : ['present', (1,5), (1,8), (8, 8)],
        '594938 2021GE13'   : ['present', (1,3), (1,6), (6, 6)]
        }
    # Assert blank file
    with pytest.raises(ValueError):
        neocc.query_object(name='foo', tab='orbit_properties',
                           orbital_elements='keplerian',
                           orbit_epoch='middle')
    with pytest.raises(ValueError):
        neocc.query_object(name='foo', tab='orbit_properties',
                           orbital_elements='equinoctial',
                           orbit_epoch='middle')
    # Assert KeyError in case some kwargs is missing
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='orbit_properties')
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='orbit_properties',
                           orbital_elements='keplerian')
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='orbit_properties',
                           orbit_epoch='middle')
    orbital_elements = ['keplerian', 'equinoctial']
    for elements in orbital_elements:
        for asteroid in list_neas:
            orb = neocc.query_object(name=asteroid,
                                     tab='orbit_properties',
                                     orbital_elements=elements,
                                     orbit_epoch=list_neas[asteroid][0])
            dict_attributes = {
                'form'      : str,
                'rectype'   : str,
                'refsys'    : str,
                'epoch'     : str,
                'mag'   : pd.DataFrame,
                'lsp'   : pd.DataFrame,
                'ngr'   : pd.DataFrame,
                }
            assert orb.lsp.shape == list_neas[asteroid][1]
            assert all(ptypes.is_int64_dtype(orb.lsp[cols])
                        for cols in orb.lsp.columns)
            for attribute in dict_attributes:
                # Check attributes exist and their type
                assert hasattr(orb, attribute)
                # Add type str in tuple for those objects whose
                # observations are strings
                assert isinstance(getattr(orb, attribute),
                                (dict_attributes[attribute], str))
            if elements == 'keplerian':
                kep_attributes = {
                'kep'           : pd.DataFrame,
                'perihelion'    : float,
                'aphelion'      : float,
                'anode'         : float,
                'dnode'         : float,
                'moid'          : float,
                'period'        : float,
                'pha'           : str,
                'vinfty'        : float,
                'u_par'         : float,
                'orb_type'      : str,
                'rms'           : pd.DataFrame,
                'cov'           : pd.DataFrame,
                'cor'           : pd.DataFrame
                }
                for kep_attribute in kep_attributes:
                    # Check attributes exist and their type
                    assert hasattr(orb, attribute)
                    # Add type str in tuple for those objects whose
                    # observations are strings
                    assert isinstance(getattr(orb, kep_attribute),
                                (kep_attributes[kep_attribute], str))
                    # Assert keplerian elements
                    assert not orb.kep.empty
                    assert orb.kep.shape == (1, 6)
                    assert all(ptypes.is_float_dtype(orb.kep[cols1])
                        for cols1 in orb.kep.columns)
                    # Assert rms and covs and check they are floats
                    assert not orb.rms.empty
                    assert not orb.cov.empty
                    assert not orb.cor.empty
                    assert orb.rms.shape == list_neas[asteroid][2]
                    assert all(ptypes.is_float_dtype(orb.rms[cols2])
                        for cols2 in orb.rms.columns)
                    assert orb.cov.shape == list_neas[asteroid][3]
                    assert all(ptypes.is_float_dtype(orb.cov[cols3])
                        for cols3 in orb.cov.columns)
                    assert orb.cor.shape == list_neas[asteroid][3]
                    assert all(ptypes.is_float_dtype(orb.cor[cols4])
                        for cols4 in orb.cor.columns)
            elif elements == 'equinoctial':
                eq_attributes = {
                'equinoctial'   : pd.DataFrame,
                'rms'           : pd.DataFrame,
                'eig'           : pd.DataFrame,
                'wea'           : pd.DataFrame,
                'cov'           : pd.DataFrame,
                'nor'           : pd.DataFrame
                }
                for eq_attribute in eq_attributes:
                    # Check attributes exist and their type
                    assert hasattr(orb, attribute)
                    # Add type str in tuple for those objects whose
                    # observations are strings
                    assert isinstance(getattr(orb, eq_attribute),
                                (eq_attributes[eq_attribute]))
                    # Assert keplerian elements
                    assert not orb.equinoctial.empty
                    assert not orb.rms.empty
                    assert not orb.eig.empty
                    assert not orb.wea.empty
                    assert not orb.cov.empty
                    assert not orb.nor.empty
                    assert orb.equinoctial.shape == (1, 6)
                    assert all(ptypes.is_float_dtype(orb.equinoctial[cols1])
                        for cols1 in orb.equinoctial.columns)
                    # Assert rms and covs and check they are floats
                    assert orb.rms.shape == list_neas[asteroid][2]
                    assert all(ptypes.is_float_dtype(orb.rms[cols2])
                        for cols2 in orb.rms.columns)
                    assert orb.eig.shape == list_neas[asteroid][2]
                    assert all(ptypes.is_float_dtype(orb.eig[cols3])
                        for cols3 in orb.eig.columns)
                    assert orb.wea.shape == list_neas[asteroid][2]
                    assert all(ptypes.is_float_dtype(orb.wea[cols4])
                        for cols4 in orb.wea.columns)
                    assert orb.cov.shape == list_neas[asteroid][3]
                    assert all(ptypes.is_float_dtype(orb.cov[cols5])
                        for cols5 in orb.cov.columns)
                    assert orb.nor.shape == list_neas[asteroid][3]
                    assert all(ptypes.is_float_dtype(orb.nor[cols6])
                        for cols6 in orb.nor.columns)
    # Choose two files to check some of the values
    ast1 = neocc.query_object(name='99942', tab='orbit_properties',
                              orbital_elements='keplerian',
                              orbit_epoch='present')
    ast2 = neocc.query_object(name='2009BD', tab='orbit_properties',
                              orbital_elements='equinoctial',
                              orbit_epoch='present')
    # Check document info
    assert ast1.form, ast2.form == 'OEF2.0'
    assert ast1.rectype, ast2.rectype == 'ML'
    assert ast1.refsys, ast2.refsys == 'ECLM J2000'
    # Check common orbit properties for both elements
    assert ast1.epoch, ast2.epoch == '59400.000000000 MJD'
    mag1 = pd.DataFrame([[18.937, 0.150]], index=['MAG'],
                        columns=['', ''])
    mag2 = pd.DataFrame([[28.241, 0.150]], index=['MAG'],
                        columns=['', ''])
    assert_frame_equal(ast1.mag, mag1)
    assert_frame_equal(ast2.mag, mag2)

    lsp1 = pd.DataFrame([[1, 2, 7, 2]], index=['LSP'],
                columns=['model used', 'number of model parameters',
                'dimension', 'list of parameters determined'])
    lsp2 = pd.DataFrame([[1, 2, 8, 1, 2]], index=['LSP'],
                columns=['model used', 'number of model parameters',
                'dimension', 'list of parameters determined', ''])
    assert_frame_equal(ast1.lsp, lsp1)
    assert_frame_equal(ast2.lsp, lsp2)

    ngr1 = pd.DataFrame([[0.0, -2.90058798774592e-04]], index=['NGR'],
                        columns=['Area-to-mass ratio in m^2/ton',
                        'Yarkovsky parameter in 1E-10au/day^2'])
    ngr2 = pd.DataFrame([[3.92228537753657E-01, -5.47745799289690E-02]],
                        index=['NGR'],
                        columns=['Area-to-mass ratio in m^2/ton',
                        'Yarkovsky parameter in 1E-10au/day^2'])
    assert_frame_equal(ast1.ngr, ngr1)
    assert_frame_equal(ast2.ngr, ngr2)
    # Check keplerian orbit properties
    keplerian_columns = ['a', 'e', 'i', 'long. node',
                         'arg. peric.', 'mean anomaly']
    kep = pd.DataFrame([[9.2269886736945861e-01, 0.191432363588237,
                         3.338871063790, 203.965677120949,
                         126.590200404569, 333.246586621592]],
                         index=['KEP'], columns=keplerian_columns)
    assert_frame_equal(ast1.kep, kep)
    assert ast1.perihelion  == 7.4606444230873448e-01
    assert ast1.aphelion    == 1.0993332924301829e+00
    assert ast1.anode       == 1.73325574027631523e-04
    assert ast1.dnode       == -1.9943018007442770e-01
    assert ast1.moid        == 5.0131935660823443e-05
    assert ast1.period      == 3.2373407064637291e+02
    assert ast1.pha         == 'T'
    assert ast1.vinfty      == 5.4765991101528
    assert ast1.u_par       == 0.0
    assert ast1.orb_type    == 'Aten'
    matrix_idx = ['a', 'e', 'i', 'long. node', 'arg. peric', 'M',
                  'Yarkovsky parameter']
    cov = pd.DataFrame([[ 7.333454e-21, -1.072918e-19, -4.176672e-18,
                          9.884855e-17, -1.661416e-16,  6.524001e-17,  1.597276e-16],
                        [-1.072918e-19,  2.019718e-18,  7.453443e-17,
                         -2.218919e-15,  3.445852e-15, -1.246500e-15, -1.955611e-15],
                        [-4.176672e-18,  7.453443e-17,  2.560049e-14,
                         -1.198457e-12,  1.308002e-12, -1.641254e-13, -2.361241e-13],
                        [ 9.884855e-17, -2.218919e-15, -1.198457e-12,
                          6.206716e-11, -6.634024e-11,  7.109227e-12,  1.033311e-11],
                        [-1.661416e-16,  3.445852e-15,  1.308002e-12,
                         -6.634024e-11,  7.155222e-11, -8.205136e-12, -1.199513e-11],
                        [ 6.524001e-17, -1.246500e-15, -1.641254e-13,
                          7.109227e-12, -8.205136e-12,  1.397697e-12,  2.027096e-12],
                        [ 1.597276e-16, -1.955611e-15, -2.361241e-13,
                          1.033311e-11, -1.199513e-11,  2.027096e-12,  5.549616e-12]],
                        index=matrix_idx, columns=matrix_idx)
    cor = pd.DataFrame([[ 1.000000, -0.881591, -0.304826,  0.146516,
                         -0.229357,  0.644397,  0.791761],
                        [-0.881591,  1.000000,  0.327784, -0.198182,
                          0.286642, -0.741892, -0.584125],
                        [-0.304826,  0.327784,  1.000000, -0.950752,
                          0.966435, -0.867651, -0.626448],
                        [ 0.146516, -0.198182, -0.950752,  1.000000,
                         -0.995485,  0.763282,  0.556761],
                        [-0.229357,  0.286642,  0.966435, -0.995485,
                          1.000000, -0.820479, -0.601952],
                        [ 0.644397, -0.741892, -0.867651,  0.763282,
                         -0.820479,  1.000000,  0.727841],
                        [ 0.791761, -0.584125, -0.626448,  0.556761,
                         -0.601952,  0.727841,  1.000000]],
                        index=matrix_idx, columns=matrix_idx)
    assert_frame_equal(ast1.cov, cov)
    assert_frame_equal(ast1.cor, cor)
    # Check equinoctial orbit properties
    equinoctial_columns = ['a', 'e*sin(LP)', 'e*cos(LP)',
                         'tan(i/2)*sin(LN)','tan(i/2)*cos(LN)',
                         'mean long.']
    equ = pd.DataFrame([[1.0617101378986786e+00, -0.025818703424772,
                        -0.044587885274639, -0.010590108706158,
                        -0.003183567935651, 328.342445924295]],
                        index=['EQU'], columns=equinoctial_columns)
    assert_frame_equal(ast2.equinoctial, equ)

    eig_wea_name = ['a', 'e*sin(LP)', 'e*cos(LP)', 'tan(i/2)*sin(LN)',
                    'tan(i/2)*cos(LN)', 'mean long.',
                    'Area-to-mass ratio', 'Yarkovsky parameter']
    eig = pd.DataFrame([[8.12187e-13, 9.91506e-11, 1.14077e-09,
                         3.23655e-09, 1.10120e-08, 2.43064e-04,
                         1.12416e-03, 3.84141e-02]],
                        index=['EIG'], columns=eig_wea_name)
    wea = pd.DataFrame([[0.00000, -0.00000, -0.00000, 0.00000,
                         0.00000, -0.00861, 0.99969, 0.02321]],
                        index=['WEA'], columns=eig_wea_name)
    assert_frame_equal(ast2.eig, eig)
    assert_frame_equal(ast2.wea, wea)

    cov_equ = pd.DataFrame([[9.045991e-15, -4.310036e-15, -3.623923e-15,  7.951277e-16,
                             2.433447e-16, -4.077556e-11,  1.856604e-09,  1.127419e-10],
                           [-4.310036e-15,  2.852694e-15,  1.695013e-15, -5.107617e-16,
                            -1.582486e-16,  2.134254e-11, -8.850409e-10, -3.395062e-11],
                           [-3.623923e-15,  1.695013e-15,  2.002430e-15, -3.168327e-16,
                            -9.416270e-17,  1.919931e-11, -1.458006e-09, -5.214811e-11],
                           [ 7.951277e-16, -5.107617e-16, -3.168327e-16,  1.218404e-16,
                             4.220573e-17, -3.756840e-12,  1.121701e-10,  5.572020e-12],
                           [ 2.433447e-16, -1.582486e-16, -9.416270e-17,  4.220573e-17,
                             1.540961e-17, -1.111871e-12,  2.171817e-11,  1.460839e-12],
                           [-4.077556e-11,  2.134254e-11,  1.919931e-11, -3.756840e-12,
                            -1.111871e-12,  2.057036e-07, -1.270112e-05, -5.031737e-07],
                           [ 1.856604e-09, -8.850409e-10, -1.458006e-09,  1.121701e-10,
                             2.171817e-11, -1.270112e-05,  1.474738e-03,  3.420817e-05],
                           [ 1.127419e-10, -3.395062e-11, -5.214811e-11,  5.572020e-12,
                             1.460839e-12, -5.031737e-07,  3.420817e-05,  2.020746e-06]],
                            index=eig_wea_name, columns=eig_wea_name)
    assert_frame_equal(ast2.cov, cov_equ)
    nor = pd.DataFrame([[1.510392e+24,  3.010614e+22, -2.847190e+22, -3.923755e+22,
                         7.119194e+22,  3.165996e+20,  1.559455e+18, -3.200500e+19],
                       [ 3.010614e+22,  6.121981e+20, -5.623474e+20, -7.986576e+20,
                         1.446145e+21,  6.307818e+18,  3.107870e+16, -6.382017e+17],
                       [-2.847190e+22, -5.623474e+20,  5.389508e+20,  7.325948e+20,
                        -1.330387e+21, -5.969337e+18, -2.939908e+16,  6.032061e+17],
                       [-3.923755e+22, -7.986576e+20,  7.325948e+20,  1.042952e+21,
                        -1.888458e+21, -8.220830e+18, -4.050471e+16,  8.317909e+17],
                       [ 7.119194e+22,  1.446145e+21, -1.330387e+21, -1.888458e+21,
                         3.420540e+21,  1.491642e+19,  7.349240e+16, -1.509124e+18],
                       [ 3.165996e+20,  6.307818e+18, -5.969337e+18, -8.220830e+18,
                         1.491642e+19,  6.636445e+16,  3.268853e+14, -6.708642e+15],
                       [ 1.559455e+18,  3.107870e+16, -2.939908e+16, -4.050471e+16,
                         7.349240e+16,  3.268853e+14,  1.610115e+12, -3.304453e+13],
                       [-3.200500e+19, -6.382017e+17,  6.032061e+17,  8.317909e+17,
                        -1.509124e+18, -6.708642e+15, -3.304453e+13,  6.781869e+14]],
                        index=eig_wea_name, columns=eig_wea_name)
    assert_frame_equal(ast2.nor, nor)


def test_tabs_ephemerides(patch_get):
    """Check data: asteroid ephemerides tab
    """
    list_neas = {
            '99942'          : ['500', '2019-05-08 01:30',
                                '2019-05-23 00:00', '1', 'days',
                                '500 - Geocentric',
                                '2019/05/08 01:30 UTC',
                                '2019/05/23 00:00 UTC', '1 days',
                                (15, 26)],
            '516976 2012HM1' : ['J75', '2020-09-01 00:00',
                                '2020-09-02 00:00', '5', 'hours',
                                'J75 - OAM Observatory, La Sagra',
                                '2020/09/01 00:00 UTC',
                                '2020/09/02 00:00 UTC', '5 hours',
                                (5, 26)]
            }

    # Assert blank file
    with pytest.raises(KeyError):
        neocc.query_object(name='foo', tab='ephemerides',
                           observatory='500', start='2021-10-01 00:00',
                           stop='2021-10-01 00:00',
                           step='1', step_unit='days')
    # Assert KeyError in case some kwargs is missing
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='ephemerides')
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='ephemerides',
                           observatory='500', stop='2021-10-01 00:00',
                           step='1', step_unit='days')
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='ephemerides',
                           observatory='500', start='2021-10-01 00:00',
                           step='1', step_unit='days')
    with pytest.raises(KeyError):
        neocc.query_object(name='99942', tab='ephemerides',
                           observatory='500', start='2021-10-01 00:00',
                           stop='2021-10-02 00:00', step_unit='days')
    with pytest.raises(KeyError):
        neocc.query_object(name='516976 2012HM1', tab='ephemerides',
                           observatory='500', start='2021-10-01 00:00',
                           stop='2021-10-02 00:00', step='2')
    for asteroid in list_neas:
        eph = neocc.query_object(name=asteroid, tab='ephemerides',
                                 observatory=list_neas[asteroid][0],
                                 start=list_neas[asteroid][1],
                                 stop=list_neas[asteroid][2],
                                 step=list_neas[asteroid][3],
                                 step_unit=list_neas[asteroid][4])
        dict_attributes = {
            'observatory'   : str,
            'tinit'         : str,
            'tfinal'        : str,
            'tstep'         : str,
            'ephemerides'   : pd.DataFrame
            }
        for attribute in dict_attributes:
            # Check attributes exist and their type
            assert hasattr(eph, attribute)
            # Add type str in tuple for those objects whose
            # observations are strings
            assert isinstance(getattr(eph, attribute),
                              dict_attributes[attribute])
            # Check values are the same from stored data
            assert eph.observatory == list_neas[asteroid][5]
            assert eph.tinit == list_neas[asteroid][6]
            assert eph.tfinal == list_neas[asteroid][7]
            assert eph.tstep == list_neas[asteroid][8]
            # Assert there are always optical observations and its size
            assert not eph.ephemerides.empty
            assert eph.ephemerides.shape == list_neas[asteroid][9]
            # Check column names
            # Rename columns
            ephem_columns = ['Date', 'MJD in UTC', 'RA h',
                             'RA m', 'RA s', 'DEC d', 'DEC \'',
                             'DEC "', 'Mag', 'Alt (deg)', 'Airmass',
                             'Sun elev. (deg)', 'SolEl (deg)',
                             'LunEl (deg)', 'Phase (deg)',
                             'Glat (deg)','Glon (deg)', 'R (au)',
                             'Delta (au)', 'Ra*cosDE ("/min)',
                             'DEC ("/min)', 'Vel ("/min)', 'PA (deg)',
                             'Err1 (")', 'Err2 (")', 'AngAx (deg)']
            assert (eph.ephemerides.columns == ephem_columns).all()
            # Assert columns data types
            # Floats
            float_cols = ['MJD in UTC', 'RA s', 'DEC "', 'Mag',
                          'Alt (deg)', 'Airmass', 'Sun elev. (deg)',
                          'SolEl (deg)', 'LunEl (deg)', 'Phase (deg)',
                          'Glat (deg)', 'Glon (deg)', 'R (au)',
                          'Delta (au)', 'Ra*cosDE ("/min)',
                          'DEC ("/min)', 'PA (deg)', 'Err1 (")',
                          'Err2 (")', 'AngAx (deg)']
            assert all(ptypes.is_float_dtype(eph.ephemerides[cols1])
                for cols1 in float_cols)
            # Int
            int_cols = ['RA h', 'RA m', 'DEC d', "DEC '"]
            assert all(ptypes.is_int64_dtype(eph.ephemerides[cols1])
                for cols1 in int_cols)
            # Datetime
            assert ptypes.is_datetime64_ns_dtype(eph.\
                ephemerides['Date'])
    # Assert fields in ephemerides DataFrame
    eph_test = {'Date'  : '2020-09-01 20:00:00',
                'MJD in UTC'   : 59093.833333,
                'RA h'  : 9, 'RA m' : 44, 'RA s' : 16.758,
                'DEC d' : 8, 'DEC \'' : 3, 'DEC "' : 5.95,
                'Mag'   : 26.65, 'Alt (deg)' : -26.3,
                'Airmass' : float('INF'),
                'Sun elev. (deg)' : -16.0, 'SolEl (deg)'  : 14.9,
                'LunEl (deg)'   : -165.4, 'Phase (deg)' : 5.7,
                'Glat (deg)'    : 41.9, 'Glon (deg)'    : 227.3,
                'R (au)'        : 2.6, 'Delta (au)'     : 3.562,
                'Ra*cosDE ("/min)'  : 0.9614, 'DEC ("/min)' : -0.33,
                'Vel ("/min)' : 1.0164, 'PA (deg)' : 108.9,
                'Err1 (")' : 0.014, 'Err2 (")' : 0.008,
                'AngAx (deg)' : 113.4}
    df_eph_test = pd.Series(eph_test)
    df_eph_test['Date'] = pd.to_datetime(df_eph_test['Date'])
    eph = neocc.query_object(name='516976 2012HM1',
                             tab='ephemerides',
                             observatory='J75',
                             start='2020-09-01 00:00',
                             stop='2020-09-02 00:00',
                             step='5', step_unit='hours')
    assert_series_equal(eph.ephemerides.iloc[4],
                         df_eph_test, check_names=False)

    df_eph_test2 = {'Date'  : '2019-05-12 01:30:00',
                'MJD in UTC'   : 58615.0625,
                'RA h'  : 6, 'RA m' : 58, 'RA s' : 15.428,
                'DEC d' : 20, 'DEC \'' : 35, 'DEC "' : 9.86,
                'Mag'   : 21.59, 'Alt (deg)' : 0.0,
                'Airmass' : float('INF'),
                'Sun elev. (deg)' : 0.0, 'SolEl (deg)'  : -52.9,
                'LunEl (deg)'   : 37.6, 'Phase (deg)'   : 47.1,
                'Glat (deg)'    : 10.7, 'Glon (deg)'    : 195.1,
                'R (au)'        : 1.099, 'Delta (au)'   : 1.358,
                'Ra*cosDE ("/min)'  : 2.1221, 'DEC ("/min)' : -0.1475,
                'Vel ("/min)' : 2.1273, 'PA (deg)' : 94.0,
                'Err1 (")' : 0.001, 'Err2 (")' : 0.0,
                'AngAx (deg)' : 122.9}
    df_eph_test2 = pd.Series(df_eph_test2)
    df_eph_test2['Date'] = pd.to_datetime(df_eph_test2['Date'])
    eph2 = neocc.query_object(name='99942', tab='ephemerides',
                              observatory='500',
                              start='2019-05-08 01:30',
                              stop='2019-05-23 00:00',
                              step='1', step_unit='days')
    assert_series_equal(eph2.ephemerides.iloc[4],
                         df_eph_test2, check_names=False)
