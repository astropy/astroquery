# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

======================
eHST Astroquery Module
======================


@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Aug. 2018


"""
from astroquery.utils import commons
from astropy import units
from astropy.coordinates import SkyCoord
from astropy.coordinates import Angle
from astropy.units import Quantity
from astroquery.utils.tap.core import TapPlus
from astroquery.utils.tap.model import modelutils
from astroquery.query import BaseQuery
from astropy.table import Table
from six import BytesIO
import shutil
import os
import json

from . import conf
from astroquery import log

__all__ = ['ESAHubble', 'ESAHubbleClass']


class ESAHubbleClass(BaseQuery):
    """
    Class to init ESA Hubble Module and communicate with eHST TAP
    """

    data_url = conf.DATA_ACTION
    metadata_url = conf.METADATA_ACTION
    target_url = conf.TARGET_ACTION
    TIMEOUT = conf.TIMEOUT
    calibration_levels = {0: "AUXILIARY", 1: "RAW", 2: "CALIBRATED",
                          3: "PRODUCT"}
    product_types = ["PRODUCT", "SCIENCE_PRODUCT", "POSTCARD"]
    copying_string = "Copying file to {0}..."

    def __init__(self, tap_handler=None):
        super(ESAHubbleClass, self).__init__()

        if tap_handler is None:
            self._tap = TapPlus(url="http://hst.esac.esa.int"
                                    "/tap-server/tap/")
        else:
            self._tap = tap_handler

    def download_product(self, observation_id, *, calibration_level=None,
                         filename=None, verbose=False, product_type=None):
        """
        Download products from EHST based on their observation ID and the
        calibration level or the product type.

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        calibration_level : string
            calibration level, optional
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
        filename : string
            file name to be used to store the artifact, optional, default
            None
            File name for the observation.
        verbose : bool
            optional, default 'False'
            flag to display information about the process
        product_type : string
            type of product retrieval, optional
            PRODUCT, SCIENCE_PRODUCT or POSTCARD

        Returns
        -------
        None. It downloads the observation indicated
        """

        params = {"OBSERVATION_ID": observation_id,
                  "USERNAME": "ehst-astroquery"}
        url = self.data_url + "?OBSERVATION_ID=" + observation_id
        url += "&USERNAME=" + "ehst-astroquery"

        if filename is None:
            filename = observation_id + ".tar"

        if calibration_level:
            params["CALIBRATION_LEVEL"] = calibration_level
            url += "&CALIBRATION_LEVEL=" + calibration_level

        if product_type:
            self.__validate_product_type(product_type)
            params["RETRIEVAL_TYPE"] = product_type
            filename = self._get_product_filename(product_type, filename)
            url += "&RETRIEVAL_TYPE=" + params["RETRIEVAL_TYPE"]

        response = self._request('GET', self.data_url, save=True, cache=True,
                                 params=params)

        if verbose:
            log.info(url)
            log.info(self.copying_string.format(filename))

        shutil.move(response, filename)

    def __validate_product_type(self, product_type):
        if(product_type not in self.product_types):
            raise ValueError("This product_type is not allowed")

    def _get_product_filename(self, product_type, filename):
        if(product_type == "PRODUCT"):
            return filename
        elif(product_type == "SCIENCE_PRODUCT"):
            log.info("This is a SCIENCE_PRODUCT, the filename will be "
                     "renamed to " + filename + ".fits.gz")
            return filename + ".fits.gz"
        else:
            log.info("This is a POSTCARD, the filename will be "
                     "renamed to " + filename + ".jpg")
            return filename + ".jpg"

    def get_artifact(self, artifact_id, filename=None, verbose=False):
        """
        Download artifacts from EHST. Artifact is a single Hubble product file.

        Parameters
        ----------
        artifact_id : string
            id of the artifact to be downloaded, mandatory
            The identifier of the physical product (file) we want to retrieve.
        filename : string
            file name to be used to store the artifact, optional, default None
            File name for the artifact
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. It downloads the artifact indicated
        """

        params = {"ARTIFACT_ID": artifact_id, "USERNAME": "ehst-astroquery"}
        response = self._request('GET', self.data_url, save=True, cache=True,
                                 params=params)
        if filename is None:
            filename = artifact_id

        if verbose:
            log.info(self.data_url + "?ARTIFACT_ID=" + artifact_id +
                     "&USERNAME=ehst-astroquery")
            log.info(self.copying_string.format(filename))

        shutil.move(response, filename)

    def get_postcard(self, observation_id, calibration_level="RAW",
                     resolution=256, filename=None, verbose=False):
        """
        Download postcards from EHST

        Parameters
        ----------
        observation_id : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        calibration_level : string
            calibration level, optional, default 'RAW'
            The identifier of the data reduction/processing applied to the
            data. By default, the most scientifically relevant level will be
            chosen. RAW, CALIBRATED, PRODUCT or AUXILIARY
        resolution : integer
            postcard resolution, optional, default 256
            Resolution of the retrieved postcard. 256 or 1024
        filename : string
            file name to be used to store the postcard, optional, default None
            File name for the artifact
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        None. It downloads the observation postcard indicated
        """

        params = {"RETRIEVAL_TYPE": "POSTCARD",
                  "OBSERVATION_ID": observation_id,
                  "CALIBRATION_LEVEL": calibration_level,
                  "RESOLUTION": resolution,
                  "USERNAME": "ehst-astroquery"}

        response = self._request('GET', self.data_url, save=True, cache=True,
                                 params=params)

        if filename is None:
            filename = observation_id

        if verbose:
            log.info(self.data_url +
                     "&".join(["?RETRIEVAL_TYPE=POSTCARD",
                               "OBSERVATION_ID=" + observation_id,
                               "CALIBRATION_LEVEL=" + calibration_level,
                               "RESOLUTION=" + str(resolution),
                               "USERNAME=ehst-astroquery"]))
            log.info(self.copying_string.format(filename))

        shutil.move(response, filename)

    def cone_search(self, coordinates, radius, filename=None,
                    output_format='votable', cache=True,
                    async_job=False, verbose=False):
        """
        To execute a cone search defined by a coordinate and a radius

        Parameters
        ----------
        coordinates : astropy.coordinate, mandatory
            coordinates of the center in the cone search
        radius : float or quantity
            radius in arcmin (int, float) or quantity of the cone_search
        filename : str, default None
            Path and name of the file to store the results.
            If the filename is defined, the file will be
            automatically saved
        output_format : string
            results format. Options are:
            'votable': str, binary VOTable format
            'csv': str, comma-separated values format
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        cache : bool
            optional, default 'True'
            Flag to save the results in the local cache
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        astropy.table.Table with the result of the cone_search
        """
        coord = self._getCoordInput(coordinates)
        if type(radius) == int or type(radius) == float:
            radius_in_grades = Angle(radius, units.arcmin).deg
        else:
            radius_in_grades = radius.to(units.deg).value
        ra = coord.ra.deg
        dec = coord.dec.deg
        query = "select o.observation_id, "\
                "o.start_time, o.end_time, o.start_time_mjd, "\
                "o.end_time_mjd, o.exposure_duration, o.release_date, "\
                "o.run_id, o.program_id, o.set_id, o.collection, "\
                "o.members_number, o.instrument_configuration, "\
                "o.instrument_name, o.obs_type, o.target_moving, "\
                "o.target_name, o.target_description, o.proposal_id, "\
                "o.pi_name, prop.title, pl.metadata_provenance, "\
                "pl.data_product_type, pl.software_version, pos.ra, "\
                "pos.dec, pos.gal_lat, pos.gal_lon, pos.ecl_lat, "\
                "pos.ecl_lon, pos.fov_size, en.wave_central, "\
                "en.wave_bandwidth, en.wave_max, en.wave_min, "\
                "en.filter from ehst.observation o join ehst.proposal "\
                "prop on o.proposal_id=prop.proposal_id join ehst.plane "\
                "pl on pl.observation_id=o.observation_id join "\
                "ehst.position pos on pos.plane_id = pl.plane_id join "\
                "ehst.energy en on en.plane_id=pl.plane_id where "\
                "pl.main_science_plane='true' and 1=CONTAINS(POINT('ICRS', "\
                "pos.ra, pos.dec),CIRCLE('ICRS', {0}, {1}, {2})) order "\
                "by prop.proposal_id desc".format(str(ra), str(dec),
                                                  str(radius_in_grades))
        if verbose:
            log.info(query)
        table = self.query_hst_tap(query=query, async_job=async_job,
                                   output_file=filename,
                                   output_format=output_format,
                                   verbose=verbose)
        return table

    def cone_search_criteria(self, radius, target=None,
                             coordinates=None,
                             calibration_level=None,
                             data_product_type=None,
                             intent=None,
                             obs_collection=None,
                             instrument_name=None,
                             filters=None,
                             async_job=True,
                             filename=None,
                             output_format='votable',
                             save=False,
                             cache=True,
                             verbose=False):
        """
        To execute a cone search defined by a coordinate (an
        astropy.coordinate element or a target name which is resolved),
        a radius and a set of criteria to filter the results. This function
        comprises the outputs of query_target, cone_search and query_criteria
        methods.

        Parameters
        ----------
        radius : float or quantity
            radius in arcmin (int, float) or quantity of the cone_search
        target : str, mandatory if no coordinates is provided
            name of the target, that will act as center in the cone search
        coordinates : astropy.coordinate, mandatory if no target is provided
            coordinates of the center in the cone search
        calibration_level : str or int, optional
            The identifier of the data reduction/processing applied to the
            data. RAW (1), CALIBRATED (2), PRODUCT (3) or AUXILIARY (0)
        data_product_type : str, optional
            High level description of the product.
            image, spectrum or timeseries.
        intent : str, optional
            The intent of the original observer in acquiring this observation.
            SCIENCE or CALIBRATION
        collection : list of str, optional
            List of collections that are available in eHST catalogue.
            HLA, HST
        instrument_name : list of str, optional
            Name(s) of the instrument(s) used to generate the dataset
        filters : list of str, optional
            Name(s) of the filter(s) used to generate the dataset
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        filename : str, default None
            Path and name of the file to store the results.
            If the filename is defined, the file will be
            automatically saved
        output_format : string
            results format. Options are:
            'votable': str, binary VOTable format
            'csv': str, comma-separated values format
        save : bool
            optional, default 'False'
            Flag to save the result in a file. If the filename
            is not defined, it will use a formatted name to save
            the file
        cache : bool
            optional, default 'True'
            Flag to save the results in the local cache
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        astropy.table.Table with the result of the cone_search
        """
        crit_query = self.query_criteria(calibration_level=calibration_level,
                                         data_product_type=data_product_type,
                                         intent=intent,
                                         obs_collection=obs_collection,
                                         instrument_name=instrument_name,
                                         filters=filters,
                                         async_job=True,
                                         get_query=True)
        if crit_query.endswith(")"):
            crit_query = crit_query[:-1] + " AND "
        else:
            crit_query = crit_query + " WHERE ("

        if target and coordinates:
            raise TypeError("Please use only target or coordinates as"
                            "parameter.")
        if target:
            ra, dec = self._query_tap_target(target)
        else:
            coord = self._getCoordInput(coordinates)
            ra = coord.ra.deg
            dec = coord.dec.deg

        if type(radius) == int or type(radius) == float:
            radius_in_grades = Angle(radius, units.arcmin).deg
        else:
            radius_in_grades = radius.to(units.deg).value
        cone_query = "1=CONTAINS(POINT('ICRS', pos.ra, pos.dec),"\
                     "CIRCLE('ICRS', {0}, {1}, {2}))".\
                     format(str(ra), str(dec), str(radius_in_grades))
        query = "{}{})".format(crit_query, cone_query)
        if verbose:
            log.info(query)

        table = self.query_hst_tap(query=query, async_job=async_job,
                                   output_file=filename,
                                   output_format=output_format,
                                   verbose=verbose)
        return table

    def _query_tap_target(self, target):
        try:
            params = {"TARGET_NAME": target,
                      "RESOLVER_TYPE": "SN",
                      "FORMAT": "json"}
            target_response = self._request('GET',
                                            self.target_url,
                                            cache=True,
                                            params=params)
            target_result = target_response.json()['data'][0]
            ra = target_result['RA_DEGREES']
            dec = target_result['DEC_DEGREES']
            return ra, dec
        except KeyError as e:
            raise ValueError("This target cannot be resolved")

    def query_metadata(self, output_format='votable', verbose=False):
        return

    def query_target(self, name, filename=None, output_format='votable',
                     verbose=False):
        """
        It executes a query over EHST and download the xml with the results.

        Parameters
        ----------
        name : string
            target name to be requested, mandatory
        filename : string
            file name to be used to store the metadata, optional, default None
        output_format : string
            optional, default 'votable'
            output format of the query
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        Table with the result of the query. It downloads metadata as a file.
        """

        params = {"RESOURCE_CLASS": "OBSERVATION",
                  "USERNAME": "ehst-astroquery",
                  "SELECTED_FIELDS": "OBSERVATION",
                  "QUERY": "(TARGET.TARGET_NAME=='" + name + "')",
                  "RETURN_TYPE": str(output_format)}
        response = self._request('GET', self.metadata_url, save=True,
                                 cache=True,
                                 params=params)

        if verbose:
            log.info(self.metadata_url + "?RESOURCE_CLASS=OBSERVATION&"
                     "SELECTED_FIELDS=OBSERVATION&QUERY=(TARGET.TARGET_NAME"
                     "=='" + name + "')&USERNAME=ehst-astroquery&"
                     "RETURN_TYPE=" + str(output_format))
            log.info(self.copying_string.format(filename))
        if filename is None:
            filename = "target.xml"

        shutil.move(response, filename)

        return modelutils.read_results_table_from_file(filename,
                                                       str(output_format))

    def query_hst_tap(self, query, async_job=False, output_file=None,
                      output_format="votable", verbose=False):
        """Launches a synchronous or asynchronous job to query the HST tap

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        if async_job:
            job = self._tap.launch_job_async(query=query,
                                             output_file=output_file,
                                             output_format=output_format,
                                             verbose=False,
                                             dump_to_file=output_file
                                             is not None)
        else:
            job = self._tap.launch_job(query=query, output_file=output_file,
                                       output_format=output_format,
                                       verbose=False,
                                       dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def query_criteria(self, calibration_level=None,
                       data_product_type=None, intent=None,
                       obs_collection=None, instrument_name=None,
                       filters=None, async_job=True, output_file=None,
                       output_format="votable", verbose=False,
                       get_query=False):
        """
        Launches a synchronous or asynchronous job to query the HST tap
        using calibration level, data product type, intent, collection,
        instrument name, and filters as criteria to create and execute the
        associated query.

        Parameters
        ----------
        calibration_level : str or int, optional
            The identifier of the data reduction/processing applied to the
            data. RAW (1), CALIBRATED (2), PRODUCT (3) or AUXILIARY (0)
        data_product_type : str, optional
            High level description of the product.
            image, spectrum or timeseries.
        intent : str, optional
            The intent of the original observer in acquiring this observation.
            SCIENCE or CALIBRATION
        collection : list of str, optional
            List of collections that are available in eHST catalogue.
            HLA, HST
        instrument_name : list of str, optional
            Name(s) of the instrument(s) used to generate the dataset
        filters : list of str, optional
            Name(s) of the filter(s) used to generate the dataset
        async_job : bool, optional, default 'True'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        get_query : bool, optional, default 'False'
            flag to return the query associated to the criteria as the result
            of this function.

        Returns
        -------
        A table object
        """

        parameters = []
        if calibration_level is not None:
            parameters.append("p.calibration_level LIKE '%{}%'".format(
                self.__get_calibration_level(calibration_level)))
        if data_product_type is not None:
            if isinstance(data_product_type, str):
                parameters.append("p.data_product_type LIKE '%{}%'".format(
                    data_product_type))
            else:
                raise ValueError("data_product_type must be a string")
        if intent is not None:
            if isinstance(intent, str):
                parameters.append("o.intent LIKE '%{}%'".format(intent))
            else:
                raise ValueError("intent must be a string")
        if self.__check_list_strings(obs_collection):
            parameters.append("(o.collection LIKE '%{}%')".format(
                "%' OR o.collection LIKE '%".join(obs_collection)
            ))
        if self.__check_list_strings(instrument_name):
            parameters.append("(o.instrument_name LIKE '%{}%')".format(
                "%' OR o.instrument_name LIKE '%".join(instrument_name)
            ))
        if self.__check_list_strings(filters):
            parameters.append("(o.instrument_configuration LIKE '%{}%')"
                              .format("%' OR o.instrument_configuration "
                                      "LIKE '%".join(filters)))
        query = "select o.*, p.calibration_level, p.data_product_type, "\
                "pos.ra, pos.dec from ehst.observation AS o JOIN "\
                "ehst.plane as p on o.observation_uuid=p.observation_uuid "\
                "JOIN ehst.position as pos on p.plane_id = pos.plane_id"
        if parameters:
            query += " where({})".format(" AND ".join(parameters))
        if verbose:
            log.info(query)
        if get_query:
            return query
        table = self.query_hst_tap(query=query, async_job=async_job,
                                   output_file=output_file,
                                   output_format=output_format,
                                   verbose=verbose)
        return table

    def __get_calibration_level(self, calibration_level):
        condition = ""
        if(calibration_level is not None):
            if isinstance(calibration_level, str):
                condition = calibration_level
            elif isinstance(calibration_level, int):
                if calibration_level < 4:
                    condition = self.calibration_levels[calibration_level]
                else:
                    raise KeyError("Calibration level must be between 0 and 3")
            else:
                raise KeyError("Calibration level must be either "
                               "a string or an integer")
        return condition

    def __check_list_strings(self, list):
        if list is None:
            return False
        if list and all(isinstance(elem, str) for elem in list):
            return True
        else:
            raise ValueError("One of the lists is empty or there are "
                             "elements that are not strings")

    def get_tables(self, only_names=True, verbose=False):
        """Get the available table in EHST TAP service

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of tables
        """

        tables = self._tap.load_tables(only_names=only_names,
                                       include_shared_tables=False,
                                       verbose=verbose)
        if only_names is True:
            table_names = []
            for t in tables:
                table_names.append(t.name)
            return table_names
        else:
            return tables

    def get_columns(self, table_name, only_names=True, verbose=False):
        """Get the available columns for a table in EHST TAP service

        Parameters
        ----------
        table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of columns
        """

        tables = self._tap.load_tables(only_names=False,
                                       include_shared_tables=False,
                                       verbose=verbose)
        columns = None
        for t in tables:
            if str(t.name) == str(table_name):
                columns = t.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "EHST TAP service")

        if only_names is True:
            column_names = []
            for c in columns:
                column_names.append(c.name)
            return column_names
        else:
            return columns

    def _getCoordInput(self, value):
        if not (isinstance(value, str) or
                isinstance(value, SkyCoord)):
            raise ValueError("Coordinates" +
                             " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            return SkyCoord(value)
        else:
            return value


ESAHubble = ESAHubbleClass()
