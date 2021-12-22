# -*- coding: utf-8 -*-
"""
This module contains all the methods required to request the data from
a particular object, obtain it from the ESA NEOCC portal and parse it
to show it properly. The information of the object is shows in the
ESA NEOCC in different tabs that correspond to the different classes
within this module.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Issue: 2.1.0
* Date: 01-03-2021
* Purpose: Module which request and parse list data from ESA NEOCC
* Module: tabs.py
* History:

========   ===========   =====================================================
Version    Date          Change History
========   ===========   =====================================================
1.0        26-02-2021    Initial version
1.1        26-03-2021    Physical properties and summary funcionalities added
1.2        17-05-2021    Adding *help* property for dataframes.\n
                         Parsing of diameter property in *summary* and
                         *physical_properties* has been modified to add
                         robustness.\n
                         In *physical_properties* the parsing of properties
                         has been modified to include cases with more
                         information.\n
                         Adding timeout of 90 seconds.
1.3        16-06-2021    URLs and timeout from configuration file for
                         astroquery implementation.\n
                         Change time format to datetime ISO format.\n
                         Change to correct types in attributes (e.g.,
                         matrices, etc.)\n
                         Change ephemerides skyfooter to fix bug.\n
                         Change *get_matrix* from *orbit_properties* for
                         objects with 2 non-gravitational parameters.
1.3.1      29-06-2021    No changes
1.4.0      29-10-2021    Tab physical_properties has been recoded to parse the
                         information through a request in the portal instead
                         of parsing the html.\n
                         Get URL function now contains the file extension for
                         physical properties.\n
                         Parsing of ephemerides has been change to adapt new
                         format.\n
                         Orb_type attribute added in tab *orbit_properties*.\n
                         Bug fix in tab *observations*.\n
                         Adding redundancy for tab *summary* parsing.
2.0.0      21-01-2022    Prepare module for Astroquery integration
2.1.0      01-03-2022    Remove *parse* dependency

© Copyright [European Space Agency][2022]
All rights reserved
"""

import io
import logging
import time
import re
from datetime import datetime, timedelta
import pandas as pd
import requests
from bs4 import BeautifulSoup
from astroquery.esa.neocc import conf

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
        Name of the request tab. Valid names are: *summary,
        orbit_properties, physical_properties, observations,
        ephemerides, close_approaches and impacts*.
    **kwargs : str
        orbit_properties and ephemerides tabs required additional
        arguments to work:

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
                "physical_properties" : '.phypro',
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
            #Check if the epoch is present day or middle obs. arch
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
    data_obj = requests.get(API_URL + url, timeout=TIMEOUT,
                            verify=VERIFICATION).content
    # Parse data and assign attributes to object

    return data_obj


def get_indexes(dfobj, value):
    """Get a list with location index of a value or string in the
    DataFrame requested.

    Parameters
    ----------
    dfobj : pandas.DataFrame
        Data frame where the value will be searched.
    value : str, int, float
        String, integer or float to be searched.

    Returns
    -------
    listofpos : list
        List which contains the location of the value in the Data
        frame. The first elements will correspond to the index and
        the second element to the columns
    """
    # Empty list
    listofpos = []

    # isin() method will return a dataframe with boolean values,
    # True at the positions where element exists
    result = dfobj.isin([value])

    # any() method will return a boolean series
    seriesobj = result.any()

    # Get list of column names where element exists
    columnnames = list(seriesobj[seriesobj].index)

    # Iterate over the list of columns and extract the row index
    # where element exists
    for col in columnnames:
        rows = list(result[col][result[col]].index)

        for row in rows:
            listofpos.append((row, col))

    return listofpos


class Impacts:
    """This class contains information of object possible impacts.

    Attributes
    ---------
    impacts : pandas.DataFrame
        Data frame where are listed all the possible impactors.
    arc_start : str
        Starting date for optical observations.
    arc_end : str
        End date for optical observations.
    observation_accepted : int
        Total number of observations subtracting rejected
        observations.
    observation_rejected : int
        Number of observations rejected.
    computation : str
        Date of computation (in format YYYYMMDD MJD TimeSys)
    info : str
        Information from the footer of the requested file.
    additional_note : str
        Additional information. Some objects (e.g. 99942 Apophis)
        have an additional note after the main footer.

    """

    def __init__(self):
        """Initialization of class attributes
        """
        self.impacts = []
        self.arc_start = []
        self.arc_end = []
        self.observation_accepted = []
        self.observation_rejected = []
        self.computation = []
        self.info = []
        self.additional_note = []

    @staticmethod
    def _get_footer(data_obj):
        """Get footer information for impacts content.

        Parameters
        ----------
        data_obj : object
            Object in byte format.

        Returns
        -------
        obs : list
            Number of observations (total and rejected).
        arc : list
            Start and end dates.
        comp : str
            Computation date.
        info : str
            Additional information.
        add_note : str
            Addition note.
        """
        # Decode data using UTF-8 and store in new space of memory
        df_txt_d = io.StringIO(data_obj.decode('utf-8'))
        # Read data as txt
        df_txt = pd.read_fwf(df_txt_d, header=None)
        # Check that there is not additonal note
        index = get_indexes(df_txt, '<p> </p>')
        # Assign the index for obtaining the rest of attributes and
        # additional note value
        if not index:
            j = 0
            add_note = 'There is no additional note for this object'
        else:
            j = 6
            index = index[0][0]
            add_note = df_txt.iloc[index+1, 0] + '\n' +\
                df_txt.iloc[index+2, 0] + '\n' +\
                df_txt.iloc[index+3, 0] + '\n' +\
                df_txt.iloc[index+4, 0] + '\n' +\
                df_txt.iloc[index+5, 0]
            # Remove unnecessary words
            add_note = add_note.replace('<p>','').replace('</p>','').\
                replace('<span style="color: #0000CD;"><strong>','').\
                replace('</strong></span>','').replace('<sup>','^').\
                replace('</sup>','')

        # Drop NaN values if necessary
        df_txt = df_txt.dropna(how='all')
        # Template for observations data:
        # Based on {total} optical observations (of which {rejected}
        # are rejected as outliers)
        obs_total = df_txt.iloc[-7-j][0].split('on ')[1].\
            split('optical')[0].strip()
        obs_rejected = df_txt.iloc[-7-j][0].split('which ')[1].\
            split('are')[0].strip()
        obs = [obs_total, obs_rejected]
        # Template for date of observations: from {start} to {end}.
        arc_start = df_txt.iloc[-6-j][0].split('from ')[1].\
            split('to ')[0].strip()
        arc_end = df_txt.iloc[-6-j][0].split('to ')[1].\
            split('.')[0] + '.' + df_txt.iloc[-6-j][0].\
            split('to ')[1].split('.')[1]
        arc = [arc_start, arc_end]
        # Computation date
        comp = df_txt.iloc[-1-j][0].split('=')[2].strip()
        # Get information text
        info = df_txt.iloc[-5-j][0] + '\n\n' + df_txt.iloc[-4-j][0] +\
            '\n' + df_txt.iloc[-3-j][0] + '\n\n' + df_txt.iloc[-2-j][0]

        return obs, arc, comp, info, add_note

    def _impacts_parser(self, data_obj):
        """Parse and arrange the possible impacts data

        Parameters
        ----------
        data_obj : object
            Object in byte format.

        Raises
        ------
        ValueError
            If there is not risk file available for requested
            object
        """
        # Check that there is not additonal note
        df_check_d = io.StringIO(data_obj.decode('utf-8'))
        # Read as txt file
        df_check = pd.read_fwf(df_check_d, engine='python')
        index = get_indexes(df_check, '<p> </p>')
        # Assign the skipfooter if there is or not additional note
        if not index:
            footer_num = 12
        else:
            footer_num = 21
        # Decode data using UTF-8 and store in memory
        df_impacts_d = io.StringIO(data_obj.decode('utf-8'))
        # Read data as csv
        df_impacts = pd.read_csv(df_impacts_d, skiprows=[0, 2, 3, 4],
                                 skipfooter=footer_num,
                                 delim_whitespace=True, engine='python')
        # Check if there are information for the object
        if len(df_impacts.index) == 0:
            logging.warning('Required risk file is not '
                            'available for this object')
            raise ValueError('Required risk file is not '
                             'available for this object')
        # The previous skipfooter allow strange cases to show proper
        # impacts table. For the rest of the cases an additional row
        # must be dropped
        if df_impacts.iloc[-1,0] == 'Based':
            # Drop last row
            df_impacts = df_impacts.iloc[:-1]
            # Reassign numeric types to columns
            df_impacts['MJD'] = pd.to_numeric(df_impacts['MJD'])
            df_impacts['sigimp'] = pd.to_numeric(df_impacts['sigimp'])
            df_impacts['dist'] = pd.to_numeric(df_impacts['dist'])
            df_impacts['width'] = pd.to_numeric(df_impacts['width'])
            df_impacts['p_RE'] = pd.to_numeric(df_impacts['p_RE'])
            df_impacts['exp.'] = pd.to_numeric(df_impacts['exp.'])
            df_impacts['en.'] = pd.to_numeric(df_impacts['en.'])
            df_impacts['PS'] = pd.to_numeric(df_impacts['PS'])

        # Convert Date column to datetime format
        # Create auxilary columns
        df_impacts[['date1','date2']] = df_impacts['date']\
                                   .str.split(".",expand=True)
        # Convert each auxiliary column to datetime format and add
        df_impacts['date'] = pd.to_datetime(df_impacts['date1'],
                                       format='%Y/%m/%d') +\
                        (df_impacts['date2'].astype(float)/1e3)\
                                           .map(timedelta)
        # Remove auxiliary columns
        df_impacts = df_impacts.drop(['date1','date2'], axis=1)
        # Add number of decimals
        df_impacts['dist'].map(lambda x: f"{x:.2f}")
        df_impacts['width'].map(lambda x: f"{x:.3f}")
        # Rename new column and drop duplicate columns
        col_dict = {'exp.': 'Exp. Energy in MT',
                    'en.': 'PS',
                    'PS': 'TS'}
        df_impacts = df_impacts.drop(columns=['+/-',
                                     'TS']).rename(
                                     columns=col_dict)
        # Adding help to impacts Dataframe
        df_impacts.help = ('Data frame with possible impacts '
                           'information:\n'
                           '-Date: date for the potential impact in '
                           'datetime format\n'
                           '-MJD: Modified Julian Day for the '
                           'potential impact\n'
                           '-sigma: approximate location along the '
                           'Line Of Variation (LOV) in sigma space\n'
                           '-sigimp: The lateral distance in '
                           'sigma-space from the LOV to the Earth '
                           'surface. A zero implies that the LOV '
                           'passes through the Earth'
                           '-dist: Minimum Distance in Earth radii. '
                           'The lateral distance from the LOV to the '
                           'center of the Earth\n'
                           '-width: one-sigma semi-width of the '
                           'Target Plane confidence region in Earth '
                           'radii\n'
                           '-stretch: Stretching factor. '
                           'It indicates how much the '
                           'confidence region at the epoch has been '
                           'stretched by the time of the approach. This is '
                           'a close cousin of the Lyapounov exponent. '
                           'Units are in Earth radii divided by sigma '
                           '(RE/sig)\n'
                           '-p_RE: probability of Earth Impact (IP)\n'
                           '-Exp. Energy in MT: Expected energy. It is '
                           'the product of the impact energy and the '
                           'impact probability\n'
                           '-PS: Palermo Scale\n'
                           '-TS: Torino Scale')
        # Assign Data structure to attribute
        self.impacts = df_impacts

        # Get info from footer
        footer = self._get_footer(data_obj)
        # Assign parsed data to attributes
        # Change format to datetime and show in isoformat()
        arc_start = footer[1][0].split('.')
        arc_start = datetime.strptime(arc_start[0], '%Y/%m/%d') +\
                    timedelta(float(arc_start[1])/1e3)
        self.arc_start = arc_start.isoformat()
        # Change format to datetime and show in isoformat()
        arc_end = footer[1][1].split('.')
        arc_end = datetime.strptime(arc_end[0], '%Y/%m/%d') +\
                    timedelta(float(arc_end[1])/1e3)
        self.arc_end = arc_end.isoformat()
        self.observation_accepted = int(footer[0][0]) - \
            int(footer[0][1])
        self.observation_rejected = int(footer[0][1])
        self.computation = footer[2]
        self.additional_note = footer[4]
        # Assign info text from pandas
        self.info = footer[3]


