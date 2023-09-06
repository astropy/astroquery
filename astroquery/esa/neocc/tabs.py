"""
This module contains all the methods required to request the data from
a particular object, obtain it from the ESA NEOCC portal and parse it
to show it properly. The information of the object is shows in the
ESA NEOCC in different tabs that correspond to the different classes
within this module.
"""

import logging
import time
import re
import requests
from bs4 import BeautifulSoup

import numpy as np

from astropy.table import Table, Column, join, vstack
from astropy.time import Time

from astroquery.esa.neocc import conf
from astroquery.esa.neocc.utils import convert_time

# Import URLs and TIMEOUT
API_URL = conf.API_URL
EPHEM_URL = conf.EPHEM_URL
SUMMARY_URL = conf.SUMMARY_URL
TIMEOUT = conf.TIMEOUT
VERIFICATION = conf.SSL_CERT_VERIFICATION


def get_object_url(name, tab, **kwargs):
    """Get url from requested object and tab name.

    Parameters
    ----------
    name : str
        Name of the requested object.
    tab : str
        Name of the requested table. Valid names are: *summary,
        orbit_properties, physical_properties, observations,
        ephemerides, close_approaches and impacts*.
    **kwargs : str
        orbit_properties and ephemerides tabs require additional arguments:

        * *orbit_properties*: the required additional arguments are:

            * *orbital_elements* : str (keplerian or equinoctial)
            * *orbit_epoch* : str (present or middle)

        * *ephemerides*: the required additional arguments are:

            * *observatory* : str (observatory code, e.g. '500', 'J04', etc.)
            * *start* : str (start date in YYYY-MM-DD HH:MM)
            * *stop* : str (end date in YYYY-MM-DD HH:MM)
            * *step* : str (time step, e.g. '2', '15', etc.)
            * *step_unit* : str (e.g. 'days', 'minutes', etc.)

    Returns
    -------
    url : string
        Final url from which data is requested.

    Raises
    ------
    KeyError
        If the requested tab is not in the dictionary.
    ValueError
        If the elements requested are not valid.
    """
    # Define the parameters of each list
    tab_dict = {"impacts": '.risk',
                "close_approaches": '.clolin',
                "physical_properties": '.phypro',
                "observations": '.rwo',
                "orbit_properties": ['.ke0', '.ke1', '.eq0', '.eq1']}

    # Raise error is input is not in dictionary
    if tab not in tab_dict:
        raise KeyError('Valid list names are impacts, close_approaches'
                       ' observations and orbit_properties')

    # Check if orbital_elements is an input
    if 'orbital_elements' in kwargs:
        # Check if the elements are Keplerian or Equinoctial
        if kwargs['orbital_elements'] == "keplerian":
            # Check if the epoch is present day or middle obs. arch
            if kwargs['orbit_epoch'] == "present":
                url = str(name).replace(' ', '%20') + tab_dict[tab][1]
            elif kwargs['orbit_epoch'] == "middle":
                url = str(name).replace(' ', '%20') + tab_dict[tab][0]
        elif kwargs['orbital_elements'] == "equinoctial":
            if kwargs['orbit_epoch'] == "present":
                url = str(name).replace(' ', '%20') + tab_dict[tab][3]
            elif kwargs['orbit_epoch'] == "middle":
                url = str(name).replace(' ', '%20') + tab_dict[tab][2]
        else:
            raise ValueError('The introduced file type does not exist.'
                             'Check that orbit elements (keplerian or '
                             'equinoctial) and orbit epoch (present or '
                             'middle).')
    else:
        url = str(name).replace(' ', '%20') + tab_dict[tab]

    return url


def get_object_data(url):
    """Get object in byte format from requested url.

    Parameters
    ----------
    url : str
        URL of the requested data.

    Returns
    -------
    data_obj : object
        Object in byte format.
    """
    # Get data from URL
    data_obj = requests.get(API_URL + url, timeout=TIMEOUT, verify=VERIFICATION).content

    return data_obj


