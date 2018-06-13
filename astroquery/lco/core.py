# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

"""
Las Cumbres Observatory
=======================

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

The service accepts the following optional keywords,

DATE_OBS:   The UTC time at the start of exposure.
PROPID: The name of the proposal for which this frame was taken. Not including this will show public data only
INSTRUME:   The instrument that produced this frame.
OBJECT: The name of the object given by the user as the target of the observation. Note this is not the same as searching by on sky position - the OBJECT header is free-form text which may or may not match the actual contents of the file.
SITEID: The site that produced this frame.
TELID:  The telescope that produced this frame.
EXPTIME:    The exposure time of the frame.
FILTER: The filter used to produce this frame.
L1PUBDAT:   The date this frame become public.
OBSTYPE:    The type of exposure: EXPOSE, BIAS, SPECTRUM, CATALOG, etc.
BLKUID: The Block ID of the frame
REQNUM: The Request number of the frame
RLEVEL: The reduction level of the frame. Currently, there are 3 reduction levels: Some of the meta-data fields are derived and not found in the FITS headers. 0 (Raw), 11 (Quicklook), 91 (Final reduced).

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
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_nosections
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync

from ..utils import system_tools
from . import conf

@async_to_sync
class LcoClass(QueryWithLogin):

    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URL = conf.server
    TIMEOUT = conf.timeout
    FRAMES_URL = conf.frames
    DTYPES = ['i','S39','S230','i','S19','S16','S20','S3','S4','f','S2','i']
    DATA_NAMES = ['id','filename','url','RLEVEL','DATE_OBS','PROPID','OBJECT','SITEID','TELID','EXPTIME','FILTER','REQNUM']
    TOKEN = None

    def query_object_async(self, object_name,
                            start='', end='', rlevel='',
                            get_query_payload=False, cache=True):
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
        rlevel: str, optional
            Pipeline reduction level of the data. Default is `None`, and will
            return all data products. Options are  0 (Raw), 11 (Quicklook), 91 (Final reduced).
        Returns
        -------
        response : `requests.Response`
            Returns an astropy Table with results. See below for table headers
            id - ID of each Frame
            filename - Name of Frame file
            url - Download URL
            RLEVEL - 0 (Raw), 11 (Quicklook), 91 (Final reduced).
            DATE_OBS - Observation data
            PROPID - LCO proposal code
            OBJECT - Object Name
            SITEID - LCO 3-letter site ID of where observation was made
            TELID - LCO 4-letter telescope ID of where observation was made
            EXPTIME - Exposure time in seconds
            FILTER - Filter name
            REQNUM - LCO ID of the observing request which originated this frame

        Examples
        --------
        # from astroquery.lco import Lco
        # Lco.login(username='jdowland')
        # Lco.query_object_async('M15', start='2016-01-01 00:00', end='2017-02-01 00:00')

        """
        kwargs  = {
                'object_name'   : object_name,
                'start'         : start,
                'end'           : end,
                'rlevel'        : rlevel
                }

        request_payload = self._args_to_payload(**kwargs)
        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload

        return self._parse_response(request_payload, cache)

    def query_region_async(self, coordinates,
                           start='', end='', rlevel='',
                           get_query_payload=False, cache=True):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
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
        kwargs  = {
                'coordinates'   : coordinates,
                'start'         : start,
                'end'           : end,
                'rlevel'        : rlevel
                }
        request_payload = self._args_to_payload(**kwargs)
        if get_query_payload:
            return request_payload

        return self._parse_response(request_payload, cache)

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()

        request_payload['OBSTYPE'] = 'EXPOSE'
        if kwargs.get('start',''):
            request_payload['start'] = validate_datetime(kwargs['start'])
        if kwargs.get('end',''):
            request_payload['end'] = validate_datetime(kwargs['end'])
        if kwargs.get('rlevel',''):
            request_payload['rlevel'] = validate_rlevel(kwargs['rlevel'])
        if kwargs.get('coordinates',''):
            request_payload['coordinates'] = validate_coordinates(kwargs['coordinates'])
        elif kwargs.get('object_name',''):
            request_payload['OBJECT'] = kwargs['object_name']
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

    def _parse_response(self, request_payload, cache):
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


Lco = LcoClass()

def validate_datetime(input):
    format_string = '%Y-%m-%d %H:%M'
    try:
        datetime.strptime(input, format_string)
        return input
    except ValueError:
        warning.warning('Input {} is not in format {} - ignoring input'.format(input, format_string))
        return ''

def validate_rlevel(input):
    excepted_vals = ['0','00','11','91']
    if str(input) in excepted_vals:
        return input
    else:
        warning.warning('Input {} is not one of {} - ignoring'.format(input,','.join(excepted_vals)))
        return ''

def validate_coordinates(coordinates):
    c = commons.parse_coordinates(coordinates)
    if c.frame.name == 'galactic':
        coords = "POINT({} {})".format(c.icrs.ra.degree, c.icrs.dec.degree)
    # for any other, convert to ICRS and send
    else:
        ra, dec = commons.coord_to_radec(c)
        coords = "POINT({} {})".format(ra, dec)
    return coords
