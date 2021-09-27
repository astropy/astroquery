# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Missions
=================

This module contains methods for searching MAST missions.
"""

import json

import astropy.units as u
import astropy.coordinates as coord

from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance

from . import utils
from .core import MastQueryWithLogin

__all__ = ['MissionsClass', 'Missions']


@async_to_sync
class MissionsClass(MastQueryWithLogin):
    """
    Missions search class.

    Class that allows direct programatic access to the MAST search API for a given mission.
    """

    def __init__(self):
        super().__init__()
        
        self.service = 'search'
        self.mission = 'hst'
        
        service_dict = {self.service: {'path': self.service, 'args': {}}}
        self._service_api_connection.set_service_params(service_dict, f"{self.service}/{self.mission}")

    def set_service(self, service):
        """
        Set the service name

        Parameters
        ----------
        service : `str`
            the name of the service
        """
        self.service = service

    def set_mission(self, mission):
        """
        Set the mission name

        Parameters
        ----------
        mission : `str`
            the name of the mission
        """

        self.mission = mission

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

        return self._service_api_connection._parse_result(response, verbose, data_key='results')

    @class_or_instance
    def query_region_async(self, coordinates, radius=3*u.arcmin, **kwargs):
        """
        Given a sky position and radius, returns a list matching datasets.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 3 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        mission : str, optional
            Default HST.
            The mission to be queried.
        **kwargs
            Other mission-specific keyword args.
            These can be found in the (service documentation)[https://mast.stsci.edu/api/v0/_services.html]
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.arcmin)

        # basic params
        params = {'target': [f"{coordinates.ra.deg} {coordinates.dec.deg}"],
                  'radius': radius.arcmin,
                  'radius_units': 'arcminutes'}


        # adding additional user specified parameters
        for prop, value in kwargs.items():
            params[prop] = value

        return self._service_api_connection.service_request_async(self.service, params, use_json=True)

    @class_or_instance
    def query_criteria_async(self, **criteria):
        """
        Given an set of filters, returns a list of catalog entries.

        Parameters
        ----------
        **criteria
            Criteria to apply. At least one non-positional criteria must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all fields listed in the column documentation for the mission being queried.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        if objectname or coordinates:
            coordinates = utils.parse_input_location(coordinates, objectname)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.arcmin)

        # build query
        params = {}
        if coordinates:
            params["target"] = [f"{coordinates.ra.deg} {coordinates.dec.deg}"]
            params["radius"] = radius.arcmin
            params["radius_units"] = 'arcminutes'

        if not self._service_api_connection.check_catalogs_criteria_params(criteria):
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

        for prop, value in criteria.items():
            params[prop] = value

        return self._service_api_connection.service_request_async(self.service, params, use_json=True)

    @class_or_instance
    def query_object_async(self, objectname, radius=3*u.arcmin, **kwargs):
        """
        Given an object name, returns a list of catalog entries.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 3 arcmin.
            The string must be parsable by `~astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        **kwargs
            Mission-specific keyword args.
            These can be found in the `service documentation <https://mast.stsci.edu/api/v0/_services.html>`__.
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response : list of `~requests.Response`
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_async(coordinates, radius)

Missions = MissionsClass()
