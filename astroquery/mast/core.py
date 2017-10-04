# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Portal
===========

Module to query the Barbara A. Mikulski Archive for Space Telescopes (MAST).

"""

from __future__ import print_function, division

import warnings
import json
import time
import os
import re

import numpy as np

from requests import HTTPError
from getpass import getpass
from base64 import b64encode
from http.cookiejar import Cookie

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack, MaskedColumn
from astropy.extern.six.moves.urllib.parse import quote as urlencode
from astropy.utils.exceptions import AstropyWarning

from ..query import QueryWithLogin
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TimeoutError, InvalidQueryError, RemoteServiceError, LoginError
from ..exceptions import NoResultsWarning
from . import conf


__all__ = ['Observations', 'ObservationsClass',
           'Mast', 'MastClass']


class ResolverError(Exception):
    pass

class InputWarning(AstropyWarning):
    pass


class AuthenticationWarning(AstropyWarning):
    pass


class MaxResultsWarning(AstropyWarning):
    pass


def _prepare_service_request_string(json_obj):
    """
    Takes a mashup JSON request object and turns it into a url-safe string.

    Parameters
    ----------
    json_obj : dict
        A Mashup request JSON object (python dictionary).

    Returns
    -------
    response : str
        URL encoded Mashup Request string.
    """
    requestString = json.dumps(json_obj)
    requestString = urlencode(requestString)
    return "request="+requestString


def _mashup_json_to_table(json_obj, col_config=None):
    """
    Takes a JSON object as returned from a Mashup request and turns it into an `astropy.table.Table`.

    Parameters
    ----------
    json_obj : dict
        A Mashup response JSON object (python dictionary)
    col_config : dict, optional
        Dictionary that defines column properties, e.g. default value.

    Returns
    -------
    response : `~astropy.table.Table`
    """

    dataTable = Table(masked=True)
    absCorr = None

    if not all(x in json_obj.keys() for x in ['fields', 'data']):
        raise KeyError("Missing required key(s) 'data' and/or 'fields.'")

    for col, atype in [(x['name'], x['type']) for x in json_obj['fields']]:

        # Removing "_selected_" column
        if col == "_selected_":
            continue

        # reading the colum config if given
        ignoreValue = None
        if col_config:
            colProps = col_config.get(col, {})
            ignoreValue = colProps.get("ignoreValue", None)

        # making type adjustments
        if atype == "string":
            atype = "str"
            ignoreValue = "" if (ignoreValue is None) else ignoreValue
        if atype == "boolean":
            atype = "bool"
        if atype == "int":  # int arrays do not admit Non/nan vals
            ignoreValue = -999 if (ignoreValue is None) else ignoreValue

        # Make the column list (don't assign final type yet or there will be errors)
        colData = np.array([x.get(col, ignoreValue) for x in json_obj['data']], dtype=object)
        if ignoreValue is not None:
            colData[np.where(np.equal(colData, None))] = ignoreValue

        # no consistant way to make the mask because np.equal fails on ''
        # and array == value fails with None
        if atype == 'str':
            colMask = (colData == ignoreValue)
        else:
            colMask = np.equal(colData, ignoreValue)

        # add the column
        dataTable.add_column(MaskedColumn(colData.astype(atype), name=col, mask=colMask))

    return dataTable


@async_to_sync
class MastClass(QueryWithLogin):
    """
    MAST query class.

    Class that allows direct programatic access to the MAST Portal,
    more flexible but less user friendly than `ObservationsClass`.
    """

    def __init__(self, username=None, password=None, session_token=None):

        super(MastClass, self).__init__()

        self._MAST_REQUEST_URL = conf.server + "/api/v0/invoke"
        self._MAST_DOWNLOAD_URL = conf.server + "/api/v0/download/file/"
        self._COLUMNS_CONFIG_URL = conf.server + "/portal/Mashup/Mashup.asmx/columnsconfig"

        # shibbolith urls
        self._SP_TARGET = conf.server + "/api/v0/Mashup/Login/login.html"
        self._IDP_ENDPOINT = conf.ssoserver + "/idp/profile/SAML2/SOAP/ECP"
        self._SESSION_INFO_URL = conf.server + "/Shibboleth.sso/Session"

        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

        self._column_configs = {}
        self._current_service = None

        if username or session_token:
            self.login(username, password, session_token)

    def _attach_cookie(self, session_token):
        """
        Attaches a valid shibboleth session cookie to the current session.

        Parameters
        ----------
        session_token : dict or  `http.cookiejar.Cookie`
            A valid MAST shibboleth session cookie.
        """

        # clear any previous shib cookies
        self._session.cookies.clear_session_cookies()

        if isinstance(session_token, Cookie):
            # check it's a shibsession cookie
            if not "shibsession" in session_token.name:
                raise LoginError("Invalid session token")

            # add cookie to session
            self._session.cookies.set_cookie(session_token)

        elif isinstance(session_token, dict):
            if len(session_token) > 1:
                warnings.warn("Too many entries in token dictionary, only shibsession cookie will be used", InputWarning)

            # get the shibsession cookie
            value = None
            for name in session_token.keys():
                if "shibsession" in name:
                    value = session_token[name]
                    break

            if not value:
                raise LoginError("Invalid session token")

            # add cookie to session
            self._session.cookies.set(name, value)

        else:
            # raise datatype error
            raise LoginError("Session token must be given as a dictionary or http.cookiejar.Cookie object")

        # Print session info
        # get user information
        response = self._session.request("GET", self._SESSION_INFO_URL)

        if response.status_code != 200:
            print("Status code:", response.status_code)
            print("Authentication failed!")
            return False

        exp = re.findall(r'<strong>Session Expiration \(barring inactivity\):</strong> (.*?)\n', response.text)
        if len(exp) == 0:
            print(response.text)
            print("Authentication failed!")
            return False
        else:
            exp = exp[0]

        print("Authentication successful!")
        print("Session Expiration: {}".format(exp))
        return True

    def _shib_login(self, username, password):
        """
        Given username and password, logs into the MAST shibboleth client.

        Parameters
        ----------
        username : string
            The user's username, will usually be the users email address.
        password : string
            Password associated with the given username.
        """

        # clear any previous shib cookies
        self._session.cookies.clear_session_cookies()

        authenticationString = b64encode((('{}:{}'.format(username, password)).replace('\n', '')).encode('utf-8'))
        del password  # do not let password hang around

        # The initial get request (will direct the user to the sso login)
        self._session.headers['Accept-Encoding'] = 'identity'
        self._session.headers['Connection'] = 'close'
        self._session.headers['Accept'] = 'text/html; application/vnd.paos+xml'
        self._session.headers['PAOS'] = 'ver="urn:liberty:paos:2003-08";"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"'
        resp = self._session.request("GET", self._SP_TARGET)

        # The idp request is the sp response sanse header
        sp_response = resp.text
        idp_request = re.sub(r'<S:Header>.*?</S:Header>', '', sp_response)

        # Removing unneeded headers
        del self._session.headers['PAOS']
        del self._session.headers['Accept']

        # Getting the idp response
        self._session.headers['Content-Type'] = 'text/xml; charset=utf-8'
        self._session.headers['Authorization'] = 'Basic {}'.format(authenticationString.decode('utf-8'))
        responseIdp = self._session.request("POST", self._IDP_ENDPOINT, data=idp_request)
        idp_response = responseIdp.text

        # Do not let the password hang around in the session headers (or anywhere else)
        del self._session.headers['Authorization']
        del authenticationString

        # collecting the information we need
        relay_state = re.findall(r'<ecp:RelayState.*ecp:RelayState>', sp_response)[0]
        response_consumer_url = re.findall(r'<paos:Request.*?responseConsumerURL="(.*?)".*?/>', sp_response)[0]
        assertion_consumer_service = re.findall(r'<ecp:Response.*?AssertionConsumerServiceURL="(.*?)".*?/>', idp_response)[0]

        # the response_consumer_url and assertion_consumer_service should be the same
        assert response_consumer_url == assertion_consumer_service

        # adding the relay_state to the sp_packacge and removing the xml header
        relay_state = re.sub(r'S:', 'soap11:', relay_state)  # is this exactly how I want to do this?
        sp_package = re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>\n(.*?)<ecp:Response.*?/>', r'\g<1>'+relay_state, idp_response)

        # Sending the last post (that should result in the shibbolith session cookie being set)
        self._session.headers['Content-Type'] = 'application/vnd.paos+xml'
        response = self._session.request("POST", assertion_consumer_service, data=sp_package)

        # setting the headers back to where they should be
        del self._session.headers['Content-Type']
        self._session.headers['Accept-Encoding'] = 'gzip, deflate'
        self._session.headers['Accept'] = '*/*'
        self._session.headers['Connection'] = 'keep-alive'

        # check that the cookie was set
        # (the name of the shib session cookie is not fixed so we have to search for it)
        cookieFound = False
        for cookie in self._session.cookies:
            if "shibsession" in cookie.name:
                cookieFound = True
                break
        if not cookieFound:
            warnings.warn("Authentication failed!", AuthenticationWarning)
            return

        # get user information
        response = self._session.request("GET", self._SESSION_INFO_URL)

        if response.status_code != 200:
            print("Authentication failed!")
            return

        exp = re.findall(r'<strong>Session Expiration \(barring inactivity\):</strong> (.*?)\n', response.text)
        if len(exp) == 0:
            print("Authentication failed!")
            return False
        else:
            exp = exp[0]

        print("Authentication successful!")
        print("Session Expiration: {}".format(exp))
        return True

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, stream=False, auth=None, retrieve_all=True):
        """
        Override of the parent method:
        A generic HTTP request method, similar to ``requests.Session.request``

        This is a low-level method not generally intended for use by astroquery
        end-users.

        The main difference in this function is that it takes care of the long
        polling requirements of the mashup server.
        Thus the cache parameter of the parent method is hard coded to false
        (the MAST server does it's own caching, no need to cache locally and it
        interferes with follow requests after an 'Executing' response was returned.)
        Also parameters that allow for file download through this method are removed


        Parameters
        ----------
        method : 'GET' or 'POST'
        url : str
        params : None or dict
        data : None or dict
        headers : None or dict
        auth : None or dict
        files : None or dict
        stream : bool
            See ``requests.request``
        retrieve_all : bool
            Default True. Retrieve all pages of data or just the one indicated in the params value.

        Returns
        -------
        response : ``requests.Response``
            The response from the server.
        """

        startTime = time.time()
        allResponses = []
        totalPages = 1
        curPage = 0

        while curPage < totalPages:
            status = "EXECUTING"

            while status == "EXECUTING":
                response = super(MastClass, self)._request(method, url, params=params, data=data,
                                                           headers=headers, files=files, cache=False,
                                                           stream=stream, auth=auth)

                if (time.time() - startTime) >= self.TIMEOUT:
                    raise TimeoutError("Timeout limit of {} exceeded.".format(self.TIMEOUT))

                result = response.json()

                if not result:  # kind of hacky, but col_config service returns nothing if there is an error
                    status = "ERROR"
                else:
                    status = result.get("status")

            allResponses.append(response)

            if (status != "COMPLETE") or (not retrieve_all):
                break

            paging = result.get("paging")
            if paging is None:
                break
            totalPages = paging['pagesFiltered']
            curPage = paging['page']

            data = data.replace("page%22%3A%20"+str(curPage)+"%2C", "page%22%3A%20"+str(curPage+1)+"%2C")

        return allResponses

    def _get_col_config(self, service):
        """
        Gets the columnsConfig entry for given service and stores it in self._column_configs.

        Parameters
        ----------
        service : string
            The service for which the columns config will be fetched.
        """

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        response = self._request("POST", self._COLUMNS_CONFIG_URL,
                                 data=("colConfigId="+service), headers=headers)

        self._column_configs[service] = response[0].json()

    def _parse_result(self, responses, verbose=False):
        """
        Parse the results of a list of ``requests.Response`` objects and returns an `astropy.table.Table` of results.

        Parameters
        ----------
        responses : list of ``requests.Response``
            List of ``requests.Response`` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `astropy.table.Table`
        """

        # loading the columns config
        colConfig = None
        if self._current_service:
            colConfig = self._column_configs.get(self._current_service)
            self._current_service = None  # clearing current service

        resultList = []

        for resp in responses:
            result = resp.json()

            # check for error message
            if result['status'] == "ERROR":
                raise RemoteServiceError(result.get('msg', "There was an error with your request."))

            resTable = _mashup_json_to_table(result, colConfig)
            resultList.append(resTable)

        return vstack(resultList)

    def _login(self, username=None, password=None, session_token=None,
               store_password=False, reenter_password=False):
        """
        Log into the MAST portal.

        Parameters
        ----------
        username : string, optional
            Default is None.
            The username for the user logging in.
            Usually this will be the user's email address.
            If a username is necessary but not supplied it will be prompted for.
        password : string, optional
            Default is None.
            The password associated with the given username.
            For security passwords should not be typed into the terminal or jupyter
            notebook, but input using a more secure method such as `~getpass.getpass`.
            If a password is necessary but not supplied it will be prompted for.
        session_token : dict or `~http.cookiejar.Cookie`, optional
            A valid MAST session cookie that will be attached to the current session
            in lieu of logging in with a username/password.
            If username and/or password is supplied, this argument will be ignored.
        store_password : bool, optional
            Default False.
            If true, username and password will be stored securely in your keyring.
        reenter_password : bool, optional
            Default False.
            Asks for the password even if it is already stored in the keyring.
            This is the way to overwrite an already stored password on the keyring.
        """

        # checking the inputs
        if (username or password) and session_token:
            warnings.warn("Both username and session token supplied, session token will be ignored.",
                          InputWarning)
            session_token = None
        elif session_token and store_password:
            warnings.warn("Password is not used for token based login, therefor password cannot be stored.",
                          InputWarning)

        if session_token:
            return self._attach_cookie(session_token)
        else:
            # get username if not supplied
            if not username:
                username = input("Enter your username: ")

            # check keyring get password if not supplied
            if not password and not reenter_password:
                password = keyring.get_password("astroquery:mast.stsci.edu", username)

            # get password if no password is found (or reenter_password is set)
            if not password:
                password = getpass("Enter password for {}: ".format(username))

            # store password if desired
            if store_password:
                keyring.set_password("astroquery:mast.stsci.edu", username, password)

            return self._shib_login(username, password)

    def login(self, username=None, password=None, session_token=None,
              store_password=False, reenter_password=False):
        """
        Log into the MAST portal.

        Parameters
        ----------
        username : string, optional
            Default is None.
            The username for the user logging in.
            Usually this will be the user's email address.
            If a username is necessary but not supplied it will be prompted for.
        password : string, optional
            Default is None.
            The password associated with the given username.
            For security passwords should not be typed into the terminal or jupyter
            notebook, but input using a more secure method such as `~getpass.getpass`.
            If a password is necessary but not supplied it will be prompted for.
        session_token : dict or `~http.cookiejar.Cookie`, optional
            A valid MAST session cookie that will be attached to the current session
            in lieu of logging in with a username/password.
            If username and/or password is supplied, this argument will be ignored.
        store_password : bool, optional
            Default False.
            If true, username and password will be stored securely in your keyring.
        reenter_password : bool, optional
            Default False.
            Asks for the password even if it is already stored in the keyring.
            This is the way to overwrite an already stored password on the keyring.
        """

        return super(MastClass, self).login(username=username, password=password,
                                                 session_token=session_token,
                                                 store_password=store_password,
                                                 reenter_password=reenter_password)

    def logout(self):
        """
        Log out of current MAST session.
        """
        self._session.cookies.clear_session_cookies()
        self._authenticated = False

    def get_token(self):
        """
        Returns MAST session cookie.

        Returns
        -------
        response : `~http.cookiejar.Cookie`
        """

        shibCookie = None
        for cookie in self._session.cookies:
            if "shibsession" in cookie.name:
                shibCookie = cookie
                break

        if not shibCookie:
            warnings.warn("No session token found.", AuthenticationWarning)

        return shibCookie

    def session_info(self, silent=False):
        """
        Displays information about current MAST session, and returns session info dictionary.

        Parameters
        ----------
        silent : bool, optional
            Default False.
            Suppresses output to stdout.

        Returns
        -------
        response : dict
        """

        # get user information
        response = self._session.request("GET", self._SESSION_INFO_URL)

        sessionInfo = response.text

        patternString = r'Session Expiration \(barring inactivity\):</strong> (.*?)\n.*?STScI_Email</strong>: (.*?)\n<strong>STScI_FirstName</strong>: (.*?)\n<strong>STScI_LastName</strong>: (.*?)\n'

        userCats = ("Session Expiration", "Username", "First Name", "Last Name")
        userInfo = re.findall(patternString, sessionInfo, re.DOTALL)

        if len(userInfo) == 0:
            infoDict = dict(zip(userCats, (None, "anonymous", "", "")))
        else:
            infoDict = dict(zip(userCats, userInfo[0]))
            infoDict['Session Expiration'] = int(re.findall(r"(\d+) minute\(s\)",
                                                            infoDict['Session Expiration'])[0])*u.min

        if not silent:
            for key in infoDict:
                print(key+":", infoDict[key])

        return infoDict

    @class_or_instance
    def service_request_async(self, service, params, pagesize=None, page=None, **kwargs):
        """
        Given a Mashup service and parameters, builds and excecutes a Mashup query.
        See documentation `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__
        for information about how to build a Mashup request.

        Parameters
        ----------
        service : str
            The Mashup service to query.
        params : dict
            JSON object containing service parameters.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize (set in configs) for this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to obtain
            a specific page of results.
        **kwargs :
            See MashupRequest properties
            `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__
            for additional keyword arguments.

        Returns
        -------
        response : list of ``requests.Response``
        """

        # setting self._current_service
        if service not in self._column_configs.keys():
            self._get_col_config(service)
        self._current_service = service

        # setting up pagination
        if not pagesize:
            pagesize = self.PAGESIZE
        if not page:
            page = 1
            retrieveAll = True
        else:
            retrieveAll = False

        # TODO: remove "Clara development" before pull request
        headers = {"User-Agent": self._session.headers["User-Agent"] + " Clara development",
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        mashupRequest = {'service': service,
                         'params': params,
                         'format': 'json',
                         'pagesize': pagesize,
                         'page': page}

        for prop, value in kwargs.items():
            mashupRequest[prop] = value

        reqString = _prepare_service_request_string(mashupRequest)
        response = self._request("POST", self._MAST_REQUEST_URL, data=reqString, headers=headers,
                                 retrieve_all=retrieveAll)

        return response

    def _resolve_object(self, objectname):
        """
        Resolves an object name to a position on the sky.

        Parameters
        ----------
        objectname : str
            Name of astronomical object to resolve.
        """

        service = 'Mast.Name.Lookup'
        params = {'input': objectname,
                  'format': 'json'}

        response = self.service_request_async(service, params)

        result = response[0].json()

        if len(result['resolvedCoordinate']) == 0:
            raise ResolverError("Could not resolve {} to a sky position.".format(objectname))

        ra = result['resolvedCoordinate'][0]['ra']
        dec = result['resolvedCoordinate'][0]['decl']
        coordinates = coord.SkyCoord(ra, dec, unit="deg")

        return coordinates


@async_to_sync
class ObservationsClass(MastClass):
    """
    MAST Observations query class.

    Class for querying MAST observational data.
    """

    def list_missions(self):
        """
        Lists data missions archived by MAST and avaiable through `astroquery.mast`.

        Returns
        --------
        response : list
            List of available missions.
        """

        # getting all the hitogram information
        service = "Mast.Caom.All"
        params = {}
        response = Mast.service_request_async(service, params, format='extjs')
        jsonResponse = response[0].json()

        # getting the list of missions
        histData = jsonResponse['data']['Tables'][0]['Columns']
        for facet in histData:
            if facet['text'] == "obs_collection":
                missionInfo = facet['ExtendedProperties']['histObj']
                missions = list(missionInfo.keys())
                missions.remove('hist')
                return missions

    def _build_filter_set(self, **filters):
        """
        Takes user input dictionary of filters and returns a filterlist that the Mashup can understand.

        Parameters
        ----------
        **filters :
            Filters to apply. At least one filter must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For example: filters=["FUV","NUV"],proposal_pi="Osten",t_max=[52264.4586,54452.8914]

        Returns
        -------
        response : list(dict)
            The mashup json filter object.
        """

        if not self._column_configs.get("Mast.Caom.Cone"):
            self._get_col_config("Mast.Caom.Cone")

        caomColConfig = self._column_configs["Mast.Caom.Cone"]

        mashupFilters = []
        for colname, value in filters.items():

            # make sure value is a list-like thing
            if np.isscalar(value,):
                value = [value]

            # Get the column type and separator
            colInfo = caomColConfig.get(colname)
            if not colInfo:
                warnings.warn("Filter {} does not exist. This filter will be skipped.".format(colname), InputWarning)
                continue

            colType = "discrete"
            if colInfo.get("vot.datatype", colInfo.get("type")) in ("double", "float"):
                colType = "continuous"

            separator = colInfo.get("separator")
            freeText = None

            # validate user input
            if colType == "continuous":
                if len(value) < 2:
                    warningString = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Not enough values provided, skipping..."
                    warnings.warn(warningString, InputWarning)
                    continue
                elif len(value) > 2:
                    warningString = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Too many values provided, the first two will be " + \
                                    "assumed to be the min and max values."
                    warnings.warn(warningString, InputWarning)
            else:  # coltype is discrete, all values should be represented as strings, even if numerical
                value = [str(x) for x in value]

                # check for wildcards

                for i, val in enumerate(value):
                    if ('*' in val) or ('%' in val):
                        if freeText:  # freeText is already set cannot set again
                            warningString = "Only one wildcarded value may be used per filter, " + \
                                            "all others must be exact.\n" + \
                                            "Skipping {}...".format(val)
                            warnings.warn(warningString, InputWarning)
                        else:
                            freeText = val.replace('*', '%')
                        value.pop(i)

            # craft mashup filter entry
            entry = {}
            entry["paramName"] = colname
            if separator:
                entry["separator"] = separator
            if colType == "continuous":
                entry["values"] = [{"min": value[0], "max":value[1]}]
            else:
                entry["values"] = value
            if freeText:
                entry["freeText"] = freeText

            mashupFilters.append(entry)

        return mashupFilters

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.

        Returns
        -------
        response : list of ``requests.Response``
        """

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        service = 'Mast.Caom.Cone'
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        return self.service_request_async(service, params, pagesize, page)

    @class_or_instance
    def query_object_async(self, objectname, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given an object name, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Defaulte None.
            Can be used to override the default behavior of all results being returned
            to obtain a specific page of results.

        Returns
        -------
        response : list of ``requests.Response``
        """

        coordinates = self._resolve_object(objectname)

        return self.query_region_async(coordinates, radius, pagesize, page)

    @class_or_instance
    def query_criteria_async(self, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns a list of MAST observations.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.
        **criteria
            Criteria to apply. At least one non-positional criteria must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]


        Returns
        -------
        response : list(`requests.Response`)
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # grabbing the observation type (science vs calibration)
        obstype = criteria.pop('obstype', 'science')

        # Build the mashup filter object
        mashupFilters = self._build_filter_set(**criteria)

        if not mashupFilters:
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

        # handle position info (if any)
        position = None

        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.")

        if objectname:
            coordinates = self._resolve_object(objectname)

        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)

            # if radius is just a number we assume degrees
            if isinstance(radius, (int, float)):
                radius = radius * u.deg
            radius = coord.Angle(radius)

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        # send query
        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "*",
                      "filters": mashupFilters,
                      "obstype": obstype,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "*",
                      "filters": mashupFilters,
                      "obstype": obstype}

        return self.service_request_async(service, params)

    def query_region_count(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns the number of MAST observations in that region.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize for.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.

        Returns
        -------
        response : int
        """

        # build the coordinates string needed by Mast.Caom.Filtered.Position
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        # turn coordinates into the format
        position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        service = "Mast.Caom.Filtered.Position"
        params = {"columns": "COUNT_BIG(*)",
                  "filters": [],
                  "position": position}

        return int(self.service_request(service, params, pagesize, page)[0][0])

    def query_object_count(self, objectname, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given an object name, returns the number of MAST observations.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.

        Returns
        -------
        response : int
        """

        coordinates = self._resolve_object(objectname)

        return self.query_region_count(coordinates, radius, pagesize, page)

    def query_criteria_count(self, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns the number of MAST observations meeting those criteria.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.
        **criteria
            Criteria to apply. At least one non-positional criterion must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]


        Returns
        -------
        response : int
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # grabbing the observation type (science vs calibration)
        obstype = criteria.pop('obstype', 'science')

        # Build the mashup filter object
        mashupFilters = self._build_filter_set(**criteria)

        # handle position info (if any)
        position = None

        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.")

        if objectname:
            coordinates = self._resolve_object(objectname)

        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)

            # if radius is just a number we assume degrees
            if isinstance(radius, (int, float)):
                radius = radius * u.deg
            radius = coord.Angle(radius)

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        # send query
        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashupFilters,
                      "obstype": obstype,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashupFilters,
                      "obstype": obstype}

        return self.service_request(service, params)[0][0].astype(int)

    @class_or_instance
    def get_product_list_async(self, observations):
        """
        Given a "Product Group Id" (column name obsid) returns a list of associated data products.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.

        Parameters
        ----------
        observations : str or `astropy.table.Row` or list/Table of same
            Row/Table of MAST query results (e.g. output from `query_object`)
            or single/list of MAST Product Group Id(s) (obsid).
            See description `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Returns
        -------
            response : list(`requests.Response`)
        """

        # getting the obsid list
        if type(observations) == Row:
            observations = observations["obsid"]
        if np.isscalar(observations):
            observations = [observations]
        if type(observations) == Table:
            observations = observations['obsid']

        service = 'Mast.Caom.Products'
        params = {'obsid': ','.join(observations)}

        return self.service_request_async(service, params)

    def filter_products(self, products, mrp_only=True, **filters):
        """
        Takes an `astropy.table.Table` of MAST observation data products and filters it based on given filters.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing data products to be filtered.
        mrp_only : bool, optional
            Default True. When set to true only "Minimum Recommended Products" will be returned.
        **filters :
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__ and 'extension'
            which is the desired file extension.
            The Column Name (or 'extension') is the keyword, with the argument being one or
            more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
        response : `~astropy.table.Table`
        """

        # Dealing with mrp first, b/c it's special
        if mrp_only:
            products.remove_rows(np.where(products['productGroupDescription'] != "Minimum Recommended Products"))

        filterMask = np.full(len(products), True, dtype=bool)

        for colname, vals in filters.items():

            if type(vals) == str:
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
                if colname == 'extension':  # extension is not actually a column
                    mask |= [x.endswith(elt) for x in products["productFilename"]]
                else:
                    mask |= (products[colname] == elt)

            filterMask &= mask

        return products[np.where(filterMask)]

    def _download_curl_script(self, products, out_dir):
        """
        Takes an `astropy.table.Table` of data products and downloads a curl script to pull the datafiles.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing products to be included in the curl script.
        out_dir : str
            Directory in which the curl script will be saved.

        Returns
        -------
        response : `astropy.table.Table`
        """

        urlList = products['dataURI']
        descriptionList = products['description']
        productTypeList = products['dataproduct_type']

        downloadFile = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        pathList = [downloadFile+"/"+x['obs_collection']+'/'+x['obs_id']+'/'+x['productFilename'] for x in products]

        service = "Mast.Bundle.Request"
        params = {"urlList": ",".join(urlList),
                  "filename": downloadFile,
                  "pathList": ",".join(pathList),
                  "descriptionList": list(descriptionList),
                  "productTypeList": list(productTypeList),
                  "extension": 'curl'}

        response = self.service_request_async(service, params)

        bundlerResponse = response[0].json()

        localPath = out_dir.rstrip('/') + "/" + downloadFile + ".sh"
        self._download_file(bundlerResponse['url'], localPath)

        status = "COMPLETE"
        msg = None
        url = None

        if not os.path.isfile(localPath):
            status = "ERROR"
            msg = "Curl could not be downloaded"
            url = bundlerResponse['url']
        else:
            missingFiles = [x for x in bundlerResponse['statusList'].keys()
                            if bundlerResponse['statusList'][x] != 'COMPLETE']
            if len(missingFiles):
                msg = "{} files could not be added to the curl script".format(len(missingFiles))
                url = ",".join(missingFiles)

        manifest = Table({'Local Path': [localPath],
                          'Status': [status],
                          'Message': [msg],
                          "URL": [url]})
        return manifest

    def _download_files(self, products, base_dir, cache=True):
        """
        Takes an `astropy.table.Table` of data products and downloads them into the dirctor given by base_dir.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing products to be downloaded.
        base_dir : str
            Directory in which files will be downloaded.
        cache : bool
            Default is True. If file is found on disc it will not be downloaded again.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        manifestArray = []
        for dataProduct in products:

            localPath = base_dir + "/" + dataProduct['obs_collection'] + "/" + dataProduct['obs_id']

            dataUrl = dataProduct['dataURI']
            if "http" not in dataUrl:  # url is actually a uri
                dataUrl = self._MAST_DOWNLOAD_URL + dataUrl.lstrip("mast:")

                # HACK: user identity info not passed properly to downloader
                # using /api/v0 url, so if user is logged in go through portal url
                # (will be fixed server side in next, this is a temporary workaround)
                if self.session_info(True)["Username"] != "anonymous":
                    dataUrl = dataUrl.replace("api/v0", "portal")

            if not os.path.exists(localPath):
                os.makedirs(localPath)

            localPath += '/' + dataProduct['productFilename']

            status = "COMPLETE"
            msg = None
            url = None

            try:
                self._download_file(dataUrl, localPath, cache=cache)

                # check file size also this is where would perform md5
                if not os.path.isfile(localPath):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = dataUrl
                else:
                    fileSize = os.stat(localPath).st_size
                    if fileSize != dataProduct["size"]:
                        status = "ERROR"
                        msg = "Downloaded filesize is {},".format(dataProduct['size']) + \
                              "but should be {}, file may be partial or corrupt.".format(fileSize)
                        url = dataUrl
            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = dataUrl

            manifestArray.append([localPath, status, msg, url])

        manifest = Table(rows=manifestArray, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest

    def download_products(self, products, download_dir=None,
                          cache=True, curl_flag=False, mrp_only=True, **filters):
        """
        Download data products.

        Parameters
        ----------
        products : str, list, `astropy.table.Table`
            Either a single or list of obsids (as can be given to `get_product_list`),
            or a Table of products (as is returned by `get_product_list`)
        download_dir : str, optional
            Optional.  Directory to download files to.  Defaults to current directory.
        cache : bool, optional
            Default is True. If file is found on disc it will not be downloaded again.
            Note: has no affect when downloading curl script.
        curl_flag : bool, optional
            Default is False.  If true instead of downloading files directly, a curl script
            will be downloaded that can be used to download the data files at a later time.
        mrp_only : bool, optional
            Default True. When set to true only "Minimum Recommended Products" will be returned.
        **filters :
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__ and 'extension'
            which is the desired file extension.
            The Column Name (or 'extension') is the keyword, with the argument being one or
            more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
        response : `~astropy.table.Table`
            The manifest of files downloaded, or status of files on disk if curl option chosen.
        """

        # If the products list is not already a table of products we need to  get the products and
        # filter them appropriately
        if type(products) != Table:

            if type(products) == str:
                products = [products]

            # collect list of products
            productLists = []
            for oid in products:
                productLists.append(self.get_product_list(oid))

            products = vstack(productLists)

        # apply filters
        products = self.filter_products(products, mrp_only, **filters)

        if not len(products):
            warnings.warn("No products to download.", NoResultsWarning)
            return

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script
            manifest = self._download_curl_script(products, download_dir)

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload"
            manifest = self._download_files(products, base_dir, cache)

        return manifest



Observations = ObservationsClass()
Mast = MastClass()
