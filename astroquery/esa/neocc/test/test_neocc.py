# -*- coding: utf-8 -*-
"""
This module contains all the monkeypatch tests. The data for these
tests is gathered in data folder and contains the information
of different lists and object information from ESA NEOCC portal.
"""

import os
import re
import pytest
import warnings

import numpy as np
import requests

from astropy.table import Table
from astropy.time import Time, TimeDelta

from astroquery.utils.mocks import MockResponse

from astroquery.esa import neocc

# Import BASE URL and TIMEOUT
API_URL = neocc.conf.API_URL
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
TIMEOUT = neocc.conf.TIMEOUT
VERIFICATION = neocc.conf.SSL_CERT_VERIFICATION


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

    # Split name (the requested url) to obtain the name of the file location stored in \data

    fileloc = name.split(r'=')[1]

    # Exception for ephemerides
    if '&oc' in fileloc:
        fileloc = fileloc.split(r'&')[0] + '.eph'

    filename = data_path(fileloc)
    with open(filename, 'rb') as FLE:
        content = FLE.read()
        content = content.replace(b"\r", b"")  # For windows tests

    return MockResponse(content)


def test_bad_list_names():
    """
    Check errors from invalid names
    """

    # Invalid inputs
    bad_names = ["ASedfe", "%&$", "ÁftR+", 154]
    foo_data = []

    # Assert for invalid names
    for elements in bad_names:
        with pytest.raises(KeyError):
            neocc.lists.get_list_url(elements)
        with pytest.raises(KeyError):
            neocc.lists.parse_list(elements, foo_data)


def check_table_structure(data_table, table_len, table_cols, float_cols=[], int_cols=[], str_cols=[], time_cols=[]):
    """
    Given a data table, checks:
    - Table length matches given table_len
    - Table column names match the given table_cols list
    - All the columns with indices given in float_cols are of float type
    - Equivalent checks for int_cols, and string_cols
    - Checks that columns with indices given in time_cols are `~astropy.time.Time` objects
    """

    table_cols = np.array(table_cols)

    assert len(data_table) == table_len
    assert len(data_table.columns) == len(table_cols)

    assert all([x == y for x, y in zip(data_table.colnames, table_cols)])

    # Ignore the FutureWarning that only comes up with the oldest dependencies
    warnings.filterwarnings("ignore", category=FutureWarning,
                            message="Conversion of the second argument of issubdtype*")
    assert all([np.issubdtype(data_table[x].dtype, float) for x in table_cols[float_cols]])
    assert all([np.issubdtype(data_table[x].dtype, int) for x in table_cols[int_cols]])
    assert all([np.issubdtype(data_table[x].dtype, str) for x in table_cols[str_cols]])

    assert all([isinstance(data_table[x], Time) for x in table_cols[time_cols]])


def check_table_values(data_table, true_value_dict):
    """
    Checks data_table rows against true values given in true_value_dict.
    The format of true_value_dict is {<row number>: [true row data], ...}
    """

    for row, values in true_value_dict.items():

        assert all([x == y if not isinstance(x, np.ma.core.MaskedConstant) else y == "masked"
                    for x, y in zip(data_table[row].values(), values)])


def test_parse_nea(patch_get):
    """
    Check data: nea_list, updated_nea and monthly_update
    """

    # NEA list, Updated NEA list and monthly update
    nea_list = neocc.neocc.query_list('nea_list')
    updated_nea = neocc.neocc.query_list('updated_nea')
    monthly_update = neocc.neocc.query_list('monthly_update')

    # Assert is a pandas Series
    assert isinstance(nea_list, Table)
    assert isinstance(updated_nea, Table)
    assert isinstance(monthly_update, Table)

    # Assert is not empty
    assert len(nea_list)
    assert len(updated_nea)
    assert len(monthly_update)

    # Check size of the files
    assert len(nea_list) == 26844
    assert len(updated_nea) == 3366
    assert len(monthly_update) == 1

    # Check some elements of the lists NEA list
    first_neas = Table(names=["NEA"],
                       data=[['433 Eros', '719 Albert', '887 Alinda',
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
                              '3122 Florence', '3199 Nefertiti']])

    assert (nea_list[:40]["NEA"] == first_neas["NEA"]).all()
    assert nea_list["NEA"][-1] == '6344P-L'

    # Updated NEA
    first_update = Table(names=["NEA"],
                         data=[['Mon Oct 04 06:30:08 UTC 2021',
                                '2021SF4', '2021SK4', '2021SL4',
                                '2021TK', '2021TL', '2021TM', '2021TN',
                                '2021TO', '2021TQ']])

    assert (updated_nea[:10]["NEA"] == first_update["NEA"]).all()
    assert updated_nea["NEA"][-1] == '2019UE2'

    # Monthly update
    assert monthly_update["NEA"][0] == 'Tue Aug 24 06:21:13 UTC 2021'
    # Check date format DDD MMM DD HH:MM:SS UTC YYYY
    assert re.match(r'\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \w{3} \d{4}', monthly_update["NEA"][0])


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
def test_parse_risk(patch_get):
    """Check data: risk_list, risk_list_special

    Ignore ERFA 'dubious year' warnings because they are expected.
    """
    # Risk and risk special lists
    risk_list = neocc.neocc.query_list("risk_list")
    risk_list_special = neocc.neocc.query_list("risk_list_special")

    # Assert is aastropy Table
    assert isinstance(risk_list, Table)
    assert isinstance(risk_list_special, Table)

    risk_columns = ['Object Name', 'Diameter in m', '*=Y', 'Date/Time', 'IP max', 'PS max', 'TS',
                    'Vel in km/s', 'First Year', 'Last Year', 'IP cum', 'PS cum']
    risk_special_columns = risk_columns[0:8]

    check_table_structure(risk_list, 1216, risk_columns, float_cols=[1, 4, 5, 7, -2, -1],
                          int_cols=[6, 8, 9], str_cols=[0, 2], time_cols=[3])
    check_table_structure(risk_list_special, 2, risk_special_columns, float_cols=[4, 5, 7],
                          int_cols=[1, 6], str_cols=[0, 2], time_cols=[3])

    # Check first, last and random mid element
    risk_dict = {}
    risk_dict[0] = ['2021QM1', 50.0, '*', Time('2052-04-02 01:36:00'),
                    0.000298, -2.72, 0, 23.72, 2050, 2054, 0.000298, -2.72]
    risk_dict[-1] = ['2021KQ2', 4.0, '*', Time('2097-05-21 03:05:00'), 1.26e-11,
                     -13.71, 0, 11.42, 2097, 2097, 1.26e-11, -13.71]
    risk_dict[608] = ['2013BR15', 30.0, '*', Time('2100-01-02 18:03:00'), 1.21e-07,
                      -7.15, 0, 17.98, 2100, 2100, 1.6e-07, -7.03]
    check_table_values(risk_list, risk_dict)


