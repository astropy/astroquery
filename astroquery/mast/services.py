# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Microservices API
======================

This module contains various methods for querying MAST microservice APIs.
"""

import time
import warnings

import numpy as np

from astropy.table import Table, MaskedColumn
from astropy.utils.decorators import deprecated_renamed_argument

from .. import log
from ..query import BaseQuery
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TimeoutError, NoResultsWarning

from . import conf


__all__ = ["ServiceAPI"]


def _json_to_table(json_obj, data_key='data'):
    """
    Takes a JSON object as returned from a MAST microservice request and turns it into an `~astropy.table.Table`.

    Parameters
    ----------
    json_obj : data array or list of dictionaries
        A MAST microservice response JSON object (python dictionary)
    data_key : str
        string that contains the key name in json_obj that stores the data rows

    Returns
    -------
    response : `~astropy.table.Table`
    """
    data_table = Table(masked=True)

    if not all(x in json_obj.keys() for x in ['info', data_key]):
        raise KeyError(f"Missing required key(s) {data_key} and/or 'info.'")

    # determine database type key in case missing
    type_key = 'type' if json_obj['info'][0].get('type') else 'db_type'

    # for each item in info, store the type and column name
    # for each item in info, type has to be converted from DB data types (SQL server in most cases)
    # from missions_mast search service such as varchar, integer, float, boolean etc
    # to corresponding numpy type
    for idx, col in enumerate(json_obj['info']):

        # get column name and type
        col_name = col.get('column_name') or col.get('name')
        col_type = col[type_key].lower()
        ignore_value = None

        # making type adjustments
        if (col_type == "char" or col_type == "string" or 'varchar' in col_type or col_type == "null"
                or col_type == 'datetime'):
            col_type = "str"
            ignore_value = ""
        elif col_type == "boolean" or col_type == "binary":
            col_type = "bool"
        elif col_type == "unsignedbyte":
            col_type = np.ubyte
        elif (col_type == "int" or col_type == "short" or col_type == "long" or col_type == "number"
                or col_type == 'integer'):
            # int arrays do not admit Non/nan vals
            col_type = np.int64
            ignore_value = -999
        elif col_type == "double" or col_type.lower() == "float" or col_type == "decimal":
            # int arrays do not admit Non/nan vals
            col_type = np.float64
            ignore_value = -999

        # Make the column list (don't assign final type yet or there will be errors)
        try:
            # Step through data array of values
            col_data = np.array([x[idx] for x in json_obj[data_key]], dtype=object)
        except KeyError:
            # it's not a data array, fall back to using column name as it is array of dictionaries
            try:
                col_data = np.array([x[col_name] for x in json_obj[data_key]], dtype=object)
            except KeyError:
                # Skip column names not found in data
                log.debug('Column %s was not found in data. Skipping...', col_name)
                continue
        if ignore_value is not None:
            col_data[np.where(np.equal(col_data, None))] = ignore_value

        # no consistent way to make the mask because np.equal fails on ''
        # and array == value fails with None
        if col_type == 'str':
            col_mask = (col_data == ignore_value)
        else:
            col_mask = np.equal(col_data, ignore_value)

        # add the column
        data_table.add_column(MaskedColumn(col_data.astype(col_type), name=col_name, mask=col_mask))

    return data_table


@async_to_sync
class ServiceAPI(BaseQuery):
    """
    MAST microservice API calls.

    Class that allows direct programmatic access to MAST microservice APIs.
    Should be used to facilitate all microservice API queries.
    """

    SERVICE_URL = conf.server
    REQUEST_URL = conf.server + "/api/v0.1/"
    MISSIONS_DOWNLOAD_URL = conf.server + "/search/"
    MAST_DOWNLOAD_URL = conf.server + "/api/v0.1/Download/file"
    SERVICES = {}

    def __init__(self, session=None):

        super().__init__()
        if session:
            self._session = session

        self.TIMEOUT = conf.timeout

    def set_service_params(self, service_dict, service_name="", server_prefix=False):
        """
        Initialize the request url and available queries for a given service.

        Parameters
        ----------
        service_dict : dict
            Dictionary of available service queries in the form
            {service_name:{"path":service_path, "args":service_args}}
        service_name : str
            Name of the specific service, i.e. catalogs or tesscut
        server_prefix : bool
            Optional, default False. If true url is formed as service_name.mast.stsci.edu
            vs. the default of mast.stsci.edu/service_name
        """

        service_url = self.SERVICE_URL
        if server_prefix:
            service_url = service_url.replace("mast", f"{service_name}.mast")
        else:
            service_url += f"/{service_name}"

        self.REQUEST_URL = f"{service_url}/api/v0.1/"
        self.SERVICES = service_dict

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, stream=False, auth=None, cache=False, use_json=False):
        """
        Override of the parent method:
        A generic HTTP request method, similar to `~requests.Session.request`

        This is a low-level method not generally intended for use by astroquery
        end-users.

        This method wraps the _request functionality to include raise_for_status
        Caching is defaulted to False but may be modified as needed
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
        cache : bool
            Default False. Use of built in caching
        use_json: bool
            Default False. if True then data is already in json format.

        Returns
        -------
        response : `~requests.Response`
            The response from the server.
        """

        start_time = time.time()

        if use_json:
            response = super()._request(method, url, params=params, json=data, headers=headers,
                                        files=files, cache=cache, stream=stream, auth=auth)
        else:
            response = super()._request(method, url, params=params, data=data, headers=headers,
                                        files=files, cache=cache, stream=stream, auth=auth)

        if (time.time() - start_time) >= self.TIMEOUT:
            raise TimeoutError("Timeout limit of {} exceeded.".format(self.TIMEOUT))

        response.raise_for_status()
        return response

    def _parse_result(self, response, verbose=False, data_key='data'):
        """
        Parses the results of a  `~requests.Response` object and returns an `~astropy.table.Table` of results.

        Parameters
        ----------
        responses : `~requests.Response`
            The restponse from a self._request call.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.
        data_key : str
            the key in response that contains the data rows

        Returns
        -------
        response : `~astropy.table.Table`
        """

        result = response.json()
        result_table = _json_to_table(result, data_key=data_key)

        # Check for no results
        if not result_table:
            warnings.warn("Query returned no results.", NoResultsWarning)
        return result_table

    @class_or_instance
    @deprecated_renamed_argument('page_size', 'pagesize', since='0.4.8')
    def service_request_async(self, service, params, pagesize=None, page=None, use_json=False, **kwargs):
        """
        Given a MAST fabric service and parameters, builds and executes a fabric microservice catalog query.
        See documentation `here <https://catalogs.mast.stsci.edu/docs/index.html>`__
        for information about how to build a MAST catalogs microservice  request.

        Parameters
        ----------
        service : str
           The MAST catalogs service to query. Should be present in self.SERVICES
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
        use_json: bool, optional
           if True, params are directly passed as json object
        **kwargs :
           See Catalogs.MAST properties in documentation referenced above

        Returns
        -------
        response : list of `~requests.Response`
        """
        service_config = self.SERVICES.get(service.lower())
        service_url = service_config.get('path')
        compiled_service_args = {}

        # Gather URL specific parameters
        for service_argument, default_value in service_config.get('args', {}).items():
            found_argument = params.pop(service_argument, None)
            if found_argument is None:
                found_argument = kwargs.pop(service_argument, default_value)
            compiled_service_args[service_argument] = found_argument.lower()

        request_url = self.REQUEST_URL + service_url.format(**compiled_service_args)

        # Default headers
        headers = {
            'User-Agent': self._session.headers['User-Agent'],
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }

        # Params as a list of tuples to allow for multiple parameters added
        catalogs_request = []
        page = page or params.pop('page', None)
        pagesize = pagesize or params.pop('pagesize', None)

        # Add pagination if specified
        if page is not None:
            catalogs_request.append(('page', page))
        if pagesize is not None:
            catalogs_request.append(('pagesize', pagesize))

        # Populate parameters based on `use_json`
        if not use_json:
            # When not using JSON, merge kwargs into params and build query
            params.update(kwargs)
            catalogs_request.extend(self._build_catalogs_params(params))
        else:
            headers['Content-Type'] = 'application/json'

            # Parameter syntax needs to be updated only for PANSTARRS catalog queries
            if service.lower() == 'panstarrs':
                catalogs_request.extend(self._build_catalogs_params(params))

                # After parameter syntax is updated, revert back to dictionary
                # so params can be passed as a JSON dictionary
                params_dict = {}
                for key, val in catalogs_request:
                    params_dict.setdefault(key, []).append(val)
                catalogs_request = params_dict

                # Removing single-element lists. Single values will live on their own (except for `sort_by`)
                catalogs_request = {
                    k: v if k == 'sort_by' or len(v) > 1 else v[0]
                    for k, v in params_dict.items()
                }

            # Otherwise, catalogs_request can remain as the original params dict
            else:
                catalogs_request = params

        response = self._request('POST', request_url, data=catalogs_request, headers=headers, use_json=use_json)
        return response

    @class_or_instance
    def missions_request_async(self, service, params):
        """
        Builds and executes an asynchronous query to the MAST Search API.
        Parameters
        ----------
        service : str
           The MAST Search API service to query. Should be present in self.SERVICES.
        params : dict
           JSON object containing service parameters.
        Returns
        -------
        response : list of `~requests.Response`
        """
        service_config = self.SERVICES.get(service.lower())
        request_url = self.REQUEST_URL + service_config.get('path')

        # Default headers
        headers = {
            'User-Agent': self._session.headers['User-Agent'],
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # make request
        data, params = (params, None)
        response = self._request(method='POST',
                                 url=request_url,
                                 params=params,
                                 data=data,
                                 headers=headers,
                                 use_json=True)
        return response

    def _build_catalogs_params(self, params):
        """
        Gathers parameters for Catalogs.MAST usage and translates to valid API syntax tuples

        Parameters
        ----------
        params: dict
            A dict of parameters to convert into valid API syntax. Will omit the "format" parameter

        Returns
        -------
        response : list(tuple)
            List of tuples representing API syntax parameters
        """
        catalog_params = []
        for prop, value in params.items():
            if prop == 'format':
                # Ignore format changes
                continue
            elif prop == 'pagesize':
                catalog_params.extend(('pagesize', value))
            elif prop == 'sort_by':
                # Loop through each value if list
                if isinstance(value, list):
                    for sort_item in value:
                        # Determine if tuple with sort direction
                        if isinstance(sort_item, tuple):
                            catalog_params.append(('sort_by', sort_item[1] + '.' + sort_item[0]))
                        else:
                            catalog_params.append(('sort_by', sort_item))
                else:
                    # A single sort
                    # Determine if tuple with sort direction
                    if isinstance(value, tuple):
                        catalog_params.append(('sort_by', value[0] + '.' + value[1]))
                    else:
                        catalog_params.append(('sort_by', value))
            elif prop == 'columns':
                catalog_params.extend(tuple(('columns', col) for col in value))
            else:
                if isinstance(value, list):
                    # A composed list of multiple filters for a single column
                    # Extract each filter value in list
                    for filter_value in value:
                        # Determine if tuple with filter decorator
                        if isinstance(filter_value, tuple):
                            catalog_params.append((prop + '.' + filter_value[0], filter_value[1]))
                        else:
                            # Otherwise just append the value without a decorator
                            catalog_params.append((prop, filter_value))
                else:
                    catalog_params.append((prop, value))

        return catalog_params

    def check_catalogs_criteria_params(self, criteria):
        """
        Tests a dict of passed criteria for Catalogs.MAST to ensure that at least one parameter is for a given criteria

        Parameters
        ----------
        criteria: dict
            A dict of parameters to test for at least one criteria parameter

        Returns
        -------
        response : boolean
            Whether the passed dict has at least one criteria parameter
        """

        non_criteria_params = ["columns", "sort_by", "page_size", "pagesize", "page"]
        return any(key not in non_criteria_params for key in criteria)
