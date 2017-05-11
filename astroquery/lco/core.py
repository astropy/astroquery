# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

"""
Las Cumbres Observatory
====

API from

 https://archive-api.lco.global

The following are endpoints of the Las Cumbres Observatory archive query service,

Endpoint            Method      Usage
/aggregate/         GET         Returns the unique values shared accross all fits files for site, telescope, instrument, filter and obstype.
/api-token-auth/    POST        Obtain an api token for use with authenticated requests.
/frames/            GET         Return a list of frames.
/frames/{id}/       GET         Return a single frame.
/frames/{id}/related/ GET       Return a list of frames related to this frame (calibration frames, catalogs, etc).
/frames/{id}/headers/ GET       Return the headers for a single frame.
/frames/zip/        POST        Returns a zip file containing all of the requested frames. Note this is not the preferred method for downloading files. Use the frame's url property instead.
/profile/           GET         Returns information about the currently authenticated user.

The service accepts the following keywords,

"""

import json
import keyring
import getpass
import warnings
from datetime import datetime

import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table
from astropy.io import fits
from astropy import log

from ..query import BaseQuery, QueryWithLogin
from ..utils import commons, system_tools, prepend_docstr_noreturns, async_to_sync
from . import conf


# export all the public classes and methods
# __all__ = ['Lco', 'LcoClass']

# declare global variables and constants if any


# Now begin your main class
# should be decorated with the async_to_sync imported previously
@async_to_sync
class LcoClass(QueryWithLogin):

    """
    Not all the methods below are necessary but these cover most of the common
    cases, new methods may be added if necessary, follow the guidelines at
    <http://astroquery.readthedocs.io/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout
    FRAMES_URL = conf.frames
    DTYPES = ['i','S39','S230','i','S19','S16','S20','S3','S4','f','S2','i']
    DATA_NAMES = ['id','filename','url','RLEVEL','DATE_OBS','PROPID','OBJECT','SITEID','TELID','EXPTIME','FILTER','REQNUM']
    TOKEN = None

    # all query methods are implemented with an "async" method that handles
    # making the actual HTTP request and returns the raw HTTP response, which
    # should be parsed by a separate _parse_result method.   The query_object
    # method is created by async_to_sync automatically.  It would look like
    # this:
    """
    def query_object(object_name, get_query_payload=False)
        response = self.query_object_async(object_name,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result
    """

    def query_object_async(self, object_name, get_query_payload=False,
                           cache=True, start=None, end=None):
        """
        This method is for services that can parse object names. Otherwise
        use :meth:`astroquery.lco.LcoClass.query_region`.
        Put a brief description of what the class does here.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            This should default to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        start: str, optional
            Default is `None`. When set this must be in iso E8601Dw.d datestamp format
            YYYY-MM-DD HH:MM
        end: str, optional
            Default is `None`. When set this must be in iso E8601Dw.d datestamp format
            YYYY-MM-DD HH:MM
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.

        """

        request_payload = self._args_to_payload(**{'object_name':object_name,'start':start, 'end':end})
        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload
        # BaseQuery classes come with a _request method that includes a
        # built-in caching system
        if not self.TOKEN:
            warnings.warn("You have not authenticated and will only get results for non-proprietary data")
            headers=None
        else:
            headers = {'Authorization': 'Token ' + self.TOKEN}
        response = self._request('GET', self.FRAMES_URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache, headers=headers)
        if response.status_code == 200:
            resp = json.loads(response.content)
            return self._parse_result(resp)
        else:
            log.exception("Failed!")
            return False

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()
        request_payload['OBJECT'] = kwargs['object_name']
        request_payload['REVEL'] = '91'
        request_payload['OBSTYPE'] = 'EXPOSE'
        if kwargs['start']:
            request_payload['start'] = validate_datetime(kwargs['start'])
        if kwargs['end']:
            request_payload['end'] = validate_datetime(kwargs['end'])
        return request_payload

    def _login(self, username=None, store_password=False,
               reenter_password=False):
        """
        Login to the LCO Archive.

        Parameters
        ----------
        username : str, optional
            Username to the Las Cumbres Observatory archive. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is False.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored password
            on the keyring. Default is False.
        """
        if username is None:
            if self.USERNAME == "":
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        # Get password from keyring or prompt
        if reenter_password is False:
            password_from_keyring = keyring.get_password(
                "astroquery:archive-api.lco.global", username)
        else:
            password_from_keyring = None

        if password_from_keyring is None:
            if system_tools.in_ipynb():
                log.warning("You may be using an ipython notebook:"
                            " the password form will appear in your terminal.")
            password = getpass.getpass("{0}, enter your Las Cumbres Observatory password:\n"
                                       .format(username))
        else:
            password = password_from_keyring
        # Authenticate
        log.info("Authenticating {0} with lco.global...".format(username))
        # Do not cache pieces of the login process
        login_response = self._request("POST", conf.get_token,
                                       cache=False, data={'username': username,
                                                          'password': password})
        # login form: method=post action=login [no id]

        if login_response.status_code == 200:
            log.info("Authentication successful!")
            token = json.loads(login_response.content)
            self.TOKEN = token['token']
        else:
            log.exception("Authentication failed!")
            token = None
        # When authenticated, save password in keyring if needed
        if token and password_from_keyring is None and store_password:
            keyring.set_password("astroquery:archive-api.lco.global", username, password)
        return

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        log.info(len(self.DTYPES),len(self.DATA_NAMES))
        t = Table(names=self.DATA_NAMES, dtype=self.DTYPES)
        if response['count']>0:
            try:
                for line in response['results']:
                    filtered_line = { key: line[key] for key in self.DATA_NAMES }
                    t.add_row(filtered_line)
            except ValueError:
                # catch common errors here, but never use bare excepts
                # return raw result/ handle in some way
                pass

        return t


Lco = LcoClass()

def validate_datetime(input):
    format_string = '%Y-%m-%d %H:%M'
    try:
        datetime.strptime(input, format_string)
        return input
    except ValueError:
        warning.warning('Input {} is not in format {} for ignoring'.format(input, format_string))
        return ''
