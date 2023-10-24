# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Missions
=================

This module contains methods for searching MAST missions.
"""

import requests
import warnings

from astropy.table import Table
import astropy.units as u
import astropy.coordinates as coord

from astroquery.utils import commons, async_to_sync
from astroquery.utils.class_or_instance import class_or_instance
from astroquery.exceptions import InvalidQueryError, MaxResultsWarning

from astroquery.mast import utils
from astroquery.mast.core import MastQueryWithLogin

from . import conf

__all__ = ['MastMissionsClass', 'MastMissions']


@async_to_sync
class MastMissionsClass(MastQueryWithLogin):
    """
    MastMissions search class.
    Class that allows direct programmatic access to retrieve metadata via the MAST search API for a given mission.
    """

    def __init__(self, *, mission='hst', service='search'):
        super().__init__()

        self._search_option_fields = ['limit', 'offset', 'sort_by', 'search_key', 'sort_desc', 'select_cols',
                                      'skip_count', 'user_fields']
        self.service = service
        self.mission = mission
        self.limit = 5000

        service_dict = {self.service: {'path': self.service, 'args': {}}}
        self._service_api_connection.set_service_params(service_dict, f"{self.service}/{self.mission}")

    def _parse_result(self, response, *, verbose=False):  # Used by the async_to_sync decorator functionality
        """
        Parse the results of a `~requests.Response` objects and return an `~astropy.table.Table` of results.

        Parameters
        ----------
        response : `~requests.Response`
            `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False. Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        results = self._service_api_connection._parse_result(response, verbose, data_key='results')
        if len(results) >= self.limit:
            warnings.warn("Maximum results returned, may not include all sources within radius.",
                          MaxResultsWarning)

        return results

    @class_or_instance
    def query_region_async(self, coordinates, *, radius=3*u.arcmin, limit=5000, offset=0, **kwargs):
        """
        Given a sky position and radius, returns a list of matching dataset IDs.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 3 arcminutes.
        limit : int
            Optional and default is 5000.
            the maximum number of dataset IDs in the results.
        offset : int
            Optional and default is 0
            the number of records you wish to skip before selecting records.
        **kwargs
            Other mission-specific keyword args.
            Any invalid keys are ignored by the API.
            All valid key names can be found using `~astroquery.mast.missions.MastMissionsClass.get_column_list`
            function.
            For example one can specify the output columns(select_cols) or use other filters(conditions)

        Returns
        -------
        response : list of `~requests.Response`
        """

        self.limit = limit

        # Put coordinates and radius into consistent format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.arcmin)

        # basic params
        params = {'target': [f"{coordinates.ra.deg} {coordinates.dec.deg}"],
                  'radius': radius.arcmin,
                  'radius_units': 'arcminutes',
                  'limit': limit,
                  'offset': offset}

        params['conditions'] = []
        # adding additional user specified parameters
        for prop, value in kwargs.items():
            if prop not in self._search_option_fields:
                params['conditions'].append({prop: value})
            else:
                params[prop] = value

        return self._service_api_connection.service_request_async(self.service, params, use_json=True)

    @class_or_instance
    def query_criteria_async(self, *, coordinates=None, objectname=None, radius=3*u.arcmin,
                             limit=5000, offset=0, select_cols=[], **criteria):
        """
        Given a set of search criteria, returns a list of mission metadata.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 3 arcminutes.
        limit : int
            Optional and default is 5000.
            the maximum number of dataset IDs in the results.
        offset : int
            Optional and default is 0.
            the number of records you wish to skip before selecting records.
        select_cols: list
            names of columns that will be included in the astropy table
        **criteria
            Criteria to apply. At least one non-positional criteria must be supplied.
            Valid criteria are coordinates, objectname, radius (as in
            `~astroquery.mast.missions.MastMissionsClass.query_region` and
            `~astroquery.mast.missions.MastMissionsClass.query_object` functions),
            and all fields listed in the column documentation for the mission being queried.
            Any invalid keys passed in criteria are ignored by the API.
            List of all valid fields that can be used to match results on criteria can be retrieved by calling
            `~astroquery.mast.missions.MastMissionsClass.get_column_list` function.

        Returns
        -------
        response : list of `~requests.Response`
        """

        self.limit = limit

        if objectname or coordinates:
            coordinates = utils.parse_input_location(coordinates, objectname)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.arcmin)

        # build query
        params = {"limit": self.limit, "offset": offset, 'select_cols': select_cols}
        if coordinates:
            params["target"] = [f"{coordinates.ra.deg} {coordinates.dec.deg}"]
            params["radius"] = radius.arcmin
            params["radius_units"] = 'arcminutes'

        if not self._service_api_connection.check_catalogs_criteria_params(criteria):
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

        params['conditions'] = []
        for prop, value in criteria.items():
            if prop not in self._search_option_fields:
                params['conditions'].append({prop: value})
            else:
                params[prop] = value

        return self._service_api_connection.service_request_async(self.service, params, use_json=True)

    @class_or_instance
    def query_object_async(self, objectname, *, radius=3*u.arcmin, limit=5000, offset=0, **kwargs):
        """
        Given an object name, returns a list of matching rows.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 3 arcmin.
            The string must be parsable by `~astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 3 arcminutes.
        limit : int
            Optional and default is 5000.
            the maximum number of dataset IDs in the results.
        offset : int
            Optional and default is 0.
            the number of records you wish to skip before selecting records.
        **kwargs
            Mission-specific keyword args.
            Any invalid keys are ignored by the API.
            All valid keys can be found by calling `~astroquery.mast.missions.MastMissionsClass.get_column_list`
            function.

        Returns
        -------
        response : list of `~requests.Response`
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_async(coordinates, radius=radius, limit=limit, offset=offset, **kwargs)

    @class_or_instance
    def get_column_list(self):
        """
        For a mission, return a list of all searchable columns and their descriptions

        Returns
        -------
        response : `~astropy.table.Table` that contains columns names, types  and their descriptions
        """

        url = f"{conf.server}/search/util/api/v0.1/column_list?mission={self.mission}"

        try:
            results = requests.get(url)
            results = results.json()
            rows = []
            for result in results:
                result.pop('field_name')
                result.pop('queryable')
                result.pop('indexed')
                result.pop('default_output')
                rows.append((result['column_name'], result['qual_type'], result['description']))
            data_table = Table(rows=rows, names=('name', 'data_type', 'description'))
            return data_table
        except Exception:
            raise Exception(f"Error occurred while trying to get column list for mission {self.mission}")


MastMissions = MastMissionsClass()