def test_parse_clo(patch_get):
    """Check data: close_approaches_upcoming, close_approaches_recent
    """

    # Close approaches upcoming and recent lists
    close_appr_upcoming = neocc.neocc.query_list("close_approaches_upcoming")
    close_appr_recent = neocc.neocc.query_list("close_approaches_recent")

    # Assert is an astropy Table
    assert isinstance(close_appr_upcoming, Table)
    assert isinstance(close_appr_recent, Table)

    close_columns = ['Object Name', 'Date', 'Miss Distance in km', 'Miss Distance in au',
                     'Miss Distance in LD', 'Diameter in m', '*=Yes', 'H', 'Max Bright',
                     'Rel. vel in km/s', 'CAI index']
    check_table_structure(close_appr_upcoming, 174, close_columns, float_cols=[3, 4, 5, 7, 8, 9, 10],
                          int_cols=[2], str_cols=[0, 6], time_cols=[1])
    check_table_structure(close_appr_recent, 60, close_columns, float_cols=[3, 4, 5, 7, 8, 9, 10],
                          int_cols=[2], str_cols=[0, 6], time_cols=[1])

    # Check first, last and random mid element
    # Close approaches upcoming
    closeup_dict = {}
    closeup_dict[0] = ['2023OW4', Time('2023-08-03 00:00:00.000'), 565277,
                       0.003779, 1.471, 10.0, '*', 27.8, 18.1, 9.7, 2.464]
    closeup_dict[-1] = ['2020PN1', Time('2024-08-02 00:00:00.000'), 6893507,
                        0.04608, 17.933, 29.0, '*', 25.5, 21.6, 5.5, 2.775]
    closeup_dict[80] = ['2010XF3', Time('2023-12-11 00:00:00.000'), 7377915,
                        0.049318, 19.193, 50.0, '*', 24.3, 19.1, 4.0, 1.828]
    check_table_values(close_appr_upcoming, closeup_dict)

    # Close approaches recent
    closere_dict = {}
    closere_dict[0] = ['2023OY4', Time('2023-08-02 00:00:00.000'), 1219027,
                       0.008149, 3.171, 30.0, '*', 25.4, 18.1, 17.6, 1.794]
    closere_dict[-1] = ['2023NG1', Time('2023-07-03 00:00:00.000'), 705381,
                        0.004715, 1.835, 20.0, '*', 26.3, 17.6, 3.8, 1.071]
    closere_dict[40] = ['2023OZ', Time('2023-07-13 00:00:00.000'), 2868022,
                        0.019172, 7.461, 19.0, '*', 26.3, 19.0, 5.9, 2.633]
    check_table_values(close_appr_recent, closere_dict)


def test_parse_pri(patch_get):
    """Check data: priority_list, priority_list_faint
    """

    # Priority list and priority faint list
    priority_list = neocc.neocc.query_list("priority_list")
    faint_list = neocc.neocc.query_list("priority_list_faint")

    # Assert is an astropy Table
    assert isinstance(priority_list, Table)
    assert isinstance(faint_list, Table)

    priority_columns = ['Priority', 'Object', 'R.A. in arcsec', 'Decl. in deg',
                        'Elong. in deg', 'V in mag', 'Sky uncert.', 'End of Visibility']
    check_table_structure(priority_list, 176, priority_columns,
                          float_cols=[2, 3, 5], int_cols=[0, 4, 6], str_cols=[1], time_cols=[-1])
    check_table_structure(faint_list, 734, priority_columns,
                          float_cols=[2, 3, 5], int_cols=[0, 4, 6], str_cols=[1], time_cols=[-1])

    # Assert tables are not empty and have the right dimension
    assert len(priority_list) == 176
    assert len(priority_list.columns) == 8

    assert len(faint_list) == 734
    assert len(faint_list.columns) == 8

    # Check first, last and random mid element
    # Priority list
    priority_dict = {}
    priority_dict[0] = [0, '2013GM8', 5880.0, 35.7, 146, 21.3, 62144, Time('2021-11-16 00:00:00')]
    priority_dict[-1] = [3, '2021NN50', 71880.0, -11.8, 108, 21.2, 0, Time('2021-11-20 00:00:00')]
    priority_dict[87] = [1, '2021SY2', 10560.0, 6.0, 146, 20.1, 3, Time('2021-10-22 00:00:00')]
    check_table_values(priority_list, priority_dict)

    # Priority faint list
    faint_dict = {}
    faint_dict[0] = [0, '2012BD77', 13800.0, -36.0, 120, 24.7, 1251, Time('2021-12-26 00:00:00')]
    faint_dict[-1] = [1, '2021SX3', 83340.0, -6.3, 155, 22.2, 1, Time('2021-12-12 00:00:00')]
    faint_dict[338] = [0, '2019UO10', 84960.0, -37.9, 135, 24.9, 9185, Time('2021-10-13 00:00:00')]
    check_table_values(faint_list, faint_dict)


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
def test_parse_encounter(patch_get):
    """Check data: encounter_list

    Ignore ERFA 'dubious year' warnings because they are expected.
    """

    encounter_list = neocc.neocc.query_list("close_encounter")

    # Assert is an astropy Table
    assert isinstance(encounter_list, Table)

    encounter_columns = ['Name/desig', 'Planet', 'Date', 'Time approach', 'Time uncert',
                         'Distance', 'Minimum distance', 'Distance uncertainty', 'Width',
                         'Stretch', 'Probability', 'Velocity', 'Max Mag']
    check_table_structure(encounter_list, 4770, encounter_columns,
                          float_cols=slice(3, None), str_cols=[0, 1], time_cols=[2])

    encounter_dict = {}
    encounter_dict[0] = ['433', 'EARTH', Time('1975-01-23T07:38:40.992'), 42435.31853255,
                         1.260737144e-05, 0.151134153855255, 0.1511340949471563, 1.962635286041312e-08,
                         1.322e-08, 6.103e-08, 1.0, 5.82530834, 7.445]
    encounter_dict[-1] = ['2002MX', 'EARTH', Time('2002-06-12T02:00:30.816'), 52437.083685526,
                          0.0002355862863, 0.04148563561205888, 0.04128486992493158, 6.692189692154938e-05,
                          2.634e-07, 6.692e-05, 1.0, 25.57598245, 17.59]
    mid_time = Time.strptime("2054/01/11", '%Y/%m/%d') + TimeDelta(.31202, format="jd")
    encounter_dict[2000] = ['2000AA6', 'EARTH', mid_time, 71278.312017212,
                            4.189937108e-05, 0.03820285368375039, 0.03820063181644156, 7.40623369935997e-07,
                            3.635e-08, 7.571e-07, 1.0, 17.16618231, 18.213]

    check_table_values(encounter_list, encounter_dict)


