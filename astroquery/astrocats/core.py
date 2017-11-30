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

    def query_object_async(self, object_name,
                           attribute_name='alias',
                           get_query_payload=False,
                           cache=True):
        """
        Query method to retrieve the desired attributes for
        an object specified by a transient name. An attribute
        must be specified to return an astropy table. If no
        attribute given, then just 'alias' is returned.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        attribute_name : str, optional
            name of attribute to retrieve (e.g., redshift, photometry)
            see API documents for details
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        >>> from astroquery.astrocats import OACAPI
        >>> photometry = OACAPI.query_object(object_name = 'GW170817',
                                             attribute = 'photometry')
        >>> print(photometry[:3])

        """

        request_payload = self._args_to_payload(object_name, attribute_name)

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
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

        request_payload['EVENT'] = args[0]
        request_payload['ATTRIBUTE'] = args[1]

        return request_payload

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            print(response)
            pass
        except ValueError:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            pass

        return Table()


OACAPI = OACAPIClass()
