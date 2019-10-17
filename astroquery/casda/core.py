# Licensed under a 3-clause BSD style license - see LICENSE.rst

# 1. standard library imports
from io import BytesIO

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_nosections
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf

# export all the public classes and methods
__all__ = ['Casda', 'CasdaClass']


@async_to_sync
class CasdaClass(BaseQuery):

    """
    Class for accessing ASKAP data through the CSIRO ASKAP Science Data Archive (CASDA). Typical usage:

    result = Casda.query_region('22h15m38.2s -45d50m30.5s', radius=0.5 * u.deg)
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout

    def query_region_async(self, coordinates, radius=None, height=None, width=None,
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates. Either a radius or both a height and a width must be provided.

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
        cache: bool, optional
            Use the astroquery internal query result cache

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates=coordinates, radius=radius, height=height,
                                                width=width)
        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)

        # result = self._parse_result(response)
        return response

    # Create the dict of HTTP request parameters by parsing the user
    # entered values.
    def _args_to_payload(self, **kwargs):
        request_payload = dict()

        # Convert the coordinates to FK5
        coordinates = kwargs.get('coordinates')
        c = commons.parse_coordinates(coordinates).transform_to(coord.FK5)

        if kwargs['radius'] is not None:
            radius = u.Quantity(kwargs['radius']).to(u.deg)
            pos = 'CIRCLE {} {} {}'.format(c.ra.degree, c.dec.degree, radius.value)
        elif kwargs['width'] is not None and kwargs['height'] is not None:
            width = u.Quantity(kwargs['width']).to(u.deg).value
            height = u.Quantity(kwargs['height']).to(u.deg).value
            top = c.dec.degree - (height/2)
            bottom = c.dec.degree + (height/2)
            left = c.ra.degree - (width/2)
            right = c.ra.degree + (width/2)
            pos = 'RANGE {} {} {} {}'.format(left, right, top, bottom)
        else:
            raise ValueError("Either 'radius' or both 'height' and 'width' must be supplied.")

        request_payload['POS'] = pos

        return request_payload

    # the methods above implicitly call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`.
    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            # do something with regex to get the result into
            # astropy.Table form. return the Table.
            data = BytesIO(response.content)
            table = Table.read(data)
            return table
        except ValueError as e:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            print("Failed to convert query result to table", e)
            return response


# the default tool for users to interact with is an instance of the Class
Casda = CasdaClass()