def test_parse_impacts(patch_get):
    """Check data: impacted objects list
    """

    impact_list = neocc.neocc.query_list("impacted_objects")

    # Assert is a astropy.table.Table
    assert isinstance(impact_list, Table)

    column_names = ['Object designator', 'Diameter in m', 'Impact date/time in UTC',
                    'Impact Velocity in km/s', 'Estimated energy in Mt', 'Measured energy in Mt']
    check_table_structure(impact_list, 5, column_names,
                          float_cols=slice(3, None), str_cols=[0, 1], time_cols=[2])

    impact_dict = {}
    impact_dict[0] = ['2022EB5', '1.9*', Time('2022-03-11 21:22:00'), 18.53, 2.96E-4, 4.00E-3]
    impact_dict[1] = ['2019MO', '5*', Time('2019-06-22 21:30:00'), 16.34, 3.82E-3, 6.00E-3]
    impact_dict[2] = ['2018LA', '2.8*', Time('2018-06-02 16:44:00'), 16.98, 8.90E-4, 9.80E-4]
    impact_dict[4] = ['2008TC3', '3*', Time('2008-10-07 02:45:00'), 11.77, 6.77E-4, 1.00E-3]
    check_table_values(impact_list, impact_dict)


def test_parse_catalogues(patch_get):
    """Check data: encounter_list
    """

    cat_current = neocc.neocc.query_list("neo_catalogue_current")
    cat_middle = neocc.neocc.query_list("neo_catalogue_middle")

    assert isinstance(cat_current, Table)
    assert isinstance(cat_middle, Table)

    cat_columns = ['Name', 'Epoch (MJD)', 'a', 'e', 'i', 'long. node', 'arg. peric.', 'mean anomaly',
                   'absolute magnitude', 'slope param.', 'non-grav param.']

    check_table_structure(cat_current, 27104, cat_columns, float_cols=slice(1, 10), str_cols=[0], int_cols=[-1])
    check_table_structure(cat_middle, 27104, cat_columns, float_cols=slice(1, 10), str_cols=[0], int_cols=[-1])

    # Check first, last and random mid element
    cat_dict = {}
    cat_dict[0] = ['433', 59600.000000, 1.4582731004919933E+00, 2.2272733518842894E-01, 1.0828461192253641E+01,
                   3.0429635501527531E+02, 1.7889716943295548E+02, 2.4690411844800099E+02, 10.85, 0.46, 0]
    cat_dict[-1] = ['6344P-L', 59400.000000, 2.8202277078203988E+00, 6.6155999676965871E-01, 4.6786111836540556E+00,
                    1.8282300248385891E+02, 2.3494660190063559E+02, 3.2386152408344321E+02, 20.40, 0.15, 0]
    cat_dict[12488] = ['2015GZ', 59400.000000, 2.8059248663363574E+00, 7.1777101854979719E-01, 1.3504485380561094E+01,
                       1.9799756552626015E+01, 1.1456930451775614E+02, 1.2828981992766344E+02, 26.06, 0.15, 0]
    check_table_values(cat_current, cat_dict)


def check_tab_result_basic(results, num_tabs):
    assert isinstance(results, list)
    assert len(results) == num_tabs


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
def test_tabs_impacts(patch_get):
    """Check data: asteroid impacts tab

    Ignore ERFA 'dubious year' warnings because they are expected.
    """

    # 433 Eros has no tab "impacts"
    with pytest.raises(ValueError):
        neocc.neocc.query_object(name="433", tab='impacts')

    meta_keys = ['Column Info', 'observation_accepted', 'observation_rejected', 'arc_start',
                 'arc_end', 'info', 'computation', 'additional_note']
    impact_columns = ['date', 'MJD', 'sigma', 'sigimp', 'dist', 'width', 'stretch', 'p_RE',
                      'Exp. Energy in MT', 'PS', 'TS']

    # Asteroid 1979XB
    impact_tab_list = neocc.neocc.query_object(name='1979XB', tab='impacts')
    check_tab_result_basic(impact_tab_list, 1)

    impact_table = impact_tab_list[0]

    for key in meta_keys[:-1]:
        assert key in impact_table.meta.keys()

    arc_tmes = [Time.strptime("1979/12/11", '%Y/%m/%d') + TimeDelta(.511, format="jd"),
                Time.strptime("1979/12/15", '%Y/%m/%d') + TimeDelta(.430, format="jd")]
    impact_meta = {'observation_accepted': 18,
                   'observation_rejected': 0,
                   'arc_start': arc_tmes[0],
                   'arc_end': arc_tmes[1],
                   'computation': '20190808 162907.255 CET'}

    for key, value in impact_meta.items():
        assert impact_table.meta[key] == value

    check_table_structure(impact_table, 8, impact_columns, float_cols=slice(1, 10), int_cols=[-1], time_cols=[0])
    impact_dict = {}
    row_time = Time.strptime("2101-12-14", '%Y-%m-%d') + TimeDelta(.203, format="jd")
    impact_dict[3] = [row_time, 88781.204, -0.384, 0.0, 0.61,
                      0.089, 194000000.0, 3.48e-09, 0.000131, -5.36, 0]
    check_table_values(impact_table, impact_dict)


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
def test_tabs_close_approach(patch_get):
    """Check data: asteroid close approaches tab

    Ignore ERFA 'dubious year' warnings because they are expected.
    """

    # Check opbject with no close approaches
    result_lst = neocc.neocc.query_object(name='594938 2021GE13', tab='close_approaches')
    check_tab_result_basic(result_lst, 1)

    close_tab = result_lst[0]
    assert isinstance(close_tab, Table)
    assert len(close_tab) == 0

    close_columns = ['BODY', 'CALENDAR-TIME', 'MJD-TIME', 'TIME-UNCERT.', 'NOM.-DISTANCE',
                     'MIN.-POSS.-DIST.', 'DIST.-UNCERT.', 'STRETCH', 'WIDTH', 'PROBABILITY']

    # 433
    result_lst = neocc.neocc.query_object(name="433", tab='close_approaches')
    check_tab_result_basic(result_lst, 1)

    close_tab = result_lst[0]
    check_table_structure(close_tab, 5, close_columns, float_cols=slice(2, None), str_cols=[0], time_cols=[1])

    close_dict = {}
    row_time = Time.strptime("2093/01/31", '%Y/%m/%d') + TimeDelta(.65750, format="jd")
    close_dict[3] = ['EARTH', row_time, 85543.657499489, 1.572619005e-05, 0.1824638321371326,
                     0.1824638180864916, 4.954403653193194e-08, 9.921e-08, 1.612e-08, 1.0]
    check_table_values(close_tab, close_dict)

    # 99942
    result_lst = neocc.neocc.query_object(name="99942", tab='close_approaches')
    check_tab_result_basic(result_lst, 1)

    close_tab = result_lst[0]
    check_table_structure(close_tab, 26, close_columns, float_cols=slice(2, None), str_cols=[0], time_cols=[1])

    close_dict = {}
    row_time = Time.strptime("1972/12/24", '%Y/%m/%d') + TimeDelta(.49470, format="jd")
    close_dict[3] = ['EARTH', row_time, 41675.494697571, 0.004521177247, 0.07923789245024694,
                     0.07920056098848807, 1.244155168249903e-05, 1.584e-05, 4.645e-09, 1.0]
    check_table_values(close_tab, close_dict)


