# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os
import tempfile
import tarfile
import sys
import re
from io import BytesIO

import six
from astropy.io import fits
from astroquery import log
import astropy.units
import astropy.io.votable as votable
from requests import HTTPError
from requests import ConnectionError

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from . import conf
from ..exceptions import TableParseError
from .. import version
from astropy.coordinates.name_resolve import sesame_database


@async_to_sync
class ESASkyClass(BaseQuery):

    URLbase = conf.urlBase
    TIMEOUT = conf.timeout
    DEFAULT_ROW_LIMIT = conf.row_limit

    __FITS_STRING = ".fits"
    __FTZ_STRING = ".FTZ"
    __TAR_STRING = ".tar"
    __ALL_STRING = "all"
    __CATALOGS_STRING = "catalogs"
    __OBSERVATIONS_STRING = "observations"
    __SPECTRA_STRING = "spectra"
    __MISSION_STRING = "mission"
    __TAP_TABLE_STRING = "tapTable"
    __TAP_NAME_STRING = "tapName"
    __TAP_RA_COLUMN_STRING = "tapRaColumn"
    __TAP_DEC_COLUMN_STRING = "tapDecColumn"
    __METADATA_STRING = "metadata"
    __PRODUCT_URL_STRING = "product_url"
    __ACCESS_URL_STRING = "access_url"
    __USE_INTERSECT_STRING = "useIntersectPolygonInsteadOfContainsPoint"
    __ZERO_ARCMIN_STRING = "0 arcmin"
    __MIN_RADIUS_CATALOG_STRING = "5 arcsec"

    __HERSCHEL_STRING = 'herschel'
    __HST_STRING = 'hst'

    __HERSCHEL_FILTERS = {
        'psw': '250',
        'pmw': '350',
        'plw': '500',
        'mapb_blue': '70',
        'mapb_green': '100',
        'mapr_': '160',
        'ssw.*ssc': 'SSW',
        'slw.*ssc': 'SLW',
        'sds': 'SSW+SLW',
        'spss': 'SSW+SLW',
        'bs_': 'blue',
        'rs_': 'red',
        'wbs': 'WBS',
        'hrs': 'HRS'
        }

    _MAPS_DOWNLOAD_DIR = "Maps"
    _SPECTRA_DOWNLOAD_DIR = "Spectra"
    _isTest = ""

    def list_maps(self):
        """
        Get a list of the mission names of the available observations in ESASky
        """
        return self._json_object_field_to_list(
            self._get_observation_json(), self.__MISSION_STRING)

    def list_catalogs(self):
        """
        Get a list of the mission names of the available catalogs in ESASky
        """
        return self._json_object_field_to_list(
            self._get_catalogs_json(), self.__MISSION_STRING)

    def list_spectra(self):
        """
        Get a list of the mission names of the available spectra in ESASky
        """
        return self._json_object_field_to_list(
            self._get_spectra_json(), self.__MISSION_STRING)

    def query_object_maps(self, position, missions=__ALL_STRING,
                          get_query_payload=False, cache=True,
                          row_limit=DEFAULT_ROW_LIMIT):
        """
        This method queries a chosen object or coordinate for all available maps
        which have observation data on the chosen position. It returns a
        TableList with all the found maps metadata for the chosen missions
        and object.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HERSCHEL' with 12 column(s) and 152 row(s)
            '1:HST-OPTICAL' with 12 column(s) and 6 row(s)

        Examples
        --------
        query_object_maps("m101", "all")

        query_object_maps("265.05, 69.0", "Herschel")
        query_object_maps("265.05, 69.0", ["Herschel", "HST-OPTICAL"])
        """
        return self.query_region_maps(position=position,
                                      radius=self.__ZERO_ARCMIN_STRING,
                                      missions=missions,
                                      get_query_payload=get_query_payload,
                                      cache=cache,
                                      row_limit=row_limit)

    def query_object_catalogs(self, position, catalogs=__ALL_STRING,
                              row_limit=DEFAULT_ROW_LIMIT,
                              get_query_payload=False, cache=True):
        """
        This method queries a chosen object or coordinate for all available
        catalogs and returns a TableList with all the found catalogs metadata
        for the chosen missions and object. To account for errors in telescope
        position, the method will look for any sources within a radius of
        5 arcsec of the chosen position.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        catalogs : string or list, optional
            Can be either a specific catalog or a list of catalogs (all catalog
            names are found in list_catalogs()) or 'all' to search in all
            catalogs. Defaults to 'all'.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            of the catalogs available for the chosen mission and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HSC' with 9 column(s) and 232 row(s)
            '1:XMM-OM' with 11 column(s) and 2 row(s)

        Examples
        --------
        query_object_catalogs("m101", "all")

        query_object_catalogs("202.469, 47.195", "HSC")
        query_object_catalogs("202.469, 47.195", ["HSC", "XMM-OM"])
        """
        return self.query_region_catalogs(position=position,
                                          radius=self.__ZERO_ARCMIN_STRING,
                                          catalogs=catalogs,
                                          row_limit=row_limit,
                                          get_query_payload=get_query_payload,
                                          cache=cache)

    def query_object_spectra(self, position, missions=__ALL_STRING,
                             get_query_payload=False, cache=True,
                             row_limit=DEFAULT_ROW_LIMIT):
        """
        This method queries a chosen object or coordinate for all available missions
        which have spectral data on the chosen position. It returns a
        TableList with all the found spectra metadata for the chosen missions
        and object.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and spectra available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HERSCHEL' with 12 column(s) and 12 row(s)
            '1:HST-OPTICAL' with 12 column(s) and 19 row(s)

        Examples
        --------
        query_object_spectra("m101", "all")

        query_object_spectra("202.469, 47.195", "Herschel")
        query_object_spectra("202.469, 47.195", ["Herschel", "HST-OPTICAL"])
        """
        return self.query_region_spectra(position=position,
                                      radius=self.__ZERO_ARCMIN_STRING,
                                      missions=missions,
                                      get_query_payload=get_query_payload,
                                      cache=cache,
                                      row_limit=row_limit)

    def query_region_maps(self, position, radius, missions=__ALL_STRING,
                          get_query_payload=False, cache=True,
                          row_limit=DEFAULT_ROW_LIMIT):
        """
        This method queries a chosen region for all available maps and returns a
        TableList with all the found maps metadata for the chosen missions and
        region.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        radius : str or `~astropy.units.Quantity`
            The radius of a region.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HERSCHEL' with 12 column(s) and 152 row(s)
            '1:HST-OPTICAL' with 12 column(s) and 71 row(s)

        Examples
        --------
        query_region_maps("m101", "14'", "all")

        import astropy.units as u
        query_region_maps("265.05, 69.0", 14*u.arcmin, "Herschel")
        query_region_maps("265.05, 69.0", 14*u.arcmin, ["Herschel", "HST-OPTICAL"])
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_mission(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(sanitized_position)

        self._store_query_result(query_result, sanitized_missions,
                                    coordinates, sanitized_radius, sanitized_row_limit,
                                    get_query_payload, cache, self._get_observation_json())

        if (get_query_payload):
            return query_result

        return commons.TableList(query_result)

    def query_region_catalogs(self, position, radius, catalogs=__ALL_STRING,
                              row_limit=DEFAULT_ROW_LIMIT,
                              get_query_payload=False, cache=True):
        """
        This method queries a chosen region for all available catalogs and
        returns a TableList with all the found catalogs metadata for the chosen
        missions and region.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        radius : str or `~astropy.units.Quantity`
            The radius of a region.
        catalogs : string or list, optional
            Can be either a specific catalog or a list of catalogs (all catalog
            names are found in list_catalogs()) or 'all' to search in all
            catalogs. Defaults to 'all'.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata of
            the catalogs available for the chosen mission and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HIPPARCOS-2' with 7 column(s) and 2 row(s)
            '1:HSC' with 9 column(s) and 10000 row(s)

        Examples
        --------
        query_region_catalogs("m101", "14'", "all")

        import astropy.units as u
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, "Hipparcos-2")
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, ["Hipparcos-2", "HSC"])
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_catalogs = self._sanitize_input_catalogs(catalogs)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(sanitized_position)

        query_result = {}

        self._store_query_result(query_result, sanitized_catalogs,
                                          coordinates, sanitized_radius,
                                          sanitized_row_limit,
                                          get_query_payload, cache, self._get_catalogs_json())

        if (get_query_payload):
            return query_result

        return commons.TableList(query_result)

    def query_region_spectra(self, position, radius, missions=__ALL_STRING,
                             row_limit=DEFAULT_ROW_LIMIT,
                             get_query_payload=False, cache=True):
        """
        This method queries a chosen region for all available spectra and returns a
        TableList with all the found spectra metadata for the chosen missions and
        region.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        radius : str or `~astropy.units.Quantity`
            The radius of a region.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.
        get_query_payload : bool, optional
            When set to True the method returns the HTTP request parameters.
            Defaults to False.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            '0:HERSCHEL' with 12 column(s) and 264 row(s)
            '1:IUE' with 12 column(s) and 14 row(s)

        Examples
        --------
        query_region_spectra("m101", "14'", "all")

        import astropy.units as u
        query_region_spectra("265.05, 69.0", 30*u.arcmin, "Herschel")
        query_region_spectra("265.05, 69.0", 30*u.arcmin, ["Herschel", "IUE"])
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_spectra(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(sanitized_position)

        self._store_query_result(query_result, sanitized_missions,
                                    coordinates, sanitized_radius, sanitized_row_limit,
                                    get_query_payload, cache, self._get_spectra_json())

        if (get_query_payload):
            return query_result

        return commons.TableList(query_result)

    def get_maps(self, query_table_list, missions=__ALL_STRING,
                 download_dir=_MAPS_DOWNLOAD_DIR, cache=True):
        """
        This method takes the dictionary of missions and metadata as returned by
        query_region_maps and downloads all maps to the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        For Herschel each item in the list is a dictionary where the used
        filter is the key and the HDUList is the value.

        Parameters
        ----------
        query_table_list : `~astroquery.utils.TableList` or dict or list of (name, `~astropy.table.Table`) pairs
            A TableList or dict or list of name and Table pairs with all the
            missions wanted and their respective metadata. Usually the
            return value of query_region_maps.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : string, optional
            The folder where all downloaded maps should be stored.
            Defaults to a folder called 'Maps' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        maps : `dict`
            All mission except Herschel returns a list of HDULists.
            For Herschel each item in the list is a dictionary where the used
            filter is the key and the HDUList is the value.
            It is structured in a dictionary like this:
            dict: {
            'HERSCHEL': [{'70': HDUList, '160': HDUList}, {'70': HDUList, '160': HDUList}, ...],
            'HST':[HDUList, HDUList, HDUList, HDUList, HDUList, ...],
            'XMM-EPIC' : [HDUList, HDUList, HDUList, HDUList, ...]
            ...
            }

        Examples
        --------
        get_maps(query_region_maps("m101", "14'", "all"))

        """
        sanitized_query_table_list = self._sanitize_input_table_list(query_table_list)
        sanitized_missions = [m.lower() for m in self._sanitize_input_mission(missions)]

        maps = dict()
        json = self._get_observation_json()

        for query_mission in sanitized_query_table_list.keys():

            if (query_mission.lower() in sanitized_missions):
                maps[query_mission] = (
                    self._get_maps_for_mission(
                        sanitized_query_table_list[query_mission],
                        query_mission,
                        download_dir,
                        cache, json))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")

        elif (len(sanitized_query_table_list) > 0):
            log.info("Maps available at {}.".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def get_images(self, position, radius=__ZERO_ARCMIN_STRING,
                   missions=__ALL_STRING, download_dir=_MAPS_DOWNLOAD_DIR,
                   cache=True):
        """
        This method gets the fits files available for the selected position and
        mission and downloads all maps to the the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        For Herschel each item in the list is a dictionary where the used
        filter is the key and the HDUList is the value.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        radius : str or `~astropy.units.Quantity`, optional
            The radius of a region. Defaults to 0.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : string, optional
            The folder where all downloaded maps should be stored.
            Defaults to a folder called 'Maps' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        maps : `dict`
            All mission except Herschel returns a list of HDULists.
            For Herschel each item in the list is a dictionary where the used
            filter is the key and the HDUList is the value.
            It is structured in a dictionary like this:
            dict: {
            'HERSCHEL': [{'70': HDUList, '160': HDUList}, {'70': HDUList, '160': HDUList}, ...],
            'HST':[HDUList, HDUList, HDUList, HDUList, HDUList, ...],
            'XMM-EPIC' : [HDUList, HDUList, HDUList, HDUList, ...]
            ...
            }

        Examples
        --------
        get_images("m101", "14'", "all")
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_mission(missions)

        maps = dict()

        map_query_result = self.query_region_maps(sanitized_position,
                                                  sanitized_radius,
                                                  sanitized_missions,
                                                  get_query_payload=False,
                                                  cache=cache)

        json = self._get_observation_json()
        for query_mission in map_query_result.keys():
            maps[query_mission] = (
                self._get_maps_for_mission(
                    map_query_result[query_mission],
                    query_mission,
                    download_dir,
                    cache, json))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")
        elif (len(map_query_result) > 0):
            log.info("Maps available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def get_spectra(self, position, radius=__ZERO_ARCMIN_STRING,
                    missions=__ALL_STRING, download_dir=_SPECTRA_DOWNLOAD_DIR,
                    cache=True):
        """
        This method gets the fits files available for the selected position and
        mission and downloads all spectra to the the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        Herschel returns a three-level dictionary.

        Parameters
        ----------
        position : str or `astropy.coordinates` object
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object.
        radius : str or `~astropy.units.Quantity`, optional
            The radius of a region. Defaults to 0.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : string, optional
            The folder where all downloaded spectra should be stored.
            Defaults to a folder called 'Spectra' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        spectra : `dict`
            All mission except Herschel returns a list of HDULists.
            Herschel returns a three-level dictionary.
            Read more about Herschel here: https://www.cosmos.esa.int/web/esdc/esasky-observations#HERSCHEL-OBS

            The response is structured in a dictionary like this:
            dict: {
            'HERSCHEL': {'1342211195': {'red' : {'HPSTBRRS' : HDUList}, 'blue' : {'HPSTBRBS': HDUList},
            '1342180796': {'WBS' : {'WBS-H_LSB_5a' : HDUList}, 'HRS' : {'HRS-H_LSB_5a': HDUList}, ...},
            'HST-IR':[HDUList, HDUList, HDUList, HDUList, HDUList, ...],
            'XMM-NEWTON' : [HDUList, HDUList, HDUList, HDUList, ...]
            ...
            }

        Examples
        --------
        get_spectra("m101", "14'", ["HST-IR", "XMM-NEWTON", "HERSCHEL"])

        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_spectra(missions)

        spectra = dict()

        spectra_query_result = self.query_region_spectra(sanitized_position,
                                                  sanitized_radius,
                                                  sanitized_missions,
                                                  get_query_payload=False,
                                                  cache=cache)
        json = self._get_spectra_json()
        for query_mission in spectra_query_result.keys():
            spectra[query_mission] = (
                self._get_maps_for_mission(
                    spectra_query_result[query_mission],
                    query_mission,
                    download_dir,
                    cache, json, True))

        if (len(spectra_query_result) > 0):
            log.info("Spectra available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No spectra found.")
        return spectra

    def get_spectra_from_table(self, query_table_list, missions=__ALL_STRING,
                               download_dir=_SPECTRA_DOWNLOAD_DIR, cache=True):
        """
        This method takes the dictionary of missions and metadata as returned by
        query_region_spectra and downloads all spectra to the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        Herschel returns a three-level dictionary.

        Parameters
        ----------
        query_table_list : `~astroquery.utils.TableList` or dict or list of (name, `~astropy.table.Table`) pairs
            A TableList or dict or list of name and Table pairs with all the
            missions wanted and their respective metadata. Usually the
            return value of query_region_spectra.
        missions : string or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : string, optional
            The folder where all downloaded spectra should be stored.
            Defaults to a folder called 'Spectra' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        spectra : `dict`
            All mission except Herschel returns a list of HDULists.
            Herschel returns a three-level dictionary.
            Read more about Herschel here: https://www.cosmos.esa.int/web/esdc/esasky-observations#HERSCHEL-OBS

            The response is structured in a dictionary like this:
            dict: {
            'HERSCHEL': {'1342211195': {'red' : {'HPSTBRRS' : HDUList}, 'blue' : {'HPSTBRBS': HDUList},
            '1342180796': {'WBS' : {'WBS-H_LSB_5a' : HDUList}, 'HRS' : {'HRS-H_LSB_5a': HDUList}, ...},
            'HST-IR':[HDUList, HDUList, HDUList, HDUList, HDUList, ...],
            'XMM-NEWTON' : [HDUList, HDUList, HDUList, HDUList, ...]
            ...
            }

        Examples
        --------
        table = query_region_spectra("m101", "14'", ["HST-IR", "XMM-NEWTON", "HERSCHEL"])
        get_spectra_from_table(table)
        """
        sanitized_query_table_list = self._sanitize_input_table_list(query_table_list)
        sanitized_missions = [m.lower() for m in self._sanitize_input_spectra(missions)]

        spectra = dict()
        json = self._get_spectra_json()

        for query_mission in sanitized_query_table_list.keys():

            if (query_mission.lower() in sanitized_missions):
                spectra[query_mission] = (
                    self._get_maps_for_mission(
                        sanitized_query_table_list[query_mission],
                        query_mission,
                        download_dir,
                        cache, json, True))

        if (len(sanitized_query_table_list) > 0):
            log.info("Spectra available at {}.".format(os.path.abspath(download_dir)))
        else:
            log.info("No spectra found.")
        return spectra

    def _sanitize_input_position(self, position):
        if (isinstance(position, str) or isinstance(position,
                                                    commons.CoordClasses)):
            return position
        else:
            raise ValueError("Position must be either a string or "
                             "astropy.coordinates")

    def _sanitize_input_radius(self, radius):
        if (isinstance(radius, str) or isinstance(radius,
                                                  astropy.units.Quantity)):
            return radius
        else:
            raise ValueError("Radius must be either a string or "
                             "astropy.units.Quantity")

    def _sanitize_input_mission(self, missions):
        if isinstance(missions, list):
            return missions
        if isinstance(missions, str):
            if (missions.lower() == self.__ALL_STRING):
                return self.list_maps()
            else:
                return [missions]
        raise ValueError("Mission must be either a string or a list of "
                         "missions")

    def _sanitize_input_spectra(self, spectra):
        if isinstance(spectra, list):
            return spectra
        if isinstance(spectra, str):
            if (spectra.lower() == self.__ALL_STRING):
                return self.list_spectra()
            else:
                return [spectra]
        raise ValueError("Spectra must be either a string or a list of "
                         "Spectra")

    def _sanitize_input_catalogs(self, catalogs):
        if isinstance(catalogs, list):
            return catalogs
        if isinstance(catalogs, str):
            if (catalogs.lower() == self.__ALL_STRING):
                return self.list_catalogs()
            else:
                return [catalogs]
        raise ValueError("Catalog must be either a string or a list of "
                         "catalogs")

    def _sanitize_input_table_list(self, table_list):
        if isinstance(table_list, commons.TableList):
            return table_list

        try:
            return commons.TableList(table_list)
        except ValueError:
            raise ValueError(
                "query_table_list must be an astroquery.utils.TableList "
                "or be able to be converted to it.")

    def _sanitize_input_row_limit(self, row_limit):
        if isinstance(row_limit, int):
            return row_limit
        raise ValueError("Row_limit must be an integer")

    def _get_maps_for_mission(self, maps_table, mission, download_dir, cache, json, is_spectra=False):
        if is_spectra and mission.lower() == self.__HERSCHEL_STRING:
            maps = dict()
        else:
            maps = []
        url_key = ""
        if self.__PRODUCT_URL_STRING in maps_table.keys():
            url_key = self.__PRODUCT_URL_STRING
        if url_key == "" and self.__ACCESS_URL_STRING in maps_table.keys():
            url_key = self.__ACCESS_URL_STRING
        if url_key == "" or mission == "ALMA" or mission == "INTEGRAL":
            log.info(mission + " does not yet support downloading of fits files")
            return maps

        if (len(maps_table[url_key]) > 0):
            mission_directory = self._create_mission_directory(mission,
                                                               download_dir)
            log.info("Starting download of {} data. ({} files)".format(
                mission, len(maps_table[url_key])))
            for index in range(len(maps_table)):
                product_url = maps_table[url_key][index]
                if isinstance(product_url, bytes):
                    product_url = product_url.decode('utf-8')
                if(mission.lower() == self.__HERSCHEL_STRING):
                    observation_id = maps_table["observation_id"][index]
                    if isinstance(observation_id, bytes):
                        observation_id = observation_id.decode('utf-8')
                else:
                    observation_id = maps_table[self._get_json_data_for_mission(json, mission)["uniqueIdentifierField"]][index]
                    if isinstance(observation_id, bytes):
                        observation_id = observation_id.decode('utf-8')
                log.info("Downloading Observation ID: {} from {}"
                         .format(observation_id, product_url))
                sys.stdout.flush()
                directory_path = mission_directory + "/"
                if mission.lower() == self.__HERSCHEL_STRING:
                    try:
                        if is_spectra:
                            key = maps_table['observation_id'][index]
                            if isinstance(key, bytes):
                                key = key.decode('utf-8')
                            maps[key] = self._get_herschel_spectra(
                                product_url,
                                directory_path,
                                cache)
                        else:
                            maps.append(self._get_herschel_map(
                                product_url,
                                directory_path,
                                cache))
                        log.info("[Done]")
                    except HTTPError as err:
                        log.error("Download failed with {}.".format(err))
                        if is_spectra:
                            key = maps_table['observation_id'][index]
                            if isinstance(key, bytes):
                                key = key.decode('utf-8')
                            maps[key] = None
                        else:
                            maps.append(None)

                else:
                    try:
                        response = self._request(
                            'GET',
                            product_url,
                            cache=cache,
                            stream=True,
                            headers=self._get_header())

                        response.raise_for_status()

                        file_name = self._extract_file_name_from_response_header(response.headers)
                        if (file_name == ""):
                            file_name = self._extract_file_name_from_url(product_url)
                        if(file_name.lower().endswith(self.__TAR_STRING)):
                            with tarfile.open(fileobj=BytesIO(response.content)) as tar:
                                for member in tar.getmembers():
                                    tar.extract(member, directory_path)
                                    maps.append(fits.open(directory_path + member.name))
                        else:
                            fits_data = response.content
                            with open(directory_path + file_name, 'wb') as fits_file:
                                fits_file.write(fits_data)
                                fits_file.flush()
                                maps.append(fits.open(directory_path + file_name))
                        log.info("[Done]")
                    except (HTTPError, ConnectionError) as err:
                        log.error("Download failed with {}.".format(err))
                        maps.append(None)

            if None in maps:
                log.error("Some downloads were unsuccessful, please check "
                          "the warnings for more details")

            log.info("Downloading of {} data complete.".format(mission))

        return maps

    def _get_herschel_map(self, product_url, directory_path, cache):
        observation = dict()
        response = self._request('GET', product_url, cache=cache,
                                 stream=True, headers=self._get_header())
        response.raise_for_status()

        with tarfile.open(fileobj=BytesIO(response.content)) as tar:
            for member in tar.getmembers():
                member_name = member.name.lower()
                if ('hspire' in member_name or 'hpacs' in member_name):
                    herschel_filter = self._get_herschel_filter_name(member_name)
                    tar.extract(member, directory_path)
                    observation[herschel_filter] = fits.open(
                        directory_path + member.name
                    )
        return observation

    def _get_herschel_spectra(self, product_url, directory_path, cache):
        spectra = dict()
        response = self._request('GET', product_url, cache=cache,
                                stream=True, headers=self._get_header())

        response.raise_for_status()

        with tarfile.open(fileobj=BytesIO(response.content)) as tar:
            for member in tar.getmembers():
                member_name = member.name.lower()
                if ('hspire' in member_name or 'hpacs' in member_name
                    or 'hhifi' in member_name):
                    herschel_filter = self._get_herschel_filter_name(member_name)
                    tar.extract(member, directory_path)
                    herschel_fits = []
                    if (herschel_filter in spectra):
                        hdul = fits.open(directory_path + member.name)
                        herschel_fits.append(hdul)
                    else:
                        herschel_fits = fits.open(directory_path + member.name)
                        if (isinstance(herschel_fits, list)):
                            herschel_fits = [herschel_fits]

                    hduListType = {}
                    for hduList in herschel_fits:
                        if(hduList[0].header['INSTRUME'] == 'HIFI'):
                            if ('BACKEND' in hduList[0].header):
                                headerKey = 'BACKEND'
                                label = hduList[0].header[headerKey].upper()
                            if('SIDEBAND' in hduList[0].header):
                                headerKey = 'SIDEBAND'
                                label = label + '_{}'.format(hduList[0].header[headerKey].upper())
                            if('BAND' in hduList[0].header):
                                headerKey = 'BAND'
                                label = label + '_{}'.format(hduList[0].header[headerKey].lower())
                            hduListType[label] = hduList
                        else:
                            headerKey = 'TYPE'
                            hduListType[hduList[0].header[headerKey]] = hduList

                    spectra[herschel_filter] = hduListType
        return spectra

    def _get_herschel_filter_name(self, member_name):
        for herschel_filter in self.__HERSCHEL_FILTERS.keys():
            if (bool(re.search(herschel_filter, member_name))):
                return self.__HERSCHEL_FILTERS[herschel_filter]

    def _remove_extra_herschel_directory(self, file_and_directory_name,
                                         directory_path):
        full_directory_path = os.path.abspath(directory_path)
        file_name = file_and_directory_name[file_and_directory_name.index("/") + 1:]

        os.renames(os.path.join(full_directory_path, file_and_directory_name),
                   os.path.join(full_directory_path, file_name))
        return file_name

    def _create_mission_directory(self, mission, download_dir):
        mission_directory = download_dir + "/" + mission
        if not os.path.exists(mission_directory):
            os.makedirs(mission_directory)
        return mission_directory

    def _extract_file_name_from_response_header(self, headers):
        content_disposition = headers.get('Content-Disposition')
        if content_disposition is None:
            return ""
        filename_string = "filename="
        start_index = (content_disposition.index(filename_string) +
                       len(filename_string))
        if (content_disposition[start_index] == '\"'):
            start_index += 1

        if (".gz" in content_disposition[start_index:].lower()):
            end_index = (
                content_disposition.lower().index(".gz", start_index + 1) + len(".gz"))
            return content_disposition[start_index: end_index]
        elif (self.__FITS_STRING in content_disposition[start_index:].lower()):
            end_index = (
                content_disposition.lower().index(self.__FITS_STRING, start_index + 1) +
                len(self.__FITS_STRING))
            return content_disposition[start_index: end_index]
        elif (self.__FTZ_STRING in content_disposition[start_index:].upper()):
            end_index = (
                content_disposition.upper().index(self.__FTZ_STRING, start_index + 1) +
                len(self.__FTZ_STRING))
            return content_disposition[start_index: end_index]
        elif (".fit" in content_disposition[start_index:].upper()):
            end_index = (
                content_disposition.upper().index(".fit", start_index + 1) + len(".fit"))
            return content_disposition[start_index: end_index]
        elif (self.__TAR_STRING in content_disposition[start_index:].lower()):
            end_index = (
                content_disposition.lower().index(self.__TAR_STRING, start_index + 1) +
                len(self.__TAR_STRING))
            return content_disposition[start_index: end_index]
        else:
            return ""

    def _extract_file_name_from_url(self, product_url):
        start_index = product_url.rindex("/") + 1
        return product_url[start_index:]

    def _query_region(self, coordinates, radius, name, row_limit,
                              get_query_payload, cache, json):
        table_tap_name = self._find_mission_tap_table_name(json, name)
        query = self._build_query(coordinates, radius, row_limit,
                                          self._find_mission_parameters_in_json(table_tap_name,
                                            json))
        request_payload = self._create_request_payload(query)
        if (get_query_payload):
            return request_payload
        return self._get_and_parse_from_tap(request_payload, cache)

    def _build_query(self, coordinates, radius, row_limit, json):
        raHours, dec = commons.coord_to_radec(coordinates)
        ra = raHours * 15.0  # Converts to degrees
        radiusDeg = commons.radius_to_unit(radius, unit='deg')

        select_query = "SELECT "
        if(row_limit > 0):
            select_query = "".join([select_query, "TOP {} ".format(row_limit)])
        elif(not row_limit == -1):
            raise ValueError("Invalid value of row_limit")

        metadata = json[self.__METADATA_STRING]
        metadata_tap_names = ", ".join(["{}".format(entry[self.__TAP_NAME_STRING])
                                        for entry in metadata])
        tapRaColumn = json[self.__TAP_RA_COLUMN_STRING]
        tapDecColumn = json[self.__TAP_DEC_COLUMN_STRING]

        from_query = " FROM {}".format(json[self.__TAP_TABLE_STRING])
        if (radiusDeg == 0):
            if(json[self.__USE_INTERSECT_STRING]):
                where_query = (" WHERE 1=INTERSECTS(CIRCLE('ICRS', {}, {}, {}), fov)".
                            format(ra, dec, commons.radius_to_unit(
                                      self.__MIN_RADIUS_CATALOG_STRING,
                                      unit='deg')))
            else:
                where_query = (" WHERE 1=CONTAINS(POINT('ICRS', {}, {}), CIRCLE('ICRS', {}, {}, {}))".
                           format(tapRaColumn, tapDecColumn,
                                  ra,
                                  dec,
                                  commons.radius_to_unit(
                                      self.__MIN_RADIUS_CATALOG_STRING,
                                      unit='deg')))
        else:
            if(json[self.__USE_INTERSECT_STRING]):
                where_query = (" WHERE 1=INTERSECTS(CIRCLE('ICRS', {}, {}, {}), fov)".
                            format(ra, dec, radiusDeg))
            else:
                where_query = (" WHERE 1=CONTAINS(POINT('ICRS', {}, {}), CIRCLE('ICRS', {}, {}, {}))".
                           format(tapRaColumn, tapDecColumn, ra, dec, radiusDeg))

        query = "".join([select_query, metadata_tap_names, from_query,
                        where_query])

        return query

    def _store_query_result(self, query_result, names, coordinates,
                                     radius, row_limit, get_query_payload, cache, json):
        for name in names:
            table = self._query_region(coordinates, radius,
                                                       name, row_limit,
                                                       get_query_payload, cache, json)
            if (len(table) > 0):
                query_result[name.upper()] = table

    def _find_mission_parameters_in_json(self, mission_tap_name, json):
        for mission in json:
            if (mission[self.__TAP_TABLE_STRING] == mission_tap_name):
                return mission
        raise ValueError("Input tap name {} not available.".format(mission_tap_name))

    def _find_mission_tap_table_name(self, json, mission_name):
        for index in range(len(json)):
            if (json[index][self.__MISSION_STRING].lower() == mission_name.lower()):
                return json[index][self.__TAP_TABLE_STRING]

        raise ValueError("Input {} not available.".format(mission_name))

    def _get_observation_json(self):
        return self._fetch_and_parse_json(self.__OBSERVATIONS_STRING)

    def _get_catalogs_json(self):
        return self._fetch_and_parse_json(self.__CATALOGS_STRING)

    def _get_spectra_json(self):
        return self._fetch_and_parse_json(self.__SPECTRA_STRING)

    def _fetch_and_parse_json(self, object_name):
        url = self.URLbase + "/" + object_name
        response = self._request(
            'GET',
            url,
            cache=False,
            headers=self._get_header())

        response.raise_for_status()

        string_response = response.content.decode('utf-8')
        json_response = json.loads(string_response)
        return json_response["descriptors"]

    def _json_object_field_to_list(self, json, field_name):
        response_list = []
        for index in range(len(json)):
            response_list.append(json[index][field_name])
        return response_list

    def _get_json_data_for_mission(self, json, mission):
        for index in range(len(json)):
            if(json[index][self.__MISSION_STRING].lower() == mission.lower()):
                return json[index]

    def _create_request_payload(self, query):
        return {'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'VOTABLE',
                'QUERY': query}

    def _get_and_parse_from_tap(self, request_payload, cache):
        response = self._send_get_request("/tap/sync", request_payload, cache)
        return self._parse_xml_table(response)

    def _send_get_request(self, url_extension, request_payload, cache):
        url = self.URLbase + url_extension
        return self._request('GET',
                             url,
                             params=request_payload,
                             timeout=self.TIMEOUT,
                             cache=cache,
                             headers=self._get_header())

    def _parse_xml_table(self, response):
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            tf = six.BytesIO(response.content)
            vo_table = votable.parse(tf, pedantic=False)
            first_table = vo_table.get_first_table()
            table = first_table.to_table(use_names_over_ids=True)
            return table
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError(
                "Failed to parse ESASky VOTABLE result! The raw response can be "
                "found in self.response, and the error in "
                "self.table_parse_error.")

    def _get_header(self):
        user_agent = 'astropy:astroquery.esasky.{vers} {isTest}'.format(
            vers=version.version,
            isTest=self._isTest)
        return {'User-Agent': user_agent}


ESASky = ESASkyClass()
