# -*- coding: utf-8 -*-
"""
This module contains all the methods required to request the list data,
obtain it from the ESA NEOCC portal and parse it to show it properly.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Issue: 2.1.0
* Date: 01-03-2021
* Purpose: Module which request and parse list data from ESA NEOCC
* Module: lists.py
* History:

========   ===========   ==========================================
Version    Date          Change History
========   ===========   ==========================================
1.0        26-02-2021    Initial version
1.1        26-03-2021    New docstrings and lists
1.2        17-05-2021    Adding *help* property for dataframes.\n
                         Adding timeout of 90 seconds.\n
                         Adding *parse_impacted* function for new
                         list.
1.3        16-06-2021    URL and Timeout from configuration file
                         for astroquery implementation.\n
                         Change dateformat to datetime ISO format
1.3.1      29-06-2021    Hotfix in Risk list (TS and Velocity)
1.4.0      29-10-2021    Adding Catalogue of NEAS (current date
                         and middle arc).\n
                         Update docstrings.
2.0.0      21-01-2022    Prepare module for Astroquery integration
2.1.0      01-03-2022    Remove *parse* dependency
========   ===========   ==========================================

© Copyright [European Space Agency][2022]
All rights reserved
"""

import io
from datetime import timedelta
from astropy.table import Table
from astropy.time import Time
import pandas as pd
import requests
from astroquery.esa.neocc import conf

# Import BASE URL and TIMEOUT
API_URL = conf.API_URL
TIMEOUT = conf.TIMEOUT
VERIFICATION = conf.SSL_CERT_VERIFICATION


def get_list_url(list_name):
    """Get url from requested list name.

    Parameters
    ----------
    list_name : str
        Name of the requested list. Valid names are: *nea_list,
        risk_list, risk_list_special, close_approaches_upcoming,
        close_approaches_recent, priority_list, priority_list_faint,
        close_encounter, impacted_objects, neo_catalogue_current and
        neo_catalogue_middle*.

    Returns
    -------
    url : str
        Final URL string.

    Raises
    ------
    KeyError
        If the requested list_name is not in the dictionary
    """
    # Define the parameters of each list
    lists_dict = {
        "nea_list": 'allneo.lst',
        "updated_nea": 'updated_nea.lst',
        "monthly_update": 'monthly_update.done',
        "risk_list": 'esa_risk_list',
        "risk_list_special": 'esa_special_risk_list',
        "close_approaches_upcoming": 'esa_upcoming_close_app',
        "close_approaches_recent": 'esa_recent_close_app',
        "priority_list": 'esa_priority_neo_list',
        "priority_list_faint": 'esa_faint_neo_list',
        "close_encounter" : 'close_encounter2.txt',
        "impacted_objects" : 'past_impactors_list',
        "neo_catalogue_current" : 'neo_kc.cat',
        "neo_catalogue_middle" : 'neo_km.cat'
        }
    # Raise error is input is not in dictionary
    if list_name not in lists_dict:
        raise KeyError('Valid list names are nea_list, updated_nea, '
                       'monthly_update, risk_list, risk_list_special, '
                       'close_approaches_upcoming, close_approaches_recent, '
                       'priority_list, priority_list_faint, '
                       'close_encounter, impacted_objects, '
                       'neo_catalogue_current and neo_catalogue_middle')
    # Get url
    url = lists_dict[list_name]

    return url


def get_list_data(url, list_name):
    """Get requested parsed list from url.

    Parameters
    ----------
    list_name : str
        Name of the requested list.
    url : str
        URL of the requested list.

    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataDrame*
        Data frame which contains the data of the requested list.
    """
    # Get data from URL
    data_list = requests.get(API_URL + url, timeout=TIMEOUT,
                             verify=VERIFICATION).content

    # Decode the data using UTF-8
    data_list_d = io.StringIO(data_list.decode('utf-8'))

    # Parse decoded data
    neocc_list = parse_list(list_name, data_list_d)

    return neocc_list


def parse_list(list_name, data_byte_d):
    """Switch function to select parse method.

    Parameters
    ----------
    list_name : str
        Name of the requested list.
    data_byte_d : object
        Decoded StringIO object.

    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with data from the list parsed.
    """
    # Parse data for each type of list
    if list_name in ("nea_list", "updated_nea", "monthly_update"):
        neocc_lst = parse_nea(data_byte_d)
    elif list_name in ("risk_list", "risk_list_special"):
        neocc_lst = parse_risk(data_byte_d)
    elif list_name in ("close_approaches_upcoming",
                       "close_approaches_recent"):
        neocc_lst = parse_clo(data_byte_d)
    elif list_name in ("priority_list", "priority_list_faint"):
        neocc_lst = parse_pri(data_byte_d)
    elif list_name == "close_encounter":
        neocc_lst = parse_encounter(data_byte_d)
    elif list_name == "impacted_objects":
        neocc_lst = parse_impacted(data_byte_d)
    elif list_name in ('neo_catalogue_current',
                       'neo_catalogue_middle'):
        neocc_lst = parse_neo_catalogue(data_byte_d)
    else:
        raise KeyError('Valid list names are nea_list, updated_nea, '
                       'monthly_update, risk_list, risk_list_special, '
                       'close_approaches_upcoming, '
                       'close_approaches_recent, '
                       'priority_list, priority_list_faint, '
                       'close_encounter, impacted_objects, '
                       'neo_catalogue_current and '
                       'neo_catalogue_middle')

    return neocc_lst


