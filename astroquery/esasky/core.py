# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
import os
import tarfile
import sys
import re
import warnings
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path

from astropy import units as u
from astropy.coordinates import Angle
from astropy.io import fits
from astropy.utils.console import ProgressBar
from astroquery import log
from requests import HTTPError
from requests import ConnectionError

from ..query import BaseQuery
from ..utils.tap.core import TapPlus
from ..utils import commons
from ..utils import async_to_sync
from . import conf
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
    __MIN_RADIUS_CATALOG_DEG = Angle(5 * u.arcsec).to_value(u.deg)

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
    _cached_tables = None

    _NUMBER_DATA_TYPES = ["REAL", "float", "INTEGER", "int", "BIGINT", "long", "DOUBLE", "double", "SMALLINT", "short"]

    SSO_TYPES = ['ALL', 'ASTEROID', 'COMET', 'SATELLITE', 'PLANET',
                 'DWARF_PLANET', 'SPACECRAFT', 'SPACEJUNK', 'EXOPLANET', 'STAR']

    def __init__(self, tap_handler=None):
        super().__init__()

        if tap_handler is None:
            self._tap = TapPlus(url=self.URLbase + "/tap")
        else:
            self._tap = tap_handler

    def query(self, query, *, output_file=None, output_format="votable", verbose=False):
        """Launches a synchronous job to query the ESASky TAP

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            possible values 'votable' or 'csv'
        verbose : bool, optional, default 'False'
            flag to display information about the process and warnings when
            the data doesn't conform to its standard.

        Returns
        -------
        A table object
        """
        if not verbose:
            with warnings.catch_warnings():
                commons.suppress_vo_warnings()
                warnings.filterwarnings("ignore", category=u.UnitsWarning)
                job = self._tap.launch_job(query=query, output_file=output_file, output_format=output_format,
                                           verbose=False, dump_to_file=output_file is not None)
        else:
            job = self._tap.launch_job(query=query, output_file=output_file, output_format=output_format,
                                       verbose=True, dump_to_file=output_file is not None)
        return job.get_results()

    def get_tables(self, *, only_names=True, verbose=False, cache=True):
        """
        Get the available table in ESASky TAP service

        Parameters
        ----------
        only_names : bool, optional, default 'True'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of tables
        """

        if cache and self._cached_tables is not None:
            tables = self._cached_tables
        else:
            tables = self._tap.load_tables(only_names=only_names, include_shared_tables=False, verbose=verbose)
            self._cached_tables = tables
        if only_names:
            return [t.name for t in tables]
        else:
            return tables

    def get_columns(self, table_name, *, only_names=True, verbose=False):
        """
        Get the available columns for a table in ESASky TAP service

        Parameters
        ----------
        table_name : str, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, optional, default 'True'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of columns
        """

        tables = self.get_tables(only_names=False, verbose=verbose)
        columns = None
        for table in tables:
            if str(table.name) == str(table_name):
                columns = table.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "ESASky TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns

    def get_tap(self):
        """
        Get a TAP+ instance for the ESASky servers, which supports
        all common TAP+ operations (synchronous & asynchronous queries,
        uploading of tables, table sharing and more)
        Full documentation and examples available here:
        https://astroquery.readthedocs.io/en/latest/utils/tap.html

        Returns
        -------
        tap : `~astroquery.utils.tap.core.TapPlus`
        """

        return self._tap

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

    def list_sso(self):
        """
        Get a list of the mission names of the available observations with SSO crossmatch in ESASky
        """
        return self._json_object_field_to_list(
            self._get_sso_json(), self.__MISSION_STRING)

    def query_object_maps(self, position, missions=__ALL_STRING, get_query_payload=False, cache=True,
                          row_limit=DEFAULT_ROW_LIMIT, verbose=False):
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
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 12 column(s) and 152 row(s)
            'HST-OPTICAL' with 12 column(s) and 6 row(s)

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
                                      row_limit=row_limit,
                                      verbose=verbose)

    def query_object_catalogs(self, position, catalogs=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                              get_query_payload=False, cache=True, verbose=False):
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
        catalogs : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            of the catalogs available for the chosen mission and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HSC' with 9 column(s) and 232 row(s)
            'XMM-OM' with 11 column(s) and 2 row(s)

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
                                          cache=cache,
                                          verbose=verbose)

    def query_object_spectra(self, position, missions=__ALL_STRING, get_query_payload=False, cache=True,
                             row_limit=DEFAULT_ROW_LIMIT, verbose=False):
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
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and spectra available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 12 column(s) and 12 row(s)
            'HST-OPTICAL' with 12 column(s) and 19 row(s)

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
                                         row_limit=row_limit,
                                         verbose=verbose)

    def find_sso(self, sso_name, *, sso_type="ALL", cache=True):
        """
        This method allows you to find solar and extra solar system objects with a given name.
        ESASky is using IMCCE's SsODNet to resolve the objects.

        Parameters
        ----------
        sso_name : str
            A name or alias of a solar system object recognized by SsODNet.
        sso_type : str, optional
            Can be any of the sso types found in SSO_TYPES.
            Defaults to 'all'.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.

        Returns
        -------
        list : `list`
            Returns a list of object matching your search.
            Each mission match has sso_name, sso_type, and aliases.

        Examples
        --------
        find_sso(sso_name="Pallas")
        find_sso(sso_name="503")
        find_sso(sso_name="503", sso_type="SATELLITE")
        """
        sso_type = self._sanitize_input_sso_type(sso_type)
        sso_name = self._sanitize_input_sso_name(sso_name)
        try:
            response = self._request(
                method='GET',
                url=self.URLbase + "/generalresolver",
                params={
                    'action': 'bytarget',
                    'target': sso_name,
                    'type': sso_type
                },
                cache=cache,
                stream=True,
                headers=self._get_header())

            response.raise_for_status()

            search_result = response.content
            if isinstance(response.content, bytes):
                search_result = response.content.decode('utf-8')

            search_result = json.loads(search_result)
            sso_result = search_result['ssoDnetResults']
            if sso_result is None:
                log.info('No SSO found with name: {} and type: {}'.format(sso_name, sso_type))
                return None
            error_message = sso_result['errorMessage']
            if error_message is not None:
                log.error('Failed to resolve SSO: {} {} - Reason: {}'.format(sso_name, sso_type, error_message))
                return None
            else:
                sso_list = sso_result['results']
                for sso in sso_list:
                    sso['sso_name'] = sso.pop('name')
                    sso['sso_type'] = sso.pop('ssoObjType')
                return sso_list
        except (HTTPError, ConnectionError) as err:
            log.error("Connection failed with {}.".format(err))

    def query_sso(self, sso_name, *, sso_type="ALL", missions=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT, verbose=False):
        """
        This method performs a crossmatch on the chosen solar system object
        and the selected missions using ESASky's crossmatch algorithm.
        The algorithm detects both targeted and serendipitous observations.
        It returns a TableList with all the found maps metadata for the
        chosen missions and object.

        Parameters
        ----------
        sso_name : str
            A name or alias of a solar system object recognized by SsODNet.
        sso_type : str, optional
            Can be any of the sso types found in SSO_TYPES.
            Defaults to 'all'.
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_sso()) or 'all' to search in all
            missions. Defaults to 'all'.
            .astropy/astroquery/cache. Defaults to True.
        row_limit : int, optional
            Determines how many rows that will be fetched from the database
            for each mission. Can be -1 to select maximum (currently 100 000).
            Defaults to 10000.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and object.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 12 column(s) and 152 row(s)
            'HST' with 12 column(s) and 6 row(s)

        Examples
        --------
        query_sso(sso_name="Pallas", missions="HST")
        query_sso(sso_name="503", sso_type="SATELLITE")
        query_sso(sso_name="503", sso_type="SATELLITE", missions=["XMM", "HST"])
        """
        sso = self.find_sso(sso_name=sso_name, sso_type=sso_type)
        if len(sso) == 0:
            # Explanatory text logged by find_sso
            return None

        if len(sso) > 1:
            type_text = ''
            specify_type = 'You can also narrow your search by specifying the sso_type.\n' \
                           'Allowed values are {}.\n'.format(', '.join(map(str, self.SSO_TYPES)))
            if sso_type != 'ALL':
                type_text = ' and type {}'.format(sso_type)
            raise ValueError('Found {num_sso} SSO\'s with name: {sso_name}{type_text}.\n'
                             'Try narrowing your search by typing a more specific sso_name.\n{specify_type}'
                             'The following SSO\'s were found:\n{found_ssos}'
                             .format(num_sso=len(sso),
                                     sso_name=sso_name,
                                     type_text=type_text,
                                     specify_type=specify_type,
                                     found_ssos='\n'.join(map(str, sso)))
                             )

        sanitized_missions = self._sanitize_input_sso_mission(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        sso = sso[0]
        sso_json = self._get_sso_json()

        query_result = {}

        sso_type = self._get_sso_db_type(sso['sso_type'])
        sso_db_identifier = self._get_db_sso_identifier(sso['sso_type'])
        top = ""
        if sanitized_row_limit > 0:
            top = "TOP {row_limit} ".format(row_limit=sanitized_row_limit)
        for name in sanitized_missions:
            data_table = self._find_mission_tap_table_name(sso_json, name)
            mission_json = self._find_mission_parameters_in_json(data_table, sso_json)
            x_match_table = mission_json['ssoXMatchTapTable']
            query = 'SELECT {top}* FROM {data_table} AS a JOIN {x_match_table} AS b ' \
                    'ON a.observation_oid = b.observation_oid JOIN sso.ssoid AS c ' \
                    'ON b.sso_oid = c.sso_oid WHERE c.{sso_db_identifier} = \'{sso_name}\' ' \
                    'AND c.sso_type = \'{sso_type}\'' \
                .format(top=top, data_table=data_table, x_match_table=x_match_table,
                        sso_db_identifier=sso_db_identifier, sso_name=sso['sso_name'], sso_type=sso_type)
            table = self.query(query, verbose=verbose)
            if len(table) > 0:
                query_result[name.upper()] = table

        return commons.TableList(query_result)

    def get_images_sso(self, *, sso_name=None, sso_type="ALL", table_list=None, missions=__ALL_STRING,
                       download_dir=_MAPS_DOWNLOAD_DIR, cache=True, verbose=False):
        """
        This method gets the fits files for the input (either a sso_name or table_list)
        and downloads all maps to the the selected folder.
        If a sso_name is entered, this method performs a crossmatch on
        the chosen solar system object and the selected missions using
        ESASky's crossmatch algorithm.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        For Herschel each item in the list is a dictionary where the used
        filter is the key and the HDUList is the value.

        Parameters
        ----------
        sso_name : str, optional
            A name or alias of a solar system object recognized by SsODNet.
            One of sso_name and table_list is required.
        sso_type : str, optional
            Can be any of the sso types found in SSO_TYPES.
            Defaults to 'all'.
        table_list : `~astroquery.utils.TableList` or dict or list of (name, `~astropy.table.Table`) pairs
            A TableList or dict or list of name and Table pairs with all the
            missions wanted and their respective metadata. Usually the
            return value of query_sso.
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_sso()) or 'all' to search in all
            missions. Defaults to 'all'.
            .astropy/astroquery/cache. Defaults to True.
        download_dir : str, optional
            The folder where all downloaded maps should be stored.
            Defaults to a folder called 'Maps' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

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
            'XMM' : [HDUList, HDUList, HDUList, HDUList, ...]
            ...
            }

        Examples
        --------
        get_images_sso(sso_name="Pallas", missions="HST")
        get_images_sso(sso_name="503", sso_type="SATELLITE")
        get_images_sso(sso_name="503", sso_type="SATELLITE", missions=["XMM", "HST"])

        table = ESASky.query_sso(sso_name="503", sso_type="SATELLITE", missions=["XMM", "HST"])
        table["XMM"].remove_rows([1, 18, 23])
        get_images_sso(table_list=table, missions="XMM")

        """
        if sso_name is None and table_list is None:
            raise ValueError("An input is required for either sso_name or table.")

        sanitized_missions = [m.lower() for m in self._sanitize_input_sso_mission(missions)]
        sso_name = self._sanitize_input_sso_name(sso_name)
        sso_type = self._sanitize_input_sso_type(sso_type)
        if table_list is None:
            map_query_result = self.query_sso(sso_name=sso_name, sso_type=sso_type, missions=sanitized_missions,
                                              verbose=verbose)
        else:
            map_query_result = self._sanitize_input_table_list(table_list)

        maps = dict()

        json = self._get_sso_json()
        for query_mission in map_query_result.keys():
            if query_mission.lower() in sanitized_missions:
                maps[query_mission] = (
                    self._get_maps_for_mission(map_query_result[query_mission], query_mission, download_dir, cache,
                                               json, verbose=verbose))

        if len(map_query_result) > 0 and all([maps[mission].count(None) == len(maps[mission])
                                              for mission in maps]):
            log.info("No maps got downloaded, check errors above.")
        elif len(maps) > 0:
            log.info("Maps available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def query_region_maps(self, position, radius, missions=__ALL_STRING, get_query_payload=False, cache=True,
                          row_limit=DEFAULT_ROW_LIMIT, verbose=False):
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
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 12 column(s) and 152 row(s)
            'HST-OPTICAL' with 12 column(s) and 71 row(s)

        Examples
        --------
        query_region_maps("m101", "14'", "all")

        import astropy.units as u
        query_region_maps("265.05, 69.0", 14*u.arcmin, "Herschel")
        query_region_maps("265.05, 69.0", 14*u.arcmin, ["Herschel", "HST-OPTICAL"])
        """
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_mission(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(position)

        self._store_query_result(query_result=query_result, names=sanitized_missions, json=self._get_observation_json(),
                                 coordinates=coordinates, radius=sanitized_radius, row_limit=sanitized_row_limit,
                                 get_query_payload=get_query_payload, cache=cache, verbose=verbose)
        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def query_region_catalogs(self, position, radius, catalogs=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                              get_query_payload=False, cache=True, verbose=False):
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
        catalogs : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata of
            the catalogs available for the chosen mission and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HIPPARCOS-2' with 7 column(s) and 2 row(s)
            'HSC' with 9 column(s) and 10000 row(s)

        Examples
        --------
        query_region_catalogs("m101", "14'", "all")

        import astropy.units as u
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, "Hipparcos-2")
        query_region_catalogs("265.05, 69.0", 14*u.arcmin, ["Hipparcos-2", "HSC"])
        """
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_catalogs = self._sanitize_input_catalogs(catalogs)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(position)

        query_result = {}

        self._store_query_result(query_result=query_result, names=sanitized_catalogs, json=self._get_catalogs_json(),
                                 coordinates=coordinates, radius=sanitized_radius, row_limit=sanitized_row_limit,
                                 get_query_payload=get_query_payload, cache=cache, verbose=verbose)

        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def query_region_spectra(self, position, radius, missions=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                             get_query_payload=False, cache=True, verbose=False):
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
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata
            and observations available for the chosen missions and region.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 12 column(s) and 264 row(s)
            'IUE' with 12 column(s) and 14 row(s)

        Examples
        --------
        query_region_spectra("m101", "14'", "all")

        import astropy.units as u
        query_region_spectra("265.05, 69.0", 30*u.arcmin, "Herschel")
        query_region_spectra("265.05, 69.0", 30*u.arcmin, ["Herschel", "IUE"])
        """
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_spectra(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}

        sesame_database.set('simbad')
        coordinates = commons.parse_coordinates(position)

        self._store_query_result(query_result=query_result, names=sanitized_missions, json=self._get_spectra_json(),
                                 coordinates=coordinates, radius=sanitized_radius, row_limit=sanitized_row_limit,
                                 get_query_payload=get_query_payload, cache=cache, verbose=verbose)

        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def query_ids_maps(self, observation_ids, *, missions=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                       get_query_payload=False, cache=True, verbose=False):
        """
        This method fetches the metadata for all the given observations id's and returns a TableList.

        Parameters
        ----------
        observation_ids : string or list
            The observation IDs to fetch.
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'HERSCHEL' with 15 column(s) and 2 row(s)
            'HST-UV' with 15 column(s) and 2 row(s)

        Examples
        --------
        query_ids_maps(observation_ids=['lbsk03vbq', 'ieag90010'], missions="HST-UV")
        query_ids_maps(observation_ids='lbsk03vbq')
        query_ids_maps(observation_ids=['lbsk03vbq', '1342221848'], missions=["Herschel", "HST-UV"])
        """
        sanitized_observation_ids = self._sanitize_input_ids(observation_ids)
        sanitized_missions = self._sanitize_input_mission(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}
        self._store_query_result(query_result=query_result, names=sanitized_missions, json=self._get_observation_json(),
                                 row_limit=sanitized_row_limit, get_query_payload=get_query_payload, cache=cache,
                                 ids=sanitized_observation_ids, verbose=verbose)

        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def query_ids_catalogs(self, source_ids, *, catalogs=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                           get_query_payload=False, cache=True, verbose=False):
        """
        This method fetches the metadata for all the given source id's and returns a TableList.

        Parameters
        ----------
        source_ids : str or list
            The source IDs / names to fetch.
        catalogs : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'CHANDRA-SC2' with 41 column(s) and 2 row(s)
            'HIPPARCOS-2' with 45 column(s) and 2 row(s)

        Examples
        --------
        query_ids_catalogs(source_ids=['2CXO J090341.1-322609', '2CXO J090353.8-322642'], catalogs="CHANDRA-SC2")
        query_ids_catalogs(source_ids='2CXO J090341.1-322609')
        query_ids_catalogs(source_ids=['2CXO J090341.1-322609', '45057'], catalogs=["CHANDRA-SC2", "Hipparcos-2"])
        """
        sanitized_catalogs = self._sanitize_input_catalogs(catalogs)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)
        sanitized_source_ids = self._sanitize_input_ids(source_ids)

        query_result = {}
        self._store_query_result(query_result=query_result, names=sanitized_catalogs, json=self._get_catalogs_json(),
                                 row_limit=sanitized_row_limit, get_query_payload=get_query_payload, cache=cache,
                                 ids=sanitized_source_ids, verbose=verbose)

        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def query_ids_spectra(self, observation_ids, *, missions=__ALL_STRING, row_limit=DEFAULT_ROW_LIMIT,
                          get_query_payload=False, cache=True, verbose=False):
        """
        This method fetches the metadata for all the given observations id's and returns a TableList.

        Parameters
        ----------
        observation_ids : str or list
            The observation IDs to fetch.
        missions : str or list, optional
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
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

        Returns
        -------
        table_list : `~astroquery.utils.TableList`
            Each mission returns a `~astropy.table.Table` with the metadata.
            It is structured in a TableList like this:
            TableList with 2 tables:
            'XMM-NEWTON' with 16 column(s) and 2 row(s)
            'HERSCHEL' with 16 column(s) and 1 row(s)

        Examples
        --------
        query_ids_spectra(observation_ids=['0001730501', '0011420101'], missions='XMM-NEWTON')
        query_ids_spectra(observation_ids='0001730501')
        query_ids_spectra(observation_ids=['0001730501', '1342246640'], missions=['XMM-NEWTON', 'Herschel'])
        """
        sanitized_observation_ids = self._sanitize_input_ids(observation_ids)
        sanitized_missions = self._sanitize_input_spectra(missions)
        sanitized_row_limit = self._sanitize_input_row_limit(row_limit)

        query_result = {}
        self._store_query_result(query_result=query_result, names=sanitized_missions, json=self._get_spectra_json(),
                                 row_limit=sanitized_row_limit, get_query_payload=get_query_payload, cache=cache,
                                 ids=sanitized_observation_ids, verbose=verbose)

        if get_query_payload:
            return query_result

        return commons.TableList(query_result)

    def get_maps(self, query_table_list, *, missions=__ALL_STRING,
                 download_dir=_MAPS_DOWNLOAD_DIR, cache=True, verbose=False):
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
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : str, optional
            The folder where all downloaded maps should be stored.
            Defaults to a folder called 'Maps' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

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

            if query_mission.lower() in sanitized_missions:
                maps[query_mission] = (
                    self._get_maps_for_mission(sanitized_query_table_list[query_mission], query_mission, download_dir,
                                               cache, json, verbose=verbose))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")

        elif len(sanitized_query_table_list) > 0:
            log.info("Maps available at {}.".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def get_images(self, *, position=None, observation_ids=None, radius=__ZERO_ARCMIN_STRING,
                   missions=__ALL_STRING, download_dir=_MAPS_DOWNLOAD_DIR,
                   cache=True, verbose=False):
        """
        This method gets the fits files available for the selected mission and
        position or observation_ids and downloads all maps to the the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        For Herschel each item in the list is a dictionary where the used
        filter is the key and the HDUList is the value.

        Parameters
        ----------
        position : str or `astropy.coordinates` object, optional
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object. An input is required for either position or observation_ids.
        observation_ids : str or list, optional
            A list of observation ID's, you would like to download.
            If this parameter is empty, a cone search will be performed instead using the radius and position.
            An input is required for either position or observation_ids.
        radius : str or `~astropy.units.Quantity`, optional
            The radius of a region. Defaults to 0.
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_missions()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : str, optional
            The folder where all downloaded maps should be stored.
            Defaults to a folder called 'Maps' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

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
        get_images(position="m101", radius="14'", missions="all")

        missions = ["SUZAKU", "ISO-IR", "Chandra", "XMM-OM-OPTICAL", "XMM", "XMM-OM-UV", "HST-IR", "Herschel", \
                    "Spitzer", "HST-UV", "HST-OPTICAL"]
        observation_ids = ["100001010", "01500403", "21171", "0852000101", "0851180201", "0851180201", "n3tr01c3q", \
                           "1342247257", "30002561-25100", "hst_07553_3h_wfpc2_f160bw_pc", "ocli05leq"]
        get_images(observation_ids=observation_ids, missions=missions)

        """
        if position is None and observation_ids is None:
            raise ValueError("An input is required for either position or observation_ids.")
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_mission(missions)
        sanitized_observation_ids = self._sanitize_input_ids(observation_ids)

        if sanitized_observation_ids is None:
            map_query_result = self.query_region_maps(position,
                                                      sanitized_radius,
                                                      sanitized_missions,
                                                      get_query_payload=False,
                                                      cache=cache,
                                                      verbose=verbose)
        else:
            map_query_result = self.query_ids_maps(missions=sanitized_missions,
                                                   observation_ids=sanitized_observation_ids,
                                                   get_query_payload=False,
                                                   cache=cache,
                                                   verbose=verbose)
        maps = dict()

        json = self._get_observation_json()
        for query_mission in map_query_result.keys():
            maps[query_mission] = (
                self._get_maps_for_mission(map_query_result[query_mission], query_mission, download_dir, cache, json,
                                           verbose=verbose))

        if all([maps[mission].count(None) == len(maps[mission])
                for mission in maps]):
            log.info("No maps got downloaded, check errors above.")
        elif len(map_query_result) > 0:
            log.info("Maps available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No maps found.")
        return maps

    def get_spectra(self, *, position=None, observation_ids=None, radius=__ZERO_ARCMIN_STRING, missions=__ALL_STRING,
                    download_dir=_SPECTRA_DOWNLOAD_DIR, cache=True, verbose=False):
        """
        This method gets the fits files available for the selected missions and
        position or observation_ids and downloads all spectra to the the selected folder.
        The method returns a dictionary which is divided by mission.
        All mission except Herschel returns a list of HDULists.
        Herschel returns a three-level dictionary.

        Parameters
        ----------
        position : str or `astropy.coordinates` object, optional
            Can either be a string of the location, eg 'M51', or the coordinates
            of the object. An input is required for either position or observation_ids.
        observation_ids : str or list, optional
            A list of observation ID's, you would like to download.
            If this parameter is empty, a cone search will be performed instead using the radius and position.
            An input is required for either position or observation_ids.
        radius : str or `~astropy.units.Quantity`, optional
            The radius of a region. Defaults to 0.
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : str, optional
            The folder where all downloaded spectra should be stored.
            Defaults to a folder called 'Spectra' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

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

        get_spectra(position="m101", radius="14'", missions=["HST-IR", "XMM-NEWTON", "HERSCHEL"])

        missions = ["ISO-IR", "Chandra", "IUE", "XMM-NEWTON", "HST-IR", "Herschel", "HST-UV", "HST-OPTICAL"]
        observation_ids = ["02101201", "1005", "LWR13178", "0001730201", "ibh706cqq", "1342253595", "oeik2s020"]
        get_spectra(observation_ids=observation_ids, missions=missions)

        """
        if position is None and observation_ids is None:
            raise ValueError("An input is required for either position or observation_ids.")
        sanitized_radius = self._sanitize_input_radius(radius)
        sanitized_missions = self._sanitize_input_spectra(missions)
        sanitized_observation_ids = self._sanitize_input_ids(observation_ids)

        spectra = dict()

        if sanitized_observation_ids is None:
            spectra_query_result = self.query_region_spectra(position, sanitized_radius, sanitized_missions,
                                                             get_query_payload=False, cache=cache, verbose=verbose)
        else:
            spectra_query_result = self.query_ids_spectra(missions=sanitized_missions,
                                                          observation_ids=sanitized_observation_ids,
                                                          get_query_payload=False, cache=cache, verbose=verbose)
        json = self._get_spectra_json()
        for query_mission in spectra_query_result.keys():
            spectra[query_mission] = (
                self._get_maps_for_mission(spectra_query_result[query_mission], query_mission, download_dir, cache,
                                           json, is_spectra=True, verbose=verbose))

        if len(spectra_query_result) > 0:
            log.info("Spectra available at {}".format(os.path.abspath(download_dir)))
        else:
            log.info("No spectra found.")
        return spectra

    def get_spectra_from_table(self, query_table_list, missions=__ALL_STRING,
                               download_dir=_SPECTRA_DOWNLOAD_DIR, cache=True, verbose=False):
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
        missions : str or list, optional
            Can be either a specific mission or a list of missions (all mission
            names are found in list_spectra()) or 'all' to search in all
            missions. Defaults to 'all'.
        download_dir : str, optional
            The folder where all downloaded spectra should be stored.
            Defaults to a folder called 'Spectra' in the current working directory.
        cache : bool, optional
            When set to True the method will use a cache located at
            .astropy/astroquery/cache. Defaults to True.
        verbose : bool, optional
            Defaults to `False`. If `True` warnings are displayed when any FITS
            data or VOTable doesn't conform to its standard.

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

            if query_mission.lower() in sanitized_missions:
                spectra[query_mission] = (
                    self._get_maps_for_mission(sanitized_query_table_list[query_mission], query_mission, download_dir,
                                               cache, json, is_spectra=True, verbose=verbose))

        if len(sanitized_query_table_list) > 0:
            log.info("Spectra available at {}.".format(os.path.abspath(download_dir)))
        else:
            log.info("No spectra found.")
        return spectra

    def _sanitize_input_radius(self, radius):
        if isinstance(radius, (str, u.Quantity)):
            return radius
        else:
            raise ValueError("Radius must be either a string or "
                             "astropy.units.Quantity")

    def _sanitize_input_mission(self, missions):
        if isinstance(missions, list):
            return missions
        if isinstance(missions, str):
            if missions.lower() == self.__ALL_STRING:
                return self.list_maps()
            else:
                return [missions]
        raise ValueError("Mission must be either a string or a list of "
                         "missions")

    def _sanitize_input_spectra(self, spectra):
        if isinstance(spectra, list):
            return spectra
        if isinstance(spectra, str):
            if spectra.lower() == self.__ALL_STRING:
                return self.list_spectra()
            else:
                return [spectra]
        raise ValueError("Spectra must be either a string or a list of "
                         "Spectra")

    def _sanitize_input_catalogs(self, catalogs):
        if isinstance(catalogs, list):
            return catalogs
        if isinstance(catalogs, str):
            if catalogs.lower() == self.__ALL_STRING:
                return self.list_catalogs()
            else:
                return [catalogs]
        raise ValueError("Catalog must be either a string or a list of "
                         "catalogs")

    def _sanitize_input_ids(self, ids):
        if isinstance(ids, list) and len(ids) > 0:
            return ids
        if isinstance(ids, str):
            return [ids]
        if ids is None:
            return None
        raise ValueError("observation_ids/source_ids must be either a string or a list of "
                         "observation/source IDs")

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

    def _sanitize_input_sso_name(self, sso_name):
        if isinstance(sso_name, str):
            return sso_name
        if sso_name is None:
            return None
        raise ValueError("sso_name must be a string")

    def _sanitize_input_sso_type(self, sso_type):
        if isinstance(sso_type, str) and sso_type.upper() in self.SSO_TYPES:
            return sso_type
        valid_types = ", ".join(map(str, self.SSO_TYPES))
        raise ValueError("sso_type must be one of {}".format(valid_types))

    def _sanitize_input_sso_mission(self, missions):
        if isinstance(missions, list):
            return missions
        if isinstance(missions, str):
            if missions.lower() == self.__ALL_STRING:
                return self.list_sso()
            else:
                return [missions]
        raise ValueError("Mission must be either a string or a list of "
                         "missions. Valid entries are found in list_sso()")

    def _get_sso_db_type(self, sso_type):
        sso_type = sso_type.lower()
        if sso_type == "asteroid" or sso_type == "dwarf_planet":
            return "aster"
        return sso_type

    def _get_db_sso_identifier(self, sso_type):
        sso_type = sso_type.lower()
        if sso_type == "comet" or sso_type == "spacecraft":
            return "sso_id"
        return "sso_name"

    def _get_maps_for_mission(self, maps_table, mission, download_dir, cache, json, is_spectra=False, verbose=False):
        if is_spectra and mission.lower() == self.__HERSCHEL_STRING:
            maps = dict()
        else:
            maps = []
        url_key = ""
        if self.__PRODUCT_URL_STRING in maps_table.keys():
            url_key = self.__PRODUCT_URL_STRING
        if url_key == "" and self.__ACCESS_URL_STRING in maps_table.keys():
            url_key = self.__ACCESS_URL_STRING
        if url_key == "" or mission == "ALMA":
            log.info(mission + " does not yet support downloading of fits files")
            return maps

        if len(maps_table[url_key]) > 0:
            mission_directory = self._create_mission_directory(mission,
                                                               download_dir)
            log.info("Starting download of {} data. ({} files)".format(mission, len(maps_table[url_key])))
            progress_bar = ProgressBar(len(maps_table[url_key]))

            for index in range(len(maps_table)):
                product_url = maps_table[url_key][index]
                if isinstance(product_url, bytes):
                    product_url = product_url.decode('utf-8')
                if mission.lower() == self.__HERSCHEL_STRING:
                    observation_id = maps_table["observation_id"][index]
                    if isinstance(observation_id, bytes):
                        observation_id = observation_id.decode('utf-8')
                else:
                    observation_id = \
                        maps_table[self._get_json_data_for_mission(json, mission)["uniqueIdentifierField"]][index]
                    if isinstance(observation_id, bytes):
                        observation_id = observation_id.decode('utf-8')
                log.debug("Downloading Observation ID: {} from {}".format(observation_id, product_url))
                sys.stdout.flush()
                directory_path = mission_directory
                if mission.lower() == self.__HERSCHEL_STRING:
                    try:
                        if is_spectra:
                            key = maps_table['observation_id'][index]
                            if isinstance(key, bytes):
                                key = key.decode('utf-8')
                            maps[key] = self._get_herschel_spectra(product_url, directory_path, cache, verbose=verbose)
                        else:
                            maps.append(self._get_herschel_map(product_url, directory_path, cache, verbose=verbose))
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

                        if ('Content-Type' in response.headers
                                and response.headers['Content-Type'] == 'application/zip'):
                            with ZipFile(file=BytesIO(response.content)) as zip:
                                for info in zip.infolist():
                                    if self._ends_with_fits_like_extentsion(info.filename):
                                        maps.append(self._open_fits(
                                            zip.extract(info.filename, path=mission_directory), verbose=verbose))
                        else:
                            file_name = self._extract_file_name_from_response_header(response.headers)
                            if file_name == "":
                                file_name = self._extract_file_name_from_url(product_url)
                            if file_name.lower().endswith(self.__TAR_STRING):
                                with tarfile.open(fileobj=BytesIO(response.content)) as tar:
                                    for member in tar.getmembers():
                                        tar.extract(member, directory_path)
                                        maps.append(self._open_fits(Path(directory_path, member.name), verbose=verbose))
                            else:
                                fits_data = response.content
                                with open(os.path.join(directory_path, file_name), 'wb') as fits_file:
                                    fits_file.write(fits_data)
                                    fits_file.flush()
                                    maps.append(
                                        self._open_fits(os.path.join(directory_path, file_name), verbose=verbose))
                    except (HTTPError, ConnectionError) as err:
                        log.error("Download failed with {}.".format(err))
                        maps.append(None)

                    progress_bar.update(index + 1)

            if None in maps:
                log.error("Some downloads were unsuccessful, please check "
                          "the warnings for more details")

        return maps

    def _open_fits(self, path, verbose=False):
        if verbose:
            return fits.open(path)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=fits.verify.VerifyWarning)
            return fits.open(path)

    def _ends_with_fits_like_extentsion(self, name):
        lower_case_name = name.lower()
        return (lower_case_name.endswith("fits")
                or lower_case_name.endswith("fits.gz")
                or lower_case_name.endswith("ftz")
                or lower_case_name.endswith("ftz.gz")
                or lower_case_name.endswith("fit")
                or lower_case_name.endswith("fit.gz")
                or lower_case_name.endswith("fts")
                or lower_case_name.endswith("fts.gz")
                )

    def _get_herschel_map(self, product_url, directory_path, cache, verbose=False):
        observation = dict()
        response = self._request('GET', product_url, cache=cache,
                                 stream=True, headers=self._get_header())
        response.raise_for_status()

        with tarfile.open(fileobj=BytesIO(response.content)) as tar:
            for member in tar.getmembers():
                member_name = member.name.lower()
                if 'hspire' in member_name or 'hpacs' in member_name:
                    herschel_filter = self._get_herschel_filter_name(member_name)
                    tar.extract(member, directory_path)
                    observation[herschel_filter] = self._open_fits(
                        os.path.join(directory_path, member.name), verbose=verbose
                    )
        return observation

    def _get_herschel_spectra(self, product_url, directory_path, cache, verbose=False):
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
                    if herschel_filter in spectra:
                        hdul = self._open_fits(os.path.join(directory_path, member.name), verbose=verbose)
                        herschel_fits.append(hdul)
                    else:
                        herschel_fits = self._open_fits(os.path.join(directory_path, member.name), verbose=verbose)
                        if isinstance(herschel_fits, list):
                            herschel_fits = [herschel_fits]

                    hduListType = {}
                    for hduList in herschel_fits:
                        if hduList[0].header['INSTRUME'] == 'HIFI':
                            if 'BACKEND' in hduList[0].header:
                                headerKey = 'BACKEND'
                                label = hduList[0].header[headerKey].upper()
                            if 'SIDEBAND' in hduList[0].header:
                                headerKey = 'SIDEBAND'
                                label = label + '_{}'.format(hduList[0].header[headerKey].upper())
                            if 'BAND' in hduList[0].header:
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
            if bool(re.search(herschel_filter, member_name)):
                return self.__HERSCHEL_FILTERS[herschel_filter]

    def _remove_extra_herschel_directory(self, file_and_directory_name,
                                         directory_path):
        full_directory_path = os.path.abspath(directory_path)
        file_name = Path(file_and_directory_name).name

        os.renames(os.path.join(full_directory_path, file_and_directory_name),
                   os.path.join(full_directory_path, file_name))
        return file_name

    def _create_mission_directory(self, mission, download_dir):
        mission_directory = os.path.join(download_dir, mission)
        if not os.path.exists(mission_directory):
            os.makedirs(mission_directory)
        return mission_directory

    def _extract_file_name_from_response_header(self, headers):
        content_disposition = headers.get('Content-Disposition')
        if content_disposition is None:
            return ""
        filename_string = "filename="
        start_index = (content_disposition.index(filename_string)
                       + len(filename_string))
        if content_disposition[start_index] == '\"':
            start_index += 1

        if ".gz" in content_disposition[start_index:].lower():
            end_index = (content_disposition.lower().index(".gz", start_index + 1) + len(".gz"))
            return os.path.basename(content_disposition[start_index: end_index])
        elif self.__FITS_STRING in content_disposition[start_index:].lower():
            end_index = (
                content_disposition.lower().index(self.__FITS_STRING, start_index + 1) + len(self.__FITS_STRING))
            return os.path.basename(content_disposition[start_index: end_index])
        elif self.__FTZ_STRING in content_disposition[start_index:].upper():
            end_index = (content_disposition.upper().index(self.__FTZ_STRING, start_index + 1) + len(self.__FTZ_STRING))
            return os.path.basename(content_disposition[start_index: end_index])
        elif ".fit" in content_disposition[start_index:].upper():
            end_index = (content_disposition.upper().index(".fit", start_index + 1) + len(".fit"))
            return os.path.basename(content_disposition[start_index: end_index])
        elif self.__TAR_STRING in content_disposition[start_index:].lower():
            end_index = (content_disposition.lower().index(self.__TAR_STRING, start_index + 1) + len(self.__TAR_STRING))
            return os.path.basename(content_disposition[start_index: end_index])
        else:
            return ""

    def _extract_file_name_from_url(self, product_url):
        start_index = product_url.rindex("/") + 1
        return product_url[start_index:]

    def _query(self, name, json, verbose=False, **kwargs):
        table_tap_name = self._find_mission_tap_table_name(json, name)
        if 'ids' in kwargs:
            query = self._build_id_query(ids=kwargs.get('ids'),
                                         row_limit=kwargs.get('row_limit'),
                                         json=self._find_mission_parameters_in_json(table_tap_name, json))
        else:
            query = self._build_region_query(coordinates=kwargs.get('coordinates'), radius=kwargs.get('radius'),
                                             row_limit=kwargs.get('row_limit'),
                                             json=self._find_mission_parameters_in_json(table_tap_name, json))

        if 'get_query_payload' in kwargs and kwargs.get('get_query_payload'):
            return self._create_request_payload(query)

        if not query:
            # Could not create query. The most common reason for this is a type mismatch between user specified ID and
            # data type of database column.
            # For example query_ids_catalogs(source_ids=["2CXO J090341.1-322609"], mission=["CHANDRA", "HSC"])
            # would be able to create a query for Chandra, but not for Hubble because the hubble source id column type
            # is a number and "2CXO J090341.1-322609" cannot be converted to a number.
            return query

        return self.query(query, output_format="votable", verbose=verbose)

    def _build_region_query(self, coordinates, radius, row_limit, json):
        ra = coordinates.transform_to('icrs').ra.deg
        dec = coordinates.transform_to('icrs').dec.deg
        radius_deg = Angle(radius).to_value(u.deg)

        select_query = "SELECT "
        if row_limit > 0:
            select_query = "".join([select_query, "TOP {} ".format(row_limit)])
        elif row_limit != -1:
            raise ValueError("Invalid value of row_limit")

        select_query = "".join([select_query, "* "])

        tap_ra_column = json[self.__TAP_RA_COLUMN_STRING]
        tap_dec_column = json[self.__TAP_DEC_COLUMN_STRING]

        from_query = " FROM {}".format(json[self.__TAP_TABLE_STRING])
        if radius_deg == 0:
            if json[self.__USE_INTERSECT_STRING]:
                where_query = (" WHERE 1=INTERSECTS(CIRCLE('ICRS', {}, {}, {}), fov)".
                               format(ra, dec, self.__MIN_RADIUS_CATALOG_DEG))
            else:
                where_query = (" WHERE 1=CONTAINS(POINT('ICRS', {}, {}), CIRCLE('ICRS', {}, {}, {}))".
                               format(tap_ra_column, tap_dec_column,
                                      ra,
                                      dec,
                                      self.__MIN_RADIUS_CATALOG_DEG))
        else:
            if json[self.__USE_INTERSECT_STRING]:
                where_query = (" WHERE 1=INTERSECTS(CIRCLE('ICRS', {}, {}, {}), fov)".
                               format(ra, dec, radius_deg))
            else:
                where_query = (" WHERE 1=CONTAINS(POINT('ICRS', {}, {}), CIRCLE('ICRS', {}, {}, {}))".
                               format(tap_ra_column, tap_dec_column, ra, dec, radius_deg))

        query = "".join([select_query, from_query,
                         where_query])

        return query

    def _build_id_query(self, ids, row_limit, json):
        select_query = "SELECT "
        if row_limit > 0:
            select_query = "".join([select_query, "TOP {} ".format(row_limit)])
        elif row_limit != -1:
            raise ValueError("Invalid value of row_limit")

        select_query = "".join([select_query, "* "])

        from_query = " FROM {}".format(json[self.__TAP_TABLE_STRING])
        id_column = json["uniqueIdentifierField"]
        if "observations" in json["tapTable"] or "spectra" in json["tapTable"]:
            if id_column in ("observation_oid", "plane_id"):
                id_column = "observation_id"
            if id_column == "designation":
                id_column = "obsid"

        data_type = None
        for column in self.get_columns(table_name=json['tapTable'], only_names=False):
            if column.name == id_column:
                data_type = column.data_type

        valid_ids = ids
        if data_type in self._NUMBER_DATA_TYPES:
            valid_ids = [int(obs_id) for obs_id in ids if obs_id.isdigit()]
            if not valid_ids:
                raise ValueError(f"Could not construct query for mission {json['mission']}. Database column type is "
                                 "a number, while none of the input id's could be interpreted as numbers.")
                return ""

        observation_ids_query_list = ", ".join(repr(id) for id in valid_ids)
        where_query = (" WHERE {} IN ({})".format(id_column, observation_ids_query_list))

        query = "".join([select_query, from_query,
                         where_query])

        return query

    def _store_query_result(self, query_result, names, json, verbose=False, **kwargs):
        for name in names:
            table = self._query(name=name, json=json, verbose=verbose, **kwargs)
            if len(table) > 0:
                query_result[name.upper()] = table

    def _find_mission_parameters_in_json(self, mission_tap_name, json):
        for mission in json:
            if mission[self.__TAP_TABLE_STRING] == mission_tap_name:
                return mission
        raise ValueError("Input tap name {} not available.".format(mission_tap_name))

    def _find_mission_tap_table_name(self, json, mission_name):
        for index in range(len(json)):
            if json[index][self.__MISSION_STRING].lower() == mission_name.lower():
                return json[index][self.__TAP_TABLE_STRING]

        raise ValueError("Input {} not available.".format(mission_name))

    def _get_observation_json(self):
        return self._fetch_and_parse_json(self.__OBSERVATIONS_STRING)

    def _get_catalogs_json(self):
        return self._fetch_and_parse_json(self.__CATALOGS_STRING)

    def _get_spectra_json(self):
        return self._fetch_and_parse_json(self.__SPECTRA_STRING)

    def _get_sso_json(self):
        return self._fetch_and_parse_json("sso")

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
            if json[index][self.__MISSION_STRING].lower() == mission.lower():
                return json[index]

    def _create_request_payload(self, query):
        return {'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'VOTABLE',
                'QUERY': query}

    def _send_get_request(self, url_extension, request_payload, cache):
        url = self.URLbase + url_extension
        return self._request('GET',
                             url,
                             params=request_payload,
                             timeout=self.TIMEOUT,
                             cache=cache,
                             headers=self._get_header())

    def _get_header(self):
        user_agent = 'astropy:astroquery.esasky.{vers} {isTest}'.format(
            vers=version.version,
            isTest=self._isTest)
        return {'User-Agent': user_agent}


ESASky = ESASkyClass()