def get_ephemerides_data(name, observatory, start, stop, step, step_unit):
    """
    Get ephemerides data object in byte format from given arguments.
    """

    # Unique base url for asteroid properties
    url_ephe = EPHEM_URL + str(name).replace(' ', '%20') +\
        '&oc=' + str(observatory) + '&t0=' +\
        str(start).replace(' ', 'T') + 'Z&t1=' +\
        str(stop).replace(' ', 'T') + 'Z&ti=' + str(step) +\
        '&tiu=' + str(step_unit)

    # Request data two times if the first attempt fails
    try:
        # Get object data
        data_obj = requests.get(url_ephe, timeout=TIMEOUT,
                                verify=VERIFICATION).content

    except ConnectionError:  # pragma: no cover
        print('Initial attempt to obtain object data failed. '
              'Reattempting...')
        logging.warning('Initial attempt to obtain object data'
                        'failed.')
        # Wait 5 seconds
        time.sleep(5)
        # Get object data
        data_obj = requests.get(url_ephe, timeout=TIMEOUT,
                                verify=VERIFICATION).content

    # Check if file contains errors due to bad URL keys
    resp_str = data_obj.decode('utf-8')
    if "[ERROR]" in resp_str:
        raise KeyError(resp_str)

    return resp_str


def get_summary_data(name):
    """
    Get the summary info html page for a given object.
    """

    url = SUMMARY_URL + str(name).replace(' ', '%20')

    contents = requests.get(url, timeout=TIMEOUT, verify=VERIFICATION).content

    return contents.decode('utf-8')


def parse_impacts(resp_str):
    """
    Parse impact table response string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : list(`astropy.table.Table`)
        The response table, with all the extra info in the meta dictionary.
    """

    # Make sure there is actually data for this object
    if "Required risk file is not available for this object" in resp_str:
        raise ValueError('Required risk file is not available for this object')

    # Split the response into parts to more easily work with.
    resp_lst = resp_str.split("\n\n")

    # Build the main data table
    impact_tble = Table.read(resp_lst[1], format='ascii', data_start=3,
                             names=["date", "MJD", "sigma", "sigimp", "dist", "+/-", "width",
                                    "stretch", "p_RE", "Exp. Energy in MT", "PS", "TS"])
    impact_tble.remove_column("+/-")
    impact_tble['date'] = convert_time(impact_tble['date'])

    # Add the column info to the meta table
    impact_tble.meta["Column Info"] = {'Date': 'date for the potential impact in datetime format',
                                       'MJD': 'Modified Julian Day for the potential impact',
                                       'sigma': 'approximate location along the Line Of Variation (LOV) in sigma space',
                                       'sigimp': ('The lateral distance in sigma-space from the LOV to the Earth '
                                                  'surface. A zero implies that the LOV passes through the Earth'),
                                       'dist': ('Minimum Distance in Earth radii. The lateral distance from the LOV '
                                                'to the center of the Earth'),
                                       'width': ('one-sigma semi-width of the Target Plane confidence region '
                                                 'in Earth radii'),
                                       'stretch': ('Stretching factor. It indicates how much the confidence region '
                                                   'at the epoch has been stretched by the time of the approach. '
                                                   'This is a close cousin of the Lyapounov exponent. Units are in '
                                                   'Earth radii divided by sigma (RE/sig)'),
                                       'p_RE': 'probability of Earth Impact (IP)',
                                       'Exp. Energy in MT': ('Expected energy. It is the product of the impact energy '
                                                             'and the impact probability'),
                                       'PS': 'Palermo Scale',
                                       'TS': 'Torino Scale'}

    # Adding the rest of the metadata from the remaining resp_lst entries
    regex = re.search((r"(\d+) optical observations.*(\d+) "
                       r"are rejected as outliers.*\nfrom (.+) to (.+)\."), resp_lst[2])
    obs_acc, obs_reg, start, end = regex.groups()

    dates = convert_time([start, end], conversion_string='%Y/%m/%d')

    impact_tble.meta["observation_accepted"] = int(obs_acc)
    impact_tble.meta["observation_rejected"] = int(obs_reg)
    impact_tble.meta["arc_start"] = dates[0]
    impact_tble.meta["arc_end"] = dates[1]

    impact_tble.meta["info"] = "/n/n".join(resp_lst[3:6])

    regex = re.search("computation=(.+)", resp_lst[6])
    impact_tble.meta["computation"] = regex.groups()[0]

    add_note = resp_lst[7].replace("\n", "")
    if add_note:
        impact_tble.meta["additional_note"] = add_note

    return impact_tble