def parse_nea(data_byte_d):
    """Parse and arrange NEA list, updated NEA and monthly update.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with NEA list data parsed.
    """
    # Read data as csv
    neocc_lst = pd.read_csv(data_byte_d, header=None)

    # Remove redundant white spaces
    neocc_lst = neocc_lst[0].str.strip().replace(r'\s+', ' ',
                                                 regex=True)\
                                        .str.replace('# ', '')

    return neocc_lst


def parse_risk(data_byte_d):
    """Parse and arrange risk lists.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.

    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with risk list data parsed.
    """
    # Read data as csv
    neocc_lst = pd.read_csv(data_byte_d, sep='|', skiprows=[3],
                            header=2)

    # Remove redundant white spaces
    neocc_lst.columns = neocc_lst.columns.str.strip()
    neocc_lst = neocc_lst.replace(r'\s+', ' ', regex=True)
    df_obj = neocc_lst.select_dtypes(['object'])
    neocc_lst[df_obj.columns] = df_obj.apply(lambda x:
                                             x.str.strip())

    # Rename columns
    col_dict = {"Num/des.       Name": 'Object Name',
                "m": 'Diameter in m',
                "Vel km/s": 'Vel in km/s'}
    neocc_lst.rename(columns=col_dict, inplace=True)

    # Remove last column
    neocc_lst = neocc_lst.drop(neocc_lst.columns[-1], axis=1)

    # Convert column with date to datetime variable
    neocc_lst['Date/Time'] = pd.to_datetime(neocc_lst['Date/Time'],
                                            errors='ignore')
    # Split Years into 2 columns to avoid dashed between integers
    # Check dataframe column length is differnt from 8 (for special risk)
    if len(neocc_lst.columns) != 8:
        neocc_lst[['First year', 'Last year']] = neocc_lst['Years']\
                                                    .str.split("-",
                                                    expand=True)\
                                                    .astype(int)
        # Drop split column
        neocc_lst = neocc_lst.drop(['Years'], axis=1)
        # Reorder columns
        neocc_lst = neocc_lst[['Object Name', 'Diameter in m', '*=Y',
                            'Date/Time', 'IP max', 'PS max', 'TS',
                            'Vel in km/s', 'First year', 'Last year',
                            'IP cum', 'PS cum']]

    # Adding metadata
    neocc_lst.help = ('Risk lists contain a data frame with the '
                      'following information:\n'
                      '-Object Name: name of the NEA\n'
                      '-Diamater in m: approximate diameter in meters\n'
                      '-*=Y: recording an asterisk if the value has '
                      'been estimated from the absolute magnitude\n'
                      '-Date/Time: predicted impact date in datetime '
                      'format\n'
                      '-IP max: Maximum Impact Probability\n'
                      '-PS max: Palermo scale rating\n'
                      '-Vel in km/s: Impact velocity at atmospheric entry'
                      ' in km/s\n'
                      '-First year: first year of possible impacts\n'
                      '-Last year: last year of possible impacts\n'
                      '-IP cum: Cumulative Impact Probability\n'
                      '-PS cum: Cumulative Palermo Scale')

    return neocc_lst