class CloseApproaches:
    """This class contains information of object close approaches.
    """
    @staticmethod
    def clo_appr_parser(data_obj):
        """Parse and arrange the close approaches data.

        Parameters
        ----------
        data_obj : object
            Object in byte format.

        Returns
        -------
        df_close_appr : pandas.DataFrame
            Data frame with the close approaches information.

        Raises
        ------
        ValueError
            If file is empty.
        """
        # Decode data using UTF-8 and store in memory
        df_impacts_d = io.StringIO(data_obj.decode('utf-8'))
        # Check if the decoded data is empty before reading
        if not df_impacts_d.getvalue():
            df_close_appr = pd.DataFrame()
        else:
            # Read data as csv
            df_close_appr = pd.read_csv(df_impacts_d,
                                        delim_whitespace=True)
            # Convert Date column to datetime format
            # Create auxilary columns
            df_close_appr[['date1','date2']] =\
                df_close_appr['CALENDAR-TIME'].str.split(".",
                                                         expand=True)
            # Convert each auxiliary column to datetime format and add
            df_close_appr['CALENDAR-TIME'] =\
                pd.to_datetime(df_close_appr['date1'],
                               format='%Y/%m/%d') +\
                              (df_close_appr['date2'].\
                               astype(float)/1e5).map(timedelta)
            # Remove auxiliary columns
            df_close_appr = df_close_appr.drop(['date1','date2'], axis=1)
            # Create help attribute
            df_close_appr.help = ('Close approaches data frame contains:\n'
                                '-BODY:  planet or massive asteroid is '
                                'involved in the close approach\n'
                                '-CALENDAR-TIME: date of the close '
                                'approach in datetime format\n'
                                '-MJD-TIME: Modified Julian Date of the'
                                'approach\n'
                                '-TIME-UNCERT.: time uncertainty in '
                                'MJD2000\n'
                                '-NOM.-DISTANCE: Nominal distance at '
                                'the close approach in au\n'
                                '-MIN.-POSS.-DIST.: Minimum possible '
                                'distance at the close approach in au\n'
                                '-DIST.-UNCERT.: distance uncertainty in '
                                'au\n'
                                '-STRETCH: It indicates how much the '
                                'confidence region at the epoch has '
                                'been stretched by the time of the '
                                'approach. This is a close cousin of '
                                'the Lyapounov exponent. Units in au\n'
                                '-WIDTH: width of the stretching\n'
                                '-PROBABITLIY: Close approach '
                                'probability. A value of 1 indicates a '
                                'certain close approach')

        return df_close_appr


class PhysicalProperties:
    """
        This class contains information of asteroid physical properties

        Attributes
        ---------
        physical_properties : DataFrame
            Data structure containing property, value, units and source
            from the complete set of physical properties
        sources : DataFrame
            Data structure containing source number, name and
            additional information

        Raises
        ------
        ValueError
            If the name of the object is not found
    """
    def __init__(self):
        """
            Initialization of class attributes
        """
        # Physical properties
        self.physical_properties = []
        # Sources
        self.sources = []

    @staticmethod
    def _get_prop_sources(data_obj_d, rows):
        """
            Obtain the sources parsed

            Parameters
            ----------
            data_obj_d : object
                Object in byte format decoded.
            rows : int
                Index where references start

            Returns
            -------
            sources : Data structure
                Data structure containing all property sources
        """
        # Read as csv to allow delimiter. Since pandas not allow ","
        # as delimiter (error in parsing columns)
        sources= pd.read_csv(data_obj_d, header=None, skiprows=rows+2,
                              engine='python', delimiter='],')
        # Add the erased bracket
        sources[0] = sources[0]+']'
        # Split first column with the first found commar
        sources[[1, 2]] = sources[1].str.split(r',', 1, expand=True)
        # Replace whitespace as blank spaces for better reading
        sources[2] = sources[2].str.replace(r"\s(?=\d\.\))", r"\n",
                                            regex=True)
        # Name columns as the portal
        sources.columns = ['No.', 'Name', 'Additional']

        return sources

    def _phys_prop_parser(self, data_obj):
        """
            Parse and arrange the physical properties data

            Parameters
            ----------
            data_obj : object
                Object in byte format.

            Raises
            ------
            ValueError
                If the name of the object is not encountered
        """
        # Check that there is not additonal note
        df_check_d = io.StringIO(data_obj.decode('utf-8'))
        if not df_check_d.getvalue():
            raise ValueError('Object not found or misspelt')
        # Read as txt file
        df_check = pd.read_fwf(df_check_d, header=None,
                               engine='python')
        # Get index where references start and count rows
        ref_index = get_indexes(df_check, "REFERENCES")
        n_rows = ref_index[0][0]
        # Set reference point at the begging of the file
        df_check_d.seek(0)
        df_check = pd.read_fwf(df_check_d, header=None,
                               engine='python', nrows=n_rows)
        # Held exception for Taxonomy (all) property
        # Split the comple DF to obtain the columns
        df_check = df_check[0].str.split(',', expand=True)
        # Initialize index
        index = 0
        if len(df_check.columns) > 4:
            # Iterate over each element in last col to find
            # rows with additional elements separated by commas
            for element in df_check.iloc[:, -1]:
                if isinstance(element, str):
                    for i in range(2, len(df_check.columns)-2):
                        df_check.iloc[index, 1] =\
                            df_check.iloc[index, 1] + ',' +\
                            df_check.iloc[index, i]
                    df_check.iloc[index,2] = df_check.iloc[index,
                                                len(df_check.columns)-2]
                    df_check.iloc[index,3] = df_check.iloc[index,
                                                len(df_check.columns)-1]
                index += 1
        # Only get the main columns
        df_check = df_check.iloc[:, 0:4]
        # Set reference point at the begging of the file
        df_check_d.seek(0)
        # Read as csv for parsing
        ast_prop = pd.read_csv(df_check_d, header=None, skiprows=0,
                               nrows=n_rows, delimiter=',',
                               on_bad_lines='skip')
        # Create if condition for the exception since Taxonomy (all)
        # will be skipped. The DF is updated with the values of the
        # redundant one
        if not 'Taxonomy (all)' in ast_prop.values:
            ast_prop.update(df_check)
        elif not 'Quality' in ast_prop.values:
            ast_prop.update(df_check)
        # Rename columns
        ast_prop.columns = ['Property', 'Value(s)', 'Units',
                            'Reference(s)']
        # Group identical properties into one. The values from the
        # other columns will be group using commas (as a list)
        phys_prop = ast_prop.groupby(['Property'], as_index=False,
                                     sort=False)[['Value(s)', 'Units',
                                                 'Reference(s)']]\
                            .agg(','.join)
        # Split using commas to create arrays
        phys_prop['Value(s)'] = phys_prop['Value(s)']\
                            .apply(lambda x: x.split(',')
                            if isinstance(x, str) and ',' in x else x)
        phys_prop['Units'] = phys_prop['Units']\
                            .apply(lambda x: x.split(',')
                            if isinstance(x, str) and ',' in x else x)
        phys_prop['Reference(s)'] = phys_prop['Reference(s)']\
                            .apply(lambda x: x.split(',')
                            if isinstance(x, str) and ',' in x else x)
        # Values need to be converted to numeric type when possible
        phys_prop['Value(s)'] = phys_prop['Value(s)']\
                            .apply(lambda x: pd.to_numeric(x,
                            errors='ignore', downcast='float'))
        # Properties
        self.physical_properties = phys_prop
        # Sources
        # Set reference point at the begging of the file
        df_check_d.seek(0)
        self.sources = self._get_prop_sources(df_check_d, n_rows)


