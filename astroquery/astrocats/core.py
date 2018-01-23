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
from astropy.table import Table
from astropy.io import fits


from ..query import BaseQuery
from ..utils import commons, prepend_docstr_nosections, async_to_sync
from . import conf

__all__ = ['OACAPI', 'OACAPIClass']

@async_to_sync
class OACAPIClass(BaseQuery):

    URL = conf.server
    TIMEOUT = conf.timeout
    HEADERS = {"Content-Type":"application/json","Accept":"application/json"}

    def query_object_async(self, 
                           object_name = 'all',
                           quantity_name =  None,
                           attribute_name = None,
                           get_query_payload = False,
                           cache=True):

        """
        Query method to retrieve the desired attributes for
        an object specified by a transient name. An attribute
        must be specified to return an astropy table. If no
        attribute given, then just 'alias' is returned.

        The complete list of available quantities and attributes 
        can be found at https://github.com/astrocatalogs/schema.

        Parameters
        ----------
        object_name : str or list
            Name of the object to query. Can be a list
            of object names.
        quantity_name : str or list, optional
            Name of quantity to retrieve. Can be a 
            a list of quantities. If no quantity is specified,
            then all quantities for each event are returned.
        attribute_name : str or list, optional
            Name of specific attributes to retrieve. Can be a list
            of attributes. If no attributes are specified,
            all attributes for a given quantity are returned. 
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
        >>> photometry = OACAPI.query_object(object_name = 'GW170817',
                                             quantity_name = 'photometry')
        >>> print(photometry[:3])

        """

        request_payload = self._args_to_payload(object_name, quantity_name, 
                                                attribute_name)

        if get_query_payload:
            return request_payload

        response = self._request('POST', self.URL,
                                 data=request_payload,
                                 headers=self.HEADERS,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    def query_region_async(self, coordinates, radius, height, width,
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        width : str or `astropy.units.Quantity`
            the width for a box region
        height : str or `astropy.units.Quantity`
            the height for a box region
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        verbose : bool, optional
            Display VOTable warnings or not.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates, radius, height,
                                                width)
        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()

        request_payload['event'] = args[0]
        request_payload['quantity'] = args[1]
        request_payload['attribute'] = args[2]

        return json.dumps(request_payload)

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.

        raw_output = response.text

        try:
            if 'message' in raw_output: raise KeyError
            pass

        except KeyError:
            print ("ERROR: API Server returned the following error:")
            print (raw_output['message'])
            return

        except ValueError:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            pass


OACAPI = OACAPIClass()
