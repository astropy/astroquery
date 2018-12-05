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
import string
import os
import re
import keyring
import threading
import requests

import numpy as np

from requests import HTTPError
from getpass import getpass
from base64 import b64encode

import astropy.units as u
import astropy.coordinates as coord
from astropy.utils import deprecated

from astropy.table import Table, Row, vstack, MaskedColumn
from astropy.extern.six.moves.urllib.parse import quote as urlencode
from astropy.extern.six.moves.http_cookiejar import Cookie
from astropy.utils.console import ProgressBarOrSpinner
from astropy.utils.exceptions import AstropyWarning
from astropy.logger import log

from ..query import QueryWithLogin
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import (TimeoutError, InvalidQueryError, RemoteServiceError,
                          LoginError, ResolverError, MaxResultsWarning,
                          NoResultsWarning, InputWarning, AuthenticationWarning)
from . import conf
from . import fpl


__all__ = ['Observations', 'ObservationsClass',
           'Mast', 'MastClass']


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
            atype = np.int64
            ignoreValue = -999 if (ignoreValue is None) else ignoreValue
        if atype == "date":
            atype = "str"
            ignoreValue = "" if (ignoreValue is None) else ignoreValue

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
        self._COLUMNS_CONFIG_URL = conf.server + "/portal/Mashup/Mashup.asmx/columnsconfig"

        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

        self._column_configs = dict()
        self._current_service = None

        try:
            self._auth_mode = self._get_auth_mode()
        except (requests.exceptions.ConnectionError, IOError):
            # this is fine, we're in test mode
            self._auth_mode = 'SHIB-ECP'

        if "SHIB-ECP" == self._auth_mode:
            log.debug("Using Legacy Shibboleth login")
            self._SESSION_INFO_URL = conf.server + "/Shibboleth.sso/Session"
            self._SP_TARGET = conf.server + "/api/v0/Mashup/Login/login.html"
            self._IDP_ENDPOINT = conf.ssoserver + "/idp/profile/SAML2/SOAP/ECP"
            self._MAST_DOWNLOAD_URL = conf.server + "/api/v0/Download/file"
        elif "MAST-AUTH" == self._auth_mode:
            log.debug("Using Auth.MAST login")
            self._SESSION_INFO_URL = conf.server + "/whoami"
            self._MAST_DOWNLOAD_URL = conf.server + "/api/v0.1/Download/file"
            self._MAST_BUNDLE_URL = conf.server + "/api/v0.1/Download/bundle"
        else:
            raise Exception("Unknown MAST Auth mode %s" % self._auth_mode)

        if username or session_token:
            self.login(username, password, session_token)

    def _get_auth_mode(self):
        _auth_mode = "SHIB-ECP"

        # Detect auth mode from auth_type endpoint
        resp = self._session.get(conf.server + '/auth_type')
        if resp.status_code == 200:
            _auth_mode = resp.text.strip()
        else:
            log.warning("Unknown MAST auth mode, defaulting to Legacy Shibboleth login")
        return _auth_mode

    def _login(self, *args, **kwargs):
        if "SHIB-ECP" == self._auth_mode:
            return self._shib_legacy_login(*args, **kwargs)
        elif "MAST-AUTH" == self._auth_mode:
            return self._authorize(*args, **kwargs)
        else:
            raise Exception("Unknown MAST Auth mode %s" % self._auth_mode)

    def get_token(self, *args, **kwargs):
        """
        Returns MAST token cookie.

        Returns
        -------
        response : `~http.cookiejar.Cookie`
        """
        if "SHIB-ECP" == self._auth_mode:
            return self._shib_get_token(*args, **kwargs)
        elif "MAST-AUTH" == self._auth_mode:
            return self._get_token(*args, **kwargs)
        else:
            raise Exception("Unknown MAST Auth mode %s" % self._auth_mode)

    def session_info(self, *args, **kwargs):  # pragma: no cover
        """
        Displays information about current MAST user, and returns user info dictionary.

        Parameters
        ----------
        silent : bool, optional
            Default False.
            Suppresses output to stdout.

        Returns
        -------
        response : dict
        """
        if "SHIB-ECP" == self._auth_mode:
            return self._shib_session_info(*args, **kwargs)
        elif "MAST-AUTH" == self._auth_mode:
            return self._session_info(*args, **kwargs)
        else:
            raise Exception("Unknown MAST Auth mode %s" % self._auth_mode)

    def _shib_attach_cookie(self, session_token):  # pragma: no cover
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
            if "shibsession" not in session_token.name:
                raise LoginError("Invalid session token")

            # add cookie to session
            self._session.cookies.set_cookie(session_token)

        elif isinstance(session_token, dict):
            if len(session_token) > 1:
                warnings.warn("Too many entries in token dictionary, only shibsession cookie will be used",
                              InputWarning)

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
            warnings.warn("Status code: {}\nAuthentication failed!".format(response.status_code),
                          AuthenticationWarning)
            return False

        exp = re.findall(r'<strong>Session Expiration \(barring inactivity\):</strong> (.*?)\n', response.text)
        if len(exp) == 0:
            warnings.warn("{}\nAuthentication failed!".format(response.text),
                          AuthenticationWarning)
            return False
        else:
            exp = exp[0]

        log.info("Authentication successful!\nSession Expiration: {}".format(exp))
        return True

    def _shib_login(self, username, password):  # pragma: no cover
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
        assertion_consumer_service = re.findall(r'<ecp:Response.*?AssertionConsumerServiceURL="(.*?)".*?/>',
                                                idp_response)[0]

        # the response_consumer_url and assertion_consumer_service should be the same
        assert response_consumer_url == assertion_consumer_service

        # adding the relay_state to the sp_packacge and removing the xml header
        relay_state = re.sub(r'S:', 'soap11:', relay_state)  # is this exactly how I want to do this?
        sp_package = re.sub(r'<\?xml version="1.0" encoding="UTF-8"\?>\n(.*?)<ecp:Response.*?/>', r'\g<1>'+relay_state,
                            idp_response)

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
            warnings.warn("Authentication failed!", AuthenticationWarning)
            return

        exp = re.findall(r'<strong>Session Expiration \(barring inactivity\):</strong> (.*?)\n', response.text)
        if len(exp) == 0:
            warnings.warn("Authentication failed!", AuthenticationWarning)
            return False
        else:
            exp = exp[0]

        log.info("Authentication successful!\nSession Expiration: {}".format(exp))
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

    def _get_col_config(self, service, fetch_name=None):
        """
        Gets the columnsConfig entry for given service and stores it in `self._column_configs`.

        Parameters
        ----------
        service : string
            The service for which the columns config will be fetched.
        fetch_name : string, optional
            If the columns-config associated with the service has a different name,
            use this argument. The default sets it to the same as service.
        """

        if not fetch_name:
            fetch_name = service

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        response = self._request("POST", self._COLUMNS_CONFIG_URL,
                                 data=("colConfigId="+fetch_name), headers=headers)

        self._column_configs[service] = response[0].json()

        more = False  # for some catalogs this is not enough information
        if "tess" in fetch_name.lower():
            all_name = "Mast.Catalogs.All.Tic"
            more = True
        elif "dd." in fetch_name.lower():
            all_name = "Mast.Catalogs.All.DiskDetective"
            more = True

        if more:
            mashupRequest = {'service': all_name, 'params': {}, 'format': 'extjs'}
            reqString = _prepare_service_request_string(mashupRequest)
            response = self._request("POST", self._MAST_REQUEST_URL, data=reqString, headers=headers)
            jsonResponse = response[0].json()

            self._column_configs[service].update(jsonResponse['data']['Tables'][0]
                                                 ['ExtendedProperties']['discreteHistogram'])
            self._column_configs[service].update(jsonResponse['data']['Tables'][0]
                                                 ['ExtendedProperties']['continuousHistogram'])
            for col, val in self._column_configs[service].items():
                val.pop('hist', None)  # don't want to save all this unecessary data

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

        allResults = vstack(resultList)

        # Check for no results
        if not allResults:
            warnings.warn("Query returned no results.", NoResultsWarning)
        return allResults

    def _authorize(self, token=None, store_token=False, reenter_token=False):  # pragma: no cover
        """
        Log into the MAST portal.

        Parameters
        ----------
        token : string, optional
            Default is None.
            The token to authenticate the user.
            This can be generated at
                https://auth.mast.stsci.edu/token?suggested_name=Astroquery&suggested_scope=mast:exclusive_access.
            If not supplied, it will be prompted for if not in the keyring or set via $MAST_API_TOKEN
        store_token : bool, optional
            Default False.
            If true, username and password will be stored securely in your keyring.
        """

        if token is None and "MAST_API_TOKEN" in os.environ:
            token = os.environ["MAST_API_TOKEN"]

        if token is None:
            token = keyring.get_password("astroquery:mast.stsci.edu.token", "masttoken")

        if token is None or reenter_token:
            auth_server = conf.server.replace("mast", "auth.mast")
            auth_link = auth_server + "/token?suggested_name=Astroquery&suggested_scope=mast:exclusive_access"
            info_msg = "If you do not have an API token already, visit the following link to create one: "
            log.info(info_msg + auth_link)
            token = getpass("Enter MAST API Token: ")

        # store password if desired
        if store_token:
            keyring.set_password("astroquery:mast.stsci.edu.token", "masttoken", token)

        self._session.headers["Accept"] = "application/json"
        self._session.cookies["mast_token"] = token
        info = self.session_info(silent=True)

        if not info["anon"]:
            log.info("MAST API token accepted, welcome %s" % info["attrib"].get("display_name"))
        else:
            log.warn("MAST API token invalid!")

        return not info["anon"]

    def _shib_legacy_login(self, username=None, password=None, session_token=None,
                           store_password=False, reenter_password=False):  # pragma: no cover
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
            return self._shib_attach_cookie(session_token)
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

    def logout(self):  # pragma: no cover
        """
        Log out of current MAST session.
        """
        self._session.cookies.clear_session_cookies()
        self._authenticated = False

    def _get_token(self):  # pragma: no cover
        """
        Returns MAST token cookie.

        Returns
        -------
        response : `~http.cookiejar.Cookie`
        """

        tokenCookie = None
        for cookie in self._session.cookies:
            if "mast_token" in cookie.name:
                tokenCookie = cookie
                break

        if not tokenCookie:
            warnings.warn("No auth token found.", AuthenticationWarning)

        return tokenCookie

    def _session_info(self, silent=False):  # pragma: no cover
        """
        Displays information about current MAST user, and returns user info dictionary.

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
        self._session.headers["Accept"] = "application/json"
        response = self._session.request("GET", self._SESSION_INFO_URL)

        infoDict = json.loads(response.text)

        if not silent:
            for key, value in infoDict.items():
                if isinstance(value, dict):
                    for subkey, subval in value.items():
                        print("%s.%s: %s" % (key, subkey, subval))
                else:
                    print("%s: %s" % (key, value))

        return infoDict

    def _shib_get_token(self):  # pragma: no cover
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

    def _shib_session_info(self, silent=False):  # pragma: no cover
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

        patternString = r'Session Expiration \(barring inactivity\):</strong> (.*?)\n.*?STScI_Email</strong>: ' + \
                        r'(.*?)\n<strong>STScI_FirstName</strong>: (.*?)\n<strong>STScI_LastName</strong>: (.*?)\n'

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
            fetch_name = kwargs.pop('fetch_name', None)
            self._get_col_config(service, fetch_name)
        self._current_service = service

        # setting up pagination
        if not pagesize:
            pagesize = self.PAGESIZE
        if not page:
            page = 1
            retrieveAll = True
        else:
            retrieveAll = False

        headers = {"User-Agent": self._session.headers["User-Agent"],
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

    def _build_filter_set(self, column_config_name, service_name=None, **filters):
        """
        Takes user input dictionary of filters and returns a filterlist that the Mashup can understand.

        Parameters
        ----------
        column_config_name : string
            The service for which the columns config will be fetched.
        service_name : string, optional
            The service that will use the columns config, default is to be the same as column_config_name.
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

        if not service_name:
            service_name = column_config_name

        if not self._column_configs.get(service_name):
            self._get_col_config(service_name, fetch_name=column_config_name)

        caomColConfig = self._column_configs[service_name]

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
            if (colInfo.get("vot.datatype", colInfo.get("type")) in ("double", "float", "numeric")) \
               or colInfo.get("treatNumeric"):
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