def parse_clo(data_byte_d):
    """Parse and arrange close approaches lists.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with close approaches list data parsed.
    """
    # Read data as csv
    neocc_lst = pd.read_csv(data_byte_d, sep='|', skiprows=[3],
                            header=2)
    # Check if there is server internal error
    if len(neocc_lst.columns) <= 1:
        raise ConnectionError('Internal Server Error. Please try '
                              'again.')
    # Remove redundant white spaces
    neocc_lst.columns = neocc_lst.columns.str.strip()
    neocc_lst = neocc_lst.replace(r'\s+', ' ', regex=True)
    df_obj = neocc_lst.select_dtypes(['object'])
    neocc_lst[df_obj.columns] = df_obj.apply(lambda x:
                                             x.str.strip())

    # Remove last column
    neocc_lst = neocc_lst.drop(neocc_lst.columns[-1], axis=1)

    # Rename columns
    neocc_lst.columns = ['Object Name', 'Date',
                         'Miss Distance in km', 'Miss Distance in au',
                         'Miss Distance in LD', 'Diameter in m',
                         '*=Yes', 'H', 'Max Bright',
                         'Rel. vel in km/s']

    # Assure that column Diameter in m is always a float
    neocc_lst = neocc_lst.astype({'Diameter in m': float})
    # Convert column with date to datetime variable
    neocc_lst['Date'] = pd.to_datetime(neocc_lst['Date'])
    # Adding metadata
    neocc_lst.help = ('Close approches lists contain a data frame with'
                      ' the following information:\n'
                      '-Object Name: name of the NEA\n'
                      '-Date: close approach date in datetime '
                      'format\n'
                      '-Miss distance in km: miss distance in kilometers'
                      ' with precision of 1 km\n'
                      '-Miss distance in au: miss distance in astronomical'
                      ' units (1 au  = 149597870.7 km)\n'
                      '-Miss distance in LD: miss distance in Lunar '
                      'Distance (1 LD = 384399 km)\n'
                      '-Diamater in m: approximate diameter in meters\n'
                      '-*=Yes: recording an asterisk if the value has '
                      'been estimated from the absolute magnitude\n'
                      '-H: Absolute Magnitude\n'
                      '-Max Bright: Maximum brightness at close approach\n'
                      '-Rel. vel in km/s: relative velocity in km/s')

    return neocc_lst


def parse_pri(data_byte_d):
    """Parse and arrange priority lists.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with priority list data parsed.
    """
    # Read as txt
    neocc_lst = pd.read_fwf(data_byte_d, skiprows=1, sep=' ',
                            header=None)

    # Merge second and first columns into 1
    neocc_lst[1] = neocc_lst[1] + " " + neocc_lst[2]
    neocc_lst = neocc_lst.drop(columns=2)
    # Removing white space from object number and designator
    neocc_lst[1] = neocc_lst[1].replace(r'\s+', '',
                                        regex=True)

    # Reindex columns
    neocc_lst.columns = range(neocc_lst.shape[1])

    # Remove quotes
    neocc_lst = neocc_lst.replace(to_replace='\"', value='',
                                  regex=True)

    # Convert column with date to datetime variable
    neocc_lst[7] = pd.to_datetime(neocc_lst[7])

    # Rename columns
    neocc_lst.columns = ['Priority', 'Object',
                         'R.A. in arcsec', 'Decl. in deg',
                         'Elong. in deg', 'V in mag', 'Sky uncert.',
                         'End of Visibility']
    # Adding metadata
    neocc_lst.help = ('Priority lists contain a data frame with'
                      ' the following information:\n'
                      '-Priority: 0=UR: Urgent, 1=NE: Necessary, '
                      '2=US: Useful, 3=LP: Low Priority\n'
                      '-Object: designator of the object\n'
                      '-R.A. in arcsec: current right ascension on '
                      'the sky, Geocentric equatorial, in arcseconds\n'
                      '-Decl. in deg: current declination on the sky'
                      ', in sexagesimal degrees\n'
                      '-Elong. in deg: current Solar elongation, in '
                      'sexagesimal degrees\n'
                      '-V in mag: current observable brightness, V '
                      'band, in magnitudes\n'
                      '-Sky uncert.: uncertainty in the plane of the '
                      'sky, in arcseconds\n'
                      '-End of Visibility: expected date of end of '
                      'visibility as YYYY.yyyyyy format')

    return neocc_lst