def test_tabs_physical_properties(patch_get):
    """Check data: physical properties tab
    """

    # Check value error if empty
    with pytest.raises(ValueError):
        neocc.neocc.query_object(name='frfre', tab='physical_properties')

    props_cols = ['Property', 'Value', 'Units', 'Reference Name', 'Reference Additional']

    # 99942
    result_lst = neocc.neocc.query_object(name='99942', tab='physical_properties')
    check_tab_result_basic(result_lst, 1)

    phys_props = result_lst[0]
    check_table_structure(phys_props, 21, props_cols, str_cols=[0, 1, 2, 3, 4])

    phys_dict = {}
    phys_dict[1] = ['Absolute Magnitude (H)', '18.937', 'mag', 'ESA ODIM',
                    'ESA orbit determination and impact monitoring system']
    phys_dict[5] = ['Color Index Information', '0.362', 'R-I', 'EARN',
                    ('1.) Lin, C-H. et al. (2018) P&SS 152, 116-135. (Photometric survey and taxonomic '
                     'identifications of 92 near-Earth asteroids)')]
    phys_dict[14] = ['Slope Parameter (G)', '0.15**', 'mag', 'ESA ODIM',
                     'ESA orbit determination and impact monitoring system']
    check_table_values(phys_props, phys_dict)

    # 1994CJ1
    result_lst = neocc.neocc.query_object(name='1994CJ1', tab='physical_properties')
    check_tab_result_basic(result_lst, 1)

    phys_props = result_lst[0]
    check_table_structure(phys_props, 12, props_cols, str_cols=[0, 1, 2, 3, 4])

    phys_dict = {}
    phys_dict[0] = ['Absolute Magnitude (H)', '21.539', 'mag', 'ESA ODIM',
                    'ESA orbit determination and impact monitoring system']
    phys_dict[2] = ['Diameter', '170*', 'm', 'Estimation', 'Estimated from absolute magnitude']
    phys_dict[8] = ['Slope Parameter (G)', '0.15**', 'mag', 'ESA ODIM',
                    'ESA orbit determination and impact monitoring system']
    check_table_values(phys_props, phys_dict)


