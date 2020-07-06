# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
JWST TAP plus
=============

@author: Raul Gutierrez-Sanchez
@contact: raul.gutierrez@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 23 oct. 2018


"""
from astroquery.utils.tap import TapPlus
from astroquery.utils import commons
from astroquery.simbad import Simbad
from astroquery.vizier import Vizier
from astroquery.ned import Ned
from astropy import units
from astropy.units import Quantity
from astropy.coordinates import SkyCoord
from astropy import log
from astropy.table import vstack

from datetime import datetime
import os
import zipfile
import tarfile
import binascii
import shutil
import gzip


from . import conf
from .data_access import JwstDataHandler

from builtins import isinstance

__all__ = ['Jwst', 'JwstClass']


class JwstClass(object):

    """
    Proxy class to default TapPlus object (pointing to JWST Archive)
    """
    JWST_MAIN_TABLE = conf.JWST_MAIN_TABLE
    JWST_OBSERVATION_TABLE = conf.JWST_OBSERVATION_TABLE
    JWST_OBS_MEMBER_TABLE = conf.JWST_OBS_MEMBER_TABLE
    JWST_MAIN_TABLE_RA = conf.JWST_MAIN_TABLE_RA
    JWST_MAIN_TABLE_DEC = conf.JWST_MAIN_TABLE_DEC
    JWST_PLANE_TABLE = conf.JWST_PLANE_TABLE
    JWST_ARTIFACT_TABLE = conf.JWST_ARTIFACT_TABLE

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
    CAL_LEVELS = ['ALL', 1, 2, 3]
    REQUESTED_OBSERVATION_ID = "Missing required argument: 'observation_id'"

    def __init__(self, tap_plus_handler=None, data_handler=None):
        if tap_plus_handler is None:
            self.__jwsttap = TapPlus(url="http://jwstdummytap.com", data_context='data')
        else:
            self.__jwsttap = tap_plus_handler

        if data_handler is None:
            self.__jwstdata = JwstDataHandler(base_url="http://jwstdummydata.com");
        else:
            self.__jwstdata = data_handler

    def load_tables(self, only_names=False, include_shared_tables=False,
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
        return self.__jwsttap.load_tables(only_names,
                                          include_shared_tables,
                                          verbose)

    def load_table(self, table, verbose=False):
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
        return self.__jwsttap.load_table(table, verbose)

    def launch_job(self, query, name=None, output_file=None,
                   output_format="votable", verbose=False, dump_to_file=False,
                   upload_resource=None, upload_table_name=None):
        """Launches a synchronous job
        TAP & TAP+

        Parameters
        ----------
        query : str, mandatory
            query to be executed
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
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided
            Default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        return self.__jwsttap.launch_job(query, name=name,
                                         output_file=output_file,
                                         output_format=output_format,
                                         verbose=verbose,
                                         dump_to_file=dump_to_file,
                                         upload_resource=upload_resource,
                                         upload_table_name=upload_table_name)

    def launch_job_async(self, query, name=None, output_file=None,
                         output_format="votable", verbose=False,
                         dump_to_file=False, background=False,
                         upload_resource=None, upload_table_name=None):
        """Launches an asynchronous job
        TAP & TAP+

        Parameters
        ----------
        query : str, mandatory
            query to be executed
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

        Returns
        -------
        A Job object
        """
        return (self.__jwsttap.launch_job_async(query,
                name=name,
                output_file=output_file,
                output_format=output_format,
                verbose=verbose,
                dump_to_file=dump_to_file,
                background=background,
                upload_resource=upload_resource,
                upload_table_name=upload_table_name))

    def load_async_job(self, jobid=None, name=None, verbose=False):
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
        return self.__jwsttap.load_async_job(jobid, name, verbose)

    def search_async_jobs(self, jobfilter=None, verbose=False):
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
        return self.__jwsttap.search_async_jobs(jobfilter, verbose)

    def list_async_jobs(self, verbose=False):
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
        return self.__jwsttap.list_async_jobs(verbose)

    def __query_region(self, coordinate, radius=None, width=None, height=None,
                       observation_id=None,
                       cal_level="Top",
                       prod_type=None,
                       instrument_name=None,
                       filter_name=None,
                       proposal_id=None,
                       only_public=False,
                       show_all_columns=False,
                       async_job=False, verbose=False):
        """Launches a job
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
        coord = self.__get_coord_input(coordinate, "coordinate")
        job = None
        if radius is not None:
            job = self.__cone_search(coord, radius,
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
            widthQuantity = self.__get_quantity_input(width, "width")
            heightQuantity = self.__get_quantity_input(height, "height")
            widthDeg = widthQuantity.to(units.deg)
            heightDeg = heightQuantity.to(units.deg)

            obsid_cond = self.__get_observationid_condition(observation_id)
            cal_level_condition = self.__get_callevel_condition(cal_level)
            public_condition = self.__get_public_condition(only_public)
            prod_cond = self.__get_plane_dataproducttype_condition(prod_type)
            instr_cond = self.__get_instrument_name_condition(instrument_name)
            filter_name_cond = self.__get_filter_name_condition(filter_name)
            props_id_cond = self.__get_proposal_id_condition(proposal_id)

            columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
            if show_all_columns:
                columns = '*'

            query = "SELECT DISTANCE(POINT('ICRS'," +\
                str(self.JWST_MAIN_TABLE_RA) + "," +\
                str(self.JWST_MAIN_TABLE_DEC) + "), \
                POINT('ICRS'," + str(ra) + "," + str(dec) + ")) "\
                "AS dist, "+columns+" \
                FROM " + str(self.JWST_MAIN_TABLE) + " \
                WHERE CONTAINS(\
                POINT('ICRS'," +\
                str(self.JWST_MAIN_TABLE_RA)+"," +\
                str(self.JWST_MAIN_TABLE_DEC)+"),\
                BOX('ICRS'," + str(ra) + "," + str(dec)+", " +\
                str(widthDeg.value)+", " +\
                str(heightDeg.value)+"))=1 " +\
                obsid_cond +\
                cal_level_condition +\
                public_condition +\
                prod_cond +\
                instr_cond + \
                filter_name_cond + \
                props_id_cond + \
                "ORDER BY dist ASC"
            print(query)
            if async_job:
                job = self.__jwsttap.launch_job_async(query, verbose=verbose)
            else:
                job = self.__jwsttap.launch_job(query, verbose=verbose)
        return job.get_results()

    def query_region(self, coordinate, radius=None, width=None, height=None,
                     observation_id=None,
                     cal_level="Top",
                     prod_type=None,
                     instrument_name=None,
                     filter_name=None,
                     proposal_id=None,
                     only_public=False,
                     show_all_columns=False,
                     verbose=False):
        """Launches a job
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinates, mandatory
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
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour
            is to show the most representative columns only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_region(coordinate, radius, width, height,
                                   only_public=only_public,
                                   observation_id=observation_id,
                                   cal_level=cal_level,
                                   prod_type=prod_type,
                                   instrument_name=instrument_name,
                                   filter_name=filter_name,
                                   proposal_id=proposal_id,
                                   show_all_columns=show_all_columns,
                                   async_job=False, verbose=verbose)

    def query_region_async(self, coordinate, radius=None,
                           width=None, height=None,
                           observation_id=None,
                           cal_level="Top",
                           prod_type=None,
                           instrument_name=None,
                           filter_name=None,
                           proposal_id=None,
                           only_public=False,
                           show_all_columns=False,
                           verbose=False):
        """Launches a job (async)
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinates, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width' nor 'height' are
            provided
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
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default
            behaviour is to show the most representative columns only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_region(coordinate, radius, width, height,
                                   observation_id=observation_id,
                                   cal_level=cal_level,
                                   async_job=True,
                                   prod_type=prod_type,
                                   instrument_name=instrument_name,
                                   filter_name=filter_name,
                                   proposal_id=proposal_id,
                                   only_public=only_public,
                                   show_all_columns=show_all_columns,
                                   verbose=verbose)

    def __cone_search(self, coordinate, radius,
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
        """Cone search sorted by distance
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
        coord = self.__get_coord_input(coordinate, "coordinate")
        ra_hours, dec = commons.coord_to_radec(coord)
        ra = ra_hours * 15.0  # Converts to degrees

        obsid_condition = self.__get_observationid_condition(observation_id)
        cal_level_condition = self.__get_callevel_condition(cal_level)
        public_condition = self.__get_public_condition(only_public)
        prod_type_cond = self.__get_plane_dataproducttype_condition(prod_type)
        inst_name_cond = self.__get_instrument_name_condition(instrument_name)
        filter_name_condition = self.__get_filter_name_condition(filter_name)
        proposal_id_condition = self.__get_proposal_id_condition(proposal_id)

        columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
        if show_all_columns:
            columns = '*'

        if radius is not None:
            radius_quantity = self.__get_quantity_input(radius, "radius")
            radius_deg = commons.radius_to_unit(radius_quantity, unit='deg')

        query = "SELECT DISTANCE(POINT('ICRS'," +\
            str(self.JWST_MAIN_TABLE_RA) + "," +\
            str(self.JWST_MAIN_TABLE_DEC) + "), \
            POINT('ICRS'," + str(ra) + "," + str(dec) + ")) AS dist, "+columns+" \
            FROM " + str(self.JWST_MAIN_TABLE) + " WHERE CONTAINS(\
            POINT('ICRS'," + str(self.JWST_MAIN_TABLE_RA) + "," +\
            str(self.JWST_MAIN_TABLE_DEC)+"),\
            CIRCLE('ICRS'," + str(ra)+"," + str(dec) + ", " +\
            str(radius_deg)+"))=1" +\
            obsid_condition +\
            cal_level_condition +\
            public_condition + \
            prod_type_cond + \
            inst_name_cond + \
            filter_name_condition + \
            proposal_id_condition + \
            "ORDER BY dist ASC"
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

    def cone_search(self, coordinate, radius=None,
                    observation_id=None,
                    cal_level="Top",
                    prod_type=None,
                    instrument_name=None,
                    filter_name=None,
                    proposal_id=None,
                    only_public=False,
                    show_all_columns=False,
                    output_file=None,
                    output_format="votable",
                    verbose=False,
                    dump_to_file=False):
        """Cone search sorted by distance (sync.)
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
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour
            is to show the most representative columns only
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
        return self.__cone_search(coordinate,
                                  radius=radius,
                                  only_public=only_public,
                                  observation_id=observation_id,
                                  cal_level=cal_level,
                                  prod_type=prod_type,
                                  instrument_name=instrument_name,
                                  filter_name=filter_name,
                                  proposal_id=proposal_id,
                                  show_all_columns=show_all_columns,
                                  async_job=False,
                                  background=False,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file)

    def cone_search_async(self, coordinate, radius=None,
                          observation_id=None,
                          cal_level="Top",
                          prod_type=None,
                          instrument_name=None,
                          filter_name=None,
                          proposal_id=None,
                          only_public=False,
                          show_all_columns=False,
                          background=False,
                          output_file=None, output_format="votable",
                          verbose=False, dump_to_file=False):
        """Cone search sorted by distance (async)
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
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output.
            Default behaviour is to show the most representative columns only
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
        return self.__cone_search(coordinate,
                                  radius=radius,
                                  observation_id=observation_id,
                                  cal_level=cal_level,
                                  prod_type=prod_type,
                                  instrument_name=instrument_name,
                                  filter_name=filter_name,
                                  proposal_id=proposal_id,
                                  only_public=only_public,
                                  show_all_columns=show_all_columns,
                                  async_job=True,
                                  background=background,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file)

    def query_target(self, target_name, target_resolver="ALL",
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
        """Launches a job
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
        coordinates = self.resolve_target_coordinates(target_name,
                                                      target_resolver)
        if async_job:
            return self.query_region_async(coordinates, radius, width, height,
                                           observation_id=observation_id,
                                           cal_level=cal_level,
                                           prod_type=prod_type,
                                           instrument_name=instrument_name,
                                           filter_name=filter_name,
                                           proposal_id=proposal_id,
                                           only_public=only_public,
                                           show_all_columns=show_all_columns,
                                           verbose=verbose)
        else:
            return self.query_region(coordinates, radius, width, height,
                                     observation_id=observation_id,
                                     cal_level=cal_level,
                                     prod_type=prod_type,
                                     instrument_name=instrument_name,
                                     filter_name=filter_name,
                                     proposal_id=proposal_id,
                                     only_public=only_public,
                                     show_all_columns=show_all_columns,
                                     verbose=verbose)

    def resolve_target_coordinates(self, target_name, target_resolver):
        if target_resolver not in self.TARGET_RESOLVERS:
            raise ValueError("This target resolver is not allowed")

        result_table = None
        if target_resolver == "ALL" or target_resolver == "SIMBAD":
            try:
                result_table = Simbad.query_object(target_name)
                return SkyCoord('{} {}'.format(result_table["RA"][0],
                                               result_table["DEC"][0]),
                                unit=(units.hourangle,
                                      units.deg), frame="icrs")
            except Exception:
                log.info("SIMBAD could not resolve this target")
        if target_resolver == "ALL" or target_resolver == "NED":
            try:
                result_table = Ned.query_object(target_name)
                return SkyCoord(result_table["RA"][0],
                                result_table["DEC"][0],
                                unit="deg", frame="fk5")
            except Exception:
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
            except Exception:
                log.info("VIZIER could not resolve this target")
        if result_table is None:
            raise ValueError("This target name cannot be determined with"
                             " this resolver: {}".format(target_resolver))

    def remove_jobs(self, jobs_list, verbose=False):
        """Removes the specified jobs
        TAP+

        Parameters
        ----------
        jobs_list : str, mandatory
            jobs identifiers to be removed
        verbose : bool, optional, default 'False'
            flag to display information about the process

        """
        return self.__jwsttap.remove_jobs(jobs_list, verbose=verbose)

    def save_results(self, job, verbose=False):
        """Saves job results
        TAP & TAP+

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.save_results(job, verbose)

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
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
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.login(user=user,
                                    password=password,
                                    credentials_file=credentials_file,
                                    verbose=verbose)

    def login_gui(self, verbose=False):
        """Performs a login using a GUI dialog
        TAP+ only

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.login_gui(verbose)

    def logout(self, verbose=False):
        """Performs a logout
        TAP+ only

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__jwsttap.logout(verbose)

    def get_product_list(self, observation_id=None,
                         cal_level="ALL",
                         product_type=None):
        """Get the list of products of a given JWST observation_id.

        Parameters
        ----------
        observation_id : str, mandatory
            Observation identifier.
        cal_level : str, optional
            Calibration level. Default value ia 'ALL', to download all the
            products associated to this observation_id and lower levels.
            Requesting more accurate levels than the one associated to the
            observation_id is not allowed (as level 3 observations are
            composite products based on level 2 products). To request upper
            levels, please use get_related_observations functions first.
            Possible values: 'ALL', '3', '2', '1'
        product_type : str, optional, default None
            List only products of the given type. If None, all products are \
            listed. Possible values: 'thumbnail', 'preview', 'info', \
            'auxiliary', 'science'.

        Returns
        -------
        The list of products (astropy.table).
        """
        self.__validate_cal_level(cal_level)

        if observation_id is None:
            raise ValueError(self.REQUESTED_OBSERVATION_ID)
        plane_ids, max_cal_level = self._get_plane_id(observation_id)
        if (cal_level == 3 and cal_level > max_cal_level):
            raise ValueError("Requesting upper levels is not allowed")
        list = self._get_associated_planes(plane_ids, cal_level,
                                           max_cal_level, False)

        query = "select distinct a.uri, a.filename, a.contenttype, "\
            "a.producttype, p.calibrationlevel, p.public FROM {0} p JOIN {1} "\
            "a ON (p.planeid=a.planeid) WHERE a.planeid IN {2}{3};"\
            .format(self.JWST_PLANE_TABLE, self.JWST_ARTIFACT_TABLE, list,
                    self.__get_artifact_producttype_condition(product_type))
        job = self.__jwsttap.launch_job(query=query)
        return job.get_results()

    def __validate_cal_level(self, cal_level):
        if (cal_level not in self.CAL_LEVELS):
            raise ValueError("This calibration level is not valid")

    def _get_associated_planes(self, plane_ids, cal_level,
                               max_cal_level, is_url):
        if (cal_level == max_cal_level):
            if (not is_url):
                list = "('{}')".format(plane_ids)
            else:
                list = "{}".format(",".join(plane_ids))
            return list
        else:
            plane_list = []
            for plane_id in plane_ids:
                siblings = self.__get_sibling_planes(plane_id, cal_level)
                members = self.__get_member_planes(plane_id, cal_level)
                plane_id_table = vstack([siblings, members])
                plane_list.extend(plane_id_table['product_planeid'].pformat(
                    show_name=False))
            if (not is_url):
                list = "('{}')".format("', '".join(plane_list))
            else:
                list = "{}".format(",".join(plane_list))
        return list

    def _get_plane_id(self, observation_id):
        try:
            planeids = []
            query_plane = "select distinct m.planeid, m.calibrationlevel "\
                "from {} m where m.observationid = '{}'"\
                .format(self.JWST_MAIN_TABLE, observation_id)
            job = self.__jwsttap.launch_job(query=query_plane)
            job.get_results().sort(["calibrationlevel"])
            job.get_results().reverse()
            max_cal_level = job.get_results()["calibrationlevel"][0]
            for row in job.get_results():
                if(row["calibrationlevel"] == max_cal_level):
                    planeids.append(row["planeid"].decode('utf-8'))
            return planeids, max_cal_level
        except Exception as e:
            raise ValueError("This observation_id does not exist in "
                             "JWST database")

    def __get_sibling_planes(self, planeid, cal_level='ALL'):
        where_clause = ""
        if (cal_level == "ALL"):
            where_clause = "WHERE sp.calibrationlevel<=p.calibrationlevel "\
                           "AND p.planeid ="
        else:
            where_clause = "WHERE sp.calibrationlevel={} AND "\
                           "p.planeid =".format(cal_level)
        try:
            query_siblings = "SELECT o.observationuri, p.planeid, "\
                             "p.calibrationlevel, sp.planeid as "\
                             "product_planeid, sp.calibrationlevel as "\
                             "product_level FROM {0} o JOIN {1} p ON "\
                             "p.obsid=o.obsid JOIN {1} sp ON "\
                             "sp.obsid=o.obsid {2}'{3}'"\
                             .format(self.JWST_OBSERVATION_TABLE,
                                     self.JWST_PLANE_TABLE,
                                     where_clause,
                                     planeid)
            job = self.__jwsttap.launch_job(query=query_siblings)
            return job.get_results()
        except Exception as e:
            raise ValueError(e)

    def __get_member_planes(self, planeid, cal_level='ALL'):
        where_clause = ""
        if (cal_level == "ALL"):
            where_clause = "WHERE p.planeid ="
        else:
            where_clause = "WHERE mp.calibrationlevel={} AND "\
                           "p.planeid =".format(cal_level)
        try:
            query_members = "SELECT o.observationuri, p.planeid, "\
                            "p.calibrationlevel, mp.planeid as "\
                            "product_planeid, mp.calibrationlevel as "\
                            "product_level FROM {0} o JOIN {1} p on "\
                            "o.obsid=p.obsid JOIN {2} m on "\
                            "o.obsid=m.compositeid JOIN {0} "\
                            "mo on m.simpleid=mo.observationuri JOIN "\
                            "{1} mp on mo.obsid=mp.obsid {3}'{4}'"\
                            .format(self.JWST_OBSERVATION_TABLE,
                                    self.JWST_PLANE_TABLE,
                                    self.JWST_OBS_MEMBER_TABLE,
                                    where_clause,
                                    planeid)
            job = self.__jwsttap.launch_job(query=query_members)
            return job.get_results()
        except Exception as e:
            raise ValueError(e)

    def get_related_observations(self, observation_id):
        """Get the list of level 3 products that make use of a given JWST
        observation_id.

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
        query_upper = "select * from {} m where m.members like "\
                      "'%{}%'".format(self.JWST_MAIN_TABLE, observation_id)
        job = self.__jwsttap.launch_job(query=query_upper)
        if any(job.get_results()["observationid"]):
            oids = job.get_results()["observationid"].pformat(show_name=False)
        else:
            oids = [observation_id]
        return oids

    def get_product(self, artifact_id=None, file_name=None):
        """Get a JWST product given its Artifact ID.

        Parameters
        ----------
        artifact_id : str, mandatory (if no file_name is provided)
            Artifact ID of the product.
        file_name : str, mandatory (if no artifact_id is provided)

        Returns
        -------
        local_path : str
            Returns the local path that the file was download to.
        """

        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        params_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'

        if artifact_id is None and file_name is None:
            raise ValueError("Missing required argument: "
                             "'artifact_id' or 'file_name'")
        else:
            if file_name is None:
                output_file_name = str(artifact_id)
                err_msg = str(artifact_id)
            else:
                output_file_name = str(file_name)
                err_msg = str(file_name)

            if artifact_id is not None:
                params_dict['ARTIFACTID'] = str(artifact_id)
            else:
                params_dict['ARTIFACT_URI'] = 'mast:JWST/product/' +\
                                            str(file_name)
        try:
            self.__jwsttap.load_data(params_dict=params_dict,
                                     output_file=output_file_name)
        except Exception as exx:
            log.info("error")
            raise ValueError('Error retrieving product for ' +
                             err_msg + ': %s' % str(exx))
        print("Product saved at: %s" % (output_file_name))
        return output_file_name

    def get_obs_products(self, observation_id=None, cal_level="ALL",
                         product_type=None, output_file=None):
        """Get a JWST product given its observation ID.

        Parameters
        ----------
        observation_id : str, mandatory
            Observation identifier.
        cal_level : str, optional
            Calibration level. Default value ia 'ALL', to download all the
            products associated to this observation_id and lower levels.
            Requesting more accurate levels than the one associated to the
            observation_id is not allowed (as level 3 observations are
            composite products based on level 2 products). To request upper
            levels, please use get_related_observations functions first.
            Possible values: 'ALL', '3', '2', '1'
        product_type : str, optional, default None
            List only products of the given type. If None, all products are \
            listed. Possible values: 'thumbnail', 'preview', 'auxiliary', \
            'science'.
        output_file : str, optional
            Output file. If no value is provided, a temporary one is created.

        Returns
        -------
        local_path : str
            Returns the local path where the product(s) are saved.
        """

        if observation_id is None:
            raise ValueError(self.REQUESTED_OBSERVATION_ID)
        plane_ids, max_cal_level = self._get_plane_id(observation_id)

        if (cal_level == 3 and cal_level > max_cal_level):
            raise ValueError("Requesting upper levels is not allowed")

        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'OBSERVATION'
        params_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'

        plane_ids = self._get_associated_planes(plane_ids, cal_level,
                                                max_cal_level, True)
        params_dict['planeid'] = plane_ids
        self.__set_additional_parameters(params_dict, cal_level, max_cal_level,
                                         product_type)
        output_file_full_path, output_dir = self.__set_dirs(output_file,
                                                            observation_id)
        # Get file name only
        output_file_name = os.path.basename(output_file_full_path)

        try:
            self.__jwsttap.load_data(params_dict=params_dict,
                                     output_file=output_file_full_path)
        except Exception as exx:
            raise ValueError('Cannot retrieve products for observation ' +
                             observation_id + ': %s' % str(exx))
        print("Product(s) saved at: %s" % output_file_full_path)

        files = []
        self.__extract_file(output_file_full_path, output_dir, files)
        if (files):
            return files

        self.__check_file_number(output_dir, output_file_name,
                                 output_file_full_path, files)

        for f in files:
            print("Product = %s" % f)

        return files

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
        if tarfile.is_tarfile(output_file_full_path):
            with tarfile.open(output_file_full_path) as tar_ref:
                tar_ref.extractall(path=output_dir)
        elif zipfile.is_zipfile(output_file_full_path):
            with zipfile.ZipFile(output_file_full_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        elif not JwstClass.is_gz_file(output_file_full_path):
            # single file: return it
            files.append(output_file_full_path)
            print("Product = %s" % output_file_full_path)
            return files

    def __set_dirs(self, output_file, observation_id):
        if output_file is None:
            now = datetime.now()
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
            print("Creation of the directory %s failed: %s"
                  % (output_dir, err.strerror))
            raise err
        return output_file_full_path, output_dir

    def __set_additional_parameters(self, param_dict, cal_level,
                                    max_cal_level, product_type):
        if cal_level is not None:
            self.__validate_cal_level(cal_level)
            if(cal_level == max_cal_level or cal_level == 2):
                param_dict['calibrationlevel'] = 'SELECTED'
            elif(cal_level == 1):
                param_dict['calibrationlevel'] = 'LEVEL1ONLY'
            else:
                param_dict['calibrationlevel'] = cal_level

        if product_type is not None:
            param_dict['product_type'] = str(product_type)

    def __get_quantity_input(self, value, msg):
        if value is None:
            raise ValueError("Missing required argument: '"+str(msg)+"'")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            q = Quantity(value)
            return q
        else:
            return value

    def __get_coord_input(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value

    def __get_observationid_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("observation_id must be string")
            else:
                condition = " AND observationid LIKE '"+value.lower()+"' "
        return condition

    def __get_callevel_condition(self, cal_level):
        condition = ""
        if(cal_level is not None):
            if(isinstance(cal_level, str) and cal_level == 'Top'):
                condition = " AND max_cal_level=calibrationlevel "
            elif(isinstance(cal_level, int)):
                condition = " AND calibrationlevel=" +\
                                        str(cal_level)+" "
            else:
                raise ValueError("cal_level must be either "
                                 "'Top' or an integer")
        return condition

    def __get_public_condition(self, only_public):
        condition = ""
        if(not isinstance(only_public, bool)):
            raise ValueError("only_public must be boolean")
        elif(only_public is True):
            condition = " AND public='true' "
        return condition

    def __get_plane_dataproducttype_condition(self, prod_type=None):
        condition = ""
        if(prod_type is not None):
            if(not isinstance(prod_type, str)):
                raise ValueError("prod_type must be string")
            elif(str(prod_type).lower() not in self.PLANE_DATAPRODUCT_TYPES):
                raise ValueError("prod_type must be one of: " +
                                 str(', '.join(self.PLANE_DATAPRODUCT_TYPES)))
            else:
                condition = " AND dataproducttype LIKE '"+prod_type.lower() + \
                    "' "
        return condition

    def __get_instrument_name_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("instrument_name must be string")
            elif(str(value).upper() not in self.INSTRUMENT_NAMES):
                raise ValueError("instrument_name must be one of: " +
                                 str(', '.join(self.INSTRUMENT_NAMES)))
            else:
                condition = " AND instrument_name LIKE '"+value.upper()+"' "
        return condition

    def __get_filter_name_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("filter_name must be string")

            else:
                condition = " AND energy_bandpassname ILIKE '%"+value+"%' "
        return condition

    def __get_proposal_id_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("proposal_id must be string")

            else:
                condition = " AND proposal_id ILIKE '%"+value+"%' "
        return condition

    def __get_artifact_producttype_condition(self, product_type=None):
        condition = ""
        if(product_type is not None):
            if(not isinstance(product_type, str)):
                raise ValueError("product_type must be string")
            elif(product_type not in self.ARTIFACT_PRODUCT_TYPES):
                raise ValueError("product_type must be one of: " +
                                 str(', '.join(self.ARTIFACT_PRODUCT_TYPES)))
            else:
                condition = " AND producttype LIKE '"+product_type+"'"
        return condition

    def __get_calibration_level_condition(self, cal_level=None):
        condition = ""
        if(cal_level is not None):
            if(not isinstance(cal_level, int)):
                raise ValueError("product_type must be an integer")
            else:
                condition = " AND m.calibrationlevel = "+str(cal_level)+" "
        else:
            condition = " AND m.calibrationlevel = m.max_cal_level"
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
            new_file_name = file[:len(file)-3]
            output = output_dir + os.sep + new_file_name
        else:
            output = input_file
        os.rename(output_decompressed_file, output)
        return output


Jwst = JwstClass()