def parse_close_aproach(resp_str):
    """
    Parse close approach response string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : Table
        The response table, with all the extra info in the meta dictionary.
    """

    # If there is nothing there, just return an empty table
    if not resp_str:
        return Table(names=['BODY', 'CALENDAR-TIME', 'MJD-TIME', 'TIME-UNCERT.', 'NOM.-DISTANCE',
                            'MIN.-POSS.-DIST.', 'DIST.-UNCERT.', 'STRETCH', 'WIDTH', 'PROBABILITY'])

    df_close_appr = Table.read(resp_str, format="ascii", header_start=1)

    df_close_appr["CALENDAR-TIME"] = convert_time(df_close_appr["CALENDAR-TIME"], conversion_string='%Y/%m/%d')

    df_close_appr.meta["Column Info"] = {'BODY': 'planet or massive asteroid is involved in the close approach',
                                         'CALENDAR-TIME': 'date of the close approach in datetime format',
                                         'MJD-TIME': 'Modified Julian Date of the approach',
                                         'TIME-UNCERT.': 'time uncertainty in MJD2000',
                                         'NOM.-DISTANCE': 'Nominal distance at the close approach in au',
                                         'MIN.-POSS.-DIST.': 'Minimum possible distance at the close approach in au',
                                         'DIST.-UNCERT.': 'distance uncertainty in au',
                                         'STRETCH': ('It indicates how much the confidence region at the epoch has '
                                                     'been stretched by the time of the approach. This is a close '
                                                     'cousin of the Lyapounov exponent. Units in au'),
                                         'WIDTH': 'width of the stretching',
                                         'PROBABITLIY': ('Close approach probability. A value of 1 indicates a '
                                                         'certain close approach')}

    return df_close_appr


def _parse_obs_meta(hdr_str):
    """
    Parse the header string for the observation tables.
    """

    mlst = hdr_str.split('\n')
    pat = re.compile(r'(\w+)\s+=\s+\'{0,1}([\w\.-]+)\'{0,1}')

    meta_dict = {}
    for ent in mlst:
        if not ent:  # Skip empty entries
            continue

        matches = pat.match(ent).groups()
        meta_dict[matches[0]] = [matches[1]]

    meta_table = Table(meta_dict)
    meta_table.meta["Title"] = "Observation metadata"
    meta_table.meta["Column Info"] = {"version": "File version",
                                      "errmod": "Error model for the data",
                                      "rmsast": "Root Mean Square for asteroid observations",
                                      "rmsmag": "Root Mean Square for magnitude"}

    # Making the columns gave the right data types
    for col in meta_table.colnames:
        if col == 'errmod':
            continue
        meta_table[col] = meta_table[col].astype(float)

    return meta_table


