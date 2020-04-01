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
from astropy import units
from astropy.units import Quantity

from . import conf
from .data_access import JwstDataHandler

from builtins import isinstance

__all__ = ['Jwst', 'JwstClass']
    
class JwstClass(object):

    """
    Proxy class to default TapPlus object (pointing to JWST Archive)
    """
    JWST_MAIN_TABLE = conf.JWST_MAIN_TABLE
    JWST_ARTIFACT_TABLE = conf.JWST_ARTIFACT_TABLE
    JWST_OBSERVATION_TABLE = conf.JWST_OBSERVATION_TABLE
    JWST_OBSERVATION_TABLE_RA = conf.JWST_OBSERVATION_TABLE_RA
    JWST_OBSERVATION_TABLE_DEC = conf.JWST_OBSERVATION_TABLE_DEC
    JWST_PLANE_TABLE = conf.JWST_PLANE_TABLE

    JWST_DEFAULT_COLUMNS = ['observationid', 'calibrationlevel', 'public',
                            'dataproducttype', 'instrument_name', 'position_bounds_center',
                            'position_bounds_spoly']
    
    PLANE_DATAPRODUCT_TYPES = ['image', 'cube', 'measurements', 'spectrum']
    ARTIFACT_PRODUCT_TYPES = ['info', 'thumbnail', 'auxiliary', 'science', 'preview']
    INSTRUMENT_NAMES = ['NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS']

    def __init__(self, tap_plus_handler=None, data_handler=None):
        if tap_plus_handler is None:

            self.__jwsttap = TapPlus(url="http://jwstdummytap.com", data_context='data')
        else:
            self.__jwsttap = tap_plus_handler
            
        if data_handler is None:
            self.__jwstdata = self.__jwsttap;
        else:
            self.__jwstdata = data_handler;

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
        upload_table_name: str, required if uploadResource is provided, default None
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
            when the job is executed in asynchronous mode, this flag specifies whether
            the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        return self.__jwsttap.launch_job_async(query,
                                               name=name,
                                               output_file=output_file,
                                               output_format=output_format,
                                               verbose=verbose,
                                               dump_to_file=dump_to_file,
                                               background=background,
                                               upload_resource=upload_resource,
                                               upload_table_name=upload_table_name)

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
        radius : astropy.units, required if no 'width' nor 'height' are provided
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour is to show the most
            representative columns only
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

            observationid_condition = self.__get_observationid_condition(observation_id)
            cal_level_condition = self.__get_callevel_condition(cal_level) 
            public_condition = self.__get_public_condition(only_public)
            prod_type_condition = self.__get_plane_dataproducttype_condition(prod_type)
            instrument_name_condition = self.__get_instrument_name_condition(instrument_name)
            filter_name_condition = self.__get_filter_name_condition(filter_name)
            proposal_id_condition = self.__get_proposal_id_condition(proposal_id)

            columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
            if show_all_columns:
                columns = '*'

            query = "SELECT DISTANCE(POINT('ICRS'," +\
                str(self.JWST_OBSERVATION_TABLE_RA) + "," +\
                str(self.JWST_OBSERVATION_TABLE_DEC) +"), \
                POINT('ICRS'," + str(ra) + "," + str(dec) +")) AS dist, "+columns+" \
                FROM jwst.main \
                WHERE CONTAINS(\
                POINT('ICRS'," +\
                str(self.JWST_OBSERVATION_TABLE_RA)+"," +\
                str(self.JWST_OBSERVATION_TABLE_DEC)+"),\
                BOX('ICRS'," + str(ra) + "," + str(dec)+", " +\
                str(widthDeg.value)+", " +\
                str(heightDeg.value)+"))=1 " +\
                observationid_condition +\
                cal_level_condition +\
                public_condition +\
                prod_type_condition +\
                instrument_name_condition + \
                filter_name_condition + \
                proposal_id_condition + \
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
        radius : astropy.units, required if no 'width' nor 'height' are provided
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour is to show the most
            representative columns only
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
        radius : astropy.units, required if no 'width' nor 'height' are provided
            radius
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour is to show the most
            representative columns only
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
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

        observationid_condition = self.__get_observationid_condition(observation_id)
        cal_level_condition = self.__get_callevel_condition(cal_level) 
        public_condition = self.__get_public_condition(only_public)
        prod_type_condition = self.__get_plane_dataproducttype_condition(prod_type)
        instrument_name_condition = self.__get_instrument_name_condition(instrument_name)
        filter_name_condition = self.__get_filter_name_condition(filter_name)
        proposal_id_condition = self.__get_proposal_id_condition(proposal_id)

        columns = str(', '.join(self.JWST_DEFAULT_COLUMNS))
        if show_all_columns:
            columns = '*'

        if radius is not None:
            radius_quantity = self.__get_quantity_input(radius, "radius")
            radius_deg = commons.radius_to_unit(radius_quantity, unit='deg')

        query = "SELECT DISTANCE(POINT('ICRS'," +\
            str(self.JWST_OBSERVATION_TABLE_RA) + "," +\
            str(self.JWST_OBSERVATION_TABLE_DEC) + "), \
            POINT('ICRS'," + str(ra) + "," + str(dec) +")) AS dist, "+columns+" \
            FROM " + str(self.JWST_MAIN_TABLE) + " WHERE CONTAINS(\
            POINT('ICRS'," + str(self.JWST_OBSERVATION_TABLE_RA) + "," +\
            str(self.JWST_OBSERVATION_TABLE_DEC)+"),\
            CIRCLE('ICRS'," + str(ra)+"," + str(dec) + ", " +\
            str(radius_deg)+"))=1" +\
            observationid_condition +\
            cal_level_condition +\
            public_condition + \
            prod_type_condition + \
            instrument_name_condition + \
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour is to show the most
            representative columns only
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
            'image','cube','measurements','spectrum': str, only results of the given product type
        instrument_name : str, optional, default None
            get the observations corresponding to the given instrument name. Options are:
            'NIRISS', 'NIRSPEC', 'NIRCAM', 'MIRI', 'FGS': str, only results of the given instrument
        filter_name : str, optional, default None
            get the observations made with the given filter.
        proposal_id : str, optional, default None
            get the observations from the given proposal ID.
        only_public : bool, optional, default 'False'
            flag to show only metadata corresponding to public observations
        show_all_columns : bool, optional, default 'False'
            flag to show all available columns in the output. Default behaviour is to show the most
            representative columns only
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
        credentials_file : str, mandatory if no 'user' & 'password' are provided
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
    
    def get_product_list(self, plane_id, product_type=None):
        """Get the list of products of a given JWST plane.

        Parameters
        ----------
        plane_id : str, mandatory
            Plane ID of the products.
        product_type : str, optional, default None
            List only products of the given type. If None, all products are \
            listed. Possible values: 'thumbnail', 'preview', 'auxiliary', \
            'science'.

        Returns
        -------
        The list of products (astropy.table).
        """
        if plane_id is None:
            raise ValueError("Missing required argument: 'plane_id'")
        
        prodtype_condition=self.__get_artifact_producttype_condition(product_type)
        query = "SELECT  * " +\
            "FROM " + str(self.JWST_ARTIFACT_TABLE) +\
            " WHERE planeid='"+plane_id+"' " +\
            prodtype_condition +\
            "ORDER BY producttype ASC"
        job = self.__jwsttap.launch_job(query=query)
        return job.get_results()
    
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
            raise ValueError("Missing required argument: 'artifact_id' or 'file_name'")
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
                params_dict['ARTIFACT_URI'] = 'mast:JWST/product/' + str(file_name)

        #url=self.__jwstdata.base_url+"RETRIEVAL_TYPE=PRODUCT&DATA_RETRIEVAL_ORIGIN=ASTROQUERY" +\
        #            "&ARTIFACTID=" + artifact_id
        #
        #try:
        #    file = self.__jwstdata.download_file(url)
        #except:
        #    raise ValueError('Product ' + artifact_id + ' not available')
        #return file
        try:
            self.__jwsttap.load_data(params_dict=params_dict, output_file=output_file_name)
        except:
            raise ValueError('Product ' + err_msg + ' not available')
        print("Product saved at: %s" % (output_file_name))
        return output_file_name

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
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
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
            if(isinstance(cal_level, str) and cal_level is 'Top'):
                condition = " AND max_cal_level=calibrationlevel "
            elif(isinstance(cal_level, int)):
                condition = " AND calibrationlevel="+\
                                        str(cal_level)+" "
            else:
                raise ValueError("cal_level must be either 'Top' or an integer")
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
                raise ValueError("prod_type must be one of: " +\
                                 str(', '.join(self.PLANE_DATAPRODUCT_TYPES)))
            else:
                condition = " AND dataproducttype LIKE '"+prod_type.lower()+"' "
        return condition

    def __get_instrument_name_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("instrument_name must be string")
            elif(str(value).upper() not in self.INSTRUMENT_NAMES):
                raise ValueError("instrument_name must be one of: " +\
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
                condition = " AND instrument_keywords LIKE '%FILTER="+value.upper()+"%' "
        return condition

    def __get_proposal_id_condition(self, value=None):
        condition = ""
        if(value is not None):
            if(not isinstance(value, str)):
                raise ValueError("proposal_id must be string")

            else:
                condition = " AND proposal_id LIKE '%FILTER="+value.upper()+"%' "
        return condition

    def __get_artifact_producttype_condition(self, product_type=None):
        condition = ""
        if(product_type is not None):
            if(not isinstance(product_type, str)):
                raise ValueError("product_type must be string")
            elif(product_type not in self.ARTIFACT_PRODUCT_TYPES):
                raise ValueError("product_type must be one of: " +\
                                 str(', '.join(self.ARTIFACT_PRODUCT_TYPES)))
            else:
                condition = " AND producttype ILIKE '"+product_type+"' "
        return condition


Jwst = JwstClass()
