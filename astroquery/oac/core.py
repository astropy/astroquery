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
import csv

import astropy.units as u
from astropy.table import Column, Table

from . import conf
from ..query import BaseQuery
from ..utils import async_to_sync, commons

__all__ = ['OAC', 'OACClass']


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
            Name of quantity to retrieve. Can be
            a list of quantities. The default is None.
        attribute : str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. The default is None.
        argument : str or list, optional
            These are special conditional arguments that can be applied
            to a query to refine.
            Examples include: 'band=i' returns only i-band photometry,
            'first' returns the first result, 'sorby=attribute' returns
            a table sorted by the given attribute, and 'complete' returns
            only those table rows with all of the requested attributes.
            A complete list of commands and their usage can be found at:
            https://github.com/astrocatalogs/OACAPI. The default is None.
        data_format: str, optional
            Specify the format for the returned data. The default is
            `CSV` for easy conversion to Astropy Tables. The user can
            also specify `JSON` which will return a JSON-compliant
            dictionary.
            Note: Not all queries can support CSV output.
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
        The default behavior returns a list of all available
        metadata for a given event.

        >>> from astroquery.oac import OAC
        >>> metadata = OAC.query_object("GW170817")
        >>> print(metadata.keys())
        >>> ['event', 'hostoffsetdist', 'masses', 'ra', 'instruments',
             'lumdist', 'hostdec', 'host', 'velocity', 'ebv', 'hostra',
             'claimedtype', 'redshift', 'maxabsmag', 'alias', 'hostoffsetang',
             'download', 'maxdate', 'discoverdate', 'xraylink', 'dec',
             'maxappmag', 'radiolink', 'spectralink', 'references', 'name',
             'photolink']

        Specific data can be requested using quantity and attribute
        entries. For example, to request a light curve for an event:

        >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                          attribute=["time", "magnitude",
                                                     "e_magnitude", "band",
                                                     "instrument"])
        >>> print(photometry[:5])
        >>> event      time    magnitude e_magnitude band instrument
            -------- --------- --------- ----------- ---- ----------
            GW170817 57743.334     20.44                r
            GW170817 57790.358     21.39                r
            GW170817 57791.323     21.34                r
            GW170817 57792.326     21.26                r
            GW170817 57793.335     21.10                r

        The results can be further refined using the argument entry:

        >>> photometry = OAC.query_object("GW170817", quantity="photometry",
                                          attribute=["time", "magnitude",
                                                     "e_magnitude", "band",
                                                     "instrument"],
                                          argument=["band=i"])
        >>> print(photometry[:5])
        >>>  event          time magnitude e_magnitude band instrument
            -------- ----------- --------- ----------- ---- ----------
            GW170817    57982.98      17.3                i
            GW170817  57982.9814     17.48        0.02    i      Swope
            GW170817 57983.00305     17.48        0.03    i      DECam
            GW170817    57983.05    16.984       0.050    i       ROS2
            GW170817 57983.23125     17.24        0.06    i        PS1

        """
        request_payload = self._args_to_payload(event,
                                                quantity,
                                                attribute,
                                                argument,
                                                data_format)

        if get_query_payload:
            return request_payload

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

        IMPORTANT: The API can only query a single set of coordinates
        at a time.

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
            or an astropy quantity. The default value is None.
        width : str, float or `astropy.units.Quantity`, optional
            The width, in arcseconds, of the box search centered
            on coordinates. Should be a single, float-convertable value
            or an astropy quantity. The default value is None.
        height : str, float or `astropy.units.Quantity`, optional
            The height, in arcseconds, of the box search centered
            on coordinates. Should be a single, float-convertable value
            or an astropy quantity. The default value is None.
        quantity: str or list, optional
            Name of quantity to retrieve. Can be a
            a list of quantities. The default is None.
        attribute: str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. The default is None.
        argument : str or list, optional
            These are special conditional arguments that can be applied
            to a query to refine.
            Examples include: 'band=i' returns only i-band photometry,
            'first' returns the first result, 'sorby=attribute' returns
            a table sorted by the given attribute, and 'complete' returns
            only those table rows with all of the requested attributes.
            A complete list of commands and their usage can be found at:
            https://github.com/astrocatalogs/OACAPI. The default is None.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        Searches can be done as a cone or a box. We first establish coordinates
        and search parameters:

        >>> import astropy.coordinates as coord
        >>> import astropy.units as u
        >>> from astroquery.oac import OAC

        >>> #Sample coordinates. We are using GW170817.
        >>> ra = 197.45037
        >>> dec = -23.38148
        >>> test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

        >>> test_radius = 10*u.arcsec
        >>> test_height = 10*u.arcsec
        >>> test_width = 10*u.arcsec

        An example cone search:
        >>> photometry = OAC.query_region(coordinates=test_coords,
                                          radius=test_radius,
                                          quantity="photometry",
                                          attribute=["time", "magnitude",
                                                     "e_magnitude", "band",
                                                     "instrument"])
        >>> print(photometry[:5])
        >>>  event      time   magnitude e_magnitude band instrument
            -------- --------- --------- ----------- ---- ----------
            GW170817 57743.334     20.44                r
            GW170817 57790.358     21.39                r
            GW170817 57791.323     21.34                r
            GW170817 57792.326     21.26                r
            GW170817 57793.335     21.10                r

        An example box search:
        >>> photometry = OAC.query_region(coordinates=test_coords,
                                          width=test_width, height=test_height,
                                          quantity="photometry",
                                          attribute=["time", "magnitude",
                                                     "e_magnitude", "band",
                                                     "instrument"])
        >>> print(photometry[:5])
        >>>  event      time   magnitude e_magnitude band instrument
            -------- --------- --------- ----------- ---- ----------
            GW170817 57743.334     20.44                r
            GW170817 57790.358     21.39                r
            GW170817 57791.323     21.34                r
            GW170817 57792.326     21.26                r
            GW170817 57793.335     21.10                r

        These searches can be refined using the quantities, attributes, and
        arguments, as with query_object.

        """
        # Default object name used for coordinate-based queries
        event = 'catalog'

        request_payload = self._args_to_payload(event,
                                                quantity,
                                                attribute,
                                                argument,
                                                data_format)

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
                raise ValueError("Please check format of input coordinates.")

        if ((not radius) and (not height) and (not width)):
            raise ValueError("Please enter a radius or width/height pair.")

        if (radius and (height or width)):
            raise ValueError("Please specify ONLY a radius or "
                             "height/width pair.")

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

    def get_photometry_async(self, event, argument=None, cache=True):
        """Retrieve all photometry for specified event(s).

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
            https://github.com/astrocatalogs/OACAPI. The default is None.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        The method is used to grab a default light curve for an object:

        >>> from astroquery.oac import OAC
        >>> photometry = OAC.get_photometry("SN2014J")
        >>> print(photometry[0:5])

        >>> event       time         magnitude     e_magnitude band instrument
            ------- -------------- ---------------- ----------- ---- ----------
            SN2014J 56677.68443724 11.3932586807338                R
            SN2014J 56678.31205141   11.00561836355                R
            SN2014J 56678.81414463 11.2078655297216               i'
            SN2014J 56678.84552409 12.5056184232995               g'
            SN2014J 56678.84552409 11.4662920294307               r'

        The search can be refined using only the argument features of
        query_object. For example:

        >>> from astroquery.oac import OAC
        >>> photometry = OAC.get_photometry("SN2014J")
        >>> print(photometry[0:5])

        >>>  event       time         magnitude     e_magnitude band instrument
            ------- -------------- ---------------- ----------- ---- ----------
            SN2014J 56677.68443724 11.3932586807338                R
            SN2014J 56678.31205141   11.00561836355                R
            SN2014J       56678.87           11.105       0.021    R
            SN2014J 56678.90828613 11.1235949161792                R
            SN2014J 56679.06518967 11.0561795725355                R

        """
        response = self.query_object_async(event=event,
                                           quantity='photometry',
                                           attribute=['time', 'magnitude',
                                                      'e_magnitude', 'band',
                                                      'instrument'],
                                           argument=argument,
                                           cache=cache
                                           )

        return response

    def get_single_spectrum_async(self, event, time, cache=True):
        """Retrieve a single spectrum at a specified time for given event.

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
            Name of the event to query. Must be a single event.
        time : float, required
            A single MJD time to query. This time does not need to be
            exact. The closest spectrum will be returned.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        This method returns a single spectrum for an object at a selected
        time in MJD. The given time does not have to be exact.

        >>> from astroquery.oac import OAC
        >>> test_time = 57740
        >>> spectrum = OAC.get_single_spectrum("GW170817", time=test_time)
        >>> print(spectrum[0:5])
        >>> wavelength    flux
            ---------- ----------
            3501.53298 3.6411e-17
            3501.73298 4.0294e-17
            3502.33298 4.0944e-17
            3502.53298 4.1159e-17
            3502.73298 4.3485e-17

        This method does not allow further customization of searches.

        """
        query_time = 'time=%s' % time
        response = self.query_object_async(event=event,
                                           quantity='spectra',
                                           attribute=['data'],
                                           argument=[query_time, 'closest'],
                                           cache=cache
                                           )

        return response

    def get_spectra_async(self, event, cache=True):
        """Retrieve all spectra for a specified event.

        This is a version of the query_object method
        that is set up to quickly return all available spectra
        for a single event.

        The spectra must be returned as a JSON-compliant dictionary.
        Multiple spectra can not be unwrapped into a csv/Table.

        More complicated queries should make use of the
        base query_object methods.

        Parameters
        ----------
        event : str, required
            Name of the event to query. Should be a single event.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        This method returns all available spectra for a single event.

        >>> from astroquery.oac import OAC
        >>> spectra = OAC.get_spectra("SN2014J")
        >>> print (spectra.keys())
        >>> dict_keys(['SN2014J'])
        >>> print (spectra["SN2014J"].keys())
        >>> dict_keys(['spectra'])
        >>> print (spectra["SN2014J"]["spectra"][0][0])
        >>> 56680.0
        >>> print (spectra["SN2014J"]["spectra"][0][1][0])
        >>> ['5976.1440', '1.17293e-14']

        Note that the query must return a JSON-compliant dictionary which will
        have nested lists of [MJD, [wavelength,flux]].

        """
        response = self.query_object_async(event=event,
                                           quantity='spectra',
                                           attribute=['time', 'data'],
                                           data_format='json',
                                           cache=cache
                                           )
        return response

    def _args_to_payload(self, event, quantity,
                         attribute, argument, data_format):
        request_payload = dict()

        if (event) and (not isinstance(event, list)):
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

        if argument:
            if 'format' in argument:
                raise KeyError("Please specify the output format using the "
                               "data_format function argument")
            if 'radius' in argument:
                raise KeyError("A search radius should be specified "
                               "explicitly using the query_region method.")
            if 'width' in argument:
                raise KeyError("A search width should be specified "
                               "explicitly using the query_region method.")
            if 'height' in argument:
                raise KeyError("A search height should be specified "
                               "explicitly using the query_region method.")

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
            raise ValueError("The format must be either csv or JSON.")

        self.FORMAT = data_format.lower()

        return request_payload

    def _format_output(self, raw_output):
        if self.FORMAT == 'csv':
            split_output = raw_output.splitlines()
            columns = list(csv.reader([split_output[0]], delimiter=',',
                           quotechar='"'))[0]
            rows = split_output[1:]

            # Quick test to see if API returned a valid csv file
            # If not, try to return JSON-compliant dictionary.
            test_row = list(csv.reader([rows[0]], delimiter=',',
                            quotechar='"'))[0]

            if (len(columns) != len(test_row)):
                print("The API did not return a valid CSV output! \n"
                      "Outputing JSON-compliant dictionary instead.")

                try:
                    output = json.loads(raw_output)
                    return output
                except Exception:
                    print("The API response could not be processed.")
                    raise Exception

            # Initialize and populate dictionary
            output_dict = {key: [] for key in columns}

            for row in rows:

                split_row = list(csv.reader([row], delimiter=',',
                                 quotechar='"'))[0]

                for ct, key in enumerate(columns):
                    output_dict[key].append(split_row[ct])

            # Convert dictionary to Astropy Table.
            output = Table(output_dict, names=columns)

        else:
            # Server response is JSON compliant. Simply
            # convert from raw text to dictionary.
            output = json.loads(raw_output)

        return output

    def _parse_result(self, response, verbose=False):
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
            print("ERROR: An error occured processing the HTTP response.")
            return

        return output_response


OAC = OACClass()
