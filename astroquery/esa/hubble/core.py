# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
======================
eHST Astroquery Module
======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
from urllib.parse import urlencode

import astroquery.esa.utils.utils as esautils

from astropy import units
from astropy.coordinates import SkyCoord
from astropy.coordinates import Angle
from numpy.ma import MaskedArray

from astroquery.utils.tap import TapPlus
from astroquery.query import BaseQuery
import json
import warnings
from astropy.utils.exceptions import AstropyDeprecationWarning
from astropy.utils.decorators import deprecated

from . import conf
from astroquery import log

__all__ = ['ESAHubble', 'ESAHubbleClass']


class ESAHubbleClass(BaseQuery):
    """
    Class to init ESA Hubble Module and communicate with eHST TAP
    """
    TIMEOUT = conf.TIMEOUT
    calibration_levels = {"AUXILIARY": 0, "RAW": 1, "CALIBRATED": 2,
                          "PRODUCT": 3}
    product_types = ["SCIENCE", "PREVIEW", "THUMBNAIL", "AUXILIARY"]
    copying_string = "Copying file to {0}..."

    def __init__(self, *, tap_handler=None, show_messages=True):
        if tap_handler is None:
            self._tap = TapPlus(url=conf.EHST_TAP_SERVER,
                                data_context='data', client_id="ASTROQUERY")
        else:
            self._tap = tap_handler
        if show_messages:
            self.get_status_messages()

    def download_product(self, observation_id, *, calibration_level=None,
                         filename=None, folder=None, verbose=False, product_type=None):
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
            File name to be used to store the artifact, optional, default
            None
        folder : string
            optional, default current folder
            Local folder to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process
        product_type : string
            type of product retrieval, optional
            SCIENCE, PREVIEW, THUMBNAIL or AUXILIARY
            ------------
            Deprecation Warning: PRODUCT, SCIENCE_PRODUCT or POSTCARD
            are no longer supported.
            ------------

        Returns
        -------
        None. It downloads the observation indicated
        """
        if product_type and product_type in ['PRODUCT', 'SCIENCE_PRODUCT', 'POSTCARD']:
            warnings.warn(
                "PRODUCT, SCIENCE_PRODUCT or POSTCARD product types are no longer supported. "
                "Please use SCIENCE, PREVIEW, THUMBNAIL or AUXILIARY instead.",
                AstropyDeprecationWarning)

        params = {"OBSERVATIONID": observation_id,
                  "TAPCLIENT": "ASTROQUERY",
                  "RETRIEVAL_TYPE": "OBSERVATION"}

        if filename is None:
            filename = observation_id

        if calibration_level:
            params["CALIBRATIONLEVEL"] = calibration_level

        # Product type check to ensure backwards compatibility
        product_type = self.__set_product_type(product_type)
        if product_type:
            self.__validate_product_type(product_type)
            params["PRODUCTTYPE"] = product_type

        filename = self._get_product_filename(product_type, filename)
        output_file = self.__get_download_path(folder, filename)
        self._tap.load_data(params_dict=params, output_file=output_file, verbose=verbose)

        return esautils.check_rename_to_gz(filename=output_file)

    def __get_download_path(self, folder, filename):
        if folder is not None:
            return os.path.join(folder, filename)
        return filename

    def __set_product_type(self, product_type):
        if product_type:
            if 'SCIENCE_PRODUCT' in product_type:
                return 'SCIENCE'
            elif 'PRODUCT' in product_type:
                return None
            elif 'POSTCARD' in product_type:
                return 'PREVIEW'
        return product_type

    def get_member_observations(self, observation_id):
        """
        Returns the related members of simple and composite observations

        Parameters
        ----------
        observation_id : str
            Observation identifier.

        Returns
        -------
        A list of strings with the observation_id of the associated
        observations
        """
        observation_type = self.get_observation_type(observation_id)

        if 'Composite' in observation_type:
            oids = self._select_related_members(observation_id)
        elif 'Simple' in observation_type:
            oids = self._select_related_composite(observation_id)
        else:
            raise ValueError("Invalid observation id")
        return oids

    def get_hap_hst_link(self, observation_id):
        """
        Returns the related members of hap and hst observations

        Parameters
        ----------
        observation_id : string
           id of the observation to be downloaded, mandatory
           The identifier of the observation we want to retrieve, regardless
           of whether it is simple or composite.

        Returns
        -------
        A list of strings with the observation_id of the associated
        observations
        """
        observation_type = self.get_observation_type(observation_id)
        if 'Composite' in observation_type:
            raise ValueError("HAP-HST link is only available for simple observations. Input observation is Composite.")
        elif 'HAP' in observation_type:
            oids = self._select_related_members(observation_id)
        elif 'HST' in observation_type:
            query = ("select observation_id from ehst.observation where obs_type='HAP Simple' "
                     f"and members like '%{observation_id}%'")
            job = self.query_tap(query=query)
            oids = job["observation_id"]
        else:
            raise ValueError("Invalid observation id")
        return oids

    def get_observation_type(self, observation_id):
        """
        Returns the type of an observation

        Parameters
        ----------
        observation_id : string
           id of the observation to be downloaded, mandatory
           The identifier of the observation we want to retrieve, regardless
           of whether it is simple or composite.

        Returns
        -------
        String with the observation type
        """
        if observation_id is None:
            raise ValueError("Please input an observation id")

        query = f"select obs_type from ehst.observation where observation_id='{observation_id}'"
        job = self.query_tap(query=query)
        if any(job["obs_type"]):
            obs_type = self._get_decoded_string(string=job["obs_type"][0])
        else:
            raise ValueError("Invalid Observation ID")
        return obs_type

    def get_observations_from_program(self, program, *, output_file=None,
                                      output_format="votable", verbose=False):
        """
        Retrieves all the observations associated to a program/proposal ID

        Parameters
        ----------
        program : int
            Program or Proposal ID associated to the observations
        output_file : string
            optional, default None
            file name to be used to store the result
        output_format : string
            results format. Options are:
            'votable': str, binary VOTable format
            'csv': str, comma-separated values format
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        return self.query_criteria(proposal=program, output_file=output_file,
                                   output_format=output_format, async_job=False, verbose=verbose)

    def download_files_from_program(self, program, *, folder=None, calibration_level=None,
                                    data_product_type=None, intent=None,
                                    obs_collection=None, instrument_name=None,
                                    filters=None, only_fits=False):
        """
        Download artifacts from EHST. Artifact is a single Hubble product file.

        Parameters
        ----------
        program : int
            Program or Proposal ID associated to the observations
        folder : string
            optional, default current path
            Local folder to store the file
        calibration_level : str or int, optional
            The identifier of the data reduction/processing applied to the
            data. RAW (1), CALIBRATED (2), PRODUCT (3) or AUXILIARY (0)
        data_product_type : str, optional
            High level description of the product.
            image, spectrum or timeseries.
        intent : str, optional
            The intent of the original observer in acquiring this observation.
            SCIENCE or CALIBRATION
        obs_collection : list of str, optional
            List of collections that are available in eHST catalogue.
            HLA, HST, HAP
        instrument_name : str or list of str, optional
            Name(s) of the instrument(s) used to generate the dataset
        filters : list of str, optional
            Name(s) of the filter(s) used to generate the dataset
        only_fits : bool
            optional, default 'False'
            flag to download only FITS files

        Returns
        -------
        None. It downloads the artifact indicated
        """
        observations = self.query_criteria(calibration_level=calibration_level,
                                           data_product_type=data_product_type,
                                           intent=intent, obs_collection=obs_collection,
                                           instrument_name=instrument_name,
                                           filters=filters,
                                           proposal=program,
                                           async_job=False)
        if only_fits:
            self.download_fits_files(observation_id=observations['observation_id'], folder=folder)
        else:
            files = self.get_associated_files(observation_id=observations['observation_id'])
            for file in files['filename']:
                self.download_file(file=file, folder=folder)

    def _select_related_members(self, observation_id):
        query = f"select members from ehst.observation where observation_id='{observation_id}'"
        job = self.query_tap(query=query)
        oids = self._get_decoded_string(string=job["members"][0]).replace("caom:HST/", "").split(" ")
        return oids

    def _select_related_composite(self, observation_id):
        query = f"select observation_id from ehst.observation where members like '%{observation_id}%'"
        job = self.query_tap(query=query)
        oids = job["observation_id"].tolist()
        return oids

    def __validate_product_type(self, product_type):
        if (product_type not in self.product_types):
            raise ValueError("This product_type is not allowed")

    def _get_product_filename(self, product_type, filename):
        if (product_type == "THUMBNAIL" or product_type == "PREVIEW"):
            log.info("This is an image, the filename will be "
                     f"renamed to {filename}.jpg")
            return f"{filename}.jpg"
        else:
            return f"{filename}.zip"

    def get_artifact(self, artifact_id, *, filename=None, folder=None, verbose=False):
        """
        Download artifacts from EHST. Artifact is a single Hubble product file.

        Parameters
        ----------
        artifact_id : string
            filename to be downloaded, mandatory
            The identifier of the physical product (file) we want to retrieve.
        filename : string
            file name to be used to store the artifact, optional, default None
            File name for the artifact
        folder : string
            optional, default current path
            Local folder to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. It downloads the artifact indicated
        """

        return self.download_file(file=artifact_id, filename=filename, folder=folder, verbose=verbose)

    def get_associated_files(self, observation_id, *, verbose=False):
        """
        Retrieves all the files associated to an observation

        Parameters
        ----------
        observation_id : string or list of strings
            id(s) of the observation(s) to be downloaded, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. The file is associated
        """
        if isinstance(observation_id, list) or isinstance(observation_id, MaskedArray):
            observation_id = "', '".join(observation_id)

        query = (f"select art.artifact_id as filename, p.calibration_level, art.archive_class as type, "
                 f"pg_size_pretty(art.size_uncompr) as size_uncompressed from ehst.artifact art "
                 f"join ehst.plane p on p.plane_id = art.plane_id where "
                 f"art.observation_id in ('{observation_id}')")
        return self.query_tap(query=query)

    def download_fits_files(self, observation_id, *, folder=None, verbose=False):
        """
        Retrieves all the FITS files associated to an observation

        Parameters
        ----------
        observation_id : string or list of strings
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        folder : string
            optional, default current path
            Local folder to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. The file is associated
        """
        results = self.get_associated_files(observation_id=observation_id, verbose=verbose)
        for file in [i['filename'] for i in results if i['filename'].endswith('.fits')]:
            if verbose:
                print(f"Downloading {file} ...")
            self.download_file(file=file, filename=file, folder=folder, verbose=verbose)

    def download_file(self, file, *, filename=None, folder=None, verbose=False):
        """
        Download a file from eHST based on its filename.

        Parameters
        ----------
        file : string
            file name of the artifact to be downloaded

        filename : string
            file name to be used to store the file, optional, default None
        folder : string
            optional, default current path
            Local folder to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None. The file is associated
        """

        params = {"RETRIEVAL_TYPE": "PRODUCT", "ARTIFACTID": file, "TAPCLIENT": "ASTROQUERY"}
        if filename is None:
            filename = file
        output_file = self.__get_download_path(folder, filename)
        self._tap.load_data(params_dict=params, output_file=output_file, verbose=verbose)

        return esautils.check_rename_to_gz(filename=output_file)

    def get_postcard(self, observation_id, *, calibration_level="RAW",
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

        params = {"RETRIEVAL_TYPE": "OBSERVATION",
                  "OBSERVATIONID": observation_id,
                  "PRODUCTTYPE": "PREVIEW",
                  "TAPCLIENT": "ASTROQUERY"}
        if calibration_level:
            params["CALIBRATIONLEVEL"] = calibration_level

        if resolution:
            params["PRODUCTTYPE"] = self.__get_product_type_by_resolution(resolution)

        if filename is None:
            filename = observation_id

        self._tap.load_data(params_dict=params, output_file=filename, verbose=verbose)

        return filename

    def __get_product_type_by_resolution(self, resolution):
        if resolution == 256:
            return 'THUMBNAIL'
        elif resolution == 1024:
            return 'PREVIEW'
        else:
            raise ValueError("Resolution must be 256 or 1024")

    def cone_search(self, coordinates, radius, *, filename=None,
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
        if isinstance(radius, int) or isinstance(radius, float):
            radius_in_grades = Angle(radius, units.arcmin).deg
        else:
            radius_in_grades = radius.to(units.deg).value
        ra = coord.ra.deg
        dec = coord.dec.deg
        query = ("select o.observation_id, "
                 "o.start_time, o.end_time, o.start_time_mjd, "
                 "o.end_time_mjd, o.exposure_duration, o.release_date, "
                 "o.run_id, o.program_id, o.set_id, o.collection, "
                 "o.members_number, o.instrument_configuration, "
                 "o.instrument_name, o.obs_type, o.target_moving, "
                 "o.target_name, o.target_description, o.proposal_id, "
                 "o.pi_name, prop.title, pl.metadata_provenance, "
                 "pl.data_product_type, pl.software_version, pos.ra, "
                 "pos.dec, pos.gal_lat, pos.gal_lon, pos.ecl_lat, "
                 "pos.ecl_lon, pos.fov_size, en.wave_central, "
                 "en.wave_bandwidth, en.wave_max, en.wave_min, "
                 "en.filter from ehst.observation o join ehst.proposal "
                 "prop on o.proposal_id=prop.proposal_id join ehst.plane "
                 "pl on pl.observation_id=o.observation_id join "
                 "ehst.position pos on pos.plane_id = pl.plane_id join "
                 "ehst.energy en on en.plane_id=pl.plane_id where "
                 "pl.main_science_plane='true' and 1=CONTAINS(POINT('ICRS', "
                 f"pos.ra, pos.dec),CIRCLE('ICRS', {str(ra)}, {str(dec)}, {str(radius_in_grades)})) order "
                 "by prop.proposal_id desc")

        if verbose:
            log.info(query)
        table = self.query_tap(query=query, async_job=async_job,
                               output_file=filename,
                               output_format=output_format,
                               verbose=verbose)
        return table

    def cone_search_criteria(self, radius, *, target=None,
                             coordinates=None,
                             calibration_level=None,
                             data_product_type=None,
                             intent=None,
                             obs_collection=None,
                             instrument_name=None,
                             filters=None,
                             proposal=None,
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
        proposal : int, optional
            Proposal ID associated to the observations
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
                                         proposal=proposal,
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
            coord = self._query_tap_target(target)
        else:
            coord = self._getCoordInput(coordinates)

        ra = coord.ra.deg
        dec = coord.dec.deg

        if isinstance(radius, int) or isinstance(radius, float):
            radius_in_grades = Angle(radius, units.arcmin).deg
        else:
            radius_in_grades = radius.to(units.deg).value
        cone_query = "1=CONTAINS(POINT('ICRS', ra, dec)," \
                     "CIRCLE('ICRS', {0}, {1}, {2}))". \
            format(str(ra), str(dec), str(radius_in_grades))
        query = "{}{})".format(crit_query, cone_query)
        if verbose:
            log.info(query)

        table = self.query_tap(query=query, async_job=async_job,
                               output_file=filename,
                               output_format=output_format,
                               verbose=verbose)
        return table

    def _query_tap_target(self, target):
        try:
            params = {"TARGET_NAME": target,
                      "RESOLVER_TYPE": "ALL",
                      "FORMAT": "json",
                      "TAPCLIENT": "ASTROQUERY"}

            subContext = conf.EHST_TARGET_ACTION
            connHandler = self._tap._TapPlus__getconnhandler()
            data = urlencode(params)
            target_response = connHandler.execute_secure(subContext, data, verbose=True)
            for line in target_response:
                target_result = json.loads(line.decode("utf-8"))
                if target_result['objects']:
                    ra = target_result['objects'][0]['raDegrees']
                    dec = target_result['objects'][0]['decDegrees']
            return SkyCoord(ra=ra, dec=dec, unit="deg")
        except (ValueError, KeyError):
            raise ValueError("This target cannot be resolved")

    def query_metadata(self, *, output_format='votable', verbose=False):
        return

    def query_target(self, name, *, filename=None, output_format='votable',
                     verbose=False, async_job=False, radius=7):
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
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        radius : int
            optional, default 7
            radius in arcmin (int, float) or quantity of the cone_search

        Returns
        -------
        Table with the result of the query. It downloads metadata as a file.
        """
        coordinates = self._query_tap_target(name)
        table = self.cone_search(coordinates, radius, filename=filename, output_format=output_format,
                                 verbose=verbose, async_job=async_job)

        return table

    def query_tap(self, query, *, async_job=False, output_file=None,
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
                                             verbose=verbose,
                                             dump_to_file=output_file is not None)
        else:
            job = self._tap.launch_job(query=query, output_file=output_file,
                                       output_format=output_format,
                                       verbose=verbose,
                                       dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    @deprecated(since="0.4.7", alternative="query_tap")
    def query_hst_tap(self, query, *, async_job=False, output_file=None,
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
        self.query_tap(query=query, async_job=False, output_file=None,
                       output_format="votable", verbose=False)

    def query_criteria(self, *, calibration_level=None,
                       data_product_type=None, intent=None,
                       obs_collection=None, instrument_name=None,
                       filters=None, proposal=None, async_job=True, output_file=None,
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
        obs_collection : list of str, optional
            List of collections that are available in eHST catalogue.
            HLA, HST, HAP
        instrument_name : str or list of str, optional
            Name(s) of the instrument(s) used to generate the dataset
        filters : list of str, optional
            Name(s) of the filter(s) used to generate the dataset
        proposal : int, optional
            Proposal ID associated to the observations
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
            parameters.append("calibration_level={}".format(
                self.__get_calibration_level(calibration_level)))
        if data_product_type is not None:
            if isinstance(data_product_type, str):
                parameters.append("data_product_type LIKE '%{}%'".format(
                    data_product_type))
            else:
                raise ValueError("data_product_type must be a string")
        if intent is not None:
            if isinstance(intent, str):
                parameters.append("intent LIKE '%{}%'".format(intent.lower()))
            else:
                raise ValueError("intent must be a string")
        if proposal is not None:
            if isinstance(proposal, int):
                parameters.append("proposal_id = '{}'".format(proposal))
            else:
                raise ValueError("Proposal ID must be an integer")
        if self.__check_list_strings(obs_collection):
            parameters.append("(collection LIKE '%{}%')".format(
                "%' OR collection LIKE '%".join(obs_collection)
            ))
        if self.__check_list_strings(instrument_name):
            if isinstance(instrument_name, str):
                instrument_name = [instrument_name]
            parameters.append("(instrument_name LIKE '%{}%')".format(
                "%' OR instrument_name LIKE '%".join(instrument_name)
            ))
        if self.__check_list_strings(filters):
            parameters.append("(filter LIKE '%{}%')"
                              .format("%' OR filter "
                                      "LIKE '%".join(filters)))
        query = "select * from ehst.archive"
        if parameters:
            query += " where({})".format(" AND ".join(parameters))
        if verbose:
            log.info(query)
        if get_query:
            return query
        table = self.query_tap(query=query, async_job=async_job,
                               output_file=output_file,
                               output_format=output_format,
                               verbose=verbose)
        return table

    def __get_calibration_level(self, calibration_level):
        condition = ""
        if (calibration_level is not None):
            if isinstance(calibration_level, int):
                if calibration_level < 4:
                    condition = calibration_level
                else:
                    raise KeyError("Calibration level must be between 0 and 3")
            elif isinstance(calibration_level, str):
                condition = self.calibration_levels[calibration_level]
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

    def get_tables(self, *, only_names=True, verbose=False):
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

    def get_status_messages(self):
        """Retrieve the messages to inform users about
        the status of eHST TAP
        """

        try:
            subContext = conf.EHST_MESSAGES
            connHandler = self._tap._TapPlus__getconnhandler()
            response = connHandler.execute_tapget(subContext, verbose=False)
            if response.status == 200:
                for line in response:
                    string_message = line.decode("utf-8")
                    print(string_message[string_message.index('=') + 1:])
        except OSError:
            print("Status messages could not be retrieved")

    def get_columns(self, table_name, *, only_names=True, verbose=False):
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
        if not (isinstance(value, str) or isinstance(value, SkyCoord)):
            raise ValueError("Coordinates must be either a string or astropy.coordinates")
        if isinstance(value, str):
            return SkyCoord(value)
        else:
            return value

    def _get_decoded_string(self, string):
        try:
            return string.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return string

    def get_datalabs_path(self, filename, default_volume=None):
        """Get the available columns for a table in EHST TAP service

        Parameters
        ----------
        filename : string, mandatory, default None
            file name to search for its full path
        default_volume : string, optional, default None
            Default folder name in datalabs. If None, it is filled automatically

        Returns
        -------
        The complete path of the file name in Datalabs
        """

        # FITS files are always compressed
        if filename.endswith('.fits'):
            filename = f"{filename}.gz"

        query = f"select file_path from ehst.artifact where file_name = '{filename}'"
        job = self.query_tap(query=query)
        if job is None:
            return None

        query2 = f"select observation_id from ehst.artifact where file_name = '{filename}'"
        job2 = self.query_tap(query=query2)
        if job2 is None:
            return None

        observation_id = job2["observation_id"][0]
        query3 = f"select instrument_name from ehst.observation where observation_id = '{observation_id}'"
        job3 = self.query_tap(query=query3)
        if job3 is None:
            return None

        instrument_name = job3["instrument_name"][0]

        # Output example for path: /hstdata/hstdata_i/i/b4x/04, or hstdata_i/i/b4x/04 for path_parsed
        path = self._get_decoded_string(string=job["file_path"][0])
        path_parsed = path.split("hstdata/", 1)[1]

        # Automatic fill: convert /hstdata/hstdata_i/i/b4x/04 to /data/user/hub_hstdata_i/i/b4x/04
        if default_volume is None:
            full_path = "/data/user/hub_" + path_parsed + "/" + filename
            file_exists = os.path.exists(full_path)

        # Use the path provided by the user: convert /hstdata/hstdata_i/i/b4x/04 to /data/user/myPath/i/b4x/04
        else:
            path_parsed = path_parsed.split("/", 1)[1]
            full_path = "/data/user/" + default_volume + "/" + path_parsed + "/" + filename
            file_exists = os.path.exists(full_path)

        if not file_exists:
            warnings.warn(f"File {filename} is not accessible. Please ensure the {instrument_name} "
                          "volume is mounted in your ESA Datalabs instance.")
        return full_path


ESAHubble = ESAHubbleClass()