def _parse_opt_obs(optical_str):
    """
    Building the optical observations table.
    """

    obs_table = Table.read(optical_str, format="ascii.fixed_width_no_header",
                           col_starts=[0, 11, 13, 15, 17, 22, 25, 40, 50, 53, 56, 64, 75, 83, 87,
                                       95, 103, 106, 110, 117, 128, 136, 140, 147, 156, 161, 164,
                                       170, 177, 180, 187, 194, 196],
                           col_ends=[10, 12, 14, 16, 21, 24, 39, 49, 52, 55, 63, 74, 82, 86, 94, 102,
                                     105, 109, 116, 127, 135, 139, 146, 155, 160, 163, 169, 176, 179,
                                     186, 193, 195, 197],
                           names=['Design.', 'K', 'T', 'N', 'Date', 'MM', 'DD.ddd',
                                  'Date Accuracy', 'RA HH', 'RA MM', 'RA SS.sss', 'RA Accuracy',
                                  'RA RMS', 'RA F', 'RA Bias', 'RA Resid', 'DEC sDD', 'DEC MM',
                                  'DEC SS.ss', 'DEC Accuracy', 'DEC RMS', 'DEC F', 'DEC Bias',
                                  'DEC Resid', 'MAG Val', 'MAG B', 'MAG RMS', 'MAG Resid',
                                  'Ast Cat', 'Obs Code', 'Chi', 'A', 'M'])

    # Combining the date columns
    date_array = [f"{x}/{y}/{z}" for x, y, z in obs_table["Date", "MM", "DD.ddd"]]
    obs_table["Date"] = convert_time(date_array, conversion_string='%Y/%m/%d')
    obs_table.remove_columns(["MM", "DD.ddd"])

    # Combinging the ra/dec columns
    ra_array = [f"{x:02d}:{y:02d}:{z:02.3f}" for x, y, z in obs_table['RA HH', 'RA MM', 'RA SS.sss']]
    obs_table.replace_column('RA HH', Column(data=ra_array))
    obs_table.rename_column("RA HH", "RA")
    obs_table.remove_columns(['RA MM', 'RA SS.sss'])

    dec_array = [f"{x:02d}:{y:02d}:{z:02.2f}" for x, y, z in obs_table['DEC sDD', 'DEC MM', 'DEC SS.ss']]
    obs_table.replace_column('DEC sDD', Column(data=dec_array))
    obs_table.rename_column("DEC sDD", "DEC")
    obs_table.remove_columns(['DEC MM', 'DEC SS.ss'])

    # Adding table metadata
    obs_table.meta["Title"] = "Optical Observations"
    obs_table.meta["Column Info"] = {'Designation': 'number or the provisional designation of the asteroid.',
                                     'K, Type': ('observation type and technology provided by the MPC. '
                                                 'Note that for satellite (s) and roving (v) observations '
                                                 'there are 2 additional dataframes which contain the '
                                                 'information given by the MPC.'),
                                     'Date': 'date in UTC iso format.',
                                     'Right Ascension': ('The data provided include the observation, the a '
                                                         'priori accuracy (as supplied by the MPC), the a '
                                                         'priori RMS used for weighing, a flag indicating a '
                                                         'forced weight, the bias, and the residuals in arcsec.'),
                                     'Declination': 'same format as Right Ascension.',
                                     'Apparent magnitude': ('The columns contain the apparent magnitude as '
                                                            'reported, the a priori RMS used for weighing, and '
                                                            'the residual, all in magnitudes.'),
                                     'Quality': ('observatory code is extracted from the MPC published '
                                                 'observation, the value of chi from the chi**2 test '
                                                 '(characterization of the relative quality of the observation). '
                                                 'The "Used A" column is "Yes" if the observation is used in '
                                                 'our orbit, and "No" if it has been discarded. The same for '
                                                 'the photometry in the "Used M" column.')}

    return obs_table


def _parse_sat_obs(sat_str):
    """
    Building the satellite observations table.
    """

    sat_table = Table.read(sat_str, format="ascii.fixed_width_no_header",
                           col_starts=[0, 11, 12, 15, 17, 22, 25, 34, 40, 64, 88, 108],
                           col_ends=[10, 12, 15, 16, 21, 24, 33, 35, 59, 83, 107, 111],
                           names=['Design.', 'K', 'T', 'N', 'Date', 'MM', 'DD.dddddd',
                                  'Parallax info.', 'X', 'Y', 'Z', 'Obs Code'])

    # Combining the date column
    date_array = [f"{x}/{y}/{z}" for x, y, z in sat_table["Date", "MM", "DD.dddddd"]]
    sat_table["Date"] = convert_time(date_array, conversion_string='%Y/%m/%d')
    sat_table.remove_columns(["MM", "DD.dddddd"])

    sat_table.meta["Title"] = "Satellite  Observations"

    return sat_table


def _parse_rov_obs(rov_str):
    """
    Building the roving observer observations table.
    """

    rov_table = Table.read(rov_str, format="ascii.fixed_width_no_header",
                           col_starts=[0, 11, 13, 15, 17, 22, 25, 34, 45, 56, 65],
                           col_ends=[10, 12, 14, 16, 21, 24, 33, 44, 55, 64, 68],
                           names=['Design.', 'K', 'T', 'N', 'Date', 'MM', 'DD.dddddd',
                                  'E longitude', 'Latitude', 'Altitude', 'Obs Code'])

    # Combining the date column
    date_array = [f"{x}/{y}/{z}" for x, y, z in rov_table["Date", "MM", "DD.dddddd"]]
    rov_table["Date"] = convert_time(date_array, conversion_string='%Y/%m/%d')
    rov_table.remove_columns(["MM", "DD.dddddd"])

    rov_table.meta["Title"] = "Roving Observer  Observations"

    return rov_table