class AsteroidObservations:
    """This class contains information of asteroid observations.

    Attributes
    ----------
    version : float
        File version.
    errmod : str
        Error model for the data.
    rmsast : float
        Root Mean Square for asteroid observations.
    rmsmag : float
        Root Mean Square for magnitude.
    optical_observations : pandas.DataFrame
        Data frame which contains optical observations (without roving
        observer and satellite observation).
    radar_observations : pandas.DataFrame
        Data structure which contains radar observations.
    roving_observations : pandas.DataFrame
        Data structure which contains "roving observer" observations.
    sat_observations : pandas.DataFrame
        Data structure which contains satellite observations.

    """

    def __init__(self):
        """Initialization of class attributes
        """
        self.version = []
        self.errmod = []
        self.rmsast = []
        self.rmsmag = []
        self.optical_observations = []
        self.radar_observations = []
        self.roving_observations = []
        self.sat_observations = []

    @staticmethod
    def _get_head_obs(df_d):
        """Get and parse header of asteroid observations file.

        Parameters
        ----------
        df_d : object
            StringIO object with data.

        Returns
        -------
        ver : int
            File version.
        err : str
            Error model.
        ast : float
            Root Mean Square for asteroid observations.
        mag : float
            Root Mean Square for magnitude.
        """
        df_head = pd.read_csv(df_d, nrows=4, header=None)
        # Template for version: version =   {ver}
        ver = df_head.iloc[0][0].split('=')[1].strip()
        ver = float(ver)
        # Template for errmod: errmod  = '{err}'
        err = df_head.iloc[1][0].split("'")[1].strip()
        # Template for RMSast: RMSast  =   {ast}
        ast = df_head.iloc[2][0].split('=')[1].strip()
        ast = float(ast)
        # Template for RMSast: RMSmag  =   {mag}
        mag = df_head.iloc[3][0]
        if mag == 'END_OF_HEADER':
            mag = 'No data for RMSmag'
        else:
            mag = float(df_head.iloc[3][0].split('=')[1].strip())


        return ver, err, ast, mag

    @staticmethod
    def _get_opt_info(data_obj, diff, head, cols_sep):
        """Get optical information from asteroid observation file.

        Parameters
        ----------
        df_d : object
            Object in byte format with data decoded.
        diff : int
            Optical observations data frame length.
        head : list
            Header rows to be skipped.

        Returns
        -------
        df_optical_obs : pandas.DataFrame
            Parsed data frame for optical observations.
        df_roving_obs : pandas.DataFrame
            Parsed data frame for "roving observer" observations.
        df_sat_obs : pandas.DataFrame
            Parsed data frame for satellite observations.
        """
        # Decode data for check v and s optical observations
        df_check = io.StringIO(data_obj.decode('utf-8'))
        # Set attributes
        df_obs = pd.read_fwf(df_check, colspecs=cols_sep, skiprows=head,
                               engine='python', skipfooter=diff)
        # Check if there are "Roving Observer" observations
        df_index = df_obs.iloc[:,1:4]
        v_indexes = get_indexes(df_index, 'v')
        # Check if there are "Roving Observer" observations
        s_index = get_indexes(df_index, 's')
        # Remove indexes located in 'N' column
        s_indexes = []
        for indexes in s_index:
            if 'T' in indexes:
                s_indexes = s_indexes + [indexes]
        # Initialization of a list which contain the row indexes
        v_rows = []
        s_rows = []

        # Roving Observations
        if not v_indexes:
            df_roving_obs = 'There are no "Roving Observer" '\
                            'observations for this object'
        else:
            # Save a list with the row indexes that needs to be saved
            for v_index in v_indexes:
                # Add to the list in order to consider header lines
                v_rows =  v_rows + [v_index[0]+len(head)+1]
            # Decode data for final roving observations
            df_v = io.StringIO(data_obj.decode('utf-8'))
            # Define colspecs fwf
            cols_v = [(0,10), (11,12), (12,14), (15,16), (17,21),
                      (22,24), (25,34), (34,44), (45,55), (56,64),
                      (65,68)]
            # Usea pandas to read these rows
            df_roving_obs = pd.read_fwf(df_v, delim_whitespace=True,
                                        skiprows=lambda x: x not in v_rows,
                                        engine='python', header=None,
                                        colspecs=cols_v)
            # Rename columns as in file
            df_roving_obs.columns = ['Design.', 'K', 'T', 'N', 'Date',
                                     'MM', 'DD.dddddd', 'E longitude',
                                     'Latitude', 'Altitude', 'Obs Code']
            # Create and Convert Date column to datetime format
            # Create date column in YYYY-MM format
            df_roving_obs['Date'] = df_roving_obs['Date'].astype(str) +\
                                    '/' + df_roving_obs['MM'].astype(str)
            # Convert to datetime and add timedelta for days substracting
            # the day added in the datetime conversion for YYYY-MM
            df_roving_obs['Date'] = pd.to_datetime(df_roving_obs['Date'],
                                                    format='%Y/%m') +\
                                    df_roving_obs['DD.dddddd']\
                                    .map(timedelta)-timedelta(days=1)
            # Remove columns for months and days
            df_roving_obs = df_roving_obs.drop(['MM','DD.dddddd'], axis=1)

        # Satellite Observations
        if not s_indexes:
            df_sat_obs = 'There are no Satellite observations for '\
                         'this object'
        else:
            # Save a list with the row indexes that needs to be saved
            for s_index in s_indexes:
                # Number 7 is add to the list in order to consider
                # header lines
                s_rows =  s_rows + [s_index[0]+len(head)+1]
            # Decode data for final satellite observations
            df_s = io.StringIO(data_obj.decode('utf-8'))
            # Define colspecs fwf
            cols_s = [(0,10), (11,12), (12,15), (15,16), (17,21),
                     (22,24), (25,34), (34,35), (40,59), (64,83),
                     (88,107), (108,111)]
            # Usea pandas to read these rows
            df_sat_obs = pd.read_fwf(df_s, delim_whitespace=True,
                                     skiprows=lambda x: x not in s_rows,
                                     engine='python', header=None,
                                     colspecs=cols_s)
            # Rename columns as in file
            df_sat_obs.columns = ['Design.', 'K', 'T', 'N', 'Date',
                                  'MM', 'DD.dddddd',
                                  'Parallax info.', 'X', 'Y',
                                  'Z', 'Obs Code']
            # Create and Convert Date column to datetime format
            # Create date column in YYYY-MM format
            df_sat_obs['Date'] = df_sat_obs['Date'].astype(str) +\
                                    '/' + df_sat_obs['MM'].astype(str)
            # Convert to datetime and add timedelta for days substracting
            # the day added in the datetime conversion for YYYY-MM
            df_sat_obs['Date'] = pd.to_datetime(df_sat_obs['Date'],
                                                    format='%Y/%m') +\
                                    df_sat_obs['DD.dddddd']\
                                    .map(timedelta)-timedelta(days=1)
            # Remove columns for months and days
            df_sat_obs = df_sat_obs.drop(['MM','DD.dddddd'], axis=1)
            # For satellite observations columns "T" contains
            # whitespacese. Strip them
            df_sat_obs['T'] = df_sat_obs['T'].str.strip()

        # Rest of optical observations
        df_opt = io.StringIO(data_obj.decode('utf-8'))
        # Read data using pandas as text, skiping header and footer
        # and v_rows and s_rows if any
        df_optical_obs = pd.read_fwf(df_opt, skipfooter=diff,
                                     colspecs=cols_sep,
                                     engine='python',
                                     skiprows=head + v_rows + s_rows)
        # Replace NaN values for blank values
        df_optical_obs = df_optical_obs.fillna('')
        # Rename Columns as in file
        df_optical_obs.columns = ['Design.', 'K', 'T', 'N', 'Date',
                                  'MM', 'DD.ddd',
                                  'Date Accuracy', 'RA HH',
                                  'RA MM', 'RA SS.sss', 'RA Accuracy',
                                  'RA RMS', 'RA F', 'RA Bias',
                                  'RA Resid', 'DEC sDD', 'DEC MM',
                                  'DEC SS.ss', 'DEC Accuracy',
                                  'DEC RMS', 'DEC F', 'DEC Bias',
                                  'DEC Resid', 'MAG Val', 'MAG B',
                                  'MAG RMS', 'MAG Resid', 'Ast Cat',
                                  'Obs Code', 'Chi', 'A', 'M']
        # Create and Convert Date column to datetime format
        # Create date column in YYYY-MM format
        df_optical_obs['Date'] = df_optical_obs['Date'].astype(str) +\
                                 '/' + df_optical_obs['MM'].astype(str)
        # Convert to datetime and add timedelta for days substracting
        # the day added in the datetime conversion for YYYY-MM
        df_optical_obs['Date'] = pd.to_datetime(df_optical_obs['Date'],
                                                 format='%Y/%m') +\
                                  df_optical_obs['DD.ddd']\
                                  .map(timedelta)-timedelta(days=1)
        # Remove columns for months and days
        df_optical_obs = df_optical_obs.drop(['MM','DD.ddd'], axis=1)
        # Create help attribute for dataframe
        df_optical_obs.help = ('This dataframe shows the information of '
                               'optical observations. The fields are:\n'
                               '-Designation: number or the provisional '
                               'designation of the asteroid.\n'
                               '-K, Type: observation type and technology'
                               ' provided by the MPC. Note that for '
                               'satellite (s) and roving (v) observations'
                               'there are 2 additional dataframes which '
                               'contain the information given by the MPC.\n'
                               '-Date: date in UTC iso format.\n'
                               '-Right Ascension: The data provided include'
                               ' the observation, the a priori accuracy (as'
                               ' supplied by the MPC), the a priori RMS '
                               'used for weighing, a flag indicating a '
                               'forced weight, the bias, and the residuals '
                               'in arcsec.\n'
                               '-Declination: same format as Right '
                               'Ascension.\n'
                               '-Apparent magnitude: The columns contain '
                               'the apparent magnitude as reported, the a '
                               'priori RMS used for weighing, and the '
                               'residual, all in magnitudes.\n'
                               '-Quality: observatory code is extracted from'
                               ' the MPC published observation, the value of'
                               ' chi from the chi**2 test (characterization '
                               'of the relative quality of the observation).'
                               ' The "Used A" column is "Yes" if the '
                               'observation is used in our orbit, and "No" '
                               'if it has been discarded. The same for the '
                               'photometry in the "Used M" column.')

        return df_optical_obs, df_roving_obs, df_sat_obs

    @staticmethod
    def _get_rad_info(df_d, index):
        """Get radar information from asteroid observations file

        Parameters
        ----------
        df_d : object
            stringIO object with data decoded.
        index : int
            Position at which radar information starts.

        Returns
        -------
        df_rad : pandas.DataFrame
            Parsed data frame for radar observations.
        """
        # Read decoded DataFrame and skip rows
        df_rad = pd.read_fwf(df_d, engine='python', sep=' ',
                             skiprows=index[0][0]+8)
        # Drop NaN columns and rename
        df_rad = df_rad.drop(['F', 'S'], axis=1)
        # Create Datetime column
        df_rad['YYYY'] = df_rad['YYYY'].apply(str) + '-' + \
            df_rad['MM'].apply(str) + '-' + df_rad['DD'].apply(str) + \
            '-' + df_rad['hh:mm:ss']
        df_rad['YYYY'] = pd.to_datetime(df_rad['YYYY'])
        # Dropping old name columns
        df_rad = df_rad.drop(['MM', 'DD', 'hh:mm:ss'], axis=1)
        # Check variable column data
        if 'rms' in df_rad.columns:
            # Rename columns
            cols_dict = {'! Design': 'Design',
                         'Unnamed: 11': 'F',
                         'Unnamed: 17': 'S',
                         'YYYY': 'Datetime'}
            df_rad.rename(columns=cols_dict, inplace=True)
        else:
            # Rename columns
            cols_dict = {'! Design': 'Design',
                         'Unnamed: 10': 'F',
                         'Unnamed: 16': 'S',
                         'YYYY': 'Datetime'}
            df_rad.rename(columns=cols_dict, inplace=True)
            # Splitting bad joined columns
            split1 = df_rad["Accuracy    rms"].str.split(" ", n=1,
                                                         expand=True)
            df_rad["Accuracy"] = split1[0]
            df_rad["rms"] = split1[1]
            # Dropping old Name columns
            df_rad.drop(columns=["Accuracy    rms"], inplace=True)

        # Splitting bad joined columns
        split2 = df_rad["TRX RCX"].str.split(" ", n=1, expand=True)
        # Making separate first name column from new Data structure
        df_rad["TRX"] = split2[0]
        # Making separate last name column from new Data structure
        df_rad["RCX"] = split2[1]
        # Dropping old Name columns
        df_rad.drop(columns=["TRX RCX"], inplace=True)

        # Reorder columns
        df_rad = df_rad[['Design', 'K', 'T', 'Datetime', 'Measure',
                         'Accuracy', 'rms', 'F', 'Bias', 'Resid',
                         'TRX', 'RCX', 'Chi', 'S']]
        df_rad.help = ('This dataframe contains the information for '
                       'radar observations:\n'
                       '-Designation: number or the provisional '
                       'designation of the asteroid.\n'
                       '-K, Type: observation type and technology'
                       'provided by the MPC. A "c" indicates the '
                       'radar observation is referenced to the '
                       'asteroid center of mass, and an "s" indicates '
                       'the measurement is referenced to the radar '
                       'bounce point.\n'
                       '-Datetime: date in UTC format.\n'
                       '-Radar range or range rate: refers to columns '
                       'measure (km or km/day), accuracy (precision of'
                       'the measurement), rms, F, bias and Resid.\n'
                       '-Quality: transmit (TRX) and receive (RCX) '
                       'station are given. When these differ, an '
                       'observation is considered as belonging to '
                       'the receiver station. the value of'
                       ' chi from the chi**2 test (characterization '
                       'of the relative quality of the observation).'
                       'The "S" column is "Yes" if the '
                       'observation is used in our orbit, and "No" '
                       'if it has been discarded.')

        return df_rad

    def _ast_obs_parser(self, data_obj):
        """Get asteroid observation properties parsed from object data

        Parameters
        ----------
        data_obj : object
            Object in byte format.

        Raises
        ------
        ValueError
            If the required observations file is empty or does not exist
        """
        # Decode data using UTF-8 and store in memory for header
        df_head_d = io.StringIO(data_obj.decode('utf-8'))
        # Check file exists or is not empty
        if not df_head_d.getvalue():
            logging.warning('Required data observations file is '
                            'empty for this object')
            raise ValueError('Required data observations file is '
                             'empty for this object')

        # Obtain header
        df_head = self._get_head_obs(df_head_d)
        self.version = df_head[0]
        self.errmod = df_head[1]
        self.rmsast = df_head[2]
        self.rmsmag = df_head[3]
        # Decode data using UTF-8 and store in memory for
        # observations
        df_d = io.StringIO(data_obj.decode('utf-8'))
        # Check there is valid data for RMS magnitude and set header
        # length
        if isinstance(self.rmsmag, str):
            head = [0, 1, 2, 3, 4]
        else:
            head = [0, 1, 2, 3, 4, 5]
        # Read data in fixed width format
        cols = [(0,10), (11,12), (12,15), (15,16), (17,21), (22,24),
                (25,38), (40,49), (50,52), (53,55), (56,62), (64,73),
                (76,82), (83,84), (87,93), (96,102), (103,106),
                (107,109), (110,115), (117,126), (129,135), (136,137),
                (140,146), (149,155), (156,161), (161,162), (164,168),
                (170,175), (177,179), (180,183), (188,193), (194,195),
                (196,197)]
        df_p = pd.read_fwf(df_d, colspecs=cols,
                           skiprows=head, engine='python')
        # Check if there is radar observations data
        if not get_indexes(df_p, '! Object'):
            # Set length of asteriod observations to zero
            diff = 0
            # Get observations
            total_observations = self._get_opt_info(data_obj, diff,
                                                    head, cols)
            # Set attributes
            self.optical_observations = total_observations[0]
            self.radar_observations = 'There is no relevant radar '\
                                      'information'
            self.roving_observations = total_observations[1]
            self.sat_observations = total_observations[2]

        else:
            # # Decode data for optical and radar observations
            df_rad = io.StringIO(data_obj.decode('utf-8'))
            # Get position at which radar observations start
            index = get_indexes(df_p, '! Object')
            # Set lenght of radar obsrevations to remove footer
            diff = len(df_p) - index[0][0]
            # Get observations
            total_observations = self._get_opt_info(data_obj, diff,
                                                    head, cols)
            # Set attributes
            self.optical_observations = total_observations[0]
            self.radar_observations = self._get_rad_info(df_rad, index)
            self.roving_observations = total_observations[1]
            self.sat_observations = total_observations[2]