@pytest.mark.filterwarnings('ignore:ERFA function *:erfa.core.ErfaWarning')
def test_tabs_observations(patch_get):
    """Check data: asteroid observations tab

    Ignore ERFA 'dubious year' warnings because they are expected.
    """

    with pytest.raises(ValueError):
        neocc.neocc.query_object(name='FOO', tab='observations')

    meta_cols = ['version', 'errmod', 'RMSast', 'RMSmag']
    opt_obs_cols = ['Design.', 'K', 'T', 'N', 'Date', 'Date Accuracy', 'RA', 'RA Accuracy', 'RA RMS', 'RA F',
                    'RA Bias', 'RA Resid', 'DEC', 'DEC Accuracy', 'DEC RMS', 'DEC F', 'DEC Bias', 'DEC Resid',
                    'MAG Val', 'MAG B', 'MAG RMS', 'MAG Resid', 'Ast Cat', 'Obs Code', 'Chi', 'A', 'M']
    sat_obs_cols = ['Design.', 'K', 'T', 'N', 'Date', 'Parallax info.', 'X', 'Y', 'Z', 'Obs Code']
    rov_obs_cols = ['Design.', 'K', 'T', 'N', 'Date', 'E longitude', 'Latitude', 'Altitude', 'Obs Code']
    radar_obs_cols = ['Design', 'K', 'T', 'N', 'Datetime', 'Measure', 'Accuracy', 'rms', 'F', 'Bias', 'Resid',
                      'TRX', 'RCX', 'Chi', 'S']

    # 433
    result_lst = neocc.neocc.query_object(name='433', tab='observations')
    check_tab_result_basic(result_lst, 4)

    meta_tab, opt_obs, sat_obs, rad_obs = result_lst

    assert list(meta_tab.meta.keys()) == ['Title', 'Column Info']
    assert meta_tab.meta["Title"] == 'Observation metadata'
    check_table_structure(meta_tab, 1, meta_cols, float_cols=[0, 2, 3], str_cols=[1])
    meta_dict = {0: [3.0, 'vfcc17', 0.332005, 0.477458]}
    check_table_values(meta_tab, meta_dict)

    assert list(opt_obs.meta.keys()) == ['Title', 'Column Info']
    assert opt_obs.meta["Title"] == 'Optical Observations'
    check_table_structure(opt_obs, 13680, opt_obs_cols, float_cols=[5, 7, 8, 11, 13, 14, 16, 17, 18, 20, 21, 24],
                          int_cols=[0, 25, 26], str_cols=[1, 2, 3, 6, 9, 10, 12, 15, 19, 22, 23], time_cols=[4])

    assert list(sat_obs.meta.keys()) == ['Title']
    assert sat_obs.meta["Title"] == 'Satellite  Observations'
    check_table_structure(sat_obs, 1772, sat_obs_cols, float_cols=[6, 7, 8], int_cols=[0, 3, 5], str_cols=[1, 2, 9],
                          time_cols=[4])

    assert list(rad_obs.meta.keys()) == ['Title', 'Column Info']
    assert rad_obs.meta["Title"] == 'Radar Observations'
    check_table_structure(rad_obs, 6, radar_obs_cols, float_cols=[5, 6, 7, 9, 10, 13], int_cols=[0, 3, 11, 12, 14],
                          str_cols=[1, 2, 8], time_cols=[4])

    # 1685
    result_lst = neocc.neocc.query_object(name='1685', tab='observations')
    check_tab_result_basic(result_lst, 5)

    meta_tab, opt_obs, sat_obs, rov_obs, rad_obs = result_lst

    assert list(meta_tab.meta.keys()) == ['Title', 'Column Info']
    assert meta_tab.meta["Title"] == 'Observation metadata'
    check_table_structure(meta_tab, 1, meta_cols, float_cols=[0, 2, 3], str_cols=[1])
    meta_dict = {0: [3.0, 'vfcc17', 0.356997, 0.417766]}
    check_table_values(meta_tab, meta_dict)

    assert list(opt_obs.meta.keys()) == ['Title', 'Column Info']
    assert opt_obs.meta["Title"] == 'Optical Observations'

    check_table_structure(opt_obs, 4468, opt_obs_cols, float_cols=[5, 7, 8, 11, 13, 14, 16, 17, 18, 20, 21, 24],
                          int_cols=[0, 25, 26], str_cols=[1, 2, 3, 6, 9, 10, 12, 15, 19, 22, 23], time_cols=[4])
    row_time = Time.strptime("1999/04/20", '%Y/%m/%d') + TimeDelta(.458706, format="jd")
    opt_dict = {290: [1685, 'O', 'C', '2', row_time, 1e-06, '17:25:59.714', 0.01261, 0.5, 'F', '0.000', -0.296,
                      '-32:45:54.61', 0.01, 0.5, 'F', 0.0, -0.062, 17.05, 'V', 0.5, -0.12, 'l', '689', 0.61, 1, 1]}
    check_table_values(opt_obs, opt_dict)

    assert list(sat_obs.meta.keys()) == ['Title']
    assert sat_obs.meta["Title"] == 'Satellite  Observations'
    check_table_structure(sat_obs, 664, sat_obs_cols, float_cols=[6, 7, 8], int_cols=[0, 3, 5], str_cols=[1, 2, 9],
                          time_cols=[4])
    row_time = Time.strptime("2010/02/11", '%Y/%m/%d') + TimeDelta(.95325, format="jd")
    sat_dict = {4: [1685, 'S', 's', 'masked', row_time, 1, -4304.3019, -4326.899999999999, -3247.9272, 'C51']}
    check_table_values(sat_obs, sat_dict)

    assert list(rov_obs.meta.keys()) == ['Title']
    assert rov_obs.meta["Title"] == 'Roving Observer  Observations'
    check_table_structure(rov_obs, 5, rov_obs_cols, float_cols=[5, 6, 7], int_cols=[0, 8], str_cols=[1, 2],
                          time_cols=[4])
    row_time = Time.strptime("2008/02/14", '%Y/%m/%d') + TimeDelta(.30053, format="jd")
    rov_dict = {0: [1685, 'O', 'v', 'masked', row_time, 237.818, 37.8191, 470.0, 247]}
    check_table_values(rov_obs, rov_dict)

    assert list(rad_obs.meta.keys()) == ['Title', 'Column Info']
    assert rad_obs.meta["Title"] == 'Radar Observations'
    check_table_structure(rad_obs, 9, radar_obs_cols, float_cols=[5, 6, 7, 9, 10, 13], int_cols=[0, 3, 11, 12, 14],
                          str_cols=[1, 2, 8], time_cols=[4])
    rad_dict = {4: [1685, 'R', 's', 'masked', Time('1988-07-24T07:35:00.000'), 31263444.2679, 2.99792,
                    2.99792, 'F', 0.0, 0.08916, -1, -1, 0.05, 1]}
    check_table_values(rad_obs, rad_dict)

    # 2016YC8
    result_lst = neocc.neocc.query_object(name='2016YC8', tab='observations')
    check_tab_result_basic(result_lst, 4)

    meta_tab, opt_obs, sat_obs, rad_obs = result_lst

    assert list(meta_tab.meta.keys()) == ['Title', 'Column Info']
    assert meta_tab.meta["Title"] == 'Observation metadata'
    check_table_structure(meta_tab, 1, meta_cols, float_cols=[0, 2, 3], str_cols=[1])
    meta_dict = {0: [3.0, 'vfcc17', 0.491024, 0.364713]}
    check_table_values(meta_tab, meta_dict)

    assert list(opt_obs.meta.keys()) == ['Title', 'Column Info']
    assert opt_obs.meta["Title"] == 'Optical Observations'
    check_table_structure(opt_obs, 86, opt_obs_cols, float_cols=[5, 7, 8, 10, 11, 13, 14, 16, 17, 18, 20, 21, 24],
                          int_cols=[25, 26], str_cols=[0, 1, 2, 3, 6, 9, 12, 15, 19, 22, 23], time_cols=[4])

    assert list(sat_obs.meta.keys()) == ['Title']
    assert sat_obs.meta["Title"] == 'Satellite  Observations'
    check_table_structure(sat_obs, 2, sat_obs_cols, float_cols=[6, 7, 8], int_cols=[3, 5], str_cols=[0, 1, 2, 9],
                          time_cols=[4])

    assert list(rad_obs.meta.keys()) == ['Title', 'Column Info']
    assert rad_obs.meta["Title"] == 'Radar Observations'
    check_table_structure(rad_obs, 2, radar_obs_cols, float_cols=[5, 6, 7, 9, 10, 13], int_cols=[3, 11, 12, 14],
                          str_cols=[0, 1, 2, 8], time_cols=[4])

    # 2020BX12
    result_lst = neocc.neocc.query_object(name='2020BX12', tab='observations')
    check_tab_result_basic(result_lst, 4)

    meta_tab, opt_obs, sat_obs, rad_obs = result_lst

    assert list(meta_tab.meta.keys()) == ['Title', 'Column Info']
    assert meta_tab.meta["Title"] == 'Observation metadata'
    check_table_structure(meta_tab, 1, meta_cols, float_cols=[0, 2, 3], str_cols=[1])
    meta_dict = {0: [3.0, 'vfcc17', 0.59903, 0.371435]}
    check_table_values(meta_tab, meta_dict)

    assert list(opt_obs.meta.keys()) == ['Title', 'Column Info']
    assert opt_obs.meta["Title"] == 'Optical Observations'
    check_table_structure(opt_obs, 164, opt_obs_cols, float_cols=[5, 7, 8, 10, 11, 13, 14, 16, 17, 18, 20, 21, 24],
                          int_cols=[25, 26], str_cols=[0, 1, 2, 3, 6, 9, 12, 15, 19, 22, 23], time_cols=[4])

    assert list(sat_obs.meta.keys()) == ['Title']
    assert sat_obs.meta["Title"] == 'Satellite  Observations'
    check_table_structure(sat_obs, 4, sat_obs_cols, float_cols=[6, 7, 8], int_cols=[3, 5], str_cols=[0, 1, 2, 9],
                          time_cols=[4])

    assert list(rad_obs.meta.keys()) == ['Title', 'Column Info']
    assert rad_obs.meta["Title"] == 'Radar Observations'
    check_table_structure(rad_obs, 2, radar_obs_cols, float_cols=[5, 6, 7, 9, 10, 13], int_cols=[3, 11, 12, 14],
                          str_cols=[0, 1, 2, 8], time_cols=[4])

    # 1979XB
    result_lst = neocc.neocc.query_object(name='1979XB', tab='observations')
    check_tab_result_basic(result_lst, 2)

    meta_tab, opt_obs = result_lst

    assert list(meta_tab.meta.keys()) == ['Title', 'Column Info']
    assert meta_tab.meta["Title"] == 'Observation metadata'
    check_table_structure(meta_tab, 1, meta_cols[:-1], float_cols=[0, 2], str_cols=[1])
    meta_dict = {0: [3.0, 'vfcc17', 0.449806]}
    check_table_values(meta_tab, meta_dict)

    assert list(opt_obs.meta.keys()) == ['Title', 'Column Info']
    assert opt_obs.meta["Title"] == 'Optical Observations'
    check_table_structure(opt_obs, 18, opt_obs_cols, float_cols=[5, 7, 8, 10, 11, 13, 14, 16, 17, 20, 21, 24],
                          int_cols=[25, 26], str_cols=[0, 1, 2, 6, 9, 12, 15], time_cols=[4])