def _parse_radar_obs(radar_str):
    """
    Building the radar observations table.
    """

    radar_str = radar_str[radar_str.find('\n')+1:]  # First row is header
    radar_table = Table.read(radar_str, format="ascii.fixed_width_no_header",
                             col_starts=[0, 11, 13, 15, 17, 22, 25, 28, 37, 54, 64,
                                         73, 75, 87, 99, 106, 112, 124],
                             col_ends=[10, 12, 14, 16, 21, 24, 27, 36, 53, 63, 72,
                                       74, 86, 98, 105, 111, 123, 125],
                             names=["Design", "K", "T", "N", "Datetime", "MM", "DD",
                                    "hh:mm:ss", "Measure", "Accuracy", "rms", "F",
                                    "Bias", "Resid", "TRX", "RCX", "Chi", "S"])

    # Combining the datetime columns
    date_array = [f"{x}/{y}/{z} {t}" for x, y, z, t in radar_table["Datetime", "MM", "DD", "hh:mm:ss"]]
    radar_table["Datetime"] = Time.strptime(date_array, '%Y/%m/%d %H:%M:%S')
    radar_table.remove_columns(["MM", "DD", "hh:mm:ss"])

    # Adding metadata
    radar_table.meta["Title"] = "Radar Observations"
    radar_table.meta["Column Info"] = {'Designation': 'number or the provisional designation of the asteroid.',
                                       'K, Type': ('observation type and technology provided by the MPC. A "c" '
                                                   'indicates the radar observation is referenced to the '
                                                   'asteroid center of mass, and an "s" indicates the measurement '
                                                   'is referenced to the radar bounce point.'),
                                       'Datetime': 'date in UTC format.',
                                       'Radar range or range rate': ('refers to columns measure (km or km/day), '
                                                                     'accuracy (precision ofthe measurement), '
                                                                     'rms, F, bias and Resid.'),
                                       'Quality': ('transmit (TRX) and receive (RCX) station are given. When '
                                                   'these differ, an observation is considered as belonging to '
                                                   'the receiver station. the value of chi from the chi**2 test '
                                                   '(characterization of the relative quality of the '
                                                   'observation).The "S" column is "Yes" if the observation is '
                                                   'used in our orbit, and "No" if it has been discarded.')}

    return radar_table


def parse_observations(resp_str, verbose=False):
    """
    Parse the close approach response string into the close approach tables.

    TODO: document properly.
    Parameters
    ----------
    resp_str : str
        String containing the raw data for the tables.

    Returns
    -------
    response : list(Table)
        List of response tables.
    """

    output_tables = list()  # Setting up to collect the output tables

    # Split the meta data from the data table(s)
    header, dat_tabs = resp_str.split("END_OF_HEADER")

    # Make the metadata table
    output_tables.append(_parse_obs_meta(header))

    # Split apart the data tables (there should be one or two of them)
    # Each Table starts with two header lines of the form:
    # ! Object ...
    # ! Design ...
    table_list = dat_tabs.split("\n!")
    optical_tab = table_list[2]  # This table will always exist

    # Pulling satellite/roving observer observations out of the optical table if
    # there are any (these rows have different column structures)
    optical_tab_list = np.array(optical_tab.split("\n")[1:])  # First row is headings
    T_col = np.array([(x[12:15]).strip() for x in optical_tab_list])
    s_rows = '\n'.join(optical_tab_list[T_col == 's'])  # looking for sattelite observations
    v_rows = '\n'.join(optical_tab_list[T_col == 'v'])  # looking for roving observer observations
    optical_str = '\n'.join(optical_tab_list[(T_col != 's') & (T_col != 'v')])

    # Building the optical observation table(s)
    output_tables.append(_parse_opt_obs(optical_str))

    if s_rows:
        if verbose:
            print("Found satellite observations")

        output_tables.append(_parse_sat_obs(s_rows))

    if v_rows:
        if verbose:
            print("Found roving observer observations.")

        output_tables.append(_parse_rov_obs(v_rows))

    # Building the radar table if it exists
    if len(table_list) >= 5:
        radar_str = table_list[4]  # This table will sometimes exist
        output_tables.append(_parse_radar_obs(radar_str))

    return output_tables