class OrbitProperties:
    """This class contains information of asteroid orbit properties.

    Attributes
    ----------
    form : str
        File format.
    rectype : str
        Record type.
    refsys : str
        Default reference system.
    epoch : str
        Epoch in MJD format.
    mag : pandas.DataFrame
        Data frame which contains magnitude values.
    lsp : pandas.DataFrame
        Data structure with information about non-gravitational
        parameters (model, numer of parameters, dimension, etc.).
    ngr : pandas.DataFrame
        Data frame which contains non-gravitational parameters.

    """

    def __init__(self):
        """Initialization of class attributes
        """
        # Document info
        self.form = []
        self.rectype = []
        self.refsys = []
        # Orbit properties
        self.epoch = []
        self.mag = []
        self.lsp = []
        # Non-gravitational parameters
        self.ngr = []

    @staticmethod
    def _get_matrix(dfd, matrix_name, dimension, orbit_element, **kwargs):
        """Get covariance or correlaton matrix from df.

        Parameters
        ----------
        dfd : pandas.DataFrame
            Data frame with object data to be parsed.
        matrix_name : str
            Matrix name to be obtained.
        dimension : int
            Matrix dimension.
        orbit_element : str
            Orbit elements for the matrix.
        **kwargs : str
            If there is only one additional NGR parameter it should be
            introduced to show properly in the matrix.

        Returns
        -------
        mat : Data structure
            Data structure with matrix data

        Raises
        ------
        ValueError
            If the matrix name is not correct
        """
        # Define dictionary for types of matrices
        matrix_dict = {'cov': 'COV',
                       'cor': 'COR',
                       'nor': 'NOR'}
        # Define indexes and colunm namaes according to orbit element type
        mat_var = {'keplerian': ['a', 'e', 'i', 'long. node',
                                   'arg. peric', 'M'],
                   'equinoctial': ['a', 'e*sin(LP)', 'e*cos(LP)',
                                     'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)',
                                     'mean long.']}
        # Get matrix location according to its name
        if matrix_name in matrix_dict:
            i = get_indexes(dfd, matrix_dict[matrix_name])[0][0]
            # Check if there is a matrix
            if not i:
                mat = 'There is no ' + matrix_dict[matrix_name]  +\
                    'matrix for this object'
                logging.warning('There is no %s matrix for this object',
                                matrix_dict[matrix_name])
            else:
                # Define the matrix according to its dimension
                if dimension == 6:
                    # Define matrix structure
                    mat_data = {mat_var[orbit_element][0]:
                                    [dfd.iloc[i, 1], dfd.iloc[i, 2],
                                    dfd.iloc[i, 3], dfd.iloc[i+1, 1],
                                    dfd.iloc[i+1, 2], dfd.iloc[i+1, 3]],
                                mat_var[orbit_element][1]:
                                    [dfd.iloc[i, 2], dfd.iloc[i+2, 1],
                                    dfd.iloc[i+2, 2], dfd.iloc[i+2, 3],
                                    dfd.iloc[i+3, 1], dfd.iloc[i+3, 2]],
                                mat_var[orbit_element][2]:
                                    [dfd.iloc[i, 3], dfd.iloc[i+2, 2],
                                    dfd.iloc[i+3, 3], dfd.iloc[i+4, 1],
                                    dfd.iloc[i+4, 2], dfd.iloc[i+4, 3]],
                                mat_var[orbit_element][3]:
                                    [dfd.iloc[i+1, 1], dfd.iloc[i+2, 3],
                                    dfd.iloc[i+4, 1], dfd.iloc[i+5, 1],
                                    dfd.iloc[i+5, 2], dfd.iloc[i+5, 3]],
                                mat_var[orbit_element][4]:
                                    [dfd.iloc[i+1, 2], dfd.iloc[i+3, 1],
                                    dfd.iloc[i+4, 2], dfd.iloc[i+5, 2],
                                    dfd.iloc[i+6, 1], dfd.iloc[i+6, 2]],
                                mat_var[orbit_element][5]:
                                    [dfd.iloc[i+1, 3], dfd.iloc[i+3, 2],
                                    dfd.iloc[i+4, 3], dfd.iloc[i+5, 3],
                                    dfd.iloc[i+6, 2], dfd.iloc[i+6, 3]]}
                    # Rename matrix indexes
                    matrix_indexes = mat_var[orbit_element]
                    # Build the matrix
                    mat = pd.DataFrame(mat_data, index=matrix_indexes)

                elif dimension == 7:
                    # Obtain from kwargs the non-gravitational parameter
                    ngr_parameter = kwargs['ngr']
                    # Define matrix structure
                    mat_data = {mat_var[orbit_element][0]:
                                    [dfd.iloc[i, 1], dfd.iloc[i, 2],
                                    dfd.iloc[i, 3], dfd.iloc[i+1, 1],
                                    dfd.iloc[i+1, 2], dfd.iloc[i+1, 3],
                                    dfd.iloc[i+2, 1]],
                                mat_var[orbit_element][1]:
                                    [dfd.iloc[i, 2], dfd.iloc[i+2, 2],
                                    dfd.iloc[i+2, 3], dfd.iloc[i+3, 1],
                                    dfd.iloc[i+3, 2], dfd.iloc[i+3, 3],
                                    dfd.iloc[i+4, 1]],
                                mat_var[orbit_element][2]:
                                    [dfd.iloc[i, 3], dfd.iloc[i+2, 3],
                                    dfd.iloc[i+4, 2], dfd.iloc[i+4, 3],
                                    dfd.iloc[i+5, 1], dfd.iloc[i+5, 2],
                                    dfd.iloc[i+5, 3]],
                                mat_var[orbit_element][3]:
                                    [dfd.iloc[i+1, 1], dfd.iloc[i+3, 1],
                                    dfd.iloc[i+4, 3], dfd.iloc[i+6, 1],
                                    dfd.iloc[i+6, 2], dfd.iloc[i+6, 3],
                                    dfd.iloc[i+7, 1]],
                                mat_var[orbit_element][4]:
                                    [dfd.iloc[i+1, 2], dfd.iloc[i+3, 2],
                                    dfd.iloc[i+5, 1], dfd.iloc[i+6, 2],
                                    dfd.iloc[i+7, 2], dfd.iloc[i+7, 3],
                                    dfd.iloc[i+8, 1]],
                                mat_var[orbit_element][5]:
                                    [dfd.iloc[i+1, 3], dfd.iloc[i+3, 3],
                                    dfd.iloc[i+5, 2], dfd.iloc[i+6, 3],
                                    dfd.iloc[i+7, 3], dfd.iloc[i+8, 2],
                                    dfd.iloc[i+8, 3]],
                                ngr_parameter: [dfd.iloc[i+2, 1],
                                                dfd.iloc[i+4, 1],
                                                dfd.iloc[i+5, 3],
                                                dfd.iloc[i+7, 1],
                                                dfd.iloc[i+8, 1],
                                                dfd.iloc[i+8, 3],
                                                dfd.iloc[i+9, 1]]}
                    # Rename matrix indexes
                    matrix_indexes = mat_var[orbit_element] + [ngr_parameter]
                    # Build the matrix
                    mat = pd.DataFrame(mat_data, index=matrix_indexes)

                elif dimension == 8:
                    # Define matrix structure
                    mat_data = {mat_var[orbit_element][0]:
                                    [dfd.iloc[i, 1], dfd.iloc[i, 2],
                                    dfd.iloc[i, 3], dfd.iloc[i+1, 1],
                                    dfd.iloc[i+1, 2], dfd.iloc[i+1, 3],
                                    dfd.iloc[i+2, 1], dfd.iloc[i+2, 2]],
                                mat_var[orbit_element][1]:
                                    [dfd.iloc[i, 2], dfd.iloc[i+2, 3],
                                    dfd.iloc[i+3, 1], dfd.iloc[i+3, 2],
                                    dfd.iloc[i+3, 3], dfd.iloc[i+4, 1],
                                    dfd.iloc[i+4, 2], dfd.iloc[i+4, 3]],
                                mat_var[orbit_element][2]:
                                    [dfd.iloc[i, 3], dfd.iloc[i+3, 1],
                                    dfd.iloc[i+5, 1], dfd.iloc[i+5, 2],
                                    dfd.iloc[i+5, 3], dfd.iloc[i+6, 1],
                                    dfd.iloc[i+6, 2], dfd.iloc[i+6, 3]],
                                mat_var[orbit_element][3]:
                                    [dfd.iloc[i+1, 1], dfd.iloc[i+3, 2],
                                    dfd.iloc[i+5, 2], dfd.iloc[i+7, 1],
                                    dfd.iloc[i+7, 2], dfd.iloc[i+7, 3],
                                    dfd.iloc[i+8, 1], dfd.iloc[i+8, 2]],
                                mat_var[orbit_element][4]:
                                    [dfd.iloc[i+1, 2], dfd.iloc[i+3, 3],
                                    dfd.iloc[i+5, 3], dfd.iloc[i+7, 2],
                                    dfd.iloc[i+8, 3], dfd.iloc[i+9, 1],
                                    dfd.iloc[i+9, 2], dfd.iloc[i+9, 3]],
                                mat_var[orbit_element][5]:
                                    [dfd.iloc[i+1, 3], dfd.iloc[i+4, 1],
                                    dfd.iloc[i+6, 1], dfd.iloc[i+7, 3],
                                    dfd.iloc[i+9, 1], dfd.iloc[i+10, 1],
                                    dfd.iloc[i+10, 2], dfd.iloc[i+10, 3]],
                                'Area-to-mass ratio':
                                    [dfd.iloc[i+2, 1], dfd.iloc[i+4, 2],
                                    dfd.iloc[i+6, 2], dfd.iloc[i+8, 1],
                                    dfd.iloc[i+9, 2], dfd.iloc[i+10, 2],
                                    dfd.iloc[i+11, 1], dfd.iloc[i+11, 2]],
                                'Yarkovsky parameter':
                                    [dfd.iloc[i+2, 2], dfd.iloc[i+4, 3],
                                    dfd.iloc[i+6, 3], dfd.iloc[i+8, 2],
                                    dfd.iloc[i+9, 3], dfd.iloc[i+10, 3],
                                    dfd.iloc[i+11, 2], dfd.iloc[i+11, 3]]}
                    # Rename matrix indexes
                    matrix_indexes = mat_var[orbit_element] +\
                        ['Area-to-mass ratio', 'Yarkovsky parameter']
                    # Build the matrix
                    mat = pd.DataFrame(mat_data, index=matrix_indexes)
        else:   # pragma: no cover
            raise ValueError('Valid matrix name are cov, cor and nor')

        return mat

    @staticmethod
    def _get_head_orb(data_obj):
        """Get and parse header of orbit properties file.

        Parameters
        ----------
        data_obj : object
            Object data in byte format.

        Returns
        -------
        form : str
            Format file.
        rectype : str
            File record type.
        refsys : str
            Default reference system.
        """
        # Decode data using UTF-8 and store in memory for doc info
        df_info_d = io.StringIO(data_obj.decode('utf-8'))
        # Read as txt file
        df_info = pd.read_fwf(df_info_d, nrows=3, header=None)
        # Template for format data:
        # format  = '{format}'       ! file format
        format_txt = df_info.iloc[0][0].split("'")[1].strip()
        form = format_txt
        # Template for record type:
        # rectype = '{rectype}'           ! record type (1L/ML)
        rectype = df_info.iloc[1][0].split("'")[1].strip()
        # Template for reference system:
        # refsys  = {refsys}     ! default reference system"
        refsys = df_info.iloc[2][0].split("=")[1].split("!")[0].strip()

        return form, rectype, refsys

    def _orb_prop_parser(self, data_obj):
        """Get orbit properties parsed from object data

        Parameters
        ----------
        data_obj : object
            Object data in byte format.

        Raises
        ------
        ValueError
            If the orbit properties file is empty or does not exists
        """
        # Decode data using UTF-8 and store in memory for orb props
        df_orb_d = io.StringIO(data_obj.decode('utf-8'))
        # Check file exists or is not empty
        if not df_orb_d.getvalue():
            logging.warning('Required orbit properties file is '
                            'empty for this object')
            raise ValueError('Required orbit properties file is '
                             'empty for this object')

        # Obtain header
        df_head = self._get_head_orb(data_obj)
        self.form = df_head[0]
        self.rectype = df_head[1]
        self.refsys = df_head[2]
        # Check if there is an additional line
        df_check_d = io.StringIO(data_obj.decode('utf-8'))
        # Read as txt file
        df_check = pd.read_fwf(df_check_d, skiprows=[0,1,2,3,4],
                               header=None, engine='python',
                               delim_whitespace=True)
        if 'SOLUTION' in df_check.iloc[0][0]:
            last_skip_rows = [0,1,2,3,4,5,10]
        else:
            last_skip_rows = [0,1,2,3,4,9]
        # Read data as csv
        df_orb = pd.read_csv(df_orb_d, delim_whitespace=True,
                             skiprows=last_skip_rows,
                             engine='python')
        # Epoch in MJD
        self.epoch = df_orb.iloc[1, 1] + ' MJD'
        # MAG
        # Get MAG index
        mag_index = get_indexes(df_orb, 'MAG')
        # Check if U_par parameter is assigned
        if bool(mag_index) is False:
            self.mag = 'There is no MAG assigned to this object'
            if 'SOLUTION' in df_check.iloc[0][0]:
                last_skip_rows = [0,1,2,3,4,5,9]
            else:
                last_skip_rows = [0,1,2,3,4,8]
        else:
            mag = df_orb.iloc[2:3, 1:3].reset_index(drop=True)
            # MAG - Rename columns and indexes
            mag.index = ['MAG']
            mag.columns = ['', '']
            self.mag = mag.astype(float)
        # Decode data using UTF-8 and store in memory for lsp
        df_new_d = io.StringIO(data_obj.decode('utf-8'))
        # Read data as csv
        df_new = pd.read_csv(df_new_d, delim_whitespace=True,
                             skiprows=last_skip_rows,
                             engine='python')
        # LSP
        # Get LSP index
        lsp_index = get_indexes(df_new, 'LSP')[0][0]
        # Check if there are additional non-gravitational parameters
        if int(df_new.iloc[lsp_index,3]) == 7:
            lsp = df_new.iloc[lsp_index:lsp_index+1, 1:5]
            lsp.columns = ['model used', 'number of model parameters',
                       'dimension', 'list of parameters determined']
            ngr = df_new.iloc[lsp_index+3:lsp_index+4, 1:3].astype(float)
            ngr.index = ['NGR']
            ngr.columns = ['Area-to-mass ratio in m^2/ton',
                           'Yarkovsky parameter in 1E-10au/day^2']
        elif int(df_new.iloc[lsp_index,3]) == 8:
            lsp = df_new.iloc[lsp_index:lsp_index+1, 1:6]
            lsp.columns = ['model used', 'number of model parameters',
                        'dimension', 'list of parameters determined', '']
            ngr = df_new.iloc[lsp_index+3:lsp_index+4, 1:3].astype(float)
            ngr.index = ['NGR']
            ngr.columns = ['Area-to-mass ratio in m^2/ton',
                           'Yarkovsky parameter in 1E-10au/day^2']
        else:
            lsp = df_new.iloc[lsp_index:lsp_index+1, 1:4]
            lsp.columns = ['model used', 'number of model parameters',
                       'dimension']
            ngr = ('There are no gravitational parameters '
                        'calculated for this object')
        # Rename indexes
        lsp.index = ['LSP']
        self.lsp = lsp.astype(int)
        # Non-gravitational parameters
        self.ngr = ngr


