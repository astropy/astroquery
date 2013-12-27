# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table
from astropy.io import fits

# 3. local imports - use relative imports
# commonly required local imports shown below as example
from ..query import BaseQuery # all Query classes should inherit from this.
from ..utils import commons # has common functions required by most modules
from ..utils import prepend_docstr_noreturns # automatically generate docs for similar functions
from ..utils import async_to_sync # all class methods must be callable as static as well as instance methods.
from . import SERVER, TIMEOUT # import configurable items declared in __init__.py


# export all the public classes and methods
__all__ = ['DummyClass']

# declare global variables and constants if any

# Now begin your main class
# should be decorated with the async_to_sync imported previously

@async_to_sync
class DummyClass(BaseQuery):

    """
    Not all the methods below are necessary but these cover most of the common cases, new methods may be added if necessary, follow the guid    elines at <http://astroquery.readthedocs.org/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL, TIMEOUT, etc.
    URL = SERVER()
    TIMEOUT = TIMEOUT()

    def query_object(self, object_name, get_query_payload=False, verbose=False):
        """
        This method is for services that can parse object names. Otherwise
        use :meth:`astroquery.template_module.DummyClass.query_region`.
        Put a brief description of what the class does here.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.
        any_other_param : <param_type>
            similarly list other parameters the method takes

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.
            All queries other than image queries should typically return
            results like this.

        Example
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.
        """

        # typically query_object should have the following steps:
        # 1. call the corresponding query_object_async method, and
        #    get the HTTP response of the query
        # 2. check if 'get_query_payload' is set to True, then
        #    simply return the dict of HTTP request parameters.
        # 3. otherwise call the parse_result method on the
        #    HTTP response returned by query_object_async and
        #    return the result parsed as astropy.Table
        # These steps are filled in below, but may be replaced
        # or modified as required.

        response = self.query_object_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    # all query methods usually have a corresponding async method
    # that handles making the actual HTTP request and returns the
    # raw HTTP response, which should be parsed by a separate
    # parse_result method. Since these async counterparts take in
    # the same parameters as the corresponding query methods, but
    # differ only in the return value, they should be decorated with
    # prepend_docstr_noreturns which will automatically generate
    # the common docs. See below for an example.



    @prepend_docstr_noreturns(query_object.__doc__)
    def query_object_async(self, object_name, get_query_payload=False) :
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        # the async method should typically have the following steps:
        # 1. First construct the dictionary of the HTTP requests.
        # 2. If get_query_payload is `True` then simply return this dict.
        # 3. Else make the actual HTTP request and return the corresponding
        #    HTTP response
        # All HTTP requests are made via the `commons.send_request` method.
        # This uses the Python Requests library internally, and also takes
        # care of error handling.
        # See below for an example:

        # first initialize the dictionary of HTTP request parameters
        request_payload = dict()

        # Now fill up the dictionary. Here the dictionary key should match
        # the exact parameter name as expected by the remote server. The
        # corresponding dict value should also be in the same format as
        # expected by the server. Additional parsing of the user passed
        # value may be required to get it in the right units or format.
        # All this parsing may be done in a separate private `_args_to_payload`
        # method for cleaner code.

        request_payload['object_name'] = object_name
        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload
        # commons.send_request takes 4 parameters - the URL to query, the dict of
        # HTTP request parameters we constructed above, the TIMEOUT which we imported
        # from __init__.py and the type of HTTP request - either 'GET' or 'POST', which
        # defaults to 'GET'.
        response = commons.send_request(DummyClass.URL, request_payload, DummyClass.TIMEOUT, request_type='GET')
        return response


    # For services that can query coordinates, use the query_region method.
    # The pattern is similar to the query_object method. The query_region
    # method also has a 'radius' keyword for specifying the radius around
    # the coordinates in which to search. If the region is a box, than
    # the keywords 'width' and 'height' should be used instead. The coordinates
    # may be accepted as an `astropy.coordinates` object or as a
    # string, which may be further parsed.

    def query_region(self, coordinates, radius, width, height, get_query_payload=False, verbose=False):
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
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.
            All queries other than image queries should typically return
            results like this.
        """
        # the documentation and code are similar to the steps outlined in the
        # `query_object` method, but a rough sketch is provided below

        response = self.query_region_async(coordinates, radius, height, width,
                                           get_query_payload=get_query_payload)
        result = self._parse_result(response, verbose=verbose)
        return result

    # similarly we write a query_region_async method that makes the
    # actual HTTP request and returns the HTTP response

    @prepend_docstr_noreturns(query_region.__doc__)
    def query_region_async(self, coordinates, radius, height, width, get_query_payload=False):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates, radius, height, width)
        if get_query_payload:
            return request_payload
        response = commons.send_request(DummyClass.URL, request_payload, DummyClass.TIMEOUT, request_type='GET')
        return response

    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()
        # code to parse input and construct the dict
        # goes here. Then return the dict to the caller
        return request_payload

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # if verbose is False then supress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            # do something with regex to get the result into
            # astropy.Table form. return the Table.
            pass
        except:
            # catch common errors here
            # return raw result/ handle in some way
            pass

     # for image queries, the