def parse_physical_properties(resp_str):
    """
    Parse the physical properties response string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : Table
        The response table.
    
    """

    if resp_str == '':
        raise ValueError('Object not found: the name of the object is wrong or misspelt')

    # Split apart the table and reference data
    tbl, refs = resp_str.split("REFERENCES")

    # Some rows have multple values which we will split into different Rows
    tbl_list = tbl.split("\n")

    repaired_string = ""
    for elt in tbl_list:
        row = elt.split(",")
        if len(row) > 4:
            for i in range(1, len(row)-2):
                repaired_string += f"{row[0]},{row[i]},{row[-2]},{row[-1]}\n"
        else:
            repaired_string += elt + "\n"

    # Building the physical properties table
    phys_prop = Table.read(repaired_string, format="ascii.no_header",
                           names=('Property', 'Value', 'Units', 'Reference'))

    # Building the referenced table
    ref_list = refs.split("\n")
    search_pat = re.compile(r"(\[\d+\]),([\w\s]+),(.+)")

    numbers = list()
    names = list()
    sources = list()

    for ref in ref_list:
        if not ref:
            continue  # some extra empty rows

        num, nm, src = search_pat.search(ref).groups()
        numbers.append(num)
        names.append(nm)
        sources.append(src)

    ref_table = Table(data=[numbers, names, sources],
                      names=["Reference", "Reference Name", "Reference Additional"])

    # Joining the tables
    phys_prop = join(phys_prop, ref_table, keys='Reference')
    phys_prop.remove_column("Reference")
    phys_prop.sort("Property")

    return phys_prop


def _make_prop_table(props, vals, secname):
    """
    Given correspondong properties and values, and the section the relate to,
    build an orbital properties style table.
    """

    prop_tab = Table(names=("Property", "Value"), data=[props, vals], dtype=[str, str])
    prop_tab["Section"] = secname
    prop_tab = prop_tab["Section", "Property", "Value"]

    return prop_tab


def _fill_sym_matrix(data, dim):
    """
    Fill a symmetrical matrix from a 1D data array, given a dimension.
    """

    matrix = np.zeros((dim, dim))
    d1, d2 = np.triu_indices(dim)

    for i, val in enumerate(data):
        matrix[d1[i], d2[i]] = val
        matrix[d2[i], d1[i]] = val

    return matrix