class KeplerianOrbitProperties(OrbitProperties):
    """This class contains information of asteroid orbit
    properties in Keplerian reference frame. This class inherits the attributes
    from OrbitProperties.

    Attributes
    ----------
    kep : pandas.DataFrame
        Data frame which contains the Keplerian elements information.
    perihelion : int
        Orbit perihelion in au.
    aphelion : int
        Orbit aphelion in au.
    anode : int
        Ascending node-Earth separation in au.
    dnode : int
        Descending node-Earth separation in au.
    moid : int
        Minimum Orbit Intersection distance in au.
    period : int
        Orbit period in days.
    pha : string
        Potential hazardous asteroid classification.
    vinfty : int
        Infinite velocity.
    u_par : int
        Uncertainty parameter as defined by MPC.
    orb_type : string
        Type of orbit.
    rms : pandas.DataFrame
        Root mean square for Keplerian elements
    cov : pandas.DataFrame
        Covariance matrix for Keplerian elements
    cor : pandas.DataFrame
        Correlation matrix for Keplerian elements

    """

    def __init__(self):
        """Initialization of class attributes
        """
        # Get attributes from paren OrbitProperties
        super().__init__()
        # Orbit properties
        self.kep = []
        self.perihelion = []
        self.aphelion = []
        self.anode = []
        self.dnode = []
        self.moid = []
        self.period = []
        self.pha = []
        self.vinfty = []
        self.u_par = []
        self.orb_type = []
        self.rms = []
        # Covariance and correlation matrices
        self.cov = []
        self.cor = []

    def _orb_kep_prop_parser(self, data_obj):
        """Get orbit properties parsed from object data

        Parameters
        ----------
        data_obj : object
            Object data in byte format.

        Raises
        ------
        ValueError
            If the required orbit properties file is empty or does not
            exist
        """
        # Assign parent attributes
        self._orb_prop_parser(data_obj)
        # Decode data using UTF-8 and store in memory for orb props
        df_orb_d = io.StringIO(data_obj.decode('utf-8'))
        # Read data as csv
        df_orb = pd.read_csv(df_orb_d, delim_whitespace=True,
                            skiprows=[0,1,2,3,4,9], engine='python')
        # Keplerian elements
        keplerian = df_orb.iloc[0:1, 1:7]
        # Kep - Rename columns and indexes
        keplerian.columns = ['a', 'e', 'i', 'long. node',
                            'arg. peric.', 'mean anomaly']
        keplerian.index = ['KEP']
        self.kep = keplerian.astype(float)
        # Get perihelion index to provide location for rest of attributes
        perihelion_index = get_indexes(df_orb, 'PERIHELION')[0][0]
        # Perihelion
        self.perihelion = float(df_orb.iloc[perihelion_index, 2])
        # Aphelion
        self.aphelion = float(df_orb.iloc[perihelion_index+1, 2])
        # Ascending node - Earth Separation
        self.anode = float(df_orb.iloc[perihelion_index+2, 2])
        # Descending node - Earth Separation
        self.dnode = float(df_orb.iloc[perihelion_index+3, 2])
        # MOID (Minimum Orbit Intersection Distance)
        self.moid = float(df_orb.iloc[perihelion_index+4, 2])
        # Period
        self.period = float(df_orb.iloc[perihelion_index+5, 2])
        # PHA (Potential Hazardous Asteroid)
        self.pha = df_orb.iloc[perihelion_index+6, 2]
        # Vinfty
        self.vinfty = float(df_orb.iloc[perihelion_index+7, 2])
        # U_par
        check_upar = get_indexes(df_orb, 'U_PAR')
        # Check if U_par parameter is assigned
        if bool(check_upar) is False:
            self.u_par = 'There is no u_par assigned to this object'
        else:
            self.u_par = float(df_orb.iloc[check_upar[0][0], 2])

        # Get index for RMS
        rms_index = get_indexes(df_orb, 'RMS')[0][0]
        # Determine Orb Type parameter knowing the RMS index
        self.orb_type = str(df_orb.iloc[rms_index-1, 2])
        # Check the dimension of the matrix to give complete RMS
        matrix_dimension = int(self.lsp.iloc[0, 2])
        if matrix_dimension == 8:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:10]
            # Rename colums
            rms.columns = ['a', 'e', 'i', 'long. node', 'arg. peric.',
                       'mean anomaly', 'Area-to-mass ratio',
                       'Yarkovsky parameter']
            ngr_parameter = 'Yarkovsky parameter and Area-to-mass ratio'
        elif matrix_dimension == 7:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:9]
            # Check which of NGR parameters is 0 to rename cols
            if float(self.ngr.iloc[0][0]) == 0:
                ngr_parameter = 'Yarkovsky parameter'
            else:
                ngr_parameter = 'Area-to-mass ratio'
            # Rename columns
            rms.columns = ['a', 'e', 'i', 'long. node',
                               'arg. peric.', 'mean anomaly',
                               ngr_parameter]
        else:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:8]
            #Rename columns
            rms.columns = ['a', 'e', 'i', 'long. node', 'arg. peric.',
                       'mean anomaly']
            ngr_parameter = 'There are no additional NRG parameters'

        # RMS - Rename indexes
        rms.index = ['RMS']
        self.rms = rms.astype(float)
        # Covariance matrix
        self.cov = self._get_matrix(df_orb, 'cov', matrix_dimension,
                                   'keplerian', ngr=ngr_parameter)\
                       .astype(float)
        # Correlation matrix
        self.cor = self._get_matrix(df_orb, 'cor', matrix_dimension,
                                   'keplerian', ngr=ngr_parameter)\
                       .astype(float)


