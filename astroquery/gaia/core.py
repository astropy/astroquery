# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

from astroquery.utils.tap import TapPlus
from astroquery.utils import commons
from astropy import units
from astropy.units import Quantity

from . import conf

__all__ = ['Gaia', 'GaiaClass']


class GaiaClass(object):

    """
    Proxy class to default TapPlus object (pointing to Gaia Archive)
    """
    MAIN_GAIA_TABLE = conf.MAIN_GAIA_TABLE
    MAIN_GAIA_TABLE_RA = conf.MAIN_GAIA_TABLE_RA
    MAIN_GAIA_TABLE_DEC = conf.MAIN_GAIA_TABLE_DEC

    def __init__(self, tap_plus_handler=None):
        if tap_plus_handler is None:
            self.__gaiatap = TapPlus(url="http://gea.esac.esa.int/tap-server/tap")
        else:
            self.__gaiatap = tap_plus_handler

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
        return self.__gaiatap.load_tables(only_names,
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
        return self.__gaiatap.load_table(table, verbose)

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
            results format
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
        return self.__gaiatap.launch_job(query, name=name,
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
            results format
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
        return self.__gaiatap.launch_job_async(query,
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
        return self.__gaiatap.load_async_job(jobid, name, verbose)

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
        return self.__gaiatap.search_async_jobs(jobfilter, verbose)

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
        return self.__gaiatap.list_async_jobs(verbose)

    def __query_object(self, coordinate, radius=None, width=None, height=None,
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
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        coord = self.__getCoordInput(coordinate, "coordinate")
        job = None
        if radius is not None:
            job = self.__cone_search(coord, radius,
                                     async_job=async_job, verbose=verbose)
        else:
            raHours, dec = commons.coord_to_radec(coord)
            ra = raHours * 15.0  # Converts to degrees
            widthQuantity = self.__getQuantityInput(width, "width")
            heightQuantity = self.__getQuantityInput(height, "height")
            widthDeg = widthQuantity.to(units.deg)
            heightDeg = heightQuantity.to(units.deg)
            query = "SELECT DISTANCE(POINT('ICRS',"+str(self.MAIN_GAIA_TABLE_RA)+","\
                + str(self.MAIN_GAIA_TABLE_DEC)+"), \
                POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
                FROM "+str(self.MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
                POINT('ICRS',"+str(self.MAIN_GAIA_TABLE_RA)+","\
                + str(self.MAIN_GAIA_TABLE_DEC)+"),\
                BOX('ICRS',"+str(ra)+","+str(dec)+", "+str(widthDeg.value)+", "\
                + str(heightDeg.value)+"))=1 \
                ORDER BY dist ASC"
            if async_job:
                job = self.__gaiatap.launch_job_async(query, verbose=verbose)
            else:
                job = self.__gaiatap.launch_job(query, verbose=verbose)
        return job.get_results()

    def query_object(self, coordinate, radius=None, width=None, height=None,
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
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius, width, height,
                                   async_job=False, verbose=verbose)

    def query_object_async(self, coordinate, radius=None, width=None,
                           height=None, verbose=False):
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
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius, width, height,
                                   async_job=True, verbose=verbose)

    def __cone_search(self, coordinate, radius, async_job=False,
                      background=False,
                      output_file=None, output_format="votable", verbose=False,
                      dump_to_file=False):
        """Cone search sorted by distance
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
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
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory

        Returns
        -------
        A Job object
        """
        coord = self.__getCoordInput(coordinate, "coordinate")
        raHours, dec = commons.coord_to_radec(coord)
        ra = raHours * 15.0  # Converts to degrees
        if radius is not None:
            radiusQuantity = self.__getQuantityInput(radius, "radius")
            radiusDeg = commons.radius_to_unit(radiusQuantity, unit='deg')
        query = "SELECT DISTANCE(POINT('ICRS',"+str(self.MAIN_GAIA_TABLE_RA)+","\
            + str(self.MAIN_GAIA_TABLE_DEC)+"), \
            POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
            FROM "+str(self.MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
            POINT('ICRS',"+str(self.MAIN_GAIA_TABLE_RA)+","+str(self.MAIN_GAIA_TABLE_DEC)+"),\
            CIRCLE('ICRS',"+str(ra)+","+str(dec)+", "+str(radiusDeg)+"))=1 \
            ORDER BY dist ASC"
        if async_job:
            return self.__gaiatap.launch_job_async(query=query,
                                                   output_file=output_file,
                                                   output_format=output_format,
                                                   verbose=verbose,
                                                   dump_to_file=dump_to_file,
                                                   background=background)
        else:
            return self.__gaiatap.launch_job(query=query,
                                             output_file=output_file,
                                             output_format=output_format,
                                             verbose=verbose,
                                             dump_to_file=dump_to_file)

    def cone_search(self, coordinate, radius=None, output_file=None,
                    output_format="votable", verbose=False,
                    dump_to_file=False):
        """Cone search sorted by distance (sync.)
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
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
                                  async_job=False,
                                  background=False,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file)

    def cone_search_async(self, coordinate, radius=None, background=False,
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
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies whether
            the execution will wait until results are available
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
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
        return self.__gaiatap.remove_jobs(jobs_list)

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
        return self.__gaiatap.save_results(job, verbose)

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        """Performs a login.
        TAP+ only
        User and password can be used or a file that contains user name and password
        (2 lines: one for user name and the following one for the password)

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
        return self.__gaiatap.login(user=user,
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
        return self.__gaiatap.login_gui(verbose)

    def logout(self, verbose=False):
        """Performs a logout
        TAP+ only

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        return self.__gaiatap.logout(verbose)

    def __checkQuantityInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")

    def __getQuantityInput(self, value, msg):
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

    def __checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")

    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value


Gaia = GaiaClass()
