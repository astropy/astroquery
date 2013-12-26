# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports

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
    Not all the methods below are necessary but these cover most of the    common cases, new methods may be added if necessary, follow the guid    elines at <http://astroquery.readthedocs.org/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL, TIMEOUT, etc.
    URL = SERVER()
    TIMEOUT = TIMEOUT()

    def query_object(self, object_name, get_query_payload=False, verbose=False):
    """
    This class is for services that can parse object names. Otherwise
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

    @prepend_docstr_noreturns
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