class EquinoctialOrbitProperties(OrbitProperties):
    """This class contains information of asteroid orbit
    properties in equinoctial reference frame. This class inherits
    the attributes from OrbitProperties.

    Attributes
    ----------
    equinoctial : pandas.DataFrame
        Data frame which contains the equinoctial elements information.
    rms : DataFrame
        Root Mean Square for equinoctial elements.
    eig : pandas.DataFrame
        Eigenvalues for the covariance matrix.
    wea : pandas.DataFrame
        Eigenvector corresponding to the largest eigenvalue.
    cov : pandas.DataFrame
        Covariance matrix for equinoctial elements.
    nor : pandas.DataFrame
        Normalization matrix for equinoctial elements.

    """

    def __init__(self):
        """Initialization of class attributes
        """
        # Get attributes from paren OrbitProperties
        super().__init__()
        # Orbit properties
        self.equinoctial = []
        self.rms = []
        self.eig = []
        self.wea = []
        # Covariance and nor matrices
        self.cov = []
        self.nor = []

    def _orb_equi_prop_parser(self, data_obj):
        """Get orbit properties parsed from object data

        Parameters
        ----------
        data_obj : object
            Object data in byte format.

        Raises
        ------
        ValueError
            If the required orbit properties file is empty or does not
            exist
        """
        # Assign parent attributes
        self._orb_prop_parser(data_obj)
        # Decode data using UTF-8 and store in memory for orb props
        df_orb_d = io.StringIO(data_obj.decode('utf-8'))
        # Check if there is an additional line
        df_check_d = io.StringIO(data_obj.decode('utf-8'))
        # Read as txt file
        df_check = pd.read_fwf(df_check_d, skiprows=[0,1,2,3,4],
                               header=None, engine='python',
                               delim_whitespace=True)
        if 'SOLUTION' in df_check.iloc[0][0]:
            last_skip_rows = [0,1,2,3,4,5,10]
        else:
            last_skip_rows = [0,1,2,3,4,9]

        # Read data as csv
        df_orb = pd.read_csv(df_orb_d, delim_whitespace=True,
                            skiprows=last_skip_rows, engine='python')
        # Equinoctial elements
        equinoctial = df_orb.iloc[0:1, 1:7]
        # Equinoctial - Rename columns and indexes
        equinoctial.columns = ['a', 'e*sin(LP)', 'e*cos(LP)',
                               'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)',
                               'mean long.']
        equinoctial.index = ['EQU']
        self.equinoctial = equinoctial.astype(float)
        # Get index for RMS
        rms_index = get_indexes(df_orb, 'RMS')[0][0]
        # Check the dimension of the matrix to give complete RMS
        matrix_dimension = int(self.lsp.iloc[0, 2])
        if matrix_dimension == 8:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:10]
            # EIG
            eig = df_orb.iloc[rms_index+1:rms_index+2, 2:10]
            # WEA
            wea = df_orb.iloc[rms_index+2:rms_index+3, 2:10]
            # Assign column names
            column_names = ['a', 'e*sin(LP)', 'e*cos(LP)',
                            'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)',
                            'mean long.', 'Area-to-mass ratio',
                            'Yarkovsky parameter']
            ngr_parameter = 'Yarkovsky parameter and Area-to-mass ratio'

        elif matrix_dimension == 7:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:9]
            # EIG
            eig = df_orb.iloc[rms_index+1:rms_index+2, 2:9]
            # WEA
            wea = df_orb.iloc[rms_index+2:rms_index+3, 2:9]
            # Check which of NGR parameters is 0 to rename cols
            if float(self.ngr.iloc[0][0]) == 0:
                ngr_parameter = 'Yarkovsky parameter'
            else:
                ngr_parameter = 'Area-to-mass ratio'
            # Assign column names
            column_names = ['a', 'e*sin(LP)', 'e*cos(LP)',
                               'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)',
                               'mean long.',
                               ngr_parameter]
        else:
            # RMS (Root Mean Square)
            rms = df_orb.iloc[rms_index:rms_index+1, 2:8]
            # EIG
            eig = df_orb.iloc[rms_index+1:rms_index+2, 2:8]
            # WEA
            wea = df_orb.iloc[rms_index+2:rms_index+3, 2:8]
            # Assign column names
            column_names = ['a', 'e*sin(LP)', 'e*cos(LP)',
                           'tan(i/2)*sin(LN)', 'tan(i/2)*cos(LN)',
                           'mean long.']
            ngr_parameter = 'There are no additional NRG parameters'

        # Rename columns
        rms.columns = eig.columns = wea.columns = column_names
        # RMS - Rename indexes
        rms.index = ['RMS']
        self.rms = rms.astype(float)
        # EIG - Rename indexes
        eig.index = ['EIG']
        self.eig = eig.astype(float)
        # EIG - Rename indexes
        wea.index = ['WEA']
        self.wea = wea.astype(float)
        # Covariance matrix
        self.cov = self._get_matrix(df_orb, 'cov', matrix_dimension,
                                   'equinoctial', ngr=ngr_parameter)\
                       .astype(float)
        # Correlation matrix
        self.nor = self._get_matrix(df_orb, 'nor', matrix_dimension,
                                   'equinoctial', ngr=ngr_parameter)\
                       .astype(float)


