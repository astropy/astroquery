# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Portal
===========

This module contains various methods for querying the MAST Portal.
"""

from __future__ import print_function, division

import warnings
import json
import time
import os
import keyring
import threading

import numpy as np

from requests import HTTPError
from getpass import getpass

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack, MaskedColumn
from astropy.logger import log

from astropy.utils import deprecated
from astropy.utils.console import ProgressBarOrSpinner
from astropy.utils.exceptions import AstropyDeprecationWarning

from six.moves.urllib.parse import quote as urlencode

from ..query import QueryWithLogin
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import (TimeoutError, InvalidQueryError, RemoteServiceError,
                          ResolverError, MaxResultsWarning,
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

    request_string = json.dumps(json_obj)
    return 'request={}'.format(urlencode(request_string))


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

    data_table = Table(masked=True)

    if not all(x in json_obj.keys() for x in ['fields', 'data']):
        raise KeyError("Missing required key(s) 'data' and/or 'fields.'")

    for col, atype in [(x['name'], x['type']) for x in json_obj['fields']]:

        # Removing "_selected_" column
        if col == "_selected_":
            continue

        # reading the colum config if given
        ignore_value = None
        if col_config:
            col_props = col_config.get(col, {})
            ignore_value = col_props.get("ignoreValue", None)

        # making type adjustments
        if atype == "string":
            atype = "str"
            ignore_value = "" if (ignore_value is None) else ignore_value
        if atype == "boolean":
            atype = "bool"
        if atype == "int":  # int arrays do not admit Non/nan vals
            atype = np.int64
            ignore_value = -999 if (ignore_value is None) else ignore_value
        if atype == "date":
            atype = "str"
            ignore_value = "" if (ignore_value is None) else ignore_value

        # Make the column list (don't assign final type yet or there will be errors)
        col_data = np.array([x.get(col, ignore_value) for x in json_obj['data']], dtype=object)
        if ignore_value is not None:
            col_data[np.where(np.equal(col_data, None))] = ignore_value

        # no consistant way to make the mask because np.equal fails on ''
        # and array == value fails with None
        if atype == 'str':
            col_mask = (col_data == ignore_value)
        else:
            col_mask = np.equal(col_data, ignore_value)

        # add the column
        data_table.add_column(MaskedColumn(col_data.astype(atype), name=col, mask=col_mask))

    return data_table


@async_to_sync
class MastClass(QueryWithLogin):
    """
    MAST query class.

    Class that allows direct programatic access to the MAST Portal,
    more flexible but less user friendly than `ObservationsClass`.
    """

    def __init__(self, mast_token=None):

        super(MastClass, self).__init__()

        self._MAST_REQUEST_URL = conf.server + "/api/v0/invoke"
        self._COLUMNS_CONFIG_URL = conf.server + "/portal/Mashup/Mashup.asmx/columnsconfig"

        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

        self._column_configs = dict()
        self._current_service = None

        self._SESSION_INFO_URL = conf.server + "/whoami"
        self._MAST_DOWNLOAD_URL = conf.server + "/api/v0.1/Download/file"
        self._MAST_BUNDLE_URL = conf.server + "/api/v0.1/Download/bundle"

        if mast_token:
            self.login(token=mast_token)

    def _login(self, token=None, store_token=False, reenter_token=False):  # pragma: no cover
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
            If true, MAST token will be stored securely in your keyring.
        reenter_token :  bool, optional
            Default False.
            Asks for the token even if it is already stored in the keyring or $MAST_API_TOKEN environment variable.
            This is the way to overwrite an already stored password on the keyring.
        """

        auth_link = (conf.server.replace("mast", "auth.mast") +
                     "/token?suggested_name=Astroquery&suggested_scope=mast:exclusive_access")

        if token is None and "MAST_API_TOKEN" in os.environ:
            token = os.environ["MAST_API_TOKEN"]

        if token is None:
            token = keyring.get_password("astroquery:mast.stsci.edu.token", "masttoken")

        if token is None or reenter_token:
            info_msg = "If you do not have an API token already, visit the following link to create one: "
            log.info(info_msg + auth_link)
            token = getpass("Enter MAST API Token: ")

        # store token if desired
        if store_token:
            keyring.set_password("astroquery:mast.stsci.edu.token", "masttoken", token)

        self._session.headers["Accept"] = "application/json"
        self._session.cookies["mast_token"] = token
        info = self.session_info(verbose=False)

        if not info["anon"]:
            log.info("MAST API token accepted, welcome %s" % info["attrib"].get("display_name"))
        else:
            warn_msg = ("MAST API token invalid!\n"
                        "To make create a new API token visit to following link: " +
                        auth_link)
            warnings.warn(warn_msg, AuthenticationWarning)

        return not info["anon"]

    @deprecated(since="v0.3.9", message=("The get_token function is deprecated, "
                                         "session token is now the token used for login."))
    def get_token(self):
        return None

    def session_info(self, silent=None, verbose=None):
        """
        Displays information about current MAST user, and returns user info dictionary.

        Parameters
        ----------
        silent :
            Deprecated. Use verbose instead.
        verbose : bool, optional
            Default True. Set to False to suppress output to stdout.

        Returns
        -------
        response : dict
        """

        # Dealing with deprecated argument
        if (silent is not None) and (verbose is not None):
            warnings.warn(("Argument 'silent' has been deprecated, "
                           "will be ignored in favor of 'verbose'"), AstropyDeprecationWarning)
        elif silent is not None:
            warnings.warn(("Argument 'silent' has been deprecated, "
                           "and will be removed in the future. "
                           " Use 'verbose' instead."), AstropyDeprecationWarning)
            verbose = not silent
        elif (silent is None) and (verbose is None):
            verbose = True

        # get user information
        self._session.headers["Accept"] = "application/json"
        response = self._session.request("GET", self._SESSION_INFO_URL)

        info_dict = response.json()

        if verbose:
            for key, value in info_dict.items():
                if isinstance(value, dict):
                    for subkey, subval in value.items():
                        print("%s.%s: %s" % (key, subkey, subval))
                else:
                    print("%s: %s" % (key, value))

        return info_dict

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, stream=False, auth=None, retrieve_all=True):
        """
        Override of the parent method:
        A generic HTTP request method, similar to `~requests.Session.request`

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
            See `~requests.request`
        retrieve_all : bool
            Default True. Retrieve all pages of data or just the one indicated in the params value.

        Returns
        -------
        response : `~requests.Response`
            The response from the server.
        """

        start_time = time.time()
        all_responses = []
        total_pages = 1
        cur_page = 0

        while cur_page < total_pages:
            status = "EXECUTING"

            while status == "EXECUTING":
                response = super(MastClass, self)._request(method, url, params=params, data=data,
                                                           headers=headers, files=files, cache=False,
                                                           stream=stream, auth=auth)

                if (time.time() - start_time) >= self.TIMEOUT:
                    raise TimeoutError("Timeout limit of {} exceeded.".format(self.TIMEOUT))

                # Raising error based on HTTP status if necessary
                response.raise_for_status()

                result = response.json()

                if not result:  # kind of hacky, but col_config service returns nothing if there is an error
                    status = "ERROR"
                else:
                    status = result.get("status")

            all_responses.append(response)

            if (status != "COMPLETE") or (not retrieve_all):
                break

            paging = result.get("paging")
            if paging is None:
                break
            total_pages = paging['pagesFiltered']
            cur_page = paging['page']

            data = data.replace("page%22%3A%20"+str(cur_page)+"%2C", "page%22%3A%20"+str(cur_page+1)+"%2C")

        return all_responses

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
            mashup_request = {'service': all_name, 'params': {}, 'format': 'extjs'}
            req_string = _prepare_service_request_string(mashup_request)
            response = self._request("POST", self._MAST_REQUEST_URL, data=req_string, headers=headers)
            json_response = response[0].json()

            self._column_configs[service].update(json_response['data']['Tables'][0]
                                                 ['ExtendedProperties']['discreteHistogram'])
            self._column_configs[service].update(json_response['data']['Tables'][0]
                                                 ['ExtendedProperties']['continuousHistogram'])
            for col, val in self._column_configs[service].items():
                val.pop('hist', None)  # don't want to save all this unecessary data

    def _parse_result(self, responses, verbose=False):
        """
        Parse the results of a list of `~requests.Response` objects and returns an `astropy.table.Table` of results.

        Parameters
        ----------
        responses : list of `~requests.Response`
            List of `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        # loading the columns config
        col_config = None
        if self._current_service:
            col_config = self._column_configs.get(self._current_service)
            self._current_service = None  # clearing current service

        result_list = []

        for resp in responses:
            result = resp.json()

            # check for error message
            if result['status'] == "ERROR":
                raise RemoteServiceError(result.get('msg', "There was an error with your request."))

            result_table = _mashup_json_to_table(result, col_config)
            result_list.append(result_table)

        all_results = vstack(result_list)

        # Check for no results
        if not all_results:
            warnings.warn("Query returned no results.", NoResultsWarning)
        return all_results

    def logout(self):  # pragma: no cover
        """
        Log out of current MAST session.
        """
        self._session.cookies.clear_session_cookies()
        self._authenticated = False

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
        response : list of `~requests.Response`
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
            retrieve_all = True
        else:
            retrieve_all = False

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        mashup_request = {'service': service,
                         'params': params,
                         'format': 'json',
                         'pagesize': pagesize,
                         'page': page}

        for prop, value in kwargs.items():
            mashup_request[prop] = value

        req_string = _prepare_service_request_string(mashup_request)
        response = self._request("POST", self._MAST_REQUEST_URL, data=req_string, headers=headers,
                                 retrieve_all=retrieve_all)

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

        caom_col_config = self._column_configs[service_name]

        mashup_filters = []
        for colname, value in filters.items():

            # make sure value is a list-like thing
            if np.isscalar(value,):
                value = [value]

            # Get the column type and separator
            col_info = caom_col_config.get(colname)
            if not col_info:
                warnings.warn("Filter {} does not exist. This filter will be skipped.".format(colname), InputWarning)
                continue

            colType = "discrete"
            if (col_info.get("vot.datatype", col_info.get("type")) in ("double", "float", "numeric")) \
               or col_info.get("treatNumeric"):
                colType = "continuous"

            separator = col_info.get("separator")
            free_text = None

            # validate user input
            if colType == "continuous":
                if len(value) < 2:
                    warning_string = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Not enough values provided, skipping..."
                    warnings.warn(warning_string, InputWarning)
                    continue
                elif len(value) > 2:
                    warning_string = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Too many values provided, the first two will be " + \
                                    "assumed to be the min and max values."
                    warnings.warn(warning_string, InputWarning)
            else:  # coltype is discrete, all values should be represented as strings, even if numerical
                value = [str(x) for x in value]

                # check for wildcards

                for i, val in enumerate(value):
                    if ('*' in val) or ('%' in val):
                        if free_text:  # free_text is already set cannot set again
                            warning_string = ("Only one wildcarded value may be used per filter, "
                                             "all others must be exact.\n"
                                             "Skipping {}...".format(val))
                            warnings.warn(warning_string, InputWarning)
                        else:
                            free_text = val.replace('*', '%')
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
            if free_text:
                entry["freeText"] = free_text

            mashup_filters.append(entry)

        return mashup_filters


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
        json_response = response[0].json()

        # getting the list of missions
        hist_data = json_response['data']['Tables'][0]['Columns']
        for facet in hist_data:
            if facet['text'] == "obs_collection":
                mission_info = facet['ExtendedProperties']['histObj']
                missions = list(mission_info.keys())
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
        response : list of `~requests.Response`
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
        response : list of `~requests.Response`
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
        response : list of `~requests.Response`
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        if ('obstype' in criteria) and ('intentType' in criteria):
            warn_string = ("Cannot specify both obstype and intentType, "
                           "obstype is the deprecated version of intentType and will be ignored.")
            warnings.warn(warn_string, InputWarning)
            criteria.pop('obstype', None)

        # Temporarily issuing warning about change in behavior
        # continuing old behavior
        # grabbing the observation type (science vs calibration)
        obstype = criteria.pop('obstype', None)
        if obstype:
            warn_string = ("Criteria obstype argument will disappear in May 2019. "
                          "Criteria 'obstype' is now 'intentType', options are 'science' or 'calibration', "
                          "if intentType is not supplied all observations (science and calibration) are returned.")
            warnings.warn(warn_string, AstropyDeprecationWarning)

            if obstype == "science":
                criteria["intentType"] = "science"
            elif obstype == "cal":
                criteria["intentType"] = "calibration"

        # Build the mashup filter object and store it in the correct service_name entry
        if coordinates or objectname:
            mashup_filters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered.Position", **criteria)
        else:
            mashup_filters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered", **criteria)

        if not mashup_filters:
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
                      "filters": mashup_filters,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "*",
                      "filters": mashup_filters}

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
            mashup_filters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered.Position", **criteria)
        else:
            mashup_filters = self._build_filter_set("Mast.Caom.Cone", "Mast.Caom.Filtered", **criteria)

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
                      "filters": mashup_filters,
                      "obstype": obstype,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashup_filters,
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
            response : list of `~requests.Response`
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

        filter_mask = np.full(len(products), True, dtype=bool)

        # Applying the special filters (mrp_only and extension)
        if mrp_only:
            filter_mask &= (products['productGroupDescription'] == "Minimum Recommended Products")

        if extension:
            mask = np.full(len(products), False, dtype=bool)
            for elt in extension:
                mask |= [False if isinstance(x, np.ma.core.MaskedConstant) else x.endswith(elt)
                         for x in products["productFilename"]]
            filter_mask &= mask

        # Applying the rest of the filters
        for colname, vals in filters.items():

            if type(vals) == str:
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
                mask |= (products[colname] == elt)

            filter_mask &= mask

        return products[np.where(filter_mask)]

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

        url_list = [("uri", url) for url in products['dataURI']]
        download_file = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        local_path = os.path.join(out_dir.rstrip('/'), download_file + ".sh")

        response = self._download_file(self._MAST_BUNDLE_URL + ".sh", local_path, data=url_list, method="POST")

        status = "COMPLETE"
        msg = None

        if not os.path.isfile(local_path):
            status = "ERROR"
            msg = "Curl could not be downloaded"

        manifest = Table({'Local Path': [local_path],
                          'Status': [status],
                          'Message': [msg]})
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
    def get_hst_s3_uris(self, data_products, include_bucket=True, full_url=False):
        return self.get_cloud_uris(data_products, include_bucket, full_url)

    def get_cloud_uris(self, data_products, include_bucket=True, full_url=False):
        """ Takes an `astropy.table.Table` of data products and turns them into s3 uris. """

        return [self.get_cloud_uri(data_product, include_bucket, full_url) for data_product in data_products]

    @deprecated(since="v0.3.9", alternative="get_cloud_uri")
    def get_hst_s3_uri(self, data_product, include_bucket=True, full_url=False):
        return self.get_cloud_uri(data_product, include_bucket, full_url)

    def get_cloud_uri(self, data_product, include_bucket=True, full_url=False):
        """ Turns a data_product into a S3 URI """

        if self._boto3 is None:
            raise AtrributeError("Must enable s3 dataset before attempting to query the s3 information")

        # This is a cheap operation and does not perform any actual work yet
        s3_client = self._boto3.client('s3')

        paths = fpl.paths(data_product)
        if paths is None:
            raise Exception("Unsupported mission")

        for path in paths:
            try:
                s3_client.head_object(Bucket=self._pubdata_bucket, Key=path, RequestPayer='requester')
                if include_bucket:
                    path = "s3://%s/%s" % (self._pubdata_bucket, path)
                elif full_url:
                    path = "http://s3.amazonaws.com/%s/%s" % (self._pubdata_bucket, path)
                return path
            except self._botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] != "404":
                    raise

        raise Exception("Unable to locate file!")

    def _download_from_cloud(self, data_product, local_path, cache=True):
        # The following is a mishmash of BaseQuery._download_file and s3 access through boto

        self._pubdata_bucket = 'stpubdata'

        # This is a cheap operation and does not perform any actual work yet
        s3 = self._boto3.resource('s3')
        s3_client = self._boto3.client('s3')
        bkt = s3.Bucket(self._pubdata_bucket)

        bucket_path = self.get_cloud_uri(data_product, False)
        info_lookup = s3_client.head_object(Bucket=self._pubdata_bucket, Key=bucket_path, RequestPayer='requester')

        # Unfortunately, we can't use the reported file size in the reported product.  STScI's backing
        # archive database (CAOM) is frequently out of date and in many cases omits the required information.
        # length = data_product["size"]
        # Instead we ask the webserver (in this case S3) what the expected content length is and use that.
        length = info_lookup["ContentLength"]

        if cache and os.path.exists(local_path):
            if length is not None:
                statinfo = os.stat(local_path)
                if statinfo.st_size != length:
                    log.warning("Found cached file {0} with size {1} that is "
                                "different from expected size {2}"
                                .format(local_path,
                                        statinfo.st_size,
                                        length))
                else:
                    log.info("Found cached file {0} with expected size {1}."
                             .format(local_path, statinfo.st_size))
                    return

        with ProgressBarOrSpinner(length, ('Downloading URL s3://{0}/{1} to {2} ...'.format(
                self._pubdata_bucket, bucket_path, local_path))) as pb:

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

            bkt.download_file(bucket_path, local_path, ExtraArgs={"RequestPayer": "requester"},
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

        manifest_array = []
        for data_product in products:

            local_path = os.path.join(base_dir, data_product['obs_collection'], data_product['obs_id'])
            data_url = self._MAST_DOWNLOAD_URL + "?uri=" + data_product["dataURI"]

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            local_path = os.path.join(local_path, data_product['productFilename'])

            status = "COMPLETE"
            msg = None
            url = None

            try:
                if self._boto3 is not None and fpl.has_path(data_product):
                    try:
                        self._download_from_cloud(data_product, local_path, cache)
                    except Exception as ex:
                        log.exception("Error pulling from S3 bucket: %s" % ex)
                        log.warn("Falling back to mast download...")
                        self._download_file(data_url, local_path, cache=cache, head_safe=True, continuation=False)
                else:
                    self._download_file(data_url, local_path, cache=cache, head_safe=True, continuation=False)

                # check if file exists also this is where would perform md5,
                # and also check the filesize if the database reliably reported file sizes
                if not os.path.isfile(local_path):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = data_url

            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = data_url

            manifest_array.append([local_path, status, msg, url])

        manifest = Table(rows=manifest_array, names=('Local Path', 'Status', 'Message', "URL"))

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
            product_lists = []
            for oid in products:
                product_lists.append(self.get_product_list(oid))

            products = vstack(product_lists)

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


@async_to_sync
class CatalogsClass(MastClass):
    """
    MAST catalog query class.

    Class for querying MAST catalog data.
    """

    def __init__(self):

        super(CatalogsClass, self).__init__()

        self.catalog_limit = None

    def _parse_result(self, response, verbose=False):

        results_table = super(CatalogsClass, self)._parse_result(response, verbose)

        if len(results_table) == self.catalog_limit:
            warnings.warn("Maximum catalog results returned, may not include all sources within radius.",
                          MaxResultsWarning)

        return results_table

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
        response : list of `~requests.Response`
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
            self.catalog_limit = kwargs.get('nr', 50000)

        elif catalog.lower() == "galex":
            service = "Mast.Galex.Catalog"
            self.catalog_limit = kwargs.get('maxrecords', 50000)

        elif catalog.lower() == "gaia":
            if version == 1:
                service = "Mast.Catalogs.GaiaDR1.Cone"
            else:
                if version not in (2, None):
                    warnings.warn("Invalid Gaia version number, defaulting to DR2.", InputWarning)
                service = "Mast.Catalogs.GaiaDR2.Cone"

        else:
            service = "Mast.Catalogs." + catalog + ".Cone"
            self.catalog_limit = None

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
        response : list of `~requests.Response`
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
        response : list of `~requests.Response`
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
            mashup_filters = self._build_filter_set("Mast.Catalogs.Tess.Cone", service, **criteria)

        elif catalog.lower() == "diskdetective":
            service = "Mast.Catalogs.Filtered.DiskDetective"
            if coordinates or objectname:
                service += ".Position"
            mashup_filters = self._build_filter_set("Mast.Catalogs.Dd.Cone", service, **criteria)

        else:
            raise InvalidQueryError("Criteria query not availible for {}".format(catalog))

        if not mashup_filters:
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
            params = {"filters": mashup_filters,
                      "ra": coordinates.ra.deg,
                      "dec": coordinates.dec.deg,
                      "radius": radius.deg}
        else:
            params = {"filters": mashup_filters}

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

        Returns
        --------
        response : list of `~requests.Response`
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

        Returns
        --------
        response : list of `~requests.Response`
        """

        service = "Mast.HscSpectra.Db.All"
        params = {}

        return self.service_request_async(service, params, pagesize, page)

    def download_hsc_spectra(self, spectra, download_dir=None, cache=True, curl_flag=False):
        """
        Download one or more Hubble Source Catalog spectra.

        Parameters
        ----------
        spectra : `~astropy.table.Table` or `astropy.table.Row`
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

        Returns
        --------
        response : list of `~requests.Response`
        """

        # if spectra is not a Table, put it in a list
        if isinstance(spectra, Row):
            spectra = [spectra]

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script

            download_file = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")

            url_list = []
            path_list = []
            for spec in spectra:
                if spec['SpectrumType'] < 2:
                    url_list.append('https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset={0}'
                                   .format(spec['DatasetName']))

                else:
                    url_list.append('https://hla.stsci.edu/cgi-bin/ecfproxy?file_id={0}'
                                   .format(spec['DatasetName']) + '.fits')

                path_list.append(download_file + "/HSC/" + spec['DatasetName'] + '.fits')

            description_list = [""]*len(spectra)
            producttype_list = ['spectrum']*len(spectra)

            service = "Mast.Bundle.Request"
            params = {"urlList": ",".join(url_list),
                      "filename": download_file,
                      "pathList": ",".join(path_list),
                      "descriptionList": list(description_list),
                      "productTypeList": list(producttype_list),
                      "extension": 'curl'}

            response = self.service_request_async(service, params)
            bundler_response = response[0].json()

            local_path = os.path.join(download_dir, "{}.sh".format(download_file))
            self._download_file(bundler_response['url'], local_path, head_safe=True, continuation=False)

            status = "COMPLETE"
            msg = None
            url = None

            if not os.path.isfile(local_path):
                status = "ERROR"
                msg = "Curl could not be downloaded"
                url = bundler_response['url']
            else:
                missing_files = [x for x in bundler_response['statusList'].keys()
                                if bundler_response['statusList'][x] != 'COMPLETE']
                if len(missing_files):
                    msg = "{} files could not be added to the curl script".format(len(missing_files))
                    url = ",".join(missing_files)

            manifest = Table({'Local Path': [local_path],
                              'Status': [status],
                              'Message': [msg],
                              "URL": [url]})

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload/HSC"

            if not os.path.exists(base_dir):
                os.makedirs(base_dir)

            manifest_array = []
            for spec in spectra:

                if spec['SpectrumType'] < 2:
                    data_url = 'https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset=' \
                              + spec['DatasetName']
                else:
                    data_url = 'https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=' \
                              + spec['DatasetName'] + '.fits'

                local_path = os.path.join(base_dir, "{}.fits".format(spec['DatasetName']))

                status = "COMPLETE"
                msg = None
                url = None

                try:
                    self._download_file(data_url, local_path, cache=cache, head_safe=True)

                    # check file size also this is where would perform md5
                    if not os.path.isfile(local_path):
                        status = "ERROR"
                        msg = "File was not downloaded"
                        url = data_url

                except HTTPError as err:
                    status = "ERROR"
                    msg = "HTTPError: {0}".format(err)
                    url = data_url

                manifest_array.append([local_path, status, msg, url])

                manifest = Table(rows=manifest_array, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest


Observations = ObservationsClass()
Catalogs = CatalogsClass()
Mast = MastClass()
