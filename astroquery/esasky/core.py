# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import json
import os
import tempfile
import tarfile
import sys

import six
from astropy.io import fits
from astropy import log
import astropy.units
import astropy.io.votable as votable
from requests import HTTPError

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
    __MISSION_STRING = "mission"
    __TAP_TABLE_STRING = "tapTable"
    __TAP_NAME_STRING = "tapName"
    __LABEL_STRING = "label"
    __METADATA_STRING = "metadata"
    __PRODUCT_URL_STRING = "product_url"
    __SOURCE_LIMIT_STRING = "sourceLimit"
    __POLYGON_NAME_STRING = "polygonNameTapColumn"
    __POLYGON_RA_STRING = "polygonRaTapColumn"
    __POLYGON_DEC_STRING = "polygonDecTapColumn"
    __POS_TAP_STRING = "posTapColumn"
    __ORDER_BY_STRING = "orderBy"
    __IS_SURVEY_MISSION_STRING = "isSurveyMission"
    __ZERO_ARCMIN_STRING = "0 arcmin"
    __MIN_RADIUS_CATALOG_STRING = "5 arcsec"

    __HERSCHEL_STRING = 'herschel'
    __HST_STRING = 'hst'
    __INTEGRAL_STRING = 'integral'
    __AKARI_STRING = 'akari'

    __HERSCHEL_FILTERS = {
        'psw': '250',
        'pmw': '350',
        'plw': '500',
        'mapb_blue': '70',
        'mapb_green': '100',
        'mapr_': '160'}

    _MAPS_DOWNLOAD_DIR = "Maps"
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

    def query_object_maps(self, position, missions=__ALL_STRING,
                          get_query_payload=False, cache=True):
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

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 8 tables:
            '0:HERSCHEL' with 8 column(s) and 25 row(s)
            '1:HST' with 8 column(s) and 735 row(s)

        Examples
        --------
        query_object_maps("m101", "all")

        query_object_maps("265.05, 69.0", "Herschel")
        query_object_maps("265.05, 69.0", ["Herschel", "HST"])
        """
        return self.query_region_maps(position=position,
                                      radius=self.__ZERO_ARCMIN_STRING,
                                      missions=missions,
                                      get_query_payload=get_query_payload,
                                      cache=cache)

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
            TableList with 8 tables:
            '0:Gaia DR1 TGA' with 8 column(s) and 25 row(s)
            '1:HSC' with 8 column(s) and 75 row(s)

        Examples
        --------
        query_object_catalogs("m101", "all")

        query_object_catalogs("265.05, 69.0", "Gaia DR1 TGA")
        query_object_catalogs("265.05, 69.0", ["Gaia DR1 TGA", "HSC"])
        """
        return self.query_region_catalogs(position=position,
                                          radius=self.__ZERO_ARCMIN_STRING,
                                          catalogs=catalogs,
                                          row_limit=row_limit,
                                          get_query_payload=get_query_payload,
                                          cache=cache)

    def query_region_maps(self, position, radius, missions=__ALL_STRING,
                          get_query_payload=False, cache=True):
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

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and region.
            It is structured in a TableList like this:
            TableList with 8 tables:
            '0:HERSCHEL' with 8 column(s) and 25 row(s)
            '1:HST' with 8 column(s) and 735 row(s)

        Examples
        --------
        query_region_maps("m101", "14'", "all")

        import astropy.units as u
        query_region_maps("265.05, 69.0", 14*u.arcmin, "Herschel")
        query_region_maps("265.05, 69.0", ["Herschel", "HST"])
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_mission(missions)

        query_result = {}

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(sanitized_position)

        self._store_query_result_maps(query_result, sanitized_missions,
                                      coordinates, sanitized_radius,
                                      get_query_payload, cache)

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
            TableList with 8 tables:
            '0:Gaia DR1 TGA' with 8 column(s) and 25 row(s)
            '1:HSC' with 8 column(s) and 75 row(s)

        Examples
        --------
        query_region_catalogs("m101", "14'", "all")

        import astropy.units as u
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, "Gaia DR1 TGA")
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, ["Gaia DR1 TGA", "HSC"])
        """
        sanitized_position = self._sanitize_input_position(position)
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_catalogs = self._sanitize_input_catalogs(catalogs)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(sanitized_position)

        query_result = {}

        self._store_query_result_catalogs(query_result, sanitized_catalogs,
                                          coordinates, sanitized_radius,
                                          sanitized_row_limit,
                                          get_query_payload, cache)

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
            'HERSCHEL': [{'70': [HDUList], '160': [HDUList]}, {'70': [HDUList], '160': [HDUList]}, ...],
            'HST':[[HDUList], [HDUList], [HDUList], [HDUList], [HDUList], ...],
            'XMM-EPIC' : [[HDUList], [HDUList], [HDUList], [HDUList], ...]
            ...
            }

        Examples
        --------
        get_maps(query_region_catalogs("m101", "14'", "all"))

        """
        sanitized_query_table_list = self._sanitize_input_table_list(query_table_list)
        sanitized_missions = [m.lower() for m in self._sanitize_input_mission(missions)]

        maps = dict()

        for query_mission in sanitized_query_table_list.keys():

            if (query_mission.lower() in sanitized_missions):
                # INTEGRAL & AKARI does not have a product url yet.
                if (query_mission.lower() == self.__INTEGRAL_STRING
                    or query_mission.lower() == self.__AKARI_STRING):
                    log.info(query_mission + " does not yet support downloading of "
                            "fits files")
                    continue
                maps[query_mission] = (
                    self._get_maps_for_mission(
                        sanitized_query_table_list[query_mission],
                        query_mission,
                        download_dir,
                        cache))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")

        elif (len(sanitized_query_table_list) > 0):
            log.info("Maps available at {}.".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def get_images(self, position, radius=__ZERO_ARCMIN_STRING, missions=__ALL_STRING,
                   download_dir=_MAPS_DOWNLOAD_DIR, cache=True):
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
            'HERSCHEL': [{'70': [HDUList], '160': [HDUList]}, {'70': [HDUList], '160': [HDUList]}, ...],
            'HST':[[HDUList], [HDUList], [HDUList], [HDUList], [HDUList], ...],
            'XMM-EPIC' : [[HDUList], [HDUList], [HDUList], [HDUList], ...]
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

        for query_mission in map_query_result.keys():
            # INTEGRAL & AKARI does not have a product url yet.
            if (query_mission.lower() == self.__INTEGRAL_STRING
                or query_mission.lower() == self.__AKARI_STRING):
                log.info(query_mission + " does not yet support downloading of "
                        "fits files")
                continue
            maps[query_mission] = (
                self._get_maps_for_mission(
                    map_query_result[query_mission],
                    query_mission,
                    download_dir,
                    cache))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")
        elif (len(map_query_result) > 0):
            log.info("Maps available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

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

    def _get_maps_for_mission(self, maps_table, mission, download_dir, cache):
        maps = []

        if (len(maps_table[self.__PRODUCT_URL_STRING]) > 0):
            mission_directory = self._create_mission_directory(mission,
                                                               download_dir)
            log.info("Starting download of {} data. ({} files)".format(
                mission, len(maps_table[self.__PRODUCT_URL_STRING])))
            for index in range(len(maps_table)):
                product_url = maps_table[self.__PRODUCT_URL_STRING][index]
                if commons.ASTROPY_LT_4_1:
                    product_url = product_url.decode('utf-8')
                if(mission.lower() == self.__HERSCHEL_STRING):
                    observation_id = maps_table["observation_id"][index]
                    if commons.ASTROPY_LT_4_1:
                        observation_id = observation_id.decode('utf-8')
                else:
                    observation_id = maps_table[self._get_tap_observation_id(mission)][index]
                    if commons.ASTROPY_LT_4_1:
                        observation_id = observation_id.decode('utf-8')
                log.info("Downloading Observation ID: {} from {}"
                         .format(observation_id, product_url))
                sys.stdout.flush()
                directory_path = mission_directory + "/"
                if (mission.lower() == self.__HERSCHEL_STRING):
                    try:
                        maps.append(self._get_herschel_map(
                            product_url,
                            directory_path,
                            cache))
                    except HTTPError as err:
                        log.error("Download failed with {}.".format(err))
                        maps.append(None)

                else:
                    response = self._request(
                        'GET',
                        product_url,
                        cache=cache,
                        headers=self._get_header())

                    try:
                        response.raise_for_status()

                        file_name = ""
                        if (product_url.endswith(self.__FITS_STRING)):
                            file_name = (directory_path +
                                         self._extract_file_name_from_url(product_url))
                        else:
                            file_name = (directory_path +
                                         self._extract_file_name_from_response_header(response.headers))

                        fits_data = response.content
                        with open(file_name, 'wb') as fits_file:
                            fits_file.write(fits_data)
                            fits_file.close()
                            maps.append(fits.open(file_name))
                    except HTTPError as err:
                        log.error("Download failed with {}.".format(err))
                        maps.append(None)

                if None in maps:
                    log.error("Some downloads were unsuccessful, please check "
                              "the warnings for more details")

                else:
                    log.info("[Done]")

            log.info("Downloading of {} data complete.".format(mission))

        return maps

    def _get_herschel_map(self, product_url, directory_path, cache):
        observation = dict()
        tar_file = tempfile.NamedTemporaryFile(delete=False)
        response = self._request('GET', product_url, cache=cache,
                                 headers=self._get_header())

        response.raise_for_status()

        tar_file.write(response.content)
        tar_file.close()
        with tarfile.open(tar_file.name, 'r') as tar:
            i = 0
            for member in tar.getmembers():
                member_name = member.name.lower()
                if ('hspire' in member_name or 'hpacs' in member_name):
                    herschel_filter = self._get_herschel_filter_name(member_name)
                    tar.extract(member, directory_path)
                    observation[herschel_filter] = fits.open(
                        directory_path +
                        member.name)
                    i += 1
        os.remove(tar_file.name)
        return observation

    def _get_herschel_filter_name(self, member_name):
        for herschel_filter in self.__HERSCHEL_FILTERS.keys():
            if herschel_filter in member_name:
                return self.__HERSCHEL_FILTERS[herschel_filter]

    def _remove_extra_herschel_directory(self, file_and_directory_name,
                                         directory_path):
        full_directory_path = os.path.abspath(directory_path)
        file_name = file_and_directory_name[file_and_directory_name.index("/") + 1:]

        os.renames(os.path.join(full_directory_path, file_and_directory_name),
                   os.path.join(full_directory_path, file_name))
        return file_name

    def _create_mission_directory(self, mission, download_dir):
        if (download_dir == self._MAPS_DOWNLOAD_DIR):
            mission_directory = self._MAPS_DOWNLOAD_DIR + "/" + mission
        else:
            mission_directory = (download_dir + "/" + self._MAPS_DOWNLOAD_DIR +
                                 "/" + mission)
        if not os.path.exists(mission_directory):
            os.makedirs(mission_directory)
        return mission_directory

    def _extract_file_name_from_response_header(self, headers):
        content_disposition = headers.get('Content-Disposition')
        filename_string = "filename="
        start_index = (content_disposition.index(filename_string) +
                       len(filename_string))
        if (content_disposition[start_index] == '\"'):
            start_index += 1

        if (self.__FITS_STRING in content_disposition[start_index:]):
            end_index = (
                content_disposition.index(self.__FITS_STRING, start_index + 1) +
                len(self.__FITS_STRING))
            return content_disposition[start_index: end_index]
        elif (self.__FTZ_STRING in content_disposition[start_index:]):
            end_index = (
                content_disposition.index(self.__FTZ_STRING, start_index + 1) +
                len(self.__FTZ_STRING))
            return content_disposition[start_index: end_index]
        elif (self.__TAR_STRING in content_disposition[start_index:]):
            end_index = (
                content_disposition.index(self.__TAR_STRING, start_index + 1) +
                len(self.__TAR_STRING))
            return content_disposition[start_index: end_index]
        else:
            raise ValueError("Could not find file name in header. "
                             "Content disposition: {}.".format(
                                 content_disposition))

    def _extract_file_name_from_url(self, product_url):
        start_index = product_url.rindex("/") + 1
        return product_url[start_index:]

    def _query_region_maps(self, coordinates, radius, observation_name,
                           get_query_payload, cache):
        observation_tap_name = (
            self._find_observation_tap_table_name(observation_name))
        query = (
            self._build_observation_query(coordinates, radius,
                                          self._find_observation_parameters(observation_tap_name)))
        request_payload = self._create_request_payload(query)
        if (get_query_payload):
            return request_payload
        return self._get_and_parse_from_tap(request_payload, cache)

    def _query_region_catalog(self, coordinates, radius, catalog_name, row_limit,
                              get_query_payload, cache):
        catalog_tap_name = self._find_catalog_tap_table_name(catalog_name)
        query = self._build_catalog_query(coordinates, radius, row_limit,
                                          self._find_catalog_parameters(catalog_tap_name))
        request_payload = self._create_request_payload(query)
        if (get_query_payload):
            return request_payload
        return self._get_and_parse_from_tap(request_payload, cache)

    def _build_observation_query(self, coordinates, radius, json):
        raHours, dec = commons.coord_to_radec(coordinates)
        ra = raHours * 15.0  # Converts to degrees
        radiusDeg = commons.radius_to_unit(radius, unit='deg')

        select_query = "SELECT DISTINCT "

        metadata = json[self.__METADATA_STRING]
        metadata_tap_names = ", ".join(["{}".format(entry[self.__TAP_NAME_STRING])
                                        for entry in metadata])

        from_query = " FROM {}".format(json[self.__TAP_TABLE_STRING])
        if (radiusDeg != 0 or json[self.__IS_SURVEY_MISSION_STRING]):
            if (json[self.__IS_SURVEY_MISSION_STRING]):
                where_query = (" WHERE 1=CONTAINS(pos, CIRCLE('ICRS', {}, {}, {}));".
                               format(ra, dec, radiusDeg))
            else:
                where_query = (" WHERE 1=INTERSECTS(CIRCLE('ICRS', {}, {}, {}), fov);".
                               format(ra, dec, radiusDeg))
        else:
            where_query = (" WHERE 1=CONTAINS(POINT('ICRS', {}, {}), fov);".
                           format(ra, dec))

        query = "".join([
            select_query,
            metadata_tap_names,
            from_query,
            where_query])
        return query

    def _build_catalog_query(self, coordinates, radius, row_limit, json):
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

        from_query = " FROM {}".format(json[self.__TAP_TABLE_STRING])
        if (radiusDeg == 0):
            where_query = (" WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {}, {}, {}))".
                           format(ra,
                                  dec,
                                  commons.radius_to_unit(
                                      self.__MIN_RADIUS_CATALOG_STRING,
                                      unit='deg')))
        else:
            where_query = (" WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {}, {}, {}))".
                           format(ra, dec, radiusDeg))
        order_by_query = ""
        if(json[self.__ORDER_BY_STRING] != ""):
            order_by_query = " ORDER BY {};".format(json[self.__ORDER_BY_STRING])

        query = "".join([select_query, metadata_tap_names, from_query,
                        where_query, order_by_query])

        return query

    def _store_query_result_maps(self, query_result, missions, coordinates,
                                 radius, get_query_payload, cache):
        for mission in missions:
            mission_table = self._query_region_maps(coordinates, radius,
                                                    mission, get_query_payload,
                                                    cache)
            if (len(mission_table) > 0):
                query_result[mission.upper()] = mission_table

    def _store_query_result_catalogs(self, query_result, catalogs, coordinates,
                                     radius, row_limit, get_query_payload, cache):
        for catalog in catalogs:
            catalog_table = self._query_region_catalog(coordinates, radius,
                                                       catalog, row_limit,
                                                       get_query_payload, cache)
            if (len(catalog_table) > 0):
                query_result[catalog.upper()] = catalog_table

    def _find_observation_parameters(self, mission_name):
        return self._find_mission_parameters_in_json(mission_name,
                                                     self._get_observation_json())

    def _find_catalog_parameters(self, catalog_name):
        return self._find_mission_parameters_in_json(catalog_name,
                                                     self._get_catalogs_json())

    def _find_mission_parameters_in_json(self, mission_tap_name, json):
        for mission in json:
            if (mission[self.__TAP_TABLE_STRING] == mission_tap_name):
                return mission
        raise ValueError("Input tap name {} not available.".format(mission_tap_name))

    def _find_observation_tap_table_name(self, mission_name):
        return self._find_mission_tap_table_name(
            self._fetch_and_parse_json(self.__OBSERVATIONS_STRING),
            mission_name)

    def _find_catalog_tap_table_name(self, mission_name):
        return self._find_mission_tap_table_name(
            self._fetch_and_parse_json(self.__CATALOGS_STRING),
            mission_name)

    def _find_mission_tap_table_name(self, json, mission_name):
        for index in range(len(json)):
            if (json[index][self.__MISSION_STRING].lower() == mission_name.lower()):
                return json[index][self.__TAP_TABLE_STRING]

        raise ValueError("Input {} not available.".format(mission_name))
        return None

    def _get_observation_json(self):
        return self._fetch_and_parse_json(self.__OBSERVATIONS_STRING)

    def _get_catalogs_json(self):
        return self._fetch_and_parse_json(self.__CATALOGS_STRING)

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

    def _get_tap_observation_id(self, mission):
        return self._get_json_data_for_mission(self._get_observation_json(), mission)["tapObservationId"]

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
