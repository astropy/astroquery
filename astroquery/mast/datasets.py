# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Datasets
=================

This module contains methods for searching MAST datasets.
"""

import json
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance

from .core import MastQueryWithLogin

__all__ = ['DatasetsClass', 'Datasets']


@async_to_sync
class DatasetsClass(MastQueryWithLogin):
    """
    MAST search datasets class.

    Class that allows direct programatic access to the MAST search API for a given mission.
    """

    def _parse_result(self, response, verbose=False):  # Used by the async_to_sync decorator functionality
        """
        Parse the results of a `~requests.Response` objects and return an `~astropy.table.Table` of results.

        Parameters
        ----------
        response : `~requests.Response`
            `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        return self._mission_api_connection._parse_result(response, verbose)

    @class_or_instance
    def service_request_async(self, params):
        """
        Given search  parameters, builds and excecutes a search query.

        Parameters
        ----------
        params : dict
            JSON object containing search parameters.

        Returns
        -------
        response : `~requests.Response`
        """

        params = json.dumps(params)
        return self._mission_api_connection.service_request_async(params)

Datasets = DatasetsClass()