def check_keplarian_elements(elt_tab):

    secs = ['Keplerian elements', "RMS"]
    props = ['PERIHELION', 'APHELION', 'ANODE', 'DNODE', 'MOID', 'PERIOD', 'PHA', 'VINFTY', 'U_PAR', 'ORB_TYPE']

    assert all([x in elt_tab['Section'] for x in secs])
    assert all([x in elt_tab['Property'] for x in props])


def test_tabs_kep_orbit_properties(patch_get):
    """Check data: asteroid orbit properties tab
    """

    # Assert blank file
    with pytest.raises(ValueError):
        neocc.neocc.query_object(name='foo', tab='orbit_properties',
                                 orbital_elements='keplerian', orbit_epoch='middle')

    # Assert KeyError in case some kwargs is missing
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='orbit_properties', orbital_elements='keplerian')

    elt_cols = ['Section', 'Property', 'Value']
    mat_cols = ['a', 'e', 'i', 'long. node', 'arg. peric.', 'mean anomaly']
    amr = ["Area-to-mass ratio [m^2/t]"]
    yp = ["Yarkovsky parameter [1E-10 au/day^2]"]

    # 433
    result_lst = neocc.neocc.query_object(name='433', tab='orbit_properties',
                                          orbital_elements="keplerian", orbit_epoch="middle")
    check_tab_result_basic(result_lst, 3)

    elements, cov, cor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 30, elt_cols, str_cols=[0, 1, 2])
    check_keplarian_elements(elements)

    check_table_structure(cov, 6, ["COV"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols)])

    check_table_structure(cor, 6, ["COR"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cor["COR"], mat_cols)])

    # 99942
    result_lst = neocc.neocc.query_object(name='99942', tab='orbit_properties',
                                          orbital_elements="keplerian", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, cor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 34, elt_cols, str_cols=[0, 1, 2])
    check_keplarian_elements(elements)

    elt_dict = {}
    elt_dict[1] = ['APHELION', 'APHELION', '1.0993332924301829E+00']
    elt_dict[5] = ['HEADER', 'refsys', 'ECLM J2000']
    elt_dict[8] = ['Keplerian elements', 'i', '3.338871063790']
    elt_dict[13] = ['MJD', '59400.000000000', 'MJD']
    elt_dict[15] = ['Non-gravitational parameters', 'model used', '1']
    elt_dict[23] = ['RMS', 'a', '8.56356E-11']
    elt_dict[-1] = ['dynamical parameters', 'Yarkovsky parameter [1E-10 au/day^2]', '-2.90058798774592E-04']
    check_table_values(elements, elt_dict)

    check_table_structure(cov, 7, ["COV"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+yp)])

    cov_arr = np.array([[7.33345e-21, -1.07291e-19, -4.17667e-18, 9.88485e-17,
                         -1.66141e-16, 6.52400e-17, 1.59727e-16],
                        [-1.07291e-19, 2.01971e-18, 7.45344e-17, -2.21891e-15,
                         3.44585e-15, -1.24650e-15, -1.95561e-15],
                        [-4.17667e-18, 7.45344e-17, 2.56004e-14, -1.19845e-12,
                         1.30800e-12, -1.64125e-13, -2.36124e-13],
                        [9.88485e-17, -2.21891e-15, -1.19845e-12, 6.20671e-11,
                         -6.63402e-11, 7.10922e-12, 1.03331e-11],
                        [-1.66141e-16, 3.44585e-15, 1.30800e-12, -6.63402e-11,
                         7.15522e-11, -8.20513e-12, -1.19951e-11],
                        [6.52400e-17, -1.24650e-15, -1.64125e-13, 7.10922e-12,
                         -8.20513e-12, 1.39769e-12, 2.02709e-12],
                        [1.59727e-16, -1.95561e-15, -2.36124e-13, 1.03331e-11,
                         -1.19951e-11, 2.02709e-12, 5.54961e-12]])
    assert np.isclose(np.array(cov[mat_cols+yp].as_array().tolist()), cov_arr, atol=0, rtol=1e-5).all()

    check_table_structure(cor, 7, ["COR"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cor["COR"], mat_cols+yp)])

    cor_arr = np.array([[1.000000, -0.881591, -0.304826, 0.146516, -0.229357, 0.644397, 0.791761],
                        [-0.881591, 1.000000, 0.327784, -0.198182, 0.286642, -0.741892, -0.584125],
                        [-0.304826, 0.327784, 1.000000, -0.950752, 0.966435, -0.867651, -0.626448],
                        [0.146516, -0.198182, -0.950752, 1.000000, -0.995485, 0.763282, 0.556761],
                        [-0.229357, 0.286642, 0.966435, -0.995485, 1.000000, -0.820479, -0.601952],
                        [0.644397, -0.741892, -0.867651, 0.763282, -0.820479, 1.000000, 0.727841],
                        [0.791761, -0.584125, -0.626448, 0.556761, -0.601952, 0.727841, 1.000000]])
    assert np.isclose(np.array(cor[mat_cols+yp].as_array().tolist()), cor_arr, atol=0, rtol=1e-5).all()

    # 99942 modif
    result_lst = neocc.neocc.query_object(name='99942 modif', tab='orbit_properties',
                                          orbital_elements="keplerian", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, cor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 34, elt_cols, str_cols=[0, 1, 2])
    check_keplarian_elements(elements)

    check_table_structure(cov, 7, ["COV"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+yp)])

    check_table_structure(cor, 7, ["COR"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cor["COR"], mat_cols+yp)])

    # 2009BD
    result_lst = neocc.neocc.query_object(name='2009BD', tab='orbit_properties',
                                          orbital_elements="keplerian", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, cor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 35, elt_cols, str_cols=[0, 1, 2])
    check_keplarian_elements(elements)

    check_table_structure(cov, 8, ["COV"]+mat_cols+amr+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+amr+yp)])

    check_table_structure(cor, 8, ["COR"]+mat_cols+amr+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cor["COR"], mat_cols+amr+yp)])

    # 594938 2021GE13
    result_lst = neocc.neocc.query_object(name='594938 2021GE13', tab='orbit_properties',
                                          orbital_elements="keplerian", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, cor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 30, elt_cols, str_cols=[0, 1, 2])
    check_keplarian_elements(elements)

    check_table_structure(cov, 6, ["COV"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols)])

    check_table_structure(cor, 6, ["COR"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cor["COR"], mat_cols)])


