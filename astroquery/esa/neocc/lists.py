"""
This module contains all the methods required to request the list data,
obtain it from the ESA NEOCC portal and parse it to show it properly.
"""

import io
import re
import requests

import numpy as np

from astropy.table import Table, Column
from astropy.time import Time, TimeDelta

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
        "close_encounter": 'close_encounter2.txt',
        "impacted_objects": 'past_impactors_list',
        "neo_catalogue_current": 'neo_kc.cat',
        "neo_catalogue_middle": 'neo_km.cat'
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
    response = requests.get(API_URL + url, timeout=TIMEOUT, verify=VERIFICATION)
    data_string = response.content.decode('utf-8')

    # Parse decoded data
    neocc_list = parse_list(list_name, data_string)

    return neocc_list


def parse_list(list_name, data_string):
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
        neocc_lst = parse_nea(data_string)
    elif list_name in ("risk_list", "risk_list_special"):
        neocc_lst = parse_risk(data_string)
    elif list_name in ("close_approaches_upcoming",
                       "close_approaches_recent"):
        neocc_lst = parse_clo(data_string)
    elif list_name in ("priority_list", "priority_list_faint"):
        neocc_lst = parse_pri(data_string)
    elif list_name == "close_encounter":
        neocc_lst = parse_encounter(data_string)
    elif list_name == "impacted_objects":
        neocc_lst = parse_impacted(data_string)
    elif list_name in ('neo_catalogue_current',
                       'neo_catalogue_middle'):
        neocc_lst = parse_neo_catalogue(data_string)
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


def parse_nea(resp_str):
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

    resp_str = resp_str.replace('#', '')
    return Table.read(resp_str, data_start=0, format="ascii.fixed_width", names=["NEA"])


def parse_risk(resp_str):
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

    neocc_lst = Table.read(resp_str, header_start=2, data_start=4, format="ascii.fixed_width")

    neocc_lst.rename_columns(("Num/des.       Name", "m",  "Vel km/s"),
                             ('Object Name', 'Diameter in m', 'Vel in km/s'))

    neocc_lst['Date/Time'] = Time(neocc_lst['Date/Time'], scale="utc") 

    if "Years" in neocc_lst.colnames:
        first_year, last_year  = np.array([x.split("-") for x in neocc_lst["Years"]]).swapaxes(0,1).astype(int)
        yr_index = neocc_lst.index_column("Years") 
        neocc_lst.remove_column("Years")
        neocc_lst.add_column(Column(name="Last Year", data=last_year), index=yr_index)
        neocc_lst.add_column(Column(name="First Year", data=first_year), index=yr_index)

    neocc_lst.meta =  {'Object Name': 'name of the NEA',
                       'Diamater in m': 'approximate diameter in meters',
                       '*=Y': 'recording an asterisk if the value has been estimated from the absolute magnitude',
                       'Date/Time': 'predicted impact date in datetime format',
                       'IP max': 'Maximum Impact Probability',
                       'PS max': 'Palermo scale rating',
                       'Vel in km/s': 'Impact velocity at atmospheric entry in km/s',
                       'First year': 'first year of possible impacts',
                       'Last year': 'last year of possible impacts',
                       'IP cum': 'Cumulative Impact Probability',
                       'PS cum': 'Cumulative Palermo Scale'}

    return neocc_lst


def parse_clo(resp_str):
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

    neocc_lst = Table.read(resp_str, header_start=2, data_start=4, format="ascii.fixed_width", 
                       names=('Object Name', 'Date', 'Miss Distance in km', 'Miss Distance in au',
                              'Miss Distance in LD', 'Diameter in m', '*=Yes', 'H', 'Max Bright',
                              'Rel. vel in km/s'))

    neocc_lst['Date'] = Time(neocc_lst['Date'], scale="utc")

    neocc_lst.meta = {'Object Name': 'name of the NEA',
                      'Date': 'close approach date in datetime format',
                      'Miss distance in km': 'miss distance in kilometers with precision of 1 km',
                      'Miss distance in au': 'miss distance in astronomical units (1 au  = 149597870.7 km)',
                      'Miss distance in LD': 'miss distance in Lunar Distance (1 LD = 384399 km)',
                      'Diamater in m': 'approximate diameter in meters',
                      '*=Yes': 'recording an asterisk if the value has been estimated from the absolute magnitude',
                      'H': 'Absolute Magnitude',
                      'Max Bright': 'Maximum brightness at close approach',
                      'Rel. vel in km/s': 'relative velocity in km/s'}

    return neocc_lst


