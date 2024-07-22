# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=======================
eJWST Astroquery Module
=======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import binascii
import gzip
import os
import shutil
import tarfile as esatar
import zipfile
from datetime import datetime, timezone
from urllib.parse import urlencode

import astroquery.esa.utils.utils as esautils

from astropy import log
from astropy import units
from astropy.coordinates import Angle, SkyCoord
from astropy.table import vstack
from astropy.units import Quantity
from requests.exceptions import ConnectionError

from astroquery.exceptions import RemoteServiceError
from astroquery.ipac.ned import Ned
from astroquery.query import BaseQuery
from astroquery.simbad import Simbad
from astroquery.utils import commons
from astroquery.utils.tap import TapPlus
from astroquery.vizier import Vizier
from . import conf
from .data_access import JwstDataHandler


__all__ = ['Jwst', 'JwstClass']


# We do trust the ESA tar files, this is to avoid the new to Python 3.12 deprecation warning
# https://docs.python.org/3.12/library/tarfile.html#tarfile-extraction-filter
if hasattr(esatar, "fully_trusted_filter"):
    esatar.TarFile.extraction_filter = staticmethod(esatar.fully_trusted_filter)


class JwstClass(BaseQuery):

    """
    Proxy class to default TapPlus object (pointing to JWST Archive)
    """

    JWST_DEFAULT_COLUMNS = ['observationid', 'calibrationlevel', 'public',
                            'dataproducttype', 'instrument_name',
                            'energy_bandpassname', 'target_name', 'target_ra',
                            'target_dec', 'position_bounds_center',
                            'position_bounds_spoly']

    PLANE_DATAPRODUCT_TYPES = ['image', 'cube', 'measurements', 'spectrum']
    ARTIFACT_PRODUCT_TYPES = ['info', 'thumbnail', 'auxiliary', 'science',
                              'preview']
    INSTRUMENT_NAMES = ['NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS']
    TARGET_RESOLVERS = ['ALL', 'SIMBAD', 'NED', 'VIZIER']
    CAL_LEVELS = ['ALL', 1, 2, 3, -1]
    REQUESTED_OBSERVATION_ID = "Missing required argument: 'observation_id'"

    def __init__(self, *, tap_plus_handler=None, data_handler=None, show_messages=True):
        if tap_plus_handler is None:
            self.__jwsttap = TapPlus(url=conf.JWST_TAP_SERVER,
                                     data_context='data', client_id='ASTROQUERY')
        else:
            self.__jwsttap = tap_plus_handler

        if data_handler is None:
            self.__jwstdata = JwstDataHandler(
                base_url=conf.JWST_DATA_SERVER)
        else:
            self.__jwstdata = data_handler

        if show_messages:
            self.get_status_messages()

    def load_tables(self, *, only_names=False, include_shared_tables=False,
                    verbose=False):
        """Loads all public tables
        TAP & TAP+

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        include_shared_tables : bool, TAP+, optional, default 'False'
            True to include shared tables
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of table objects
        """
        return self.__jwsttap.load_tables(only_names=only_names,
                                          include_shared_tables=include_shared_tables,
                                          verbose=verbose)

    def load_table(self, table, *, verbose=False):
        """Loads the specified table
        TAP+ only

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        return self.__jwsttap.load_table(table, verbose=verbose)

    def launch_job(self, query, *, name=None, output_file=None,
                   output_format="votable", verbose=False, dump_to_file=False,
                   background=False, upload_resource=None, upload_table_name=None,
                   async_job=False):
        """Launches a synchronous or asynchronous job
        TAP & TAP+

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional, default None
            name of the job to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format. Options are:
            'votable': str, binary VOTable format
            'csv': str, comma-separated values format
            'fits': str, FITS format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided
            Default None
            resource temporary table name associated to the uploaded resource
        async_job: bool, optional, default 'False'
            tag to execute the job in sync or async mode

        Returns
        -------
        A Job object
        """
        if async_job:
            return (self.__jwsttap.launch_job_async(query=query,
                                                    name=name,
                                                    output_file=output_file,
                                                    output_format=output_format,
                                                    verbose=verbose,
                                                    dump_to_file=dump_to_file,
                                                    background=background,
                                                    upload_resource=upload_resource,
                                                    upload_table_name=upload_table_name))
        else:
            return self.__jwsttap.launch_job(query=query,
                                             name=name,
                                             output_file=output_file,
                                             output_format=output_format,
                                             verbose=verbose,
                                             dump_to_file=dump_to_file,
                                             upload_resource=upload_resource,
                                             upload_table_name=upload_table_name)

    def load_async_job(self, *, jobid=None, name=None, verbose=False):
        """Loads an asynchronous job
        TAP & TAP+

        Parameters
        ----------
        jobid : str, mandatory if no name is provided, default None
            job identifier
        name : str, mandatory if no jobid is provided, default None
            job name
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """
        return self.__jwsttap.load_async_job(jobid=jobid, name=name, verbose=verbose)

    def search_async_jobs(self, *, jobfilter=None, verbose=False):
        """Searches for jobs applying the specified filter
        TAP+ only

        Parameters
        ----------
        jobfilter : JobFilter, optional, default None
            job filter
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        return self.__jwsttap.search_async_jobs(jobfilter=jobfilter, verbose=verbose)

    def list_async_jobs(self, *, verbose=False):
        """Returns all the asynchronous jobs
        TAP & TAP+

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        return self.__jwsttap.list_async_jobs(verbose=verbose)

    def query_region(self, coordinate, *,
                     radius=None,
                     width=None,
                     height=None,
                     observation_id=None,
                     cal_level="Top",
                     prod_type=None,
                     instrument_name=None,
                     filter_name=None,
                     proposal_id=None,
                     only_public=False,
                     show_all_columns=False,
                     async_job=False, verbose=False):
        """Launches a query region job in sync/async mode
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width' nor 'height'
            are provided
            radius (deg)
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        observation_id : str, optional, default None
            get the observation given by its ID.
        cal_level : object, optional, default 'Top'
            get the planes with the given calibration level. Options are:
            'Top': str, only the planes with the highest calibration level
            1,2,3: int, the given calibration level
        prod_type : str, optional, default None
            get the observations providing the given product type. Options are:
            'image','cube','measurements','spectrum': str, only results of the
            given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name.
            Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of
            the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output.
            Default behaviour is to show the most representative columns only
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        coord = self.__get_coord_input(value=coordinate, msg="coordinate")
        job = None
        if radius is not None:
            job = self.cone_search(coordinate=coord,
                                   radius=radius,
                                   only_public=only_public,
                                   observation_id=observation_id,
                                   cal_level=cal_level,
                                   prod_type=prod_type,
                                   instrument_name=instrument_name,
                                   filter_name=filter_name,
                                   proposal_id=proposal_id,
                                   show_all_columns=show_all_columns,
                                   async_job=async_job, verbose=verbose)
        else:
            raHours, dec = commons.coord_to_radec(coord)
            ra = raHours * 15.0  # Converts to degrees
            widthQuantity = self.__get_quantity_input(value=width, msg="width")
            heightQuantity = self.__get_quantity_input(value=height, msg="height")
            widthDeg = widthQuantity.to(units.deg)
            heightDeg = heightQuantity.to(units.deg)

            obsid_cond = self.__get_observationid_condition(value=observation_id)
            cal_level_condition = self.__get_callevel_condition(cal_level=cal_level)
            public_condition = self.__get_public_condition(only_public=only_public)
            prod_cond = self.__get_plane_dataproducttype_condition(prod_type=prod_type)
            instr_cond = self.__get_instrument_name_condition(value=instrument_name)
            filter_name_cond = self.__get_filter_name_condition(value=filter_name)
            props_id_cond = self.__get_proposal_id_condition(value=proposal_id)

            columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
            if show_all_columns:
                columns = '*'

            query = (f"SELECT DISTANCE(POINT('ICRS',"
                     f"{str(conf.JWST_MAIN_TABLE_RA)},"
                     f"{str(conf.JWST_MAIN_TABLE_DEC)} ), "
                     f"POINT('ICRS',{str(ra)},{str(dec)} )) "
                     f"AS dist, {columns} "
                     f"FROM {str(conf.JWST_MAIN_TABLE)} "
                     f"WHERE CONTAINS("
                     f"POINT('ICRS',"
                     f"{str(conf.JWST_MAIN_TABLE_RA)},"
                     f"{str(conf.JWST_MAIN_TABLE_DEC)}),"
                     f"BOX('ICRS',{str(ra)},{str(dec)}, "
                     f"{str(widthDeg.value)}, "
                     f"{str(heightDeg.value)}))=1 "
                     f"{obsid_cond}"
                     f"{cal_level_condition}"
                     f"{public_condition}"
                     f"{prod_cond}"
                     f"{instr_cond}"
                     f"{filter_name_cond}"
                     f"{props_id_cond}"
                     f"ORDER BY dist ASC")
            if verbose:
                print(query)
            if async_job:
                job = self.__jwsttap.launch_job_async(query=query, verbose=verbose)
            else:
                job = self.__jwsttap.launch_job(query=query, verbose=verbose)
        return job.get_results()

    def cone_search(self, coordinate, radius, *,
                    observation_id=None,
                    cal_level="Top",
                    prod_type=None,
                    instrument_name=None,
                    filter_name=None,
                    proposal_id=None,
                    only_public=False,
                    show_all_columns=False,
                    async_job=False,
                    background=False,
                    output_file=None,
                    output_format="votable",
                    verbose=False,
                    dump_to_file=False):
        """Cone search sorted by distance in sync/async mode
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        observation_id : str, optional, default None
            get the observation given by its ID.
        cal_level : object, optional, default 'Top'
            get the planes with the given calibration level. Options are:
            'Top': str, only the planes with the highest calibration level
            1,2,3: int, the given calibration level
        prod_type : str, optional, default None
            get the observations providing the given product type. Options are:
            'image','cube','measurements','spectrum': str, only results of
            the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name.
            Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results
            of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour
            is to show the most representative columns only
        async_job : bool, optional, default 'False'
            executes the job in asynchronous/synchronous mode (default
            synchronous)
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format. Options are:
            'votable': str, binary VOTable format
            'csv': str, comma-separated values format
            'fits': str, FITS format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory

        Returns
        -------
        A Job object
        """
        coord = self.__get_coord_input(value=coordinate, msg="coordinate")
        ra_hours, dec = commons.coord_to_radec(coord)
        ra = ra_hours * 15.0  # Converts to degrees

        obsid_condition = self.__get_observationid_condition(value=observation_id)
        cal_level_condition = self.__get_callevel_condition(cal_level=cal_level)
        public_condition = self.__get_public_condition(only_public=only_public)
        prod_type_cond = self.__get_plane_dataproducttype_condition(prod_type=prod_type)
        inst_name_cond = self.__get_instrument_name_condition(value=instrument_name)
        filter_name_condition = self.__get_filter_name_condition(value=filter_name)
        proposal_id_condition = self.__get_proposal_id_condition(value=proposal_id)

        columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
        if show_all_columns:
            columns = '*'

        if radius is not None:
            radius_quantity = self.__get_quantity_input(value=radius, msg="radius")
            radius_deg = Angle(radius_quantity).to_value(units.deg)

        query = (f"SELECT DISTANCE(POINT('ICRS',"
                 f"{str(conf.JWST_MAIN_TABLE_RA)},"
                 f"{str(conf.JWST_MAIN_TABLE_DEC)}), "
                 f"POINT('ICRS',{str(ra)},{str(dec)})) AS dist, {columns} "
                 f"FROM {str(conf.JWST_MAIN_TABLE)} WHERE CONTAINS("
                 f"POINT('ICRS',{str(conf.JWST_MAIN_TABLE_RA)},"
                 f"{str(conf.JWST_MAIN_TABLE_DEC)}),"
                 f"CIRCLE('ICRS',{str(ra)},{str(dec)}, "
                 f"{str(radius_deg)}))=1"
                 f"{obsid_condition}"
                 f"{cal_level_condition}"
                 f"{public_condition}"
                 f"{prod_type_cond}"
                 f"{inst_name_cond}"
                 f"{filter_name_condition}"
                 f"{proposal_id_condition}"
                 f"ORDER BY dist ASC")
        if async_job:
            return self.__jwsttap.launch_job_async(query=query,
                                                   output_file=output_file,
                                                   output_format=output_format,
                                                   verbose=verbose,
                                                   dump_to_file=dump_to_file,
                                                   background=background)
        else:
            return self.__jwsttap.launch_job(query=query,
                                             output_file=output_file,
                                             output_format=output_format,
                                             verbose=verbose,
                                             dump_to_file=dump_to_file)

    def query_target(self, target_name, *, target_resolver="ALL",
                     radius=None,
                     width=None,
                     height=None,
                     observation_id=None,
                     cal_level="Top",
                     prod_type=None,
                     instrument_name=None,
                     filter_name=None,
                     proposal_id=None,
                     only_public=False,
                     show_all_columns=False,
                     async_job=False,
                     verbose=False):
        """Searches for a specific target defined by its name and other parameters
        TAP & TAP+

        Parameters
        ----------
        target_name : str, mandatory
            name of the target that will be used as center point
        target_resolver : str, optional, default ALL
            resolver used to associate the target name with its coordinates.
            The ALL option evaluates a "SIMBAD then NED then VIZIER"
            approach. Options are: ALL, SIMBAD, NED, VIZIER.
        radius : astropy.units, required if no 'width' nor 'height' are
            provided.
            radius (deg)
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        observation_id : str, optional, default None
            get the observation given by its ID.
        cal_level : object, optional, default 'Top'
            get the planes with the given calibration level. Options are:
            'Top': str, only the planes with the highest calibration level
            1,2,3: int, the given calibration level
        prod_type : str, optional, default None
            get the observations providing the given product type. Options are:
            'image','cube','measurements','spectrum': str, only results of the
            given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name.
            Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results
            of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour
            is to show the most
            representative columns only
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        coordinates = self.resolve_target_coordinates(target_name=target_name,
                                                      target_resolver=target_resolver)
        return self.query_region(coordinate=coordinates,
                                 radius=radius,
                                 width=width,
                                 height=height,
                                 observation_id=observation_id,
                                 cal_level=cal_level,
                                 prod_type=prod_type,
                                 instrument_name=instrument_name,
                                 filter_name=filter_name,
                                 proposal_id=proposal_id,
                                 only_public=only_public,
                                 async_job=async_job,
                                 show_all_columns=show_all_columns,
                                 verbose=verbose)

    def resolve_target_coordinates(self, target_name, target_resolver):
        if target_resolver not in self.TARGET_RESOLVERS:
            raise ValueError("This target resolver is not allowed")

        result_table = None
        if target_resolver == "ALL" or target_resolver == "SIMBAD":
            try:
                result_table = Simbad.query_object(target_name)
                # new simbad behavior does not return None but an empty table
                if len(result_table) == 0:
                    result_table = None
                return SkyCoord((f'{result_table["ra"][0]} '
                                 f'{result_table["dec"][0]}'),
                                unit=(units.deg,
                                      units.deg), frame="icrs")
            except (KeyError, TypeError, ConnectionError):
                log.info("SIMBAD could not resolve this target")
        if target_resolver == "ALL" or target_resolver == "NED":
            try:
                result_table = Ned.query_object(target_name)
                return SkyCoord(result_table["RA"][0],
                                result_table["DEC"][0],
                                unit="deg", frame="fk5")
            except (RemoteServiceError, KeyError, ConnectionError):
                log.info("NED could not resolve this target")
        if target_resolver == "ALL" or target_resolver == "VIZIER":
            try:
                result_table = Vizier.query_object(target_name,
                                                   catalog="II/336/apass9")[0]
                # Sorted to use the record with the least uncertainty
                result_table.sort(["e_RAJ2000", "e_DEJ2000"])
                return SkyCoord(result_table["RAJ2000"][0],
                                result_table["DEJ2000"][0],
                                unit="deg", frame="fk5")
            except (IndexError, AttributeError, ConnectionError):
                log.info("VIZIER could not resolve this target")
        if result_table is None:
            raise ValueError(f"This target name cannot be determined with"
                             f" this resolver: {target_resolver}")

    def remove_jobs(self, jobs_list, *, verbose=False):
        """Removes the specified jobs
        TAP+

        Parameters
        ----------
        jobs_list : str, mandatory
            jobs identifiers to be removed
        verbose : bool, optional, default 'False'
            flag to display information about the process

        """
        return self.__jwsttap.remove_jobs(jobs_list=jobs_list, verbose=verbose)

    def save_results(self, job, *, verbose=False):
        """Saves job results
        TAP & TAP+

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.save_results(job=job, verbose=verbose)

    def login(self, *, user=None, password=None, credentials_file=None,
              token=None, verbose=False):
        """Performs a login.
        TAP+ only
        User and password can be used or a file that contains user name and
        password (2 lines: one for user name and the following one for the
        password)

        Parameters
        ----------
        user : str, mandatory if 'file' is not provided, default None
            login name
        password : str, mandatory if 'file' is not provided, default None
            user password
        credentials_file : str, mandatory if no 'user' & 'password' are
            provided
            file containing user and password in two lines
        token: str, optional
            MAST token to have access to propietary data
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        self.__jwsttap.login(user=user,
                             password=password,
                             credentials_file=credentials_file,
                             verbose=verbose)
        if token:
            self.set_token(token=token)

    def logout(self, *, verbose=False):
        """Performs a logout
        TAP+ only

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.logout(verbose=verbose)

    def set_token(self, token):
        """Links a MAST token to the logged user

        Parameters
        ----------
        token: str, mandatory
            MAST token to have access to propietary data
        """
        subContext = conf.JWST_TOKEN
        data = urlencode({"token": token})
        connHandler = self.__jwsttap._TapPlus__getconnhandler()
        response = connHandler.execute_secure(subcontext=subContext, data=data, verbose=True)
        if response.status == 403:
            print("ERROR: MAST tokens cannot be assigned or requested by anonymous users")
        elif response.status == 500:
            print("ERROR: Server error when setting the token")
        else:
            print("MAST token has been set successfully")

    def get_status_messages(self):
        """Retrieve the messages to inform users about
        the status of JWST TAP
        """

        try:
            subContext = conf.JWST_MESSAGES
            connHandler = self.__jwsttap._TapPlus__getconnhandler()
            response = connHandler.execute_tapget(subContext, verbose=False)
            if response.status == 200:
                for line in response:
                    string_message = line.decode("utf-8")
                    print(string_message[string_message.index('=') + 1:])
        except OSError:
            print("Status messages could not be retrieved")

    def get_product_list(self, *, observation_id=None,
                         cal_level="ALL",
                         product_type=None):
        """Get the list of products of a given JWST observation_id.

        Parameters
        ----------
        observation_id : str, mandatory
            Observation identifier.
        cal_level : str or int, optional
            Calibration level. Default value is 'ALL', to download all the
            products associated to this observation_id and lower processing
            levels. Requesting more accurate levels than the one associated
            to the observation_id is not allowed (as level 3 observations are
            composite products based on level 2 products). To request upper
            levels, please use get_related_observations functions first.
            Possible values: 'ALL', 3, 2, 1, -1
        product_type : str, optional, default None
            List only products of the given type. If None, all products are
            listed. Possible values: 'thumbnail', 'preview', 'info',
            'auxiliary', 'science'.

        Returns
        -------
        The list of products (astropy.table).
        """
        self.__validate_cal_level(cal_level=cal_level)

        if observation_id is None:
            raise ValueError(self.REQUESTED_OBSERVATION_ID)
        plane_ids, max_cal_level = self._get_plane_id(observation_id=observation_id)
        if cal_level == 3 and cal_level > max_cal_level:
            raise ValueError("Requesting upper levels is not allowed")
        list = self._get_associated_planes(plane_ids=plane_ids,
                                           cal_level=cal_level,
                                           max_cal_level=max_cal_level,
                                           is_url=False)

        query = (f"select distinct a.uri, a.artifactid, a.filename, "
                 f"a.contenttype, a.producttype, p.calibrationlevel, "
                 f"p.public FROM {conf.JWST_PLANE_TABLE} p JOIN "
                 f"{conf.JWST_ARTIFACT_TABLE} a ON (p.planeid=a.planeid) "
                 f"WHERE a.planeid IN {list}"
                 f"{self.__get_artifact_producttype_condition(product_type=product_type)};")
        job = self.__jwsttap.launch_job(query=query)
        return job.get_results()

    def __validate_cal_level(self, cal_level):
        if (cal_level not in self.CAL_LEVELS):
            raise ValueError("This calibration level is not valid")

    def _get_associated_planes(self, plane_ids, cal_level,
                               max_cal_level, is_url):
        if (cal_level == max_cal_level):
            if (not is_url):
                list = "('{}')".format("', '".join(plane_ids))
            else:
                list = "{}".format(",".join(plane_ids))
            return list
        else:
            plane_list = []
            for plane_id in plane_ids:
                siblings = self.__get_sibling_planes(planeid=plane_id, cal_level=cal_level)
                members = self.__get_member_planes(planeid=plane_id, cal_level=cal_level)
                plane_id_table = vstack([siblings, members])
                plane_list.extend(plane_id_table['product_planeid'])
            if (not is_url):
                list = "('{}')".format("', '".join(plane_list))
            else:
                list = "{}".format(",".join(plane_list))
        return list

    def _get_plane_id(self, observation_id):
        try:
            planeids = []
            query_plane = (f"select distinct m.planeid, m.calibrationlevel "
                           f"from {conf.JWST_MAIN_TABLE} m where "
                           f"m.observationid = '{observation_id}'")
            job = self.__jwsttap.launch_job(query=query_plane)
            job.get_results().sort(["calibrationlevel"])
            job.get_results().reverse()
            max_cal_level = job.get_results()["calibrationlevel"][0]
            for row in job.get_results():
                if row["calibrationlevel"] == max_cal_level:
                    planeids.append(
                        JwstClass.get_decoded_string(row["planeid"]))
            return planeids, max_cal_level
        except Exception:
            raise ValueError("This observation_id does not exist in "
                             "JWST database")

    def __get_sibling_planes(self, planeid, *, cal_level='ALL'):
        where_clause = ""
        if (cal_level == "ALL"):
            where_clause = "WHERE sp.calibrationlevel<=p.calibrationlevel "\
                           "AND p.planeid ="
        else:
            where_clause = (f"WHERE sp.calibrationlevel={cal_level} AND "
                            f"p.planeid =")
        try:
            query_siblings = (f"SELECT o.observationuri, p.planeid, "
                              f"p.calibrationlevel, sp.planeid as "
                              f"product_planeid, sp.calibrationlevel as "
                              f"product_level FROM "
                              f"{conf.JWST_OBSERVATION_TABLE} o JOIN "
                              f"{conf.JWST_PLANE_TABLE} p ON "
                              f"p.obsid=o.obsid JOIN "
                              f"{conf.JWST_PLANE_TABLE} sp ON "
                              f"sp.obsid=o.obsid {where_clause}'{planeid}'")
            job = self.__jwsttap.launch_job(query=query_siblings)
            return job.get_results()
        except Exception as e:
            raise ValueError(e)

    def __get_member_planes(self, planeid, *, cal_level='ALL'):
        where_clause = ""
        if (cal_level == "ALL"):
            where_clause = "WHERE p.planeid ="
        else:
            where_clause = (f"WHERE mp.calibrationlevel={cal_level} AND "
                            f"p.planeid =")
        try:
            query_members = (f"SELECT o.observationuri, p.planeid, "
                             f"p.calibrationlevel, mp.planeid as "
                             f"product_planeid, mp.calibrationlevel as "
                             f"product_level FROM "
                             f"{conf.JWST_OBSERVATION_TABLE} o JOIN "
                             f"{conf.JWST_PLANE_TABLE} p on "
                             f"o.obsid=p.obsid JOIN "
                             f"{conf.JWST_OBS_MEMBER_TABLE} m on "
                             f"o.obsid=m.parentid JOIN "
                             f"{conf.JWST_OBSERVATION_TABLE} "
                             f"mo on m.memberid=mo.observationuri JOIN "
                             f"{conf.JWST_PLANE_TABLE} mp on "
                             f"mo.obsid=mp.obsid "
                             f"{where_clause}'{planeid}'")
            job = self.__jwsttap.launch_job(query=query_members)
            return job.get_results()
        except Exception as e:
            raise ValueError(e)

    def get_related_observations(self, observation_id):
        """In case of processing levels < 3, get the list of level 3
        products that make use of a given JWST observation_id. In case of
        processing level 3, retrieves the list of products used to create
        this composite observation

        Parameters
        ----------
        observation_id : str, mandatory
            Observation identifier.

        Returns
        -------
        A list of strings with the observation_id of the associated
        observations that can be used in get_product_list and
        get_obs_products functions
        """
        if observation_id is None:
            raise ValueError(self.REQUESTED_OBSERVATION_ID)
        query_upper = (f"select * from {conf.JWST_MAIN_TABLE} m "
                       f"where m.members like "
                       f"'%{observation_id}%'")
        job = self.__jwsttap.launch_job(query=query_upper)
        if any(job.get_results()["observationid"]):
            oids = job.get_results()["observationid"]
        else:
            query_members = (f"select m.members from {conf.JWST_MAIN_TABLE} "
                             f"m where m.observationid"
                             f"='{observation_id}'")
            job = self.__jwsttap.launch_job(query=query_members)
            oids = JwstClass.get_decoded_string(
                job.get_results()["members"][0]).\
                replace("caom:JWST/", "").split(" ")
        return oids

    def get_product(self, *, artifact_id=None, file_name=None):
        """Get a JWST product given its Artifact ID or File name.

        Parameters
        ----------
        artifact_id : str, mandatory (if no file_name is provided)
            Artifact ID of the product.
        file_name : str, mandatory (if no artifact_id is provided)

        Returns
        -------
        local_path : str
            Returns the local path that the file was downloaded to.
        """

        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        params_dict['TAPCLIENT'] = 'ASTROQUERY'

        self.__check_product_input(artifact_id=artifact_id,
                                   file_name=file_name)

        if file_name is None:
            try:
                output_file_name = self._query_get_product(artifact_id=artifact_id)
                err_msg = str(artifact_id)
            except Exception as exx:
                raise ValueError(f"Cannot retrieve product for artifact_id {artifact_id}: {exx}")
        else:
            output_file_name = str(file_name)
            err_msg = str(file_name)

        if artifact_id is not None:
            params_dict['ARTIFACTID'] = str(artifact_id)
        else:
            try:
                params_dict['ARTIFACTID'] = (self._query_get_product(
                                             file_name=file_name))
            except Exception as exx:
                raise ValueError(f"Cannot retrieve product for file_name {file_name}: {exx}")

        try:
            self.__jwsttap.load_data(params_dict=params_dict,
                                     output_file=output_file_name)
        except Exception as exx:
            log.info("error")
            raise ValueError(f"Error retrieving product for {err_msg}: {exx}")

        return esautils.check_rename_to_gz(filename=output_file_name)

    def _query_get_product(self, *, artifact_id=None, file_name=None):
        if file_name:
            query_artifactid = (f"select * from {conf.JWST_ARTIFACT_TABLE} "
                                f"a where a.filename = "
                                f"'{file_name}'")
            job = self.__jwsttap.launch_job(query=query_artifactid)
            return JwstClass.get_decoded_string(
                job.get_results()['artifactid'][0])
        else:
            query_filename = (f"select * from {conf.JWST_ARTIFACT_TABLE} a "
                              f"where a.artifactid = "
                              f"'{artifact_id}'")
            job = self.__jwsttap.launch_job(query=query_filename)
            return JwstClass.get_decoded_string(
                job.get_results()['filename'][0])

    def __check_product_input(self, artifact_id, file_name):
        if artifact_id is None and file_name is None:
            raise ValueError("Missing required argument: "
                             "'artifact_id' or 'file_name'")

    def get_obs_products(self, *, observation_id=None, cal_level="ALL",
                         product_type=None, output_file=None):
        """Get a JWST product given its observation ID.

        Parameters
        ----------
        observation_id : str, mandatory
            Observation identifier.
        cal_level : str or int, optional
            Calibration level. Default value ia 'ALL', to download all the
            products associated to this observation_id and lower levels.
            Requesting more accurate levels than the one associated to the
            observation_id is not allowed (as level 3 observations are
            composite products based on level 2 products). To request upper
            levels, please use get_related_observations functions first.
            Possible values: 'ALL', 3, 2, 1, -1
        product_type : str or list, optional, default None
            If the string or at least one element of the list is empty, the value is replaced by None.
            With None, all products will be downloaded.
            Possible string values: 'thumbnail', 'preview', 'auxiliary', 'science' or 'info'.
            Posible list values: any combination of string values.
        output_file : str, optional
            Output file. If no value is provided, a temporary one is created.

        Returns
        -------
        local_path : str
            Returns the local path where the product(s) are saved.
        """

        if (isinstance(product_type, list) and '' in product_type) or not product_type:
            product_type = None
        if observation_id is None:
            raise ValueError(self.REQUESTED_OBSERVATION_ID)
        plane_ids, max_cal_level = self._get_plane_id(observation_id=observation_id)

        if (cal_level == 3 and cal_level > max_cal_level):
            raise ValueError("Requesting upper levels is not allowed")

        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'OBSERVATION'
        params_dict['TAPCLIENT'] = 'ASTROQUERY'

        plane_ids = self._get_associated_planes(plane_ids=plane_ids,
                                                cal_level=cal_level,
                                                max_cal_level=max_cal_level,
                                                is_url=True)
        params_dict['planeid'] = plane_ids

        if type(product_type) is list:
            tap_product_type = ",".join(str(elem) for elem in product_type)
        else:
            tap_product_type = product_type

        self.__set_additional_parameters(param_dict=params_dict,
                                         cal_level=cal_level,
                                         max_cal_level=max_cal_level,
                                         product_type=tap_product_type)
        output_file_full_path, output_dir = self.__set_dirs(output_file=output_file,
                                                            observation_id=observation_id)
        # Get file name only
        output_file_name = os.path.basename(output_file_full_path)

        try:
            self.__jwsttap.load_data(params_dict=params_dict,
                                     output_file=output_file_full_path)
        except Exception as exx:
            raise ValueError(f"Cannot retrieve products for observation {observation_id}: {exx}")

        files = []
        self.__extract_file(output_file_full_path=output_file_full_path,
                            output_dir=output_dir,
                            files=files)
        if (files):
            return files

        self.__check_file_number(output_dir=output_dir,
                                 output_file_name=output_file_name,
                                 output_file_full_path=output_file_full_path,
                                 files=files)

        return files

    def download_files_from_program(self, proposal_id, *, product_type=None, verbose=False):
        """Get JWST products given its proposal ID.

        Parameters
        ----------
        proposal_id : int, mandatory
            Program or Proposal ID associated to the observations.
        product_type : str or list, optional, default None
            If the string or at least one element of the list is empty,
            the value is replaced by None.
            With None, all products will be downloaded.
            Possible string values: 'thumbnail', 'preview', 'auxiliary', 'science' or 'info'.
            Posible list values: any combination of string values.
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        allobs : list
            Returns the observationsid included into the proposal_id.
        """

        query = (f"SELECT observationid "
                 f"FROM {str(conf.JWST_ARCHIVE_TABLE)} "
                 f"WHERE proposal_id='{str(proposal_id)}'")
        if verbose:
            print(query)
        job = self.__jwsttap.launch_job_async(query=query, verbose=verbose)
        allobs = set(JwstClass.get_decoded_string(job.get_results()['observationid']))
        for oid in allobs:
            log.info(f"Downloading products for Observation ID: {oid}")
            self.get_obs_products(observation_id=oid, product_type=product_type)
        return list(allobs)

    def __check_file_number(self, output_dir, output_file_name,
                            output_file_full_path, files):
        num_files_in_dir = len(os.listdir(output_dir))
        if num_files_in_dir == 1:
            if output_file_name.endswith("_all_products"):
                p = output_file_name.rfind('_all_products')
                output_f = output_file_name[0:p]
            else:
                output_f = output_file_name

            output_full_path = output_dir + os.sep + output_f

            os.rename(output_file_full_path, output_full_path)
            files.append(output_full_path)
        else:
            # r=root, d=directories, f = files
            for r, d, f in os.walk(output_dir):
                for file in f:
                    if file != output_file_name:
                        files.append(os.path.join(r, file))

    def __extract_file(self, output_file_full_path, output_dir, files):
        if esatar.is_tarfile(output_file_full_path):
            with esatar.open(output_file_full_path) as tar_ref:
                tar_ref.extractall(path=output_dir)
        elif zipfile.is_zipfile(output_file_full_path):
            with zipfile.ZipFile(output_file_full_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        elif not JwstClass.is_gz_file(output_file_full_path):
            # single file: return it
            files.append(output_file_full_path)
            return files

    def __set_dirs(self, output_file, observation_id):
        if output_file is None:
            now = datetime.now(timezone.utc)
            formatted_now = now.strftime("%Y%m%d_%H%M%S")
            output_dir = os.getcwd() + os.sep + "temp_" + \
                formatted_now
            output_file_full_path = output_dir + os.sep + observation_id +\
                "_all_products"
        else:
            output_file_full_path = output_file
            output_dir = os.path.dirname(output_file_full_path)
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as err:
            raise OSError(f"Creation of the directory {output_dir} failed: {err.strerror}")
        return output_file_full_path, output_dir

    def __set_additional_parameters(self, param_dict, cal_level,
                                    max_cal_level, product_type):
        if cal_level is not None:
            self.__validate_cal_level(cal_level=cal_level)
            if (cal_level == max_cal_level or cal_level == 2):
                param_dict['calibrationlevel'] = 'SELECTED'
            elif (cal_level == 1):
                param_dict['calibrationlevel'] = 'LEVEL1ONLY'
            else:
                param_dict['calibrationlevel'] = cal_level

        if product_type is not None:
            param_dict['product_type'] = str(product_type)

    def __get_quantity_input(self, value, msg):
        if value is None:
            raise ValueError(f"Missing required argument: '{msg}'")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(f"{msg} must be either a string or units.Quantity")
        if isinstance(value, str):
            q = Quantity(value)
            return q
        else:
            return value

    def __get_coord_input(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(f"{msg} must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value

    def __get_observationid_condition(self, *, value=None):
        condition = ""
        if (value is not None):
            if (not isinstance(value, str)):
                raise ValueError("observation_id must be string")
            else:
                condition = f" AND observationid LIKE '{value.lower()}' "
        return condition

    def __get_callevel_condition(self, cal_level):
        condition = ""
        if (cal_level is not None):
            if (isinstance(cal_level, str) and cal_level == 'Top'):
                condition = " AND max_cal_level=calibrationlevel "
            elif (isinstance(cal_level, int)):
                condition = f" AND calibrationlevel={str(cal_level)} "
            else:
                raise ValueError("cal_level must be either "
                                 "'Top' or an integer")
        return condition

    def __get_public_condition(self, only_public):
        condition = ""
        if (not isinstance(only_public, bool)):
            raise ValueError("only_public must be boolean")
        elif (only_public is True):
            condition = " AND public='true' "
        return condition

    def __get_plane_dataproducttype_condition(self, *, prod_type=None):
        condition = ""
        if prod_type is not None:
            if not isinstance(prod_type, str):
                raise ValueError("prod_type must be string")
            elif str(prod_type).lower() not in self.PLANE_DATAPRODUCT_TYPES:
                raise ValueError("prod_type must be one of: {str(', '.join(self.PLANE_DATAPRODUCT_TYPES))}")
            else:
                condition = f" AND dataproducttype ILIKE '%{prod_type.lower()}%' "
        return condition

    def __get_instrument_name_condition(self, *, value=None):
        condition = ""
        if (value is not None):
            if (not isinstance(value, str)):
                raise ValueError("instrument_name must be string")
            elif (str(value).upper() not in self.INSTRUMENT_NAMES):
                raise ValueError(f"instrument_name must be one of: {str(', '.join(self.INSTRUMENT_NAMES))}")
            else:
                condition = f" AND instrument_name ILIKE '%{value.upper()}%' "
        return condition

    def __get_filter_name_condition(self, *, value=None):
        condition = ""
        if (value is not None):
            if (not isinstance(value, str)):
                raise ValueError("filter_name must be string")

            else:
                condition = f" AND energy_bandpassname ILIKE '%{value}%' "
        return condition

    def __get_proposal_id_condition(self, *, value=None):
        condition = ""
        if (value is not None):
            if (not isinstance(value, str)):
                raise ValueError("proposal_id must be string")

            else:
                condition = f" AND proposal_id ILIKE '%{value}%' "
        return condition

    def __get_artifact_producttype_condition(self, *, product_type=None):
        condition = ""
        if (product_type is not None):
            if (not isinstance(product_type, str)):
                raise ValueError("product_type must be string")
            elif (product_type not in self.ARTIFACT_PRODUCT_TYPES):
                raise ValueError(f"product_type must be one of: {str(', '.join(self.ARTIFACT_PRODUCT_TYPES))}")
            else:
                condition = f" AND producttype ILIKE '%{product_type}%'"
        return condition

    @staticmethod
    def is_gz_file(filepath):
        with open(filepath, 'rb') as test_f:
            return binascii.hexlify(test_f.read(2)) == b'1f8b'

    @staticmethod
    def gzip_uncompress(input_file, output_file):
        with open(output_file, 'wb') as f_out, gzip.open(input_file,
                                                         'rb') as f_in:
            shutil.copyfileobj(f_in, f_out)

    @staticmethod
    def gzip_uncompress_and_rename_single_file(input_file):
        output_dir = os.path.dirname(input_file)
        file = os.path.basename(input_file)
        output_decompressed_file = output_dir + os.sep + file + "_decompressed"
        JwstClass.gzip_uncompress(input_file=input_file,
                                  output_file=output_decompressed_file)
        # Remove uncompressed file and rename decompressed file to the
        # original one
        os.remove(input_file)
        if file.lower().endswith(".gz"):
            # remove .gz
            new_file_name = file[:len(file) - 3]
            output = output_dir + os.sep + new_file_name
        else:
            output = input_file
        os.rename(output_decompressed_file, output)
        return output

    @staticmethod
    def get_decoded_string(str):
        try:
            return str.decode('utf-8')
            # return str
        except (UnicodeDecodeError, AttributeError):
            return str


Jwst = JwstClass()
