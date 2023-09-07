# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Main module from ESA NEOCC library. This module contains the two main
methods of the library: *query_list* and *query_object*. The information
is obtained from ESA Near-Earth Object Coordination Centre's (NEOCC) web
portal: https://neo.ssa.esa.int/.
"""

import time

from astroquery.query import BaseQuery
from astroquery.utils import async_to_sync

from astroquery.esa.neocc import lists, tabs

__all__ = ['neocc', 'ESAneoccClass']


@async_to_sync
class ESAneoccClass(BaseQuery):
    """
    Class to init ESA NEOCC Python interface library
    """
    @staticmethod
    def query_list(list_name):
        """Get requested list data from ESA NEOCC.

        Different lists that can be requested are:

        * All NEA list: *nea_list*
        * Updated NEA list: *updated_nea*
        * Monthly computation date: *monthly_update*
        * Risk list (normal): *risk_list*
        * Risk list (special): *risk_list_special*
        * Close approaches (upcoming): *close_approaches_upcoming*
        * Close approaches (recent): *close_approaches_recent*
        * Priority list (normal): *priority_list*
        * Priority list (faint): *priority_list_faint*
        * Close encounter list: *close_encounter*
        * Impacted objects: *impacted_objects*
        * Catalogue of NEAs (current date): *neo_catalogue_current*
        * Catalogue of NEAs (middle arc): *neo_catalogue_middle*

        These lists are referenced in https://neo.ssa.esa.int/computer-access

        Parameters
        ----------
        list_name : str
            Name of the requested list. Valid names are: *nea_list,
            updated_nea, monthly_update, risk_list, risk_list_special,
            close_approaches_upcoming, close_approaches_recent, priority_list,
            priority_list_faint, close_encounter, impacted_objects,
            neo_catalogue_current and neo_catalogue_middle*.

        Returns
        -------
        neocc_lst : `~astropy.table.Table`
            Astropy Table which contains the data of the requested list.

        Examples
        --------
        **NEA list** The output of this list is a `~astropy.table.Table` which contains
        the list of all NEAs currently considered in the NEOCC system.

        >>> from astroquery.esa.neocc import neocc
        >>> list_data = neocc.query_list(list_name='nea_list')  # doctest: +REMOTE_DATA
        >>> print(list_data)  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
             NEA
        ---------------
               433 Eros
             719 Albert
             887 Alinda
           1036 Ganymed
              1221 Amor
            1566 Icarus
                    ...
                 2023RD
                 2023RE
                 2023RF
                6344P-L
        Length = 32558 rows

        **Close approaches (upcoming):**  The output of this list is a `~astropy.table.Table` which
        contains object with upcoming close approaches.

        >>> from astroquery.esa.neocc import neocc
        >>> list_data = neocc.query_list(list_name='close_approaches_upcoming')  # doctest: +REMOTE_DATA
        >>> print(list_data)  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
        Object Name           Date          ... Rel. vel in km/s CAI index
        ----------- ----------------------- ... ---------------- ---------
            2021JA5 2023-09-07 00:00:00.000 ...             11.0     3.496
            2023QC5 2023-09-08 00:00:00.000 ...              7.6     2.662
             2020GE 2023-09-08 00:00:00.000 ...              1.4     3.308
            2020RS1 2023-09-10 00:00:00.000 ...              9.1     4.071
            2023QE8 2023-09-10 00:00:00.000 ...             14.5     1.039
                ...                     ... ...              ...       ...
           2012SX49 2024-08-29 00:00:00.000 ...              4.3     2.665
           2016RJ20 2024-08-30 00:00:00.000 ...             14.8     2.118
             2021JT 2024-09-02 00:00:00.000 ...              8.3     4.216
           2021RB16 2024-09-02 00:00:00.000 ...              8.5     3.685
            2007RX8 2024-09-02 00:00:00.000 ...              7.0     2.322
        Length = 176 rows

        Note
        ----
        If the contents request fails the following message will be printed:

        *Initial attempt to obtain list failed. Reattempting...*

        Then a second request will be automatically sent to the NEOCC portal.
        """

        # Get URL to obtain the data from NEOCC
        url = lists.get_list_url(list_name)

        # Request list two times if the first attempt fails
        try:
            # Parse decoded data
            neocc_list = lists.get_list_data(url, list_name)

            return neocc_list

        except ConnectionError:  # pragma: no cover
            print('Initial attempt to obtain list failed. Reattempting...')
            # Wait 5 seconds
            time.sleep(5)
            # Parse decoded data
            neocc_list = lists.get_list_data(url, list_name)

            return neocc_list

    @staticmethod
    def query_object(name, tab, **kwargs):
        """Get requested object data from ESA NEOCC.

        Parameters
        ----------
        name : str
            Name of the requested object
        tab : str
            Name of the request tab. Valid names are: summary,
            orbit_properties, physical_properties, observations,
            ephemerides, close_approaches and impacts.
        **kwargs : str
            Tabs orbit_properties and ephemerides tabs required additional
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
        neocc_obj : list of `~astropy.table.Table`
            One or more tables containing the requested object data.
            the tab selected.

        Examples
        --------
        **Impacts**: This example shows several ways to build a table query for the
        impacts table. Note that this table only requires the name of the object
        as input and returns only a single table.

        The information can be obtained introducing directly the name of
        the object, but it can be also added from the output of a
        *query_list* search:

        >>> from astroquery.esa.neocc import neocc
        >>> ast_impacts = neocc.query_object(name='1979XB', tab='impacts')  # doctest: +REMOTE_DATA

        or

        >>> nea_list = neocc.query_list(list_name='nea_list')  # doctest: +REMOTE_DATA
        >>> print(nea_list["NEA"][3163])  # doctest: +REMOTE_DATA
        1979XB
        >>> ast_impacts = neocc.query_object(name=nea_list["NEA"][3163], tab='impacts')  # doctest: +REMOTE_DATA

        or

        >>> risk_list = neocc.query_list(list_name='risk_list')  # doctest: +REMOTE_DATA
        >>> print(risk_list['Object Name'][1])  # doctest: +REMOTE_DATA
        1979XB
        >>> ast_impacts = neocc.query_object(name=risk_list['Object Name'][1], tab='impacts')  # doctest: +REMOTE_DATA

        This query returns a list containing a single table:

        >>> print(ast_impacts[0])  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
                  date             MJD    sigma  sigimp ... Exp. Energy in MT   PS   TS
        ----------------------- --------- ------ ------ ... ----------------- ----- ---
        2056-12-12 21:38:52.800 72344.902  0.255    0.0 ...             0.013 -2.86   0
        2065-12-16 11:06:43.200 75635.463  -1.11    0.0 ...           3.3e-05 -5.42   0
        2101-12-14 04:53:45.600 88781.204 -0.384    0.0 ...           8.6e-05 -5.32   0
        2113-12-14 18:04:19.200 93164.753 -0.706    0.0 ...           0.00879 -3.35   0


        Note
        ----
            Most of the tables returned by this tye of query contain additional information
            in the 'meta' property, including information about the table columns.

            >>> print(ast_impacts[0].meta.keys())  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
            odict_keys(['Column Info', 'observation_accepted', 'observation_rejected',
                        'arc_start', 'arc_end', 'info', 'computation'])


        **Physical Properties:** This example shows how to obtain the physical properties table.

        >>> from astroquery.esa.neocc import neocc
        >>> properties = neocc.query_object(name='433', tab='physical_properties')  # doctest: +REMOTE_DATA

        Again, the output is a list containing a single table.

        >>> print(properties[0])  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
                Property        ...
        ----------------------- ...
         Absolute Magnitude (H) ...
         Absolute Magnitude (H) ...
                         Albedo ...
                      Amplitude ...
        Color Index Information ...
        Color Index Information ...
        Color Index Information ...
        Color Index Information ...
                       Diameter ...
                        Quality ...
             Rotation Direction ...
                Rotation Period ...
                      Sightings ...
                      Sightings ...
            Slope Parameter (G) ...
                   Spinvector B ...
                   Spinvector L ...
                       Taxonomy ...
                 Taxonomy (all) ...


        **Observations:** In this example we query for Observations tables, a query that
        returns a list containing 3-5 `astropy.table.Table`s depending if there are
        "Roving observer" or satellite observations.

        >>> ast_observations = neocc.query_object(name='99942', tab='observations')  # doctest: +REMOTE_DATA
        >>> for tab in ast_observations:  # doctest: +REMOTE_DATA
        ...     print(tab.meta["Title"])
        Observation metadata
        Optical Observations
        Satellite  Observations
        Radar Observations
        >>> sat_obs = ast_observations[2]  # doctest: +REMOTE_DATA
        >>> print(sat_obs)  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
        Design.  K   T   N  ...     X              Y                 Z          Obs Code
        ------- --- --- --- ... ---------- ----------------- ------------------ --------
          99942   S   s  -- ... -5634.1734        -2466.2657         -3038.3924      C51
          99942   S   s  -- ... -5654.1816        -2501.9465         -2971.1902      C51
          99942   S   s  -- ... -5645.7831        -2512.1036         -2978.6411      C51
          99942   S   s  -- ... -5617.3465        -2486.4031         -3053.2209      C51
          99942   S   s  -- ... -5620.3829        -2542.3521         -3001.1135      C51
            ... ... ... ... ...        ...               ...                ...      ...
          99942   S   s  -- ... -4105.3228 5345.915299999999          1235.1318      C51
          99942   S   s  -- ... -4117.8192         5343.1834          1205.2107      C51
          99942   S   s  -- ... -4137.4411         5329.7318          1197.3972      C51
          99942   S   s  -- ... -4144.5939 5319.084499999999          1219.4675      C51
        Length = 1357 rows

        **Close Approaches**: This example queris for close approaches, another query
        which results in a single data table.

        >>> close_appr = neocc.query_object(name='99942', tab='close_approaches')  # doctest: +REMOTE_DATA
        >>> print(close_appr[0])  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
        BODY      CALENDAR-TIME          MJD-TIME    ...  STRETCH    WIDTH   PROBABILITY
        ----- ----------------------- --------------- ... --------- --------- -----------
        EARTH 1957-04-01T03:19:44.544 35929.138710654 ... 2.871e-05 5.533e-09         1.0
        EARTH 1964-10-24T21:44:40.127 38692.906017295 ...  1.72e-05 5.033e-09         1.0
        EARTH 1965-02-11T12:15:30.527 38802.510774301 ... 4.732e-06 1.272e-09         1.0
        EARTH 1972-12-24T11:51:41.472 41675.494228687 ... 1.584e-05 4.627e-09         1.0
        EARTH 1980-12-18T01:51:14.400 44591.077250448 ... 1.136e-05 5.436e-09         1.0
          ...                     ...             ... ...       ...       ...         ...
        EARTH 2087-04-07T09:10:54.912 83417.382583343 ...   0.01214 3.978e-08         1.0
        EARTH 2102-09-11T03:12:44.640 89052.133849042 ...   0.08822 1.191e-06       0.751
        EARTH 2109-03-22T13:19:55.200 91436.555501683 ...    0.3509 1.066e-06       0.189
        EARTH 2109-06-08T14:21:12.384 91514.598061046 ...    0.1121 1.149e-06       0.577
        EARTH 2116-04-07T12:48:42.912  94009.53382919 ...    0.7074 9.723e-08      0.0943
        [18 rows x 10 columns]

        **Orbit Properties:** In order to access the orbital properties
        information, it is necessary to provide two additional inputs to
        *query_object* method: `orbital_elements` andv`orbit_epoch`.

        This query returns a list of three tables, the orbital properties, and the covariance
        and corotation matrices.

        >>> ast_orbit_prop = neocc.query_object(name='99942', tab='orbit_properties', orbital_elements='keplerian',
        ...                                     orbit_epoch='present')  # doctest: +REMOTE_DATA
        >>> for tab in ast_orbit_prop:  # doctest: +REMOTE_DATA
        ...     print(tab.meta["Title"])
        Orbital Elements
        COV
        COR
        >>> print(ast_orbit_prop[0][:5])  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
        Section  Property          Value
        -------- -------- -----------------------
           ANODE    ANODE -8.6707715058413322E-04
        APHELION APHELION  1.0993687643243035E+00
           DNODE    DNODE -1.9894296321957006E-01
          HEADER   format                  OEF2.0
          HEADER  rectype                      ML


        **Ephemerides:** In order to access ephemerides information, it
        is necessary to provide five additional inputs to *query_object*
        method: `observatory`, `start`, `stop`, `step` and `step_unit`.

        >>> ast_ephemerides = neocc.query_object(name='99942', tab='ephemerides', observatory='500',
        ...                                      start='2019-05-08 01:30', stop='2019-05-23 01:30',
        ...                                      step='1', step_unit='days')  # doctest: +REMOTE_DATA
        >>> ast_ephemerides = ast_ephemerides[0]  # doctest: +REMOTE_DATA
        >>> print(ast_ephemerides.meta.keys())  # doctest: +REMOTE_DATA
        odict_keys(['Ephemerides generation for', 'Observatory', 'Initial Date',
                    'Final Date', 'Time step', 'Column Info'])
        >>> print(ast_ephemerides)  # doctest: +IGNORE_OUTPUT +REMOTE_DATA
                  Date          MJD (UTC)  RA (h  m  s) ... Err1 (") Err2 (") AngAx (deg)
        ----------------------- ---------- ------------ ... -------- -------- -----------
        2019-05-08T01:30:00.000 58611.0625  6 43 40.510 ...    0.001      0.0       115.8
        2019-05-09T01:30:00.000 58612.0625  6 47 20.055 ...    0.001      0.0       117.3
        2019-05-10T01:30:00.000 58613.0625  6 50 59.059 ...    0.001      0.0       119.0
        2019-05-11T01:30:00.000 58614.0625  6 54 37.518 ...    0.001      0.0       120.8
        2019-05-12T01:30:00.000 58615.0625  6 58 15.428 ...    0.001      0.0       122.8
                            ...        ...          ... ...      ...      ...         ...
        2019-05-19T01:30:00.000 58622.0625  7 23 25.375 ...    0.001      0.0       143.8
        2019-05-20T01:30:00.000 58623.0625  7 26 58.899 ...    0.001      0.0       147.6
        2019-05-21T01:30:00.000 58624.0625  7 30 31.891 ...    0.001      0.0       151.5
        2019-05-22T01:30:00.000 58625.0625  7 34  4.357 ...    0.001    0.001       155.2
        2019-05-23T01:30:00.000 58626.0625  7 37 36.303 ...    0.001    0.001       158.7
        """

        # Define a list with all possible tabs to be requested
        tab_list = ['impacts', 'close_approaches', 'observations',
                    'physical_properties', 'orbit_properties',
                    'ephemerides', 'summary']

        # Check the input of the method if tab is not in the list
        # print and error and show the valid names
        if tab not in tab_list:
            raise KeyError(("Please introduce a valid table name. "
                           f"Valid names are: {', '.join(tab_list)}"))
        # Depending on the tab selected the information will be requested
        # following different methods. Create "switch" for each case:

        # Impacts, close approaches and observations
        if tab in ('impacts', 'close_approaches', 'observations',
                   'physical_properties'):
            # Get URL to obtain the data from NEOCC
            url = tabs.get_object_url(name, tab)

            # Request data two times if the first attempt fails
            try:
                # Get object data
                data_obj = tabs.get_object_data(url)
            except ConnectionError:  # pragma: no cover
                print('Initial attempt to obtain object data failed. '
                      'Reattempting...')

                # Wait 5 seconds
                time.sleep(5)

                # Get object data
                data_obj = tabs.get_object_data(url)

            resp_str = data_obj.decode('utf-8')

            if tab == 'impacts':
                neocc_obj = tabs.parse_impacts(resp_str)
            elif tab == 'close_approaches':
                neocc_obj = tabs.parse_close_aproach(resp_str)
            elif tab == 'observations':
                neocc_obj = tabs.parse_observations(resp_str)
            elif tab == 'physical_properties':
                neocc_obj = tabs.parse_physical_properties(resp_str)

        # Orbit properties
        elif tab == 'orbit_properties':
            # Raise error if no elements are provided
            if 'orbital_elements' not in kwargs:
                raise KeyError('Please specify type of orbital_elements: '
                               'keplerian or equinoctial '
                               '(e.g., orbital_elements="keplerian")')

            # Raise error if no epoch is provided
            if 'orbit_epoch' not in kwargs:
                raise KeyError('Please specify type of orbit_epoch: '
                               'present or middle '
                               '(e.g., orbit_epoch="middle")')

            # Get URL to obtain the data from NEOCC
            url = tabs.get_object_url(name, tab,
                                      orbital_elements=kwargs['orbital_elements'],
                                      orbit_epoch=kwargs['orbit_epoch'])

            # Request data two times if the first attempt fails
            try:
                # Get object data
                data_obj = tabs.get_object_data(url)
            except ConnectionError:  # pragma: no cover
                print('Initial attempt to obtain object data failed. '
                      'Reattempting...')

                # Wait 5 seconds
                time.sleep(5)

                # Get object data
                data_obj = tabs.get_object_data(url)

            resp_str = data_obj.decode('utf-8')
            neocc_obj = tabs.parse_orbital_properties(resp_str)

        # Ephemerides
        elif tab == 'ephemerides':
            # Create dictionary for kwargs
            args_dict = {'observatory': 'observatory (e.g., observatory="500")',
                         'start': 'start date (e.g., start="2021-05-17 00:00")',
                         'stop': 'end date (e.g., stop="2021-05-18 00:00")',
                         'step': 'time step (e.g., step="1")',
                         'step_unit': 'step unit (e.g., step_unit="days")'}

            # Check if any kwargs is missing
            for element in args_dict:
                if element not in kwargs:
                    raise KeyError(f'Please specify {args_dict[element]} for ephemerides.')

            resp_str = tabs.get_ephemerides_data(name, observatory=kwargs['observatory'],
                                                 start=kwargs['start'], stop=kwargs['stop'],
                                                 step=kwargs['step'], step_unit=kwargs['step_unit'])
            neocc_obj = tabs.parse_ephemerides(resp_str)

        elif tab == 'summary':
            resp_str = tabs.get_summary_data(name)
            neocc_obj = tabs.parse_summary(resp_str)

        if not isinstance(neocc_obj, list):
            neocc_obj = [neocc_obj]

        return neocc_obj


neocc = ESAneoccClass()