def parse_orbital_properties(resp_str):
    """
    Parse the orbintal properties response string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : list(Table)
        List of response tables.
    """

    table_lst = list()

    header, body = resp_str.split("END_OF_HEADER")

    # Parse Header
    pat = re.compile(r'(\w+)\s+=\s+\'?([^\']+)\'?\s+!')
    props = list()
    vals = list()

    for row in header.split("\n"):
        if not row:  # Skip empty entries
            continue
        matches = pat.match(row).groups()
        props.append(matches[0])
        vals.append(matches[1].strip())

    table_lst.append(_make_prop_table(props, vals, "HEADER"))

    body_lst = body.split("! ")
    pat = re.compile("(.+): +")

    # Keplerian or equinoctial elements
    ek_elts = body_lst[1].split("\n")
    ek_section = pat.search(ek_elts[0]).groups()[0]
    ek_names = re.split(", +", pat.sub("", ek_elts[0]))

    prop_list = list()
    for ek in ek_elts[1:]:
        eklst = re.split(r"\s+", ek)
        if len(eklst) < 2:  # skip empty rows
            continue
        if eklst[1] in ("KEP", "EQU"):
            ek_vals = eklst[2:]
        else:
            prop_list.append((eklst[1], eklst[2]))

    ek_tbl = _make_prop_table(ek_names, ek_vals, ek_section)
    for prop in prop_list:
        ek_tbl.add_row([prop[0], prop[1], prop[0]])

    table_lst.append(ek_tbl)

    # We need this list of properties for a number of tables so pull them out now
    cols = list(ek_tbl["Property"][ek_tbl["Section"] == ek_section])

    # Non-gravitational parameters
    lsp_lst = body_lst[2].split("\n")

    section = pat.search(lsp_lst[0]).groups()[0]
    lsp_names = re.split(", +", pat.sub("", lsp_lst[0]))
    lsp_vals = re.split(r"\s+", lsp_lst[1], maxsplit=len(lsp_names)+1)[2:]

    lps_tbl = _make_prop_table(lsp_names, lsp_vals, section)
    table_lst.append(lps_tbl)

    # dynamical parameters
    kep_n = 3
    if 'parameters' in body_lst[3]:
        section = re.search(r"(\w+ parameters)", body_lst[3]).groups()[0]

        ngr_names, ngr_vals = body_lst[4].split("\n")[:2]
        ngr_names = re.split(r",\s+", ngr_names)
        ngr_vals = re.split(r"\s+", ngr_vals)[2:]

        ngr_tbl = _make_prop_table(ngr_names, ngr_vals, section)
        table_lst.append(ngr_tbl)

        for row in ngr_tbl:
            if float(row["Value"]):
                cols.append(row["Property"])

        kep_n = 5

    # Equinoctial or Keplarian specific code
    if "Equinoctial" in ek_section:

        for row in body_lst[-3:]:
            if "WEA" in row:
                row, cov = re.split("\n", row, maxsplit=1)

            row_list = re.split(r"\s+", row)
            table_lst.append(_make_prop_table(cols, row_list[1:len(cols)+1], row_list[0]))

    else:  # Keplarian
        props = list()
        vals = list()
        pat = re.compile(r"(\w+)\s+(.+)\n")

        for row in body_lst[kep_n:-1]:
            matches = pat.match(row).groups()

            props.append(matches[0])
            vals.append(matches[1])

        table_lst.append(_make_prop_table(props, vals, props))

        row, cov = re.split("\n", body_lst[-1], maxsplit=1)
        row_list = re.split(r"\s+", row)
        table_lst.append(_make_prop_table(cols, row_list[1:len(cols)+1], row_list[0]))

    # Building the main table, adding the section grouping, and putting in the return list
    main_table = vstack(table_lst)
    main_table.meta["Title"] = "Orbital Elements"
    orbital_table_list = [main_table.group_by("Section")]

    # Making the matrix tables (COV/COR/NOR)
    mat_dict = dict()

    for row in cov.split("\n"):
        rlst = re.split(r"\s+", row)
        if len(rlst) < 2:
            continue

        mat_dict[rlst[1]] = mat_dict.get(rlst[1], []) + rlst[2:]

    dimension = int(lps_tbl["Value"][lps_tbl["Property"] == "dimension"][0])

    for mat_name in mat_dict:
        mat_arr = _fill_sym_matrix(np.array(mat_dict[mat_name]).astype(float), dimension)
        mat_table = Table(data=mat_arr, names=cols)
        mat_table.add_column(Column(name=mat_name, data=cols), index=0)

        mat_table.meta["Title"] = mat_name

        orbital_table_list.append(mat_table)

    return orbital_table_list