def parse_pri(resp_str):
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

    neocc_lst = Table.read(resp_str, data_start=1, format="ascii.no_header", 
                       names=['Priority', 'Object', 'R.A. in arcsec', 'Decl. in deg',
                              'Elong. in deg', 'V in mag', 'Sky uncert.', 'End of Visibility'])

    neocc_lst['End of Visibility'] = Time.strptime(neocc_lst['End of Visibility'], '%Y/%m/%d')

    neocc_lst.meta = {'Priority': '0=UR: Urgent, 1=NE: Necessary, 2=US: Useful, 3=LP: Low Priority',
                      'Object': 'designator of the object',
                      'R.A. in arcsec': 'current right ascension on the sky, Geocentric equatorial, in arcseconds',
                      'Decl. in deg': 'current declination on the sky, in sexagesimal degrees',
                      'Elong. in deg': 'current Solar elongation, in sexagesimal degrees',
                      'V in mag': 'current observable brightness, V band, in magnitudes',
                      'Sky uncert.': 'uncertainty in the plane of the sky, in arcseconds',
                      'End of Visibility': 'expected date of end of visibility'}

    return neocc_lst


def parse_encounter(resp_str):
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

    neocc_lst = Table.read(resp_str, header_start=1, data_start=3, format="ascii.fixed_width")

    day, tme = np.array([x.split(".") for x in neocc_lst['Date']]).swapaxes(0,1)
    neocc_lst['Date'] = Time.strptime(day, '%Y/%m/%d') + TimeDelta(tme.astype(int)/1e5, format="jd")

    neocc_lst.meta = {'Name/design': 'designator of the NEA',
                      'Planet': 'planet or massive asteroid is involved in the close approach',
                      'Date': 'close encounter date in datetime format',
                      'Time approach': 'close encounter date in MJD2000',
                      'Time uncert': 'time uncertainty in MJD2000',
                      'Distance': 'Nominal distance at the close approach in au',
                      'Minimum distance': 'minimum possible distance at the close approach in au',
                      'Distance uncertainty': 'distance uncertainty in in au',
                      'Width': 'width of the strechin in au',
                      'Stretch': ('stretching. It indicates how much the confidence region at the '
                                  'epoch has been stretched by the time of the approach. This is a '
                                  'close cousin of the Lyapounov exponent'),
                      'Probability': 'close approach probability. A value of 1 indicates a certain close approach',
                      'Velocity': 'velocity in km/s',
                      'Max Mag': 'maximum brightness magnitude at close approach'}

    return neocc_lst


def parse_impacted(resp_str):
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

    neocc_table = Table.read(resp_str, header_start=1, format="ascii.fixed_width", fill_values = ['n/a', np.nan])
    neocc_table['Impact date/time in UTC'] = Time(neocc_table['Impact date/time in UTC'], scale='utc')

    return neocc_table


def parse_neo_catalogue(resp_str):
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

    neocc_lst = Table.read(resp_str, data_start=6, format="ascii.no_header", 
                           names=['Name', 'Epoch (MJD)', 'a', 'e', 'i', 'long. node', 'arg. peric.', 
                                  'mean anomaly', 'absolute magnitude', 'slope param.', 'non-grav param.'])

    neocc_lst.meta = {'Name': 'designator of the NEA',
                      'Epoch (MJD)': 'epoch of the orbit involved in the close approach',
                      'Six orbital elements': ('semimajor axis (a), eccentricity (e), inclination (i), '
                                               'longitude of the ascending node (long. node), argument of '
                                               'pericenter (arg. peric) and mean anomaly'),
                      'slope param': 'Slope parameter',
                      'non-grav param.': 'Number of non-gravitational parameters'}

    regex = re.search("(format) += '(.+)'.+\n(rectype) += '(.+)'.+\n(elem) += '(.+)'.+\n(refsys) += (\w+ \w+)", resp_str)
    keyvals = zip(regex.groups()[::2], regex.groups()[1::2])
    for k,v in keyvals:
        neocc_lst.meta[k] = v

    return neocc_lst
