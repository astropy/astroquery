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

__all__ = ['neocc', 'NEOCCClass']


@async_to_sync
class NEOCCClass(BaseQuery):
    """
    Class to init ESA NEOCC Python interface library
    """

    def query_list(self, list_name):
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

    def query_object(self, name, tab, *,
                     orbital_elements=None, orbit_epoch=None,
                     observatory=None, start=None, stop=None, step=None, step_unit=None):
        """Get requested object data from ESA NEOCC.

        Parameters
        ----------
        name : str
            Name of the requested object
        tab : str
            Name of the request tab. Valid names are: summary,
            orbit_properties, physical_properties, observations,
            ephemerides, close_approaches and impacts.
        orbital_elements : str
            Additional required argument for "orbit_properties" table.
            Valid arguments are: keplerian, equinoctial
        orbit_epoch : str
            Additional required argument for "orbit_properties" table.
            Valid arguments are: present, middle
        observatory : str
            Additional required argument for "ephemerides" table.
            Observatory code, e.g. '500', 'J04', etc.
        start : str
            Additional required argument for "ephemerides" table.
            Start date in YYYY-MM-DD HH:MM
        stop : str
            Additional required argument for "ephemerides" table.
            End date in YYYY-MM-DD HH:MM
        step : str
            Additional required argument for "ephemerides" table.
            Time step, e.g. '2', '15', etc.
        step_unit : str
            Additional required argument for "ephemerides" table.
            Unit for time step e.g. 'days', 'minutes', etc.

        Returns
        -------
        neocc_obj : list of `~astropy.table.Table`
            One or more tables containing the requested object data.
            the tab selected.
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

            # Raise error if  elements or epoch are not provided
            if not all([orbital_elements, orbit_epoch]):
                raise KeyError(("orbital_elements and orbit_epoch must be specified"
                                "for an orbit_properties query."))

            # Get URL to obtain the data from NEOCC
            url = tabs.get_object_url(name, tab, orbital_elements=orbital_elements, orbit_epoch=orbit_epoch)

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

            if not all([observatory, start, stop, step, step_unit]):
                raise KeyError(("Ephemerides queries require the following arguments:"
                                "observatory, start, stop, step, and step_unit"))

            resp_str = tabs.get_ephemerides_data(name, observatory=observatory, start=start, stop=stop,
                                                 step=step, step_unit=step_unit)
            neocc_obj = tabs.parse_ephemerides(resp_str)

        elif tab == 'summary':
            resp_str = tabs.get_summary_data(name)
            neocc_obj = tabs.parse_summary(resp_str)

        if not isinstance(neocc_obj, list):
            neocc_obj = [neocc_obj]

        return neocc_obj


neocc = NEOCCClass()