def check_equinoctial_elements(elt_tab):
    secs = ["Equinoctial elements", "RMS", "EIG", "WEA"]
    assert all([x in elt_tab['Section'] for x in secs])


def test_tabs_equi_orbit_properties(patch_get):
    """Check data: asteroid orbit properties tab
    """

    # Assert blank file
    with pytest.raises(ValueError):
        neocc.neocc.query_object(name='foo', tab='orbit_properties',
                                 orbital_elements='equinoctial', orbit_epoch='middle')
    # Assert KeyError in case some kwargs is missing
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='orbit_properties')
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='orbit_properties', orbit_epoch='middle')

    elt_cols = ['Section', 'Property', 'Value']
    mat_cols = ['a', 'e*sin(LP)', 'e*cos(LP)', 'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)', 'mean long.']
    amr = ["Area-to-mass ratio [m^2/t]"]
    yp = ["Yarkovsky parameter [1E-10 au/day^2]"]

    # 433
    result_lst = neocc.neocc.query_object(name='433', tab='orbit_properties',
                                          orbital_elements="equinoctial", orbit_epoch="middle")
    check_tab_result_basic(result_lst, 3)

    elements, cov, nor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 32, elt_cols, str_cols=[0, 1, 2])
    check_equinoctial_elements(elements)

    check_table_structure(cov, 6, ["COV"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols)])

    check_table_structure(nor, 6, ["NOR"]+mat_cols, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(nor["NOR"], mat_cols)])

    # 99942
    result_lst = neocc.neocc.query_object(name='99942', tab='orbit_properties',
                                          orbital_elements="equinoctial", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, nor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 38, elt_cols, str_cols=[0, 1, 2])
    check_equinoctial_elements(elements)

    check_table_structure(cov, 7, ["COV"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+yp)])

    check_table_structure(nor, 7, ["NOR"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(nor["NOR"], mat_cols+yp)])

    # 99942 modif
    result_lst = neocc.neocc.query_object(name='99942 modif', tab='orbit_properties',
                                          orbital_elements="equinoctial", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, nor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 38, elt_cols, str_cols=[0, 1, 2])
    check_equinoctial_elements(elements)

    check_table_structure(cov, 7, ["COV"]+mat_cols+amr, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+amr)])

    check_table_structure(nor, 7, ["NOR"]+mat_cols+amr, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(nor["NOR"], mat_cols+amr)])

    # 2009BD
    result_lst = neocc.neocc.query_object(name='2009BD', tab='orbit_properties',
                                          orbital_elements="equinoctial", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, nor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 41, elt_cols, str_cols=[0, 1, 2])
    check_equinoctial_elements(elements)

    elt_dict = {}
    elt_dict[0] = ['EIG', 'a', '8.12187E-13']
    elt_dict[8] = ['Equinoctial elements', 'a', '1.0617101378986786E+00']
    elt_dict[14] = ['HEADER', 'format', 'OEF2.0']
    elt_dict[20] = ['Non-gravitational parameters', 'number of model parameters', '2']
    elt_dict[28] = ['RMS', 'mean long.', '4.53546E-04']
    elt_dict[31] = ['WEA', 'a', '0.00000']
    elt_dict[39] = ['dynamical parameters', 'Area-to-mass ratio [m^2/t]', '3.92228537753657E-01']
    check_table_values(elements, elt_dict)

    check_table_structure(cov, 8, ["COV"]+mat_cols+amr+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+amr+yp)])

    cov_arr = np.array([[9.04599e-15, -4.31003e-15, -3.62392e-15, 7.95127e-16,
                         2.43344e-16, -4.07755e-11, 1.85660e-09, 1.12741e-10],
                        [-4.31003e-15, 2.85269e-15, 1.69501e-15, -5.10761e-16,
                         -1.58248e-16, 2.13425e-11, -8.85040e-10, -3.39506e-11],
                        [-3.62392e-15, 1.69501e-15, 2.00243e-15, -3.16832e-16,
                         -9.41627e-17, 1.91993e-11, -1.45800e-09, -5.21481e-11],
                        [7.95127e-16, -5.10761e-16, -3.16832e-16, 1.21840e-16,
                         4.22057e-17, -3.75684e-12, 1.12170e-10, 5.57202e-12],
                        [2.43344e-16, -1.58248e-16, -9.41627e-17, 4.22057e-17,
                         1.54096e-17, -1.11187e-12, 2.17181e-11, 1.46083e-12],
                        [-4.07755e-11, 2.13425e-11, 1.91993e-11, -3.75684e-12,
                         -1.11187e-12, 2.05703e-07, -1.27011e-05, -5.03173e-07],
                        [1.85660e-09, -8.85040e-10, -1.45800e-09, 1.12170e-10,
                         2.17181e-11, -1.27011e-05, 1.47473e-03, 3.42081e-05],
                        [1.12741e-10, -3.39506e-11, -5.21481e-11, 5.57202e-12,
                         1.46083e-12, -5.03173e-07, 3.42081e-05, 2.02074e-06]])
    assert np.isclose(np.array(cov[mat_cols+amr+yp].as_array().tolist()), cov_arr, atol=0, rtol=1e-5).all()

    check_table_structure(nor, 8, ["NOR"]+mat_cols+amr+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(nor["NOR"], mat_cols+amr+yp)])

    nor_arr = np.array([[1.510392e+24, 3.010614e+22, -2.847190e+22, -3.923755e+22,
                         7.119194e+22, 3.165996e+20, 1.559455e+18, -3.200500e+19],
                        [3.010614e+22, 6.121981e+20, -5.623474e+20, -7.986576e+20,
                         1.446145e+21, 6.307818e+18, 3.107870e+16, -6.382017e+17],
                        [-2.847190e+22, -5.623474e+20, 5.389508e+20, 7.325948e+20,
                         -1.330387e+21, -5.969337e+18, -2.939908e+16, 6.032061e+17],
                        [-3.923755e+22, -7.986576e+20, 7.325948e+20, 1.042952e+21,
                         -1.888458e+21, -8.220830e+18, -4.050471e+16, 8.317909e+17],
                        [7.119194e+22, 1.446145e+21, -1.330387e+21, -1.888458e+21,
                         3.420540e+21, 1.491642e+19, 7.349240e+16, -1.509124e+18],
                        [3.165996e+20, 6.307818e+18, -5.969337e+18, -8.220830e+18,
                         1.491642e+19, 6.636445e+16, 3.268853e+14, -6.708642e+15],
                        [1.559455e+18, 3.107870e+16, -2.939908e+16, -4.050471e+16,
                         7.349240e+16, 3.268853e+14, 1.610115e+12, -3.304453e+13],
                        [-3.200500e+19, -6.382017e+17, 6.032061e+17, 8.317909e+17,
                         -1.509124e+18, -6.708642e+15, -3.304453e+13, 6.781869e+14]])
    assert np.isclose(np.array(nor[mat_cols+amr+yp].as_array().tolist()), nor_arr, atol=0, rtol=1e-5).all()

    # 594938 2021GE13
    result_lst = neocc.neocc.query_object(name='99942', tab='orbit_properties',
                                          orbital_elements="equinoctial", orbit_epoch="present")
    check_tab_result_basic(result_lst, 3)

    elements, cov, nor = result_lst
    assert elements.meta["Title"] == 'Orbital Elements'
    check_table_structure(elements, 38, elt_cols, str_cols=[0, 1, 2])
    check_equinoctial_elements(elements)

    check_table_structure(cov, 7, ["COV"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(cov["COV"], mat_cols+yp)])

    check_table_structure(nor, 7, ["NOR"]+mat_cols+yp, str_cols=[0], float_cols=slice(1, None))
    all([x == y for x, y in zip(nor["NOR"], mat_cols+yp)])