def parse_ephemerides(resp_str):
    """
    Parse the ephemerides response string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : Table
        The response table.
    """

    if "No ephemerides file" in resp_str:
        raise ValueError('No ephemerides file found for this object.')

    # Splitting the string into lines up to the nines which is where the table data starts
    resp_list = re.split("\n", resp_str, maxsplit=9)

    # Parsing the table info
    # This row defines the column widthes as == ==== ...
    col_inds = np.array([[m.start(0), m.end(0)] for m in re.finditer(r'\s+(=+)', resp_list[8])])

    # Want to combine the column names and units
    colnames = [(' '.join(x)).strip() for x in zip([resp_list[6][x:y].strip() for x, y in col_inds],
                                                   [resp_list[7][x:y].strip() for x, y in col_inds])]

    ephem_table = Table.read(resp_list[9], format="ascii.fixed_width_no_header",
                             col_starts=col_inds[:, 0], col_ends=col_inds[:, 1], names=colnames)

    # Combine Date and Hour columns and make into time object
    ephem_table["Date"] = convert_time(ephem_table["Date"], ephem_table["Hour (UTC)"]/24, conversion_string="%d %b %Y")
    ephem_table.remove_column("Hour (UTC)")

    # Change error columns in to floats and give column names units
    ephem_table["Err1"] = [float(x.replace('"', '')) for x in ephem_table["Err1"]]
    ephem_table.rename_column("Err1", 'Err1 (")')

    ephem_table["Err2"] = [float(x.replace('"', '')) for x in ephem_table["Err2"]]
    ephem_table.rename_column("Err2", 'Err2 (")')

    # Parse the query meta data and add to the table
    for meta in resp_list[:5]:
        elts = meta.split(": ")
        ephem_table.meta[elts[0]] = elts[1]

    # Adding the column info
    ephem_table.meta["Column Info"] = ('Ephemerides data frame shows:\n'
                                       '-The Date and the Hour considered\n'
                                       '-The Right Ascension (RA) and Declination (DEC) '
                                       'coordinates\n'
                                       '-The estimated V magnitude (Mag) of the object\n'
                                       '-The Altitude (Alt) over the horizon of the '
                                       'target at the specific time for the specific '
                                       'location. For negative values the object is '
                                       'unobservable. For geocentric position and for '
                                       'space telescopes the value is meaningless\n'
                                       '-The Airmass for the specific time. The Airmass'
                                       ' is INF when the object is under the horizon. '
                                       'For geocentric position and space telescope the'
                                       ' value is meaningless\n'
                                       '-The Sun elevation (Sun elev.) of the target, '
                                       'that means the angle of the Sun above or under '
                                       'the Horizon\n'
                                       '-The Solar elongation (SolEl) of the target, '
                                       'that means the angle Sun-observer-target\n'
                                       '-The Lunar elongation (LunEl) of the target, '
                                       'that means the angle Moon-observer-target\n'
                                       '-The Phase angle, that is the angle '
                                       'Sun-target-observer\n'
                                       '-The Galactic Latitude (Glat)\n'
                                       '-The Galactic Longitude (Glon)\n'
                                       '-The distance Sun-object (R)\n'
                                       '-The distance Earth-object (Delta)\n'
                                       '-The Apparent motion in RA (corrected by '
                                       'cos(DEC), which means the real motion on sky), '
                                       'and in DEC, in arcsec/min of the object\n'
                                       '-The angular velocity (Vel) in arcsec/min\n'
                                       '-The position Angle (PA) value\n'
                                       '-The Sky plane error with the long axis (Err1),'
                                       ' short axis (Err2)\n'
                                       '-The uncertainty ellipse position angle, given '
                                       'in degrees. It gives the primary axis '
                                       'orientation of the major axis of the ellipse in'
                                       ' degrees measured from North.')

    return ephem_table


def parse_summary(resp_str):
    """
    Parse the summary data string.

    Parameters
    ----------
    resp_str : str
        String containing the raw data for the table.

    Returns
    -------
    response : Table
        The response table.
    """

    if "Object not found" in resp_str:
        raise ValueError('Object not found: the name of the object is wrong or misspelt')

    parsed_html = BeautifulSoup(resp_str, 'lxml')

    # Pull out the properties
    props = parsed_html.find_all("div", {"class": "simple-list__cell"})
    prop_list = [str(x.contents[0]).strip() for x in props]

    # Pulling out Discovery data/Observatory if they are present
    # (These don't follow the name-value-unit format
    try:
        obs_ind = prop_list.index("Discovery Date")
    except ValueError:
        try:
            obs_ind = prop_list.index("Observatory")
        except ValueError:
            obs_ind = len(prop_list)

    obs_props = prop_list[obs_ind:]
    prop_list = prop_list[:obs_ind]

    # Building the table
    summary_tab = Table(names=["Physical Properties", "Value", "Units"],
                        data=np.array(prop_list).reshape((len(prop_list)//3, 3)))

    # Dealing with the special cases
    diameter = parsed_html.find_all("span", {"id": re.compile("_NEOSearch_WAR_PSDBportlet_.*diameter-value.*")})
    diameter = diameter[0].contents[0]
    summary_tab["Value"][summary_tab["Physical Properties"] == "Diameter"] = diameter

    summary_tab["Physical Properties"][summary_tab["Physical Properties"] == ""] = ("Nominal distance "
                                                                                    "(from Earth center)")

    # Adding the other properties as metadata
    for i in range(0, len(obs_props), 2):
        summary_tab.meta[obs_props[i]] = obs_props[i+1]

    return summary_tab
