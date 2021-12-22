# -*- coding: utf-8 -*-
"""
Main module from ESA NEOCC library. This module contains the two main
methods of the library: *query_list* and *query_object*. The information
is obtained from ESA Near-Earth Object Coordination Centre's (NEOCC) web
portal: https://neo.ssa.esa.int/.

* Project: NEOCC portal Python interface
* Property: European Space Agency (ESA)
* Developed by: Elecnor Deimos
* Author: C. Álvaro Arroyo Parejo
* Issue: 2.1.0
* Date: 01-03-2021
* Purpose: Main module which gets NEAs data from https://neo.ssa.esa.int/
* Module: core.py
* History:

========   ===========   ============================================
Version    Date          Change History
========   ===========   ============================================
1.0        26-02-2021    Initial version
1.1        26-03-2021    Adding new docstrings
1.2        17-05-2021    Adding new docstrings for *help*
                         property in dataframes and *<tab>*
                         specification for obtaining attributes.\n
                         For orbit properties *orbit_elements*
                         changes to *orbital_elements*.\n
                         Adding impacted objects lists.\n
                         Minor typos changes.
1.3        16-06-2021    Renamed module from *neocc* to *core*.\n
                         Adding class type as for astroquery
                         implementation.\n
                         Define methods as static.\n
1.3.1      29-06-2021    No changes
1.4.0      29-10-2021    Adding new docstrings.\n
                         Change method for obtaining physical
                         properties
2.0.0      21-01-2022    Prepare module for Astroquery integration
2.1.0      01-03-2022    Remove *parse* dependency

© Copyright [European Space Agency][2022]
All rights reserved
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
        neocc_lst : *pandas.Series* or *pandas.DataFrame*
            Data Frame which contains the information of the requested list

        Examples
        --------
        **NEA list, Updated NEA list, Monthly computation date:** The output
        of this list is a *pandas.Series* which contains the list of all NEAs
        currently considered in the NEOCC system.

        >>> from astroquery.esa.neocc import neocc
        >>> list_data = neocc.query_list(list_name='nea_list')
        >>> list_data
        0            433 Eros
        1          719 Albert
        2          887 Alinda
        3        1036 Ganymed
        4           1221 Amor
                    ...
        25191          2021DY
        25192         2021DY1
        25193          2021DZ
        25194         2021DZ1
        25195         6344P-L
        Name: 0, Length: 25196, dtype: object

        Each asteroid can be accessed using its index. This information can
        be used as input for *query_object* method.

        >>> list_data[4]
        '1221 Amor'

        **Other lists:**  The output of this list is a *pandas.DataFrame* which
        contains the information of the requested list.

        >>> from astroquery.esa.neocc import neocc
        >>> list_data = neocc.query_list(list_name='close_approaches_upcoming')
        >>> list_data
                Object Name         Date   ...   Rel. vel in km/s
        0             2021DE  2021.156164  ...                26.0
        1             2021DM  2021.158904  ...                10.2
        2             2011DW  2021.161644  ...                13.6
        3           2011EH17  2021.161644  ...                16.8
        4            2016DV1  2021.164384  ...                18.6
        ..               ...          ...  ...                 ...
        141           2020DF  2022.120548  ...                 8.6
        142          2018CW2  2022.131507  ...                10.8
        143          2020CX1  2022.131507  ...                 8.2
        144  455176 1999VF22  2022.142466  ...                25.1
        145          2017CX1  2022.145205  ...                 5.0
        [146 rows x 10 columns]

        The information of the columns can be accessed through (see
        `pandas <https://pandas.pydata.org/pandas-docs/stable/index.html>`_
        for further information about data access):

        >>> list_data['Object Name']
        0               2021DE
        1               2021DM
        2               2011DW
        3             2011EH17
        4              2016DV1
                    ...
        141             2020DF
        142            2018CW2
        143            2020CX1
        144    455176 1999VF22
        145            2017CX1
        Name: Object Name, Length: 146, dtype: object

        And the information of the rows can be accessed using:

        >>> list_data.iloc[2]
        Object Name              2011DW
        Date                    2021.16
        Miss Distance in km     5333057
        Miss Distance in au    0.035649
        Miss Distance in LD      13.874
        Diameter in m                90
        *=Yes                         *
        H                          22.9
        Max Bright                 16.4
        Rel. vel in km/s           13.6
        Name: 2, dtype: object

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

        except ConnectionError: # pragma: no cover
            print('Initial attempt to obtain list failed. Reattempting...')
            # Wait 5 seconds
            time.sleep(5)
            # Parse decoded data
            neocc_list = lists.get_list_data(url, list_name)

            return neocc_list

    # pylint: disable=c0301
    # pylint: disable=w0212
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
        neocc_obj : object
            Object data which contains different attributes depending on
            the tab selected.

        Examples
        --------
        **Impacts, Physical Properties and Observations**: This example
        tries to summarize how to access the data of this tabs and how to
        use it. Note that this classes only require as inputs the name of
        the object and the requested tab.

        The information can be obtained introducing directly the name of
        the object, but it can be also added from the output of a
        *query_list* search:

        >>> from astroquery.esa.neocc import neocc
        >>> ast_impacts = neocc.query_object(name='1979XB', tab='impacts')

        or

        >>> nea_list = neocc.query_list(list_name='nea_list')
        >>> nea_list[2921]
        '1979XB'
        >>> ast_impacts = neocc.query_object(name=nea_list[2921], tab='impacts')

        or

        >>> risk_list = neocc.query_list(list_name='risk_list')
        >>> risk_list['Object Name'][1]
        '1979XB'
        >>> ast_impacts = neocc.query_object(name=risk_list['Object Name'][1],
                                            tab='impacts')

        The output provides an object with the different attributes:

        >>> ast_impacts.<tab>
        ast.additional_note       ast.impacts
        ast.arc_end               ast.info
        ast.arc_start             ast.observation_accepted
        ast.computation           ast.observation_rejected

        By adding the attribute its information can be accessed:

        >>> ast_impacts.impacts
                    date        MJD  sigma  ...  Exp. Energy in MT    PS  TS
        0  2056-12-12.902  72344.902  0.255  ...           0.011500 -3.22   0
        1  2065-12-16.462  75635.463 -1.110  ...           0.000090 -5.36   0
        2  2086-12-16.663  83305.664 -1.101  ...           0.002390 -4.03   0
        3  2101-12-14.203  88781.204 -0.384  ...           0.000131 -5.36   0
        4  2105-12-12.764  90240.765  1.003  ...           0.000574 -4.75   0
        5  2113-12-14.753  93164.753 -0.706  ...           0.018500 -3.25   0
        6  2113-12-14.756  93164.756 -0.708  ...           0.000163 -5.30   0
        7  2117-12-15.496  94626.496 -1.316  ...           0.000069 -5.68   0
        [8 rows x 11 columns]

        Note
        ----
            Most of the dataframes of the object tabs contain the
            'help' property which contains information about the fields
            of the dataframe.

            >>> print(ast_impacts.impacts.help)
            Data frame with possible impacts information:
            -Date: date for the potential impact in YYYY-MM-DD.ddd format
            -MJD: Modified Julian Day for the potential impact
            -sigma: approximate location along the Line Of Variation (LOV)
            in sigma space
            -sigimp: The lateral distance in sigma-space from the LOV to
            the Earth surface. A zero implies that the LOV passes through
            the Earth-dist: Minimum Distance in Earth radii. The lateral
            distance from the LOV to the centre of the Earth
            -width: one-sigma semi-width of the Target Plane confidence
            region in Earth radii
            -stretch: Stretching factor. It indicates how much the
            confidence region at the epoch has been stretched by the time
            of the approach. This is a close cousin of the Lyapounov
            exponent. Units are in Earth radii divided by sigma (RE/sig)
            -p_RE: probability of Earth Impact (IP)
            -Exp. Energy in MT: Expected energy. It is the product of the
            impact energy and the impact probability
            -PS: Palermo Scale
            -TS: Torino Scale

        Another example is shown to obtain the physical properties:

        >>> from astroquery.esa.neocc import neocc
        >>> properties = neocc.query_object(name='433', tab='physical_properties')

        Again, the output provides an object with different attributes:

        >>> properties.<tab>
        properties.physical_properties  properties.sources
        >>> properties.physical_properties
                        Property                  Value(s)                 Units              Reference(s)
        0           Rotation Period                      5.27                     h                       [4]
        1                   Quality                       4.0                     -                       [4]
        2                 Amplitude                 0.04-1.49                   mag                       [4]
        3        Rotation Direction                       PRO                     -                       [1]
        4              Spinvector L                      16.0                   deg                       [1]
        5              Spinvector B                       9.0                   deg                       [1]
        6                  Taxonomy                        Sq                     -                       [2]
        7            Taxonomy (all)                         S                     -                       [3]
        8    Absolute Magnitude (H)           [10.853, 10.31]            [mag, mag]                [[5], [6]]
        9       Slope Parameter (G)     [0.46**, 0.2, 0.46**]       [mag, mag, mag]           [[7], [8], [5]]
        10                   Albedo                      0.24                     -                       [9]
        11                 Diameter                   23300.0                     m                      [10]
        12  Color Index Information  [0.85, 0.48, 0.39, 0.52]  [B-V, V-R, R-I, U-B]  [[11], [11], [11], [12]]
        13                Sightings       [Radar R, Visual S]                [-, -]              [[13], [14]]


        Note
        ----
            For the case of tab Observations there are objects which contain
            "Roving observer" and satellite observations. In the original
            requested data the information of these observations produces two
            lines of data, where the second line does not fit the structure of
            the data frame
            (https://www.minorplanetcenter.org/iau/info/OpticalObs.html).
            In order to solve this problem those second lines
            have been extracted in another attribute (e.g. sat_observations or
            roving_observations) to make the data more readable.

            Since this information can be requested in pairs, i.e. it is needed
            to access both lines of data, this can be made using the date of the
            observations which will be the same for both attributes:

            >>> ast_observations = neocc.query_object(name='99942',
            tab='observations')
            >>> sat_obs = ast_observations.sat_observations
            >>> sat_obs
                Design.  K  T  N  YYYY  MM  DD.dddddd  ... Obs Code
            0     99942  S  s     2020  12   18.97667  ...      C51
            1     99942  S  s     2020  12   19.10732  ...      C51
            ...     ...            ...            ...  ...      ...
            10    99942  S  s     2021   1   16.92315  ...      C53
            11    99942  S  s     2021   1   19.36233  ...      C53
            12    99942  S  s     2021   1   19.36927  ...      C53
            >>> opt_obs = ast_ast_observations.optical_observations
            >>> opt_obs.loc[opt_obs['DD.dddddd'] == sat_obs['DD.dddddd'][0]]
                    Design.  K  T N  YYYY  MM  ...  Obs Code   Chi  A  M
            4582    99942    S  S    2020  12  ...       C51  1.13  1  1
            [1 rows x 33 columns]

        **Close Approaches**: This example corresponds to the class close
        approaches. As for the previous example, the information can be
        obtained by directly introducing the name of the object or from a
        previous *query_list* search.

        In this particular case, there are no attributes and the data obtained is
        a DataFrame which contains the information for close approaches:

        >>> close_appr = neocc.query_object(name='99942', tab='close_approaches')
        >>> close_appr
            BODY     CALENDAR-TIME  ...         WIDTH  PROBABILITY
        0   EARTH  1957/04/01.13908  ...  1.318000e-08        1.000
        1   EARTH  1964/10/24.90646  ...  1.119000e-08        1.000
        2   EARTH  1965/02/11.51118  ...  4.004000e-09        1.000
        ...   ...               ...  ...           ...          ...
        16  EARTH  2080/05/09.23878  ...  1.206000e-06        0.821
        17  EARTH  2087/04/07.54747  ...  1.254000e-08        0.327
        [18 rows x 10 columns]

        **Orbit Properties:** In order to access the orbit properties
        information, it is necessary to provide two additional inputs to
        *query_object* method: **orbital_elements** and **orbit_epoch**.

        It is mandatory to write these two parameters as: *orbit_epoch=' '*
        to make the library works.

        >>> ast_orbit_prop = neocc.query_object(name='99942',
        tab='orbit_properties',orbital_elements='keplerian', orbit_epoch='present')
        >>> ast_orbit_prop.<tab>
        ast_orbit_prop.anode       ast_orbit_prop.ngr
        ast_orbit_prop.aphelion    ast_orbit_prop.orb_type
        ast_orbit_prop.cor         ast_orbit_prop.perihelion
        ast_orbit_prop.cov         ast_orbit_prop.period
        ast_orbit_prop.dnode       ast_orbit_prop.pha
        ast_orbit_prop.epoch       ast_orbit_prop.rectype
        ast_orbit_prop.form        ast_orbit_prop.refsys
        ast_orbit_prop.kep         ast_orbit_prop.rms
        ast_orbit_prop.lsp         ast_orbit_prop.u_par
        ast_orbit_prop.mag         ast_orbit_prop.vinfty
        ast_orbit_prop.moid

        **Ephemerides:** In order to access ephemerides information, it
        is necessary to provide five additional inputs to *query_object*
        method: **observatory**, **start**, **stop**, **step** and
        **step_unit***.

        It is mandatory to write these five parameters as: *observatory=' '*
        to make the library works.

        >>> ast_ephemerides = neocc.query_object(name='99942',
        tab='ephemerides', observatory='500', start='2019-05-08 01:30',
        stop='2019-05-23 01:30', step='1', step_unit='days')
        >>> ast_ephemerides.<tab>
        ast_ephemerides.ephemerides  ast_ephemerides.tinit
        ast_ephemerides.observatory  ast_ephemerides.tstep
        ast_ephemerides.tfinal
        """

        # Define a list with all possible tabs to be requested
        tab_list = ['impacts', 'close_approaches', 'observations',
                    'physical_properties', 'orbit_properties',
                    'ephemerides', 'summary']
        # Check the input of the method if tab is not in the list
        # print and error and show the valid names
        if tab not in tab_list:
            raise KeyError('Please introduce a valid tab name. '
                        'valid tabs names are: ' +\
                            ', '.join([str(elem) for elem in tab_list]))
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
            except ConnectionError: # pragma: no cover
                print('Initial attempt to obtain object data failed. '
                    'Reattempting...')
                # Wait 5 seconds
                time.sleep(5)
                # Get object data
                data_obj = tabs.get_object_data(url)

            if tab == 'impacts':
                # Create empty object with class Impacts
                neocc_obj = tabs.Impacts()
                # Parse the requested data using Impacts parser
                neocc_obj._impacts_parser(data_obj)
            elif tab == 'close_approaches':
                # Parse the requested data using Close Approaches parser
                neocc_obj = tabs.CloseApproaches.clo_appr_parser(data_obj)
            elif tab == 'observations':
                # Create empty object
                neocc_obj = tabs.AsteroidObservations()
                # Get object with attributes from data
                neocc_obj._ast_obs_parser(data_obj)
            elif tab == 'physical_properties':
                # Create empty object with class Physical properties
                neocc_obj = tabs.PhysicalProperties()
                # Parse the requested data using Physical properties parser
                neocc_obj._phys_prop_parser(data_obj)
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
            except ConnectionError: # pragma: no cover
                print('Initial attempt to obtain object data failed. '
                    'Reattempting...')
                # Wait 5 seconds
                time.sleep(5)
                # Get object data
                data_obj = tabs.get_object_data(url)

            # Assign orbit properties depending on the elements requested
            if kwargs['orbital_elements'] == "keplerian":
                # Create empty object with class Orbit properties
                neocc_obj = tabs.KeplerianOrbitProperties()
                # Parse the requested data using Orbit properties parser
                neocc_obj._orb_kep_prop_parser(data_obj)
            elif kwargs['orbital_elements'] == "equinoctial":
                # Create empty object with class Orbit properties
                neocc_obj = tabs.EquinoctialOrbitProperties()
                # Parse the requested data using Orbit properties parser
                neocc_obj._orb_equi_prop_parser(data_obj)

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
                    raise KeyError ('Please specify ' + args_dict[element]
                                    + ' for ephemerides')

            # Create empty object with class Ephemerides
            neocc_obj = tabs.Ephemerides()
            # Parse the requested data using Ephemerides parser
            neocc_obj._ephem_parser(name, observatory=kwargs['observatory'],
                                start=kwargs['start'], stop=kwargs['stop'],
                                step=kwargs['step'],
                                step_unit=kwargs['step_unit'])
        elif tab == 'summary':
            # Create empty object with class Summary
            neocc_obj = tabs.Summary()
            # Parse the requested data using Summary parser
            neocc_obj._summary_parser(name)

        return neocc_obj


neocc = ESAneoccClass()