def test_tabs_ephemerides(patch_get):
    """Check data: asteroid ephemerides tab
    """

    # Assert blank file
    with pytest.raises(ValueError):
        neocc.neocc.query_object(name='foo', tab='ephemerides', observatory='500', start='2021-10-01 00:00',
                                 stop='2021-10-01 00:00', step='1', step_unit='days')
    # Assert KeyError in case some kwargs is missing
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='ephemerides')
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='ephemerides',
                                 observatory='500', stop='2021-10-01 00:00',
                                 step='1', step_unit='days')
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='ephemerides',
                                 observatory='500', start='2021-10-01 00:00',
                                 step='1', step_unit='days')
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='99942', tab='ephemerides',
                                 observatory='500', start='2021-10-01 00:00',
                                 stop='2021-10-02 00:00', step_unit='days')
    with pytest.raises(KeyError):
        neocc.neocc.query_object(name='516976 2012HM1', tab='ephemerides',
                                 observatory='500', start='2021-10-01 00:00',
                                 stop='2021-10-02 00:00', step='2')

    ephem_columns = ['Date', 'MJD (UTC)', 'RA (h  m  s)', 'DEC (d  \'  ")', 'Mag', 'Alt (deg)', 'Airmass',
                     'Sun elev. (deg)', 'SolEl (deg)', 'LunEl (deg)', 'Phase (deg)', 'Glat (deg)',
                     'Glon (deg)', 'R (au)', 'Delta (au)', 'RA*cosDE ("/min)', 'DEC ("/min)',
                     'Vel ("/min)', 'PA (deg)', 'Err1 (")', 'Err2 (")', 'AngAx (deg)']

    # 99942
    eph_lst = neocc.neocc.query_object(name='99942', tab='ephemerides', observatory='500',
                                       start='2019-05-08 01:30', stop='2019-05-23 00:00',
                                       step='1', step_unit='days')
    assert len(eph_lst) == 1

    eph = eph_lst[0]

    # Checking the metadata
    assert eph.meta['Observatory'] == '500 - Geocentric'
    assert eph.meta['Initial Date'] == '2019/05/08 01:30 UTC'
    assert eph.meta['Final Date'] == '2019/05/23 00:00 UTC'
    assert eph.meta['Time step'] == '1 days'

    # Checking the table
    check_table_structure(eph, 15, ephem_columns, str_cols=[2, 3], time_cols=[0],
                          float_cols=[1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
    eph_dict = {4: [Time('2019-05-12T01:30:00.000'), 58615.0625, '6 58 15.428', '+20 35  9.86', 21.59, 0.0,
                    np.inf, 0.0, -52.9, 37.6, 47.1, 10.7, 195.1, 1.099, 1.358, 2.1221, -0.1475, 2.1273, 94.0,
                    0.001, 0.0, 122.9]}
    check_table_values(eph, eph_dict)

    # 516976 2012HM1
    eph_lst = neocc.neocc.query_object(name='516976 2012HM1', tab='ephemerides', observatory='J75',
                                       start='2020-09-01 00:00', stop='2020-09-02 00:00',
                                       step='5', step_unit='hours')
    assert len(eph_lst) == 1

    eph = eph_lst[0]

    # Checking the metadata
    assert eph.meta['Observatory'] == 'J75 - OAM Observatory, La Sagra'
    assert eph.meta['Initial Date'] == '2020/09/01 00:00 UTC'
    assert eph.meta['Final Date'] == '2020/09/02 00:00 UTC'
    assert eph.meta['Time step'] == '5 hours'

    # Checking the table
    check_table_structure(eph, 5, ephem_columns, str_cols=[2, 3], time_cols=[0],
                          float_cols=[1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21])
    eph_dict = {0: [Time('2020-09-01T00:00:00.000'), 59093.0, '9 42 59.688', '+ 8  9 39.70', 26.64, -42.6,
                    np.inf, -43.8, 14.5, 169.8, 5.6, 41.6, 226.9, 2.603, 3.568, 0.9632, -0.327, 1.0172, 108.7,
                    0.014, 0.008, 113.3]}
    check_table_values(eph, eph_dict)