def parse_encounter(data_byte_d):
    """Parse and arrange close encounter lists.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_lst : *pandas.Series* or *pandas.DataFrame*
        Data frame with close encounter list data parsed.
    """
    # Read data as csv
    neocc_lst = pd.read_csv(data_byte_d, sep='|', skiprows=[0,2],
                            low_memory=False)
    # Check if there is server internal error
    if len(neocc_lst.columns) <= 1:
        raise ConnectionError('Internal Server Error. Please try '
                              'again.')
    # Remove redundant white spaces
    neocc_lst.columns = neocc_lst.columns.str.strip()
    neocc_lst = neocc_lst.replace(r'\s+', ' ', regex=True)
    df_obj = neocc_lst.select_dtypes(['object'])
    neocc_lst[df_obj.columns] = df_obj.apply(lambda x:
                                             x.str.strip())
    # Convert designator to str/object type
    neocc_lst['Name/desig'] = neocc_lst['Name/desig'].astype(str)
    # Convert Date column to datetime format
    # Create auxilary columns
    neocc_lst[['Date1','Date2']] = neocc_lst['Date']\
                                   .str.split(".",expand=True)
    # Convert each auxiliary column to datetime format and add
    neocc_lst['Date'] = pd.to_datetime(neocc_lst['Date1'],
                                       format='%Y/%m/%d') +\
                        (neocc_lst['Date2'].astype(float)/1e5)\
                                           .map(timedelta)
    # Remove auxiliary columns
    neocc_lst = neocc_lst.drop(['Date1','Date2'], axis=1)

    neocc_lst.help = ('Close encounter list contains a data frame with'
                      ' the following information:\n'
                      '-Name/design: designator of the NEA\n'
                      '-Planet:  planet or massive asteroid is '
                      'involved in the close approach\n'
                      '-Date: close encounter date in datetime '
                      'format\n'
                      '-Time approach: close encounter date in '
                      'MJD2000\n'
                      '-Time uncert: time uncertainty in MJD2000\n'
                      '-Distance: Nominal distance at the close '
                      'approach in au\n'
                      '-Minimum distance: minimum possible distance at'
                      ' the close approach in au\n'
                      '-Distance uncertainty: distance uncertainty in '
                      'in au\n'
                      '-Width: width of the strechin in au\n'
                      '-Stretch: stretching. It indicates how much the '
                      'confidence region at the epoch has been '
                      'stretched by the time of the approach. This is '
                      'a close cousin of the Lyapounov exponent\n'
                      '-Probability: close approach probability. A '
                      'value of 1 indicates a certain close approach\n'
                      '-Velocity: velocity in km/s\n'
                      '-Max Mag: maximum brightness magnitude at close'
                      'approach')

    return neocc_lst


def parse_impacted(data_byte_d):
    """Parse impacted objects list.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_table : *astropy.table.table.Table*
        Astropy table with impacted objects list data parsed.
    """
    # Read data as csv using astropy.table
    neocc_table = Table.read(data_byte_d, format='pandas.csv',
                             delimiter=r'\s+\|\s+|\s+\|',
                             engine='python', header=1,
                             dtype={'Object designator': str,
                                    'Diameter in m': str,
                                    'Impact date/time in UTC': str,
                                    'Impact Velocity in km/s': float,
                                    'Estimated energy in Mt': float,
                                    'Measured energy in Mt': float})
    neocc_table.remove_column('Unnamed: 6')
    # Convert column with date to astropy.time ISO format variable
    neocc_table['Impact date/time in UTC'] =\
         Time(neocc_table['Impact date/time in UTC'], scale='utc')

    return neocc_table


def parse_neo_catalogue(data_byte_d):
    """Parse neo catalogues (current or middle arc) lists.

    Parameters
    ----------
    data_byte_d : object
        Decoded StringIO object.
    Returns
    -------
    neocc_lst : *pandas.DataFrame*
        Data frame with catalogues of NEAs list data parsed.
    """
    # Read data as csv
    neocc_lst = pd.read_csv(data_byte_d, header=None, skiprows=6,
                            delim_whitespace=True)
    # Specify file columns
    neocc_lst.columns = ['Name', 'Epoch (MJD)', 'a', 'e', 'i',
                  'long. node', 'arg. peric.', 'mean anomaly',
                  'absolute magnitude', 'slope param.',
                  'non-grav param.']
    # Set the reference point at the beginning of the file to parse
    # the header
    data_byte_d.seek(0)
    # Read the header
    neocc_head = pd.read_fwf(data_byte_d, header=None, nrows=4)
    # Template for format data:
    # format  = '{format}'       ! file format
    format_txt = neocc_head.iloc[0][0].split("'")[1].strip()
    neocc_lst.form = format_txt
    # Template for record type:
    # rectype = '{rectype}'           ! record type (1L/ML)
    rectype = neocc_head.iloc[1][0].split("'")[1].strip()
    neocc_lst.rectype = rectype
    # Template for type of orbital element
    # elem    = '{elem}'          ! type of orbital elements
    elem = neocc_head.iloc[2][0].split("'")[1].strip()
    neocc_lst.elem = elem
    # Template for reference system
    # refsys  = {refsys}     ! default reference system
    refsys = neocc_head.iloc[3][0].split("=")[1].split("!")[0].strip()
    neocc_lst.refsys = refsys
    neocc_lst.help = ('These catalogues represent the list of '
                      'Keplerian orbit for each asteroid in the '
                      'input list at mean epoch and at current epoch.'
                      'The following information is contained:\n'
                      '-Name: designator of the NEA\n'
                      '-Epoch (MJD): epoch of the orbit'
                      'involved in the close approach\n'
                      '-Six orbital elements: semimajor axis (a), '
                      'eccentricity (e), inclination (i), longitude of'
                      ' the ascending node (long. node), '
                      'argument of pericenter (arg. peric) '
                      'and mean anomaly\n'
                      '-Slope parameter (slope param.)\n'
                      '-Number of non-gravitational parameters '
                      '(non-grav. param.')


    return neocc_lst

