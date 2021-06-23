# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Missions API
======================

This module contains various methods for querying MAST missions search APIs.
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
from ..exceptions import InputWarning, NoResultsWarning, RemoteServiceError

from . import conf, utils


__all__ = []


def _json_to_table(json_obj, col_config=None):
    """
    Takes a JSON object as returned from a mission search request and turns it into an `~astropy.table.Table`.

    Parameters
    ----------
    json_obj : dict
        A Mission search response JSON object (python dictionary)
    col_config : dict, optional
        Dictionary that defines column properties, e.g. default value.

    Returns
    -------
    response : `~astropy.table.Table`
    """


    col_type = 'str'
    ignore_value = None
    column_names = ()
    column_types = ()
    rows = []

    for result in json_obj['results']:
        rows.append([])
        for key, val in result.items():
            if val === 'null':
                val = ''
            if isinstance(val, str):
                col_type = 'str'
                ignore_value = ''
            elif isinstance(val, bool):
                col_type = 'bool'
                ignore_value = ''
            elif isinstance(val, int):
                col_type = np.int64
                ignore_value = -999
            elif isinstance(val, float):
                col_type = np.float64
                ignore_value = -999
            rows[-1].append(val)
        
            column_names = column_names + (val,)
            column_types = column_types + (col_type,)

    data_table = Table(rows, masked=True, names=column_names, dtype=column_types)
    return data_table

@async_to_sync
class MissionSearchAPI(BaseQuery):
    """
    MAST Mission Search API class.

    Class that allows direct programatic access to the MAST Mission Search APIs.
    Should be used to facilitate all Mission search API queries.
    """

    def __init__(self, session=None):

        super(MissionSearchAPI, self).__init__()
        if session:
            self._session = session

        self.MAST_SEARCH_URL = conf.server + "/search/hst/api/v0.1/search"

        self.TIMEOUT = conf.timeout

        self._current_service = None

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, stream=False, auth=None, cache=False):
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
            Default False. Use of bulit in _request caching

        Returns
        -------
        response : `~requests.Response`
            The response from the server.
        """

        start_time = time.time()

        response = super(MissionSearchAPI, self)._request(method, url, params=params, data=data, headers=headers,
                                    files=files, cache=cache, stream=stream, auth=auth)

        if (time.time() - start_time) >= self.TIMEOUT:
            raise TimeoutError("Timeout limit of {} exceeded.".format(self.TIMEOUT))

        response.raise_for_status()
        return response

    def _parse_result(self, response, verbose=False):
        """
        Parse the results of a `~requests.Response` objects and returns an `~astropy.table.Table` of results.

        Parameters
        ----------
        responses : `~requests.Response`
            `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        result = resp.json()

        result_table = _json_to_table(result)

        return result_table

    @class_or_instance
    def service_request_async(self, params):
        """
        Given a parameters, builds and excecutes a Mission search query.

        Parameters
        ----------
        params : dict
            JSON object containing search parameters.

        Returns
        -------
        response : ~requests.Response`
        """

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/json;charset=UTF-8",
                   "Accept": "application/json"}

        response = self._request('POST', self.MAST_SEARCH_URL, data=params, headers=headers)

        return response