@async_to_sync
class ObservationsClass(MastClass):
    """
    MAST Observations query class.

    Class for querying MAST observational data.
    """

    def __init__(self, *args, **kwargs):

        super(ObservationsClass, self).__init__(*args, **kwargs)

        self._boto3 = None
        self._botocore = None
        self._pubdata_bucket = "stpubdata"

    def list_missions(self):
        """
        Lists data missions archived by MAST and avaiable through `astroquery.mast`.

        Returns
        --------
        response : list
            List of available missions.
        """

        # getting all the histogram information
        service = "Mast.Caom.All"
        params = {}
        response = self.service_request_async(service, params, format='extjs')
        jsonResponse = response[0].json()

        # getting the list of missions
        histData = jsonResponse['data']['Tables'][0]['Columns']
        for facet in histData:
            if facet['text'] == "obs_collection":
                missionInfo = facet['ExtendedProperties']['histObj']
                missions = list(missionInfo.keys())
                missions.remove('hist')
                return missions

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

        # Build the mashup filter object and store it in the correct service_name entry
        if coordinates or objectname:
            mashupFilters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered.Position", **criteria)
        else:
            mashupFilters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered", **criteria)

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

        # Build the mashup filter object and store it in the correct service_name entry
        if coordinates or objectname:
            mashupFilters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered.Position", **criteria)
        else:
            mashupFilters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered", **criteria)

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

    def filter_products(self, products, mrp_only=False, extension=None, **filters):
        """
        Takes an `astropy.table.Table` of MAST observation data products and filters it based on given filters.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing data products to be filtered.
        mrp_only : bool, optional
            Default False. When set to true only "Minimum Recommended Products" will be returned.
        extension : string, optional
            Default None. Option to filter by file extension.
        **filters :
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.
            The column name is the keyword, with the argument being one or more acceptable values
            for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
        response : `~astropy.table.Table`
        """

        filterMask = np.full(len(products), True, dtype=bool)

        # Applying the special filters (mrp_only and extension)
        if mrp_only:
            filterMask &= (products['productGroupDescription'] == "Minimum Recommended Products")

        if extension:
            mask = np.full(len(products), False, dtype=bool)
            for elt in extension:
                mask |= [False if isinstance(x, np.ma.core.MaskedConstant) else x.endswith(elt)
                         for x in products["productFilename"]]
            filterMask &= mask

        # Applying the rest of the filters
        for colname, vals in filters.items():

            if type(vals) == str:
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
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

        urlList = [("uri", url) for url in products['dataURI']]
        downloadFile = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        localPath = os.path.join(out_dir.rstrip('/'), downloadFile + ".sh")

        response = self._download_file(self._MAST_BUNDLE_URL + ".sh", localPath, data=urlList, method="POST")

        status = "COMPLETE"
        msg = None

        if not os.path.isfile(localPath):
            status = "ERROR"
            msg = "Curl could not be downloaded"

        manifest = Table({'Local Path': [localPath],
                          'Status': [status],
                          'Message': [msg]})
        return manifest

    def _shib_download_curl_script(self, products, out_dir):
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
        downloadFile = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        descriptionList = products['description']
        productTypeList = products['dataproduct_type']

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

    @deprecated(since="v0.3.9", alternative="enable_cloud_dataset")
    def enable_s3_hst_dataset(self):
        return self.enable_cloud_dataset()

    def enable_cloud_dataset(self, provider="AWS", profile=None):
        """
        Attempts to enable downloading public files from S3 instead of MAST.
        Requires the boto3 library to function.
        """
        import boto3
        import botocore
        if profile is not None:
            self._boto3 = boto3.Session(profile_name=profile)
        else:
            self._boto3 = boto3
        self._botocore = botocore

        log.info("Using the S3 STScI public dataset")
        log.warning("Your AWS account will be charged for access to the S3 bucket")
        log.info("See Request Pricing in https://aws.amazon.com/s3/pricing/ for details")
        log.info("If you have not configured boto3, follow the instructions here: "
                 "https://boto3.readthedocs.io/en/latest/guide/configuration.html")

    @deprecated(since="v0.3.9", alternative="disable_cloud_dataset")
    def disable_s3_hst_dataset(self):
        return self.disable_cloud_dataset()

    def disable_cloud_dataset(self):
        """
        Disables downloading public files from S3 instead of MAST
        """
        self._boto3 = None
        self._botocore = None

    @deprecated(since="v0.3.9", alternative="get_cloud_uris")
    def get_hst_s3_uris(self, dataProducts, includeBucket=True, fullUrl=False):
        return self.get_cloud_uris(dataProducts, includeBucket, fullUrl)

    def get_cloud_uris(self, dataProducts, includeBucket=True, fullUrl=False):
        """ Takes an `astropy.table.Table` of data products and turns them into s3 uris. """

        return [self.get_cloud_uri(dataProduct, includeBucket, fullUrl) for dataProduct in dataProducts]

    @deprecated(since="v0.3.9", alternative="get_cloud_uri")
    def get_hst_s3_uri(self, dataProduct, includeBucket=True, fullUrl=False):
        return self.get_cloud_uri(dataProduct, includeBucket, fullUrl)

    def get_cloud_uri(self, dataProduct, includeBucket=True, fullUrl=False):
        """ Turns a dataProduct into a S3 URI """

        if self._boto3 is None:
            raise AtrributeError("Must enable s3 dataset before attempting to query the s3 information")

        # This is a cheap operation and does not perform any actual work yet
        s3_client = self._boto3.client('s3')

        paths = fpl.paths(dataProduct)
        if paths is None:
            raise Exception("Unsupported mission")

        for path in paths:
            try:
                s3_client.head_object(Bucket=self._pubdata_bucket, Key=path, RequestPayer='requester')
                if includeBucket:
                    path = "s3://%s/%s" % (self._pubdata_bucket, path)
                elif fullUrl:
                    path = "http://s3.amazonaws.com/%s/%s" % (self._pubdata_bucket, path)
                return path
            except self._botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != "404":
                    raise

        raise Exception("Unable to locate file!")

    def _download_from_cloud(self, dataProduct, localPath, cache=True):
        # The following is a mishmash of BaseQuery._download_file and s3 access through boto

        self._pubdata_bucket = 'stpubdata'

        # This is a cheap operation and does not perform any actual work yet
        s3 = self._boto3.resource('s3')
        s3_client = self._boto3.client('s3')
        bkt = s3.Bucket(self._pubdata_bucket)

        bucketPath = self.get_cloud_uri(dataProduct, False)
        info_lookup = s3_client.head_object(Bucket=self._pubdata_bucket, Key=bucketPath, RequestPayer='requester')

        # Unfortunately, we can't use the reported file size in the reported product.  STScI's backing
        # archive database (CAOM) is frequently out of date and in many cases omits the required information.
        # length = dataProduct["size"]
        # Instead we ask the webserver (in this case S3) what the expected content length is and use that.
        length = info_lookup["ContentLength"]

        if cache and os.path.exists(localPath):
            if length is not None:
                statinfo = os.stat(localPath)
                if statinfo.st_size != length:
                    log.warning("Found cached file {0} with size {1} that is "
                                "different from expected size {2}"
                                .format(localPath,
                                        statinfo.st_size,
                                        length))
                else:
                    log.info("Found cached file {0} with expected size {1}."
                             .format(localPath, statinfo.st_size))
                    return

        with ProgressBarOrSpinner(length, ('Downloading URL s3://{0}/{1} to {2} ...'.format(
                self._pubdata_bucket, bucketPath, localPath))) as pb:

            # Bytes read tracks how much data has been received so far
            # This variable will be updated in multiple threads below
            global bytes_read
            bytes_read = 0

            progress_lock = threading.Lock()

            def progress_callback(numbytes):
                # Boto3 calls this from multiple threads pulling the data from S3
                global bytes_read

                # This callback can be called in multiple threads
                # Access to updating the console needs to be locked
                with progress_lock:
                    bytes_read += numbytes
                    pb.update(bytes_read)

            bkt.download_file(bucketPath, localPath, ExtraArgs={"RequestPayer": "requester"},
                              Callback=progress_callback)

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
            dataUrl = self._MAST_DOWNLOAD_URL + "?uri=" + dataProduct["dataURI"]

            if not os.path.exists(localPath):
                os.makedirs(localPath)

            localPath += '/' + dataProduct['productFilename']

            status = "COMPLETE"
            msg = None
            url = None

            try:
                if self._boto3 is not None and fpl.has_path(dataProduct):
                    try:
                        self._download_from_cloud(dataProduct, localPath, cache)
                    except Exception as ex:
                        log.exception("Error pulling from S3 bucket: %s" % ex)
                        log.warn("Falling back to mast download...")
                        self._download_file(dataUrl, localPath, cache=cache, head_safe=True)
                else:
                    self._download_file(dataUrl, localPath, cache=cache, head_safe=True)

                # check if file exists also this is where would perform md5,
                # and also check the filesize if the database reliably reported file sizes
                if not os.path.isfile(localPath):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = dataUrl

            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = dataUrl

            manifestArray.append([localPath, status, msg, url])

        manifest = Table(rows=manifestArray, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest

    def download_products(self, products, download_dir=None,
                          cache=True, curl_flag=False, mrp_only=False, **filters):
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
            Default False. When set to true only "Minimum Recommended Products" will be returned.
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

        # If the products list is not already a table of products we need to
        # get the products and filter them appropriately
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
            if "SHIB-ECP" == self._auth_mode:
                manifest = self._shib_download_curl_script(products, download_dir)
            else:
                manifest = self._download_curl_script(products, download_dir)

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload"
            manifest = self._download_files(products, base_dir, cache)

        return manifest


@async_to_sync
class CatalogsClass(MastClass):
    """
    MAST catalog query class.

    Class for querying MAST catalog data.
    """

    def __init__(self):

        super(CatalogsClass, self).__init__()

        self.catalogLimit = None

    def _parse_result(self, response, verbose=False):

        resultsTable = super(CatalogsClass, self)._parse_result(response, verbose)

        if len(resultsTable) == self.catalogLimit:
            warnings.warn("Maximum catalog results returned, may not include all sources within radius.",
                          MaxResultsWarning)

        return resultsTable

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.2*u.deg, catalog="Hsc",
                           version=None, pagesize=None, page=None, **kwargs):
        """
        Given a sky position and radius, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.htmll>`__.

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
        catalog : str, optional
            Default HSC.
            The catalog to be queried.
        version : int, optional
            Version number for catalogs that have versions. Default is highest version.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.
        **kwargs
            Other catalog-specific keyword args.
            These can be found in the (service documentation)[https://mast.stsci.edu/api/v0/_services.html]
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response: list of ``requests.Response``
        """

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        # Figuring out the service
        if catalog.lower() == "hsc":
            if version == 2:
                service = "Mast.Hsc.Db.v2"
            else:
                if version not in (3, None):
                    warnings.warn("Invalid HSC version number, defaulting to v3.", InputWarning)
                service = "Mast.Hsc.Db.v3"
            self.catalogLimit = kwargs.get('nr', 50000)

        elif catalog.lower() == "galex":
            service = "Mast.Galex.Catalog"
            self.catalogLimit = kwargs.get('maxrecords', 50000)

        elif catalog.lower() == "gaia":
            if version == 1:
                service = "Mast.Catalogs.GaiaDR1.Cone"
            else:
                if version not in (2, None):
                    warnings.warn("Invalid Gaia version number, defaulting to DR2.", InputWarning)
                service = "Mast.Catalogs.GaiaDR2.Cone"

        else:
            service = "Mast.Catalogs." + catalog + ".Cone"
            self.catalogLimit = None

        # basic params
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        # Hsc specific parameters (can be overridden by user)
        params['nr'] = 50000
        params['ni'] = 1
        params['magtype'] = 1

        # galex specific parameters (can be overridden by user)
        params['maxrecords'] = 50000

        # adding additional parameters
        for prop, value in kwargs.items():
            params[prop] = value

        return self.service_request_async(service, params, pagesize, page)

    @class_or_instance
    def query_object_async(self, objectname, radius=0.2*u.deg, catalog="Hsc",
                           pagesize=None, page=None, **kwargs):
        """
        Given an object name, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        catalog : str, optional
            Default HSC.
            The catalog to be queried.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Defaulte None.
            Can be used to override the default behavior of all results being returned
            to obtain a specific page of results.
        **kwargs
            Catalog-specific keyword args.
            These can be found in the `service documentation <https://mast.stsci.edu/api/v0/_services.html>`__.
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response: list of ``requests.Response``
        """

        coordinates = self._resolve_object(objectname)

        return self.query_region_async(coordinates, radius, catalog, pagesize, page, **kwargs)

    @class_or_instance
    def query_criteria_async(self, catalog, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.htmll>`__.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one specific page of results.
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

        # Build the mashup filter object
        if catalog.lower() == "tic":
            service = "Mast.Catalogs.Filtered.Tic"
            if coordinates or objectname:
                service += ".Position"
            mashupFilters = self._build_filter_set("Mast.Catalogs.Tess.Cone", service, **criteria)

        elif catalog.lower() == "diskdetective":
            service = "Mast.Catalogs.Filtered.DiskDetective"
            if coordinates or objectname:
                service += ".Position"
            mashupFilters = self._build_filter_set("Mast.Catalogs.Dd.Cone", service, **criteria)

        else:
            raise InvalidQueryError("Criteria query not availible for {}".format(catalog))

        if not mashupFilters:
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

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

        # build query
        if coordinates:
            params = {"filters": mashupFilters,
                      "ra": coordinates.ra.deg,
                      "dec": coordinates.dec.deg,
                      "radius": radius.deg}
        else:
            params = {"filters": mashupFilters}

        # TIC needs columns specified
        if catalog == "Tic":
            params["columns"] = "*"

        return self.service_request_async(service, params, pagesize=pagesize, page=page)

    @class_or_instance
    def query_hsc_matchid_async(self, match, version=3, pagesize=None, page=None):
        """
        Returns all the matches for a given Hubble Source Catalog MatchID.

        Parameters
        ----------
        match : int or `~astropy.table.Row`
            The matchID or HSC entry to return matches for.
        version : int, optional
            The HSC version to match against. Default is v3.
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.

        Response
        --------
        response : list(`requests.Response`)
        """

        if isinstance(match, Row):
            match = match["MatchID"]
        match = str(match)  # np.int64 gives json serializer problems, so strigify right here

        if version == 2:
            service = "Mast.HscMatches.Db.v2"
        else:
            if version not in (3, None):
                warnings.warn("Invalid HSC version number, defaulting to v3.", InputWarning)
            service = "Mast.HscMatches.Db.v3"

        params = {"input": match}

        return self.service_request_async(service, params, pagesize, page)

    @class_or_instance
    def get_hsc_spectra_async(self, pagesize=None, page=None):
        """
        Returns all Hubble Source Catalog spectra.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.

        Response
        --------
        response : list(`requests.Response`)
        """

        service = "Mast.HscSpectra.Db.All"
        params = {}

        return self.service_request_async(service, params, pagesize, page)

    def download_hsc_spectra(self, spectra, download_dir=None, cache=True, curl_flag=False):
        """
        Download one or more Hubble Source Catalog spectra.

        Parameters
        ----------
        specrtra : `~astropy.table.Table` or `astropy.table.Row`
            One or more HSC spectra to be downloaded.
        download_dir : str, optional
           Specify the base directory to download spectra into.
           Spectra will be saved in the subdirectory download_dir/mastDownload/HSC.
           If download_dir is not specified the base directory will be '.'.
        cache : bool, optional
            Default is True. If file is found on disc it will not be downloaded again.
            Note: has no affect when downloading curl script.
        curl_flag : bool, optional
            Default is False.  If true instead of downloading files directly, a curl script
            will be downloaded that can be used to download the data files at a later time.

        Response
        --------
        response : list(`requests.Response`)
        """

        # if spectra is not a Table, put it in a list
        if isinstance(spectra, Row):
            spectra = [spectra]

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script

            downloadFile = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")

            urlList = []
            pathList = []
            for spec in spectra:
                if spec['SpectrumType'] < 2:
                    urlList.append('https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset={0}'
                                   .format(spec['DatasetName']))

                else:
                    urlList.append('https://hla.stsci.edu/cgi-bin/ecfproxy?file_id={0}'
                                   .format(spec['DatasetName']) + '.fits')

                pathList.append(downloadFile + "/HSC/" + spec['DatasetName'] + '.fits')

            descriptionList = [""]*len(spectra)
            productTypeList = ['spectrum']*len(spectra)

            service = "Mast.Bundle.Request"
            params = {"urlList": ",".join(urlList),
                      "filename": downloadFile,
                      "pathList": ",".join(pathList),
                      "descriptionList": list(descriptionList),
                      "productTypeList": list(productTypeList),
                      "extension": 'curl'}

            response = self.service_request_async(service, params)
            bundlerResponse = response[0].json()

            localPath = download_dir.rstrip('/') + "/" + downloadFile + ".sh"
            self._download_file(bundlerResponse['url'], localPath, head_safe=True)

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

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload/HSC"

            if not os.path.exists(base_dir):
                os.makedirs(base_dir)

            manifestArray = []
            for spec in spectra:

                # localPath = base_dir + "/HSC"# + spec['DatasetName'] + ".fits"

                if spec['SpectrumType'] < 2:
                    dataUrl = 'https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset=' \
                              + spec['DatasetName']
                else:
                    dataUrl = 'https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=' \
                              + spec['DatasetName'] + '.fits'

                localPath = base_dir + '/' + spec['DatasetName'] + ".fits"

                status = "COMPLETE"
                msg = None
                url = None

                try:
                    self._download_file(dataUrl, localPath, cache=cache, head_safe=True)

                    # check file size also this is where would perform md5
                    if not os.path.isfile(localPath):
                        status = "ERROR"
                        msg = "File was not downloaded"
                        url = dataUrl

                except HTTPError as err:
                    status = "ERROR"
                    msg = "HTTPError: {0}".format(err)
                    url = dataUrl

                manifestArray.append([localPath, status, msg, url])

                manifest = Table(rows=manifestArray, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest


Observations = ObservationsClass()
Catalogs = CatalogsClass()
Mast = MastClass()
