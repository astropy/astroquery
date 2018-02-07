# Licensed under a 3-clause BSD style license - see LICENSE.rst.
"""
OPEN ASTRONOMY CATALOG (OAC) API TOOL
-------------------------
This module allows access to the OAC API and
all available functionality. For more information
see: api.astrocats.space.
:authors: Philip S. Cowperthwaite (pcowpert@cfa.harvard.edu)
and James Guillochon (jguillochon@cfa.harvard.edu)
"""

from __future__ import print_function

import json

import astropy.units as u
from astropy.table import Column, Table

from . import conf
from ..query import BaseQuery
from ..utils import async_to_sync, commons

__all__ = ('OAC', 'OACClass')


@async_to_sync
class OACClass(BaseQuery):
    """OAC class."""

    URL = conf.server
    TIMEOUT = conf.timeout
    HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    FORMAT = None

    def query_object_async(self,
                           event,
                           quantity=None,
                           attribute=None,
                           argument=None,
                           data_format='csv',
                           get_query_payload=False, cache=True):
        """Retrieve object(s) asynchronously.

        Query method to retrieve the desired quantities and
        attributes for an object specified by a transient name.

        If no quantities or attributes are given then the query
        returns the top-level metadata about the event(s).

        The complete list of available quantities and attributes
        can be found at https://github.com/astrocatalogs/schema.

        Parameters
        ----------
        event : str or list, required
            Name of the event to query. Can be a list
            of event names.
        quantity : str or list, optional
            Name of quantity to retrieve. Can be a
            a list of quantities. If no quantity is specified,
            then photometry is returned by default.
        attribute : str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. If no attributes are specified,
            then a time vs. magnitude light curve is returned.
        argument : str or list, optional
            These are special conditional arguments that can be applied
            to a query to refine.
            Examples include: 'band=i' returns only i-band photometry,
            'first' returns the first result, 'sorby=attribute' returns
            a table sorted by the given attribute, and 'complete' returns
            only those table rows with all of the requested attributes.
            A complete list of commands and their usage can be found at:
            https://github.com/astrocatalogs/OACAPI
        data_format: str, optional
            Specify the format for the returned data. The default is
            `CSV` for easy conversion to Astropy Tables. The user can
            also specify `JSON` which will return the raw JSON output
            from the API.
            Note 1: Not all queries can support CSV output.
            Note 2: Setting the format to JSON will return the JSON
            dictionary instead of an Astropy Table.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        Examples
        --------
        >>> from astroquery.oac import OAC
        >>> photometry = OAC.query_object(event=['GW170817'],
                                          quantity='photometry',
                                          attribute=[
                                          'time', 'magnitude',
                                          'e_magnitude','band','instrument']
                                         )
        >>> print(photometry[:5])

        >>> time   magnitude e_magnitude band instrument
            --------- --------- ----------- ---- ----------
            57743.334     20.44                r
            57790.358     21.39                r
            57791.323     21.34                r
            57792.326     21.26                r
            57793.335     21.10                r

        """
        request_payload = self._args_to_payload(event,
                                                quantity,
                                                attribute,
                                                argument,
                                                data_format)

        if get_query_payload:
            return request_payload

        print(request_payload)

        response = self._request('GET', self.URL,
                                 data=json.dumps(request_payload),
                                 timeout=self.TIMEOUT,
                                 headers=self.HEADERS,
                                 cache=cache)

        return response

    def query_region_async(self, coordinates,
                           radius=None,
                           height=None, width=None,
                           quantity=None,
                           attribute=None,
                           argument=None,
                           data_format='csv',
                           get_query_payload=False, cache=True):
        """Query a region asynchronously.

        Query method to retrieve the desired quantities and
        attributes for an object specified by a region on the sky.
        The search can be either a cone search (using the radius
        parameter) or a box search (using the width/height parameters).

        IMPORTANT: The API can only query a single set of coordinates at a
        time.

        The complete list of available quantities and attributes
        can be found at https://github.com/astrocatalogs/schema.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            A single set of ra/dec coorindates to query. Can be either
            a list with [ra,dec] or an astropy coordinates object.
            Can be given in sexigesimal or decimal format. The API
            can not query multiple sets of coordinates.
        radius : str, float or `astropy.units.Quantity`, optional
            The radius, in arcseconds, of the cone search centered
            on coordinates. Should be a single, float-convertable value
            or an astropy quantity. The default value is 10 arcsecons.
        width : str, float or `astropy.units.Quantity`, optional
            The width, in arcseconds, of the box search centered
            on coordinates. Should be a single, float-convertable value
            or an astropy quantity. The default value is None (e.g.,
            a cone search is performed by default).
        height : str, float or `astropy.units.Quantity`, optional
            The height, in arcseconds, of the box search centered
            on coordinates. Should be a single, float-convertable value
            or an astropy quantity. The default value is None (e.g.,
            a cone search is performed by default).
        quantity: str or list, optional
            Name of quantity to retrieve. Can be a
            a list of quantities. If no quantity is specified,
            then photometry is returned by default.
        attribute: str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. If no attributes are specified,
            then a time vs. magnitude light curve is returned.
        argument : str or list, optional
            These are special conditional arguments that can be applied
            to a query to refine.
            Examples include: 'band=i' returns only i-band photometry,
            'first' returns the first result, 'sorby=attribute' returns
            a table sorted by the given attribute, and 'complete' returns
            only those table rows with all of the requested attributes.
            A complete list of commands and their usage can be found at:
            https://github.com/astrocatalogs/OACAPI
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """

        # No object name is used for coordinate-based queries
        event = 'catalog'

        request_payload = self._args_to_payload(event,
                                                quantity,
                                                attribute,
                                                argument,
                                                data_format)

        # Add coordinate information to payload.
        # Check that coordinate object is a valid astropy coordinate object
        # Criteria/Code from ../sdss/core.py
        if (not isinstance(coordinates, list) and
            not isinstance(coordinates, Column) and
            not (isinstance(coordinates, commons.CoordClasses) and
                 not coordinates.isscalar)):

            request_payload['ra'] = coordinates.ra.deg
            request_payload['dec'] = coordinates.dec.deg

        else:
            try:
                request_payload['ra'] = coordinates[0]
                request_payload['dec'] = coordinates[1]
            except Exception:
                raise ValueError("Please check format of input coordinates")

        # Check that the user entered a radius or width/height.
        if ((not radius) and (not height) and (not width)):
            raise ValueError("Please enter a radius or width/height pair")

        # Check that user is only requesting cone OR box search.
        if (radius and (height or width)):
            raise ValueError(
                "Please specify ONLY a radius or height/width pair.")

        # Check that a box search has both width and height.
        if ((not radius) and ((not height) or (not width))):
            raise ValueError("Please enter both a width and height "
                             "for a box search.")

        # Check that any values are in the proper format.
        # Criteria/Code from ../sdss/core.py
        if radius:
            if isinstance(radius, u.Quantity):
                radius = radius.to(u.arcsec).value
            else:
                try:
                    float(radius)
                except TypeError:
                    raise TypeError("radius should be either Quantity or "
                                    "convertible to float.")

            request_payload['radius'] = radius

        if (width and height):
            if isinstance(width, u.Quantity):
                width = width.to(u.arcsec).value
            else:
                try:
                    float(width)
                except TypeError:
                    raise TypeError("width should be either Quantity or "
                                    "convertible to float.")

            if isinstance(height, u.Quantity):
                height = height.to(u.arcmin).value
            else:
                try:
                    float(height)
                except TypeError:
                    raise TypeError("height should be either Quantity or "
                                    "convertible to float.")

            request_payload['width'] = width
            request_payload['height'] = height

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL,
                                 data=json.dumps(request_payload),
                                 timeout=self.TIMEOUT,
                                 headers=self.HEADERS,
                                 cache=cache)

        return response

    def get_photometry(self, event,
                       argument=None):
        """Retrieve object(s) photometry.

        This is a version of the query_object method
        that is set up to quickly return the complete set
        of light curve(s) for the given event(s).

        The light curves are returned by default as an
        Astropy Table.

        Additional arguments can be specified but more complicated
        queries should make use of the base query_object method
        instead of get_photometry.

        Parameters
        ----------
        event : str or list, required
            Name of the event to query. Can be a list
            of event names.
        argument : str or list, optional
            These are special conditional arguments that can be applied
            to a query to refine.
            Examples include: 'band=i' returns only i-band photometry,
            'first' returns the first result, 'sorby=attribute' returns
            a table sorted by the given attribute, and 'complete' returns
            only those table rows with all of the requested attributes.
            A complete list of commands and their usage can be found at:
            https://github.com/astrocatalogs/OACAPI

        Returns
        -------
        output : `Astropy Table`
            An astropy table of all requested photometry with
            columns:
            ['event', 'time', 'magnitude', 'e_magnitude', 'band', 'instrument']

        Examples
        --------

        """
        response = self.query_object_async(event=event,
                                           quantity='photometry',
                                           attribute=['time', 'magnitude',
                                                      'e_magnitude', 'band',
                                                      'instrument'],
                                           argument=argument
                                           )

        output = self._parse_result(response)

        return output

    # Get Single Spectrum - Require time (closest by default)
    def get_single_spectrum(self, event, time):
        """Retrieve a single spectrum at a specified time for
        the given event.

        This is a version of the query_object method
        that is set up to quickly return a single spectrum
        at a user-specified time. The time does not have to be
        precise as the method uses the closest option by default.

        The spectrum is returned as an astropy table.

        More complicated queries, or queries requesting multiple spectra,
        should make use of the base query_object or get_spectra methods.

        Parameters
        ----------
        event : str, required
            Name of the event to query. Should be a single event.
        time : float, required
            A single MJD time

        Returns
        -------
        output : `Astropy Table`
            An Astropy Table with columns:
            [wavelength, flux, e_flux (if available)]


        Examples
        --------
        """
        query_time = 'time=%s' % time
        response = self.query_object_async(event=event,
                                           quantity='spectra',
                                           attribute=['data'],
                                           argument=[query_time, 'closest']
                                           )

        output = self._parse_result(response)

        return output

    # Get spectra - JSON dump all spectra
    def get_spectra(self, event):
        """Retrieve all available spectra for the given event.

        This is a version of the query_object method
        that is set up to quickly return a single spectrum
        at a user-specified time. The time does not have to be
        precise as the method uses the closest option by default.

        The spectra must be returned as a JSON-compliant dictionary

        More complicated queries should make use of the
        base query_object methods.

        Parameters
        ----------
        event : str, required
            Name of the event to query. Should be a single event.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        Examples
        --------
        """

        response = self.query_object_async(event=event,
                                           quantity='spectra',
                                           attribute=['time', 'data'],
                                           data_format='json'
                                           )

        output = self._parse_result(response)

        return output

    def _args_to_payload(self, event, quantity,
                         attribute, argument, data_format):
        request_payload = dict()

        # Convert non-list entries to lists
        if (event) and not isinstance(event, list):
            event = [event]

        if (quantity) and (not isinstance(quantity, list)):
            quantity = [quantity]

        if (attribute) and (not isinstance(attribute, list)):
            attribute = [attribute]

        if (argument) and (not isinstance(argument, list)):
            argument = [argument]

        request_payload['event'] = event
        request_payload['quantity'] = quantity
        request_payload['attribute'] = attribute

        # If special keys are included, append to attribute list
        if argument:
            for arg in argument:
                if '=' in arg:
                    split_arg = arg.split('=')
                    request_payload[split_arg[0]] = split_arg[1]
                else:
                    request_payload[arg] = True

        if ((data_format.lower() == 'csv') or
                (data_format.lower() == 'json')):
            request_payload['format'] = data_format.lower()
        else:
            raise ValueError("The format must be either csv "
                             "or JSON.")

        self.FORMAT = data_format.lower()

        return request_payload

    def _format_output(self, raw_output):
        if self.FORMAT == 'csv':
            raw_output = raw_output.splitlines()
            columns = raw_output[0].split(',')
            rows = raw_output[1:]

            output_dict = {key: [] for key in columns}

            for row in rows:

                split_row = row.split(',')

                for ct, key in enumerate(columns):
                    output_dict[key].append(split_row[ct])

            output = Table(output_dict)

        else:
            output = json.loads(raw_output)

        return output

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        try:
            if response.status_code != 200:
                raise AttributeError

            if 'message' in response:
                raise KeyError

            raw_output = response.text
            output_response = self._format_output(raw_output)

        except AttributeError:
            print("ERROR: The web service returned error code: %s" %
                  response.status_code)
            return

        except KeyError:
            print("ERROR: API Server returned the following error:")
            print(response['message'])
            return

        except Exception:
            print("ERROR: An error occured with astropy table construction.")
            return

        return output_response


OAC = OACClass()
