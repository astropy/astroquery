# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Discovery Portal API
====================

This module contains various methods for querying the MAST Discovery Portal API.
"""

import warnings
import uuid
import json
import time

import numpy as np

from urllib.parse import quote as urlencode

from astropy.table import Table, vstack, MaskedColumn
from astropy.utils import deprecated

from ..query import BaseQuery, QueryWithLogin
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import InputWarning, NoResultsWarning

from . import conf, utils


__all__ = []


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

    # Append cache breaker
    if not 'cacheBreaker' in json_obj:
        json_obj['cacheBreaker'] = str(uuid.uuid4())
    request_string = json.dumps(json_obj)
    return 'request={}'.format(urlencode(request_string))


def _json_to_table(json_obj, col_config=None):
    """
    Takes a JSON object as returned from a Mashup request and turns it into an `~astropy.table.Table`.

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

        # regularlizing the type
        reg_type = utils.parse_type(atype)
        atype = reg_type[1]
        ignore_value = reg_type[2] if (ignore_value is None) else ignore_value

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
class PortalAPI(BaseQuery):
    """
    MAST Discovery Portal API calss.

    Class that allows direct programatic access to the MAST Portal.
    Should be used to facilitate all Portal API queries.
    """

    def __init__(self, session=None):

        super(PortalAPI, self).__init__()
        if session:
            self._session = session

        self.MAST_REQUEST_URL = conf.server + "/api/v0/invoke"
        self.COLUMNS_CONFIG_URL = conf.server + "/portal/Mashup/Mashup.asmx/columnsconfig"
        self.MAST_DOWNLOAD_URL = conf.server + "/api/v0.1/Download/file"
        self.MAST_BUNDLE_URL = conf.server + "/api/v0.1/Download/bundle"

        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

        self._column_configs = dict()
        self._current_service = None

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
                response = super(PortalAPI, self)._request(method, url, params=params, data=data,
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

        response = self._request("POST", self.COLUMNS_CONFIG_URL,
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
            response = self._request("POST", self.MAST_REQUEST_URL, data=req_string, headers=headers)
            json_response = response[0].json()

            self._column_configs[service].update(json_response['data']['Tables'][0]
                                                 ['ExtendedProperties']['discreteHistogram'])
            self._column_configs[service].update(json_response['data']['Tables'][0]
                                                 ['ExtendedProperties']['continuousHistogram'])
            for col, val in self._column_configs[service].items():
                val.pop('hist', None)  # don't want to save all this unecessary data

    def _parse_result(self, responses, verbose=False):
        """
        Parse the results of a list of `~requests.Response` objects and returns an `~astropy.table.Table` of results.

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

        result_list = []

        # loading the columns config
        col_config = None
        if self._current_service:
            col_config = self._column_configs.get(self._current_service)
            self._current_service = None  # clearing current service

        for resp in responses:
            result = resp.json()

            # check for error message
            if result['status'] == "ERROR":
                raise RemoteServiceError(result.get('msg', "There was an error with your request."))

            result_table = _json_to_table(result, col_config)
            result_list.append(result_table)

        all_results = vstack(result_list)

        # Check for no results
        if not all_results:
            warnings.warn("Query returned no results.", NoResultsWarning)
        return all_results

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
        response = self._request("POST", self.MAST_REQUEST_URL, data=req_string, headers=headers,
                                 retrieve_all=retrieve_all)

        return response

    def build_filter_set(self, column_config_name, service_name=None, **filters):
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

    def _get_columnsconfig_metadata(self, colconf_name):
        """
        Given a columns config id make a table of the associated metadata properties.

        Parameters
        ----------
        colconf_name : str
            The columns config idea to find metadata for (ex. Mast.Caom.Cone).

        Returns
        -------
        response : `~astropy.table.Table`
            The metadata table.
        """

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        response = self._request("POST", self.COLUMNS_CONFIG_URL,
                                 data=("colConfigId={}".format(colconf_name)), headers=headers)

        column_dict = response[0].json()

        meta_fields = ["Column Name", "Column Label", "Data Type", "Units", "Description", "Examples/Valid Values"]
        names = []
        labels = []
        data_types = []
        field_units = []
        descriptions = []
        examples = []

        for colname in column_dict:
            # skipping the _selected column (gets rmoved in return table)
            if colname == "_selected_":
                continue

            field = column_dict[colname]

            # skipping any columns that are removed
            if field.get("remove", False):
                continue

            names.append(colname)
            labels.append(field.get("text", colname))

            # datatype is a little more complicated
            d_type = utils.parse_type(field.get("type", ""))[0]
            if not d_type:
                d_type = utils.parse_type(field.get("vot.datatype", ""))[0]
            data_types.append(d_type)

            # units
            units = field.get("unit", "")
            if not units:
                units = field.get("vot.unit", "")
            field_units.append(units)

            descriptions.append(field.get("vot.description", ""))
            examples.append(field.get("example", ""))

        meta_table = Table(names=meta_fields, data=[names, labels, data_types, field_units, descriptions, examples])

        # Removing any empty columns
        for colname in meta_table.colnames:
            if (meta_table[colname] == "").all():
                meta_table.remove_column(colname)

        return meta_table
