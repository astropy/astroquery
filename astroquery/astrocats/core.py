# Licensed under a 3-clause BSD style license - see LICENSE.rst
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
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table, Column
from astropy.io import fits

from ..query import BaseQuery
from ..utils import commons, prepend_docstr_nosections, async_to_sync
from . import conf

__all__ = ['OACAPI', 'OACAPIClass']

@async_to_sync
class OACAPIClass(BaseQuery):

    URL = conf.server
    TIMEOUT = conf.timeout
    HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    def query_object_async(self, 
                           object_name,
                           quantity_name =  'photometry',
                           attribute_name=['time', 'magnitude', 'e_magnitude','band','instrument'],
                           get_query_payload = False,
                           cache=False):

        """
        Query method to retrieve the desired quantities and 
        attributes for an object specified by a transient name. 

        The complete list of available quantities and attributes 
        can be found at https://github.com/astrocatalogs/schema.

        Parameters
        ----------
        object_name : str or list, required
            Name of the event to query. Can be a list
            of event names. 
        quantity_name : str or list, optional
            Name of quantity to retrieve. Can be a 
            a list of quantities. If no quantity is specified,
            then photometry is returned by default.
        attribute_name : str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. If no attributes are specified,
            then a time vs. magnitude light curve is returned. 
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request 
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.
        verbose : bool, optional
            When set to `True` it displays VOTable warnings. The
            default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        Examples
        --------
        >>> from astroquery.astrocats import OACAPI
        >>> photometry = OACAPI.query_object(object_name=['GW170817'],
                                             quantity_name='photometry',
                                             attribute_name=['time', 'magnitude', 'e_magnitude','band','instrument'])
        >>> print(photometry[:5])

        >>> time   magnitude e_magnitude band instrument
            --------- --------- ----------- ---- ----------
            57743.334     20.44                r
            57790.358     21.39                r
            57791.323     21.34                r
            57792.326     21.26                r
            57793.335     21.10                r

        """

        request_payload = self._args_to_payload(object_name,
                                                quantity_name, 
                                                attribute_name)

        print (request_payload)

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL,
                                 data=json.dumps(request_payload),
                                 timeout=self.TIMEOUT, 
                                 headers = self.HEADERS,
                                 cache=cache)

        return response

    def query_region_async(self, coordinates, 
                           radius=None, 
                           height=None, width=None,
                           quantity_name =  'photometry',
                           attribute_name = ['time', 'magnitude', 'e_magnitude','band','instrument'],
                           get_query_payload=False, cache=False):

        """
        Query method to retrieve the desired quantities and 
        attributes for an object specified by a region on the sky.
        The search can be either a cone search (using the radius 
        parameter) or a box search (using the width/height parameters).

        IMPORTANT: The API can only query a single set of coordinates at a time.

        The complete list of available quantities and attributes 
        can be found at https://github.com/astrocatalogs/schema.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            A single set of ra/dec coorindates to query. Can be either
            a list with [ra,dec] or an astropy coordinates object.
            Can be given in sexigesimal or decimal format.
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
        quantity_name : str or list, optional
            Name of quantity to retrieve. Can be a 
            a list of quantities. If no quantity is specified,
            then photometry is returned by default.
        attribute_name : str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. If no attributes are specified,
            then a time vs. magnitude light curve is returned.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request 
            parameters as a dict. The actual HTTP request is not made.
            The default value is False.
        verbose : bool, optional
            When set to `True` it displays VOTable warnings. The
            default value is False.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """

        # No object name is used for coordinate-based queries
        object_name = 'catalog'

        request_payload = self._args_to_payload(object_name, 
                                                quantity_name, 
                                                attribute_name)

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
            except:
                raise ValueError("Please check format of input coordinates")

        # Check that the user entered a radius or width/height.
        if ((not radius) and (not height) and (not width)):
            raise ValueError("Please enter a radius or width/height pair")

        # Check that user is only requesting cone OR box search.
        if (radius and (height or width)):
           raise ValueError("Please specify ONLY a radius or height/width pair.")

        # Check that a box search has both width and height.
        if ((not radius) and ((not height) or (not width))):
           raise ValueError("Please enter both a width and height for a box search.")

        # Check that any values are in the proper format.
        # Criteria/Code from ../sdss/core.py
        if radius:
            if  isinstance(radius, u.Quantity):
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

        print (request_payload)

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL,
                                 data=json.dumps(request_payload),
                                 timeout=self.TIMEOUT, 
                                 headers = self.HEADERS,
                                 cache=cache)

        return response

    def _args_to_payload(self, object_name, quantity_name, attribute_name):
        request_payload = dict()

        request_payload['event'] = object_name
        request_payload['quantity'] = quantity_name
        request_payload['attribute'] = attribute_name

        # Force CSV/Text output for easy conversion to astropy table.
        request_payload['format'] = 'csv'

        return request_payload


    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        try:
            if response.status_code != 200: raise AttributeError

            raw_output = response.text.splitlines()

            if 'message' in raw_output: raise KeyError

            columns = raw_output[0].split(',')
            rows = raw_output[1:]

            output_dict = {key : [] for key in columns}

            for row in rows:

                split_row = row.split(',')

                for ct,key in enumerate(columns):
                    output_dict[key].append(split_row[ct])

            output_table = Table(output_dict)

        except AttributeError:
            print ("ERROR: The web service returned error code: %s" %response.status_code)
            return

        except KeyError:
            print ("ERROR: API Server returned the following error:")
            print (raw_output['message'])
            return

        except ValueError:
            print("ERROR: An error occured with astropy table construction.")
            return

        return output_table


OACAPI = OACAPIClass()