class Ephemerides:
    """This class contains information of object ephemerides.

    Attributes
    ----------
    observatory : str
        Name of the observatory from which ephemerides are obtained.
    tinit : str
        Start date from which ephemerides are obtained.
    tfinal : str
        End date from which ephemerides are obtained.
    tstep : str
        Time step and time unit used during ephemerides calculation.
    ephemerides : pandas.DataFrame
        Data frame which contains the information of the object
        ephemerides.

    """

    def __init__(self):
        """Initialization of class attributes
        """
        # # Document info
        self.observatory = []
        self.tinit = []
        self.tfinal = []
        self.tstep = []
        # Ephemerides
        self.ephemerides = []

    @staticmethod
    def _get_head_ephem(data_obj):
        """Get and parse header of ephemerides file.

        Parameters
        ----------
        data_obj : object
            Object in bytes format.

        Returns
        -------
        obs : str
            Observatory name.
        idate : str
            Start date of the ephemerides.
        fdate : str
            Final date of the ephemerides.
        tstep : str
            Value and units for time step.
        """
        data_d = io.StringIO(data_obj.decode('utf-8'))
        head_ephe = pd.read_fwf(data_d, nrows=5, header=None)
        # Template for observatory: Observatory: {observatory}
        obs = head_ephe.iloc[1][0].split(':')[1].strip()
        # Template for initial date: Initial Date: {init_date}
        idate = head_ephe.iloc[2][0].split(':')[1].strip() + ':' +\
            head_ephe.iloc[2][0].split(':')[2].strip()
        # Template for initial date: Final Date: {final_date}
        fdate = head_ephe.iloc[3][0].split(':')[1].strip() + ':' +\
            head_ephe.iloc[3][0].split(':')[2].strip()
        # Template for initial date: Time step: {step}
        tstep = head_ephe.iloc[4][0].split(':')[1].strip()


        return obs, idate, fdate, tstep

    def _ephem_parser(self, name, observatory, start, stop, step, step_unit):
        """Parse and arrange the ephemeries data.

            Parameters
            ----------
            name : str
                Name of the requested object.
            observatory :
                Name of the observatory from which ephemerides are obtained.
            start : str
                Start date from which ephemerides are obtained.
            stop : str
                End date from which ephemerides are obtained.
            step : str
                Value for the time step (e.g. '1', '0.1', etc.).
            step_unit : str
                Units of the time step.
            Raises
            ------
            KeyError
                Some of the parameters introduced in the method is not
                valid.
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

        except ConnectionError: # pragma: no cover
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
        check = io.StringIO(data_obj.decode('utf-8'))
        check_r = pd.read_fwf(check, delimiter='"', header=None)
        if len(check_r) == 1:
            error = check_r[0][0]
            raise KeyError(error)

        # Get ephemerides if file is correct
        ephems_d = io.StringIO(data_obj.decode('utf-8'))
        # Since ephemerides col space is fixed, it is defined in order
        # to set the length (number of spaces) for each field
        col_space = [(1,12), (13,19), (20,32) ,(34,37), (38,40),
                     (41,47), (49,52), (53,55), (56, 61), (62,68),
                     (69,74), (75,83), (84, 95), (96,102), (103, 109),
                     (110,116), (117,122), (123,128), (129,136),
                     (137,144), (146,154), (156,164), (166,174),
                     (175,180), (182,189), (192,199), (201,206)]
        # Read pandas as txt
        ephem = pd.read_fwf(ephems_d, header=None, skiprows=9,
                            engine='python', colspecs=col_space)
        # Rename columns
        ephem.columns = ['Date', 'Hour', 'MJD in UTC', 'RA h', 'RA m',
                         'RA s', 'DEC d', 'DEC \'','DEC "', 'Mag',
                         'Alt (deg)', 'Airmass', 'Sun elev. (deg)',
                         'SolEl (deg)', 'LunEl (deg)', 'Phase (deg)',
                         'Glat (deg)', 'Glon (deg)', 'R (au)',
                         'Delta (au)', 'Ra*cosDE ("/min)',
                         'DEC ("/min)', 'Vel ("/min)', 'PA (deg)',
                         'Err1 (")', 'Err2 (")', 'AngAx (deg)']
        # Convert Date to datetime iso format
        ephem['Date'] = pd.to_datetime(ephem['Date'])
        # Convert Hout column to days
        ephem['Hour'] = ephem['Hour']/24
        # Add hours to date
        ephem['Date'] = ephem['Date'] + ephem['Hour'].map(timedelta)
        # Remove Hour column
        ephem = ephem.drop(['Hour'], axis=1)
        # Convert to str type and remove mid whitespaces from declination,
        # if any, and apply int format
        ephem['DEC d'] = ephem['DEC d'].astype(str)
        ephem['DEC d'] = ephem['DEC d'].str.replace(' ','').astype(int)
        #Adding help to ephemerides data frame
        ephem.help = ('Ephemerides data frame shows:\n'
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
        # Get header data
        header_date = self._get_head_ephem(data_obj)
        # Assign attributes
        self.ephemerides = ephem
        self.observatory = header_date[0]
        self.tinit = header_date[1]
        self.tfinal = header_date[2]
        self.tstep = header_date[3]


class Summary:
    """This class contains the information from the Summary tab.

    Attributes
    ----------
    physical_properties : pandas.DataFrame
        Data frame which contains the information of the object
        physical properties, their value and their units.
    discovery_date : str
        Provides the object discovery date
    observatory : str
        Provides the name of the observatory where object was discovered

    """

    def __init__(self):
        """Initialization of parameters
        """
        self.physical_properties = []
        self.discovery_date = []
        self.observatory = []

    def _summary_parser(self, name):
        """Parse and arrange the summary data

        Parameters
        ----------
        name : str
            Name of the requested object
        """
        # Final url = SUMMARY_URÑ + desig in which white spaces,
        # if any, are replaced by %20 to complete the designator
        url = SUMMARY_URL + str(name).replace(' ', '%20')

        # Read the url as html
        contents = requests.get(url, timeout=TIMEOUT,
                                verify=VERIFICATION).content
        # Parse html using BS
        parsed_html = BeautifulSoup(contents, 'lxml')
        # Summary properties are in </div>. Search for them:
        props = parsed_html.find_all("div",
                                     {"class": "simple-list__cell"})
        # Convert properties from BS to string type
        props_str = str(props).replace('<div class="simple-list__cell">',
                                    '').replace('</div>', '').\
                                        replace(',', '').strip()
        # Convert into bytes to allow pandas read
        props_byte = io.StringIO(props_str)
        props_df = pd.read_fwf(props_byte, engine='python', header=None)
        # Diameter property is an exception. Use BS and REGEX
        # to find and parse it
        diameter = parsed_html.find_all("span",
                                        {"id": re.compile("_NEOSearch_WAR_"\
                                                          "PSDBportlet_"\
                                                          ".*diameter-value.*"
                                                          )})
        # Obtain the text in the span location. Note that the diameter type
        # will be str since * can be given in the value. If this field is
        # not obtain then, there is no object so ValueErro appears
        try:
            diam_p = BeautifulSoup(str(diameter), 'html.parser').span.text
        except:
            logging.warning('Object not found: the name of the '
                            'object is wrong or misspelt')
            raise ValueError('Object not found: the name of the '
                             'object is wrong or misspelt')
        # Get indexes to locate the required properties.
        # In this code only the location of Absolute Magnitude is obtained
        index = get_indexes(props_df, 'Absolute Magnitude (H)')
        if index[0][1] == 0:
            index = index[0][0]
            # Adding a second index for Rotation Period since diameter can
            # change the dimensions of the line
            red_index = get_indexes(props_df, 'Rotation period (T)')
            red_index = red_index[0][0]
            physical_properties = {'Physical Properties':
                                    ['Absolute Magnitude (H)',
                                    'Diameter', 'Taxonomic Type',
                                    'Rotation Period (T)'],
                                   'Value': [props_df[0][index+1],
                                            diam_p,
                                            props_df[0][index+9],
                                            props_df[0][red_index+1]],
                                   'Units': [props_df[0][index+2],
                                            props_df[0][index+7],
                                            ' ',
                                            props_df[0][red_index+2]]}
            # Create DataFrame
            physical_properties_df = pd.DataFrame(physical_properties)
            self.physical_properties = physical_properties_df
            # Assign attributes for discovery date and observatory
            if not get_indexes(props_df, 'Observatory'):
                self.discovery_date = 'Discovery date is not available'
                self.observatory = 'Observatory is not available'
            else:
                discovery_date = props_df[0][red_index+4]
                self.discovery_date = discovery_date
                observatory = props_df[0][red_index+6]
                self.observatory = observatory

        else:
            index = index[0][0]
            red_index = get_indexes(props_df, 'Rotation period (T)')
            red_index = red_index[0][0]
            physical_properties = {'Physical Properties':
                                    ['Absolute Magnitude (H)',
                                    'Diameter', 'Taxonomic Type',
                                    'Rotation Period (T)'],
                                   'Value': [props_df[1][index+1],
                                            diam_p,
                                            props_df[1][index+7],
                                            props_df[1][red_index+1]],
                                   'Units': [props_df[1][index+2],
                                            props_df[0][index+5],
                                            ' ',
                                            props_df[1][red_index+2]]}

            # Create DataFrame
            physical_properties_df = pd.DataFrame(physical_properties)
            self.physical_properties = physical_properties_df
            # Assign attributes for discovery date and observatory
            if not get_indexes(props_df, 'Observatory'):
                self.discovery_date = 'Discovery date is not available'
                self.observatory = 'Observatory is not available'
            else:
                discovery_date = props_df[1][red_index+4]
                self.discovery_date = discovery_date
                observatory = props_df[1][red_index+6]
                self.observatory = observatory
