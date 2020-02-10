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
import six
from astroquery.utils.tap import taputils
from . import conf


class GaiaClass(TapPlus):

    """
    Proxy class to default TapPlus object (pointing to Gaia Archive)
    """
    MAIN_GAIA_TABLE = conf.MAIN_GAIA_TABLE
    MAIN_GAIA_TABLE_RA = conf.MAIN_GAIA_TABLE_RA
    MAIN_GAIA_TABLE_DEC = conf.MAIN_GAIA_TABLE_DEC
    ROW_LIMIT = conf.ROW_LIMIT

    def __init__(self, tap_plus_conn_handler=None, datalink_handler=None):
        super(GaiaClass, self).__init__(url="https://gea.esac.esa.int/",
                                        server_context="tap-server",
                                        tap_context="tap",
                                        upload_context="Upload",
                                        table_edit_context="TableTool",
                                        data_context="data",
                                        datalink_context="datalink",
                                        connhandler=tap_plus_conn_handler)
        # Data uses a different TapPlus connection
        if datalink_handler is None:
            self.__gaiadata = TapPlus(url="https://geadata.esac.esa.int/",
                                      server_context="data-server",
                                      tap_context="tap",
                                      upload_context="Upload",
                                      table_edit_context="TableTool",
                                      data_context="data",
                                      datalink_context="datalink")
        else:
            self.__gaiadata = datalink_handler

    def load_data(self, ids, retrieval_type="epoch_photometry",
                  valid_data=True, band=None, format="VOTABLE",
                  output_file=None, verbose=False):
        """Loads the specified table
        TAP+ only

        Parameters
        ----------
        ids : str list, mandatory
            list of identifiers
        retrieval_type : str, optional, default 'epoch_photometry'
            retrieval type identifier
        valid_data : bool, optional, default True
            By default, the epoch photometry service returns only valid data,
            that is, all data rows where flux is not null and
            rejected_by_photometry flag is not true. In order to retrieve
            all data associated to a given source without this filter,
            this request parameter should be included (valid_data=False)
        band : str, optional, default None, valid values: G, BP, RP
            By default, the epoch photometry service returns all the
            available photometry bands for the requested source.
            This parameter allows to filter the output lightcurve by its band.
        format : str, optional, default 'votable'
            loading format
        output_file : string, optional, default None
            file where the results are saved.
            If it is not provided, the http response contents are returned.
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        if retrieval_type is None:
            raise ValueError("Missing mandatory argument 'retrieval_type'")
        if ids is None:
            raise ValueError("Missing mandatory argument 'ids'")
        params_dict = {}
        if valid_data:
            params_dict['VALID_DATA'] = "true"
        else:
            params_dict['VALID_DATA'] = "false"
        if band is not None:
            if band != 'G' and band != 'BP' and band != 'RP':
                raise ValueError("Invalid band value '%s' (Valid values: " +
                                 "'G', 'BP' and 'RP)" % band)
            else:
                params_dict['BAND'] = band
        if isinstance(ids, six.string_types):
            ids_arg = ids
        else:
            if isinstance(ids, int):
                ids_arg = str(ids)
            else:
                ids_arg = ','.join(str(item) for item in ids)
        params_dict['ID'] = ids_arg
        params_dict['FORMAT'] = str(format)
        params_dict['RETRIEVAL_TYPE'] = str(retrieval_type)
        return self.__gaiadata.load_data(params_dict=params_dict,
                                         output_file=output_file,
                                         verbose=verbose)

    def get_datalinks(self, ids, verbose=False):
        """Gets datalinks associated to the provided identifiers
        TAP+ only

        Parameters
        ----------
        ids : str list, mandatory
            list of identifiers
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        return self.__gaiadata.get_datalinks(ids=ids, verbose=verbose)

    def __query_object(self, coordinate, radius=None, width=None, height=None,
                       async_job=False, verbose=False, columns=[]):
        """Launches a job
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width' nor 'height' are
        provided
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
        columns: list, optional, default []
            if empty, all columns will be selected

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

            if columns:
                columns = ','.join(map(str, columns))
            else:
                columns = "*"

            query = """
                    SELECT
                      {row_limit}
                      DISTANCE(
                        POINT('ICRS', {ra_column}, {dec_column}),
                        POINT('ICRS', {ra}, {dec})
                      ) as dist,
                      {columns}
                    FROM
                      {table_name}
                    WHERE
                      1 = CONTAINS(
                        POINT('ICRS', {ra_column}, {dec_column}),
                        BOX(
                          'ICRS',
                          {ra},
                          {dec},
                          {width},
                          {height}
                        )
                      )
                    ORDER BY
                      dist ASC
                    """.format(**{
                        'row_limit': "TOP {0}".format(self.ROW_LIMIT) if self.ROW_LIMIT > 0 else "",
                        'ra_column': self.MAIN_GAIA_TABLE_RA,
                        'dec_column': self.MAIN_GAIA_TABLE_DEC,
                        'columns': columns, 'table_name': self.MAIN_GAIA_TABLE,
                        'ra': ra, 'dec': dec, 'width': widthDeg.value, 'height': heightDeg.value,
                    })

            if async_job:
                job = self.launch_job_async(query, verbose=verbose)
            else:
                job = self.launch_job(query, verbose=verbose)
        return job.get_results()

    def query_object(self, coordinate, radius=None, width=None, height=None,
                     verbose=False, columns=[]):
        """Launches a job
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinates, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width'/'height' are provided
            radius (deg)
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        verbose : bool, optional, default 'False'
            flag to display information about the process
        columns: list, optional, default []
            if empty, all columns will be selected

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius, width, height,
                                   async_job=False, verbose=verbose, columns=columns)

    def query_object_async(self, coordinate, radius=None, width=None,
                           height=None, verbose=False, columns=[]):
        """Launches a job (async)
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinates, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width'/'height' are provided
            radius
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode
            (default synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius, width, height,
                                   async_job=True, verbose=verbose, columns=columns)

    def __cone_search(self, coordinate, radius, table_name=MAIN_GAIA_TABLE,
                      ra_column_name=MAIN_GAIA_TABLE_RA,
                      dec_column_name=MAIN_GAIA_TABLE_DEC,
                      async_job=False,
                      background=False,
                      output_file=None, output_format="votable", verbose=False,
                      dump_to_file=False,
                      columns=[]):
        """Cone search sorted by distance
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table
            table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
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
        columns: list, optional, default []
            if empty, all columns will be selected

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

        if columns:
            columns = ','.join(map(str, columns))
        else:
            columns = "*"

        query = """
                SELECT
                  {row_limit}
                  {columns},
                  DISTANCE(
                    POINT('ICRS', {ra_column}, {dec_column}),
                    POINT('ICRS', {ra}, {dec})
                  ) AS dist
                FROM
                  {table_name}
                WHERE
                  1 = CONTAINS(
                    POINT('ICRS', {ra_column}, {dec_column}),
                    CIRCLE('ICRS', {ra}, {dec}, {radius})
                  )
                ORDER BY
                  dist ASC
                """.format(**{
                    'ra_column': ra_column_name,
                    'row_limit': "TOP {0}".format(self.ROW_LIMIT) if self.ROW_LIMIT > 0 else "",
                    'dec_column': dec_column_name,
                    'columns': columns, 'ra': ra,
                    'dec': dec, 'radius': radiusDeg,
                    'table_name': table_name
                })

        if async_job:
            return self.launch_job_async(query=query,
                                         output_file=output_file,
                                         output_format=output_format,
                                         verbose=verbose,
                                         dump_to_file=dump_to_file,
                                         background=background)
        else:
            return self.launch_job(query=query,
                                   output_file=output_file,
                                   output_format=output_format,
                                   verbose=verbose,
                                   dump_to_file=dump_to_file)

    def cone_search(self, coordinate, radius=None,
                    table_name=MAIN_GAIA_TABLE,
                    ra_column_name=MAIN_GAIA_TABLE_RA,
                    dec_column_name=MAIN_GAIA_TABLE_DEC,
                    output_file=None,
                    output_format="votable", verbose=False,
                    dump_to_file=False,
                    columns=[]):
        """Cone search sorted by distance (sync.)
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table
            table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        columns: list, optional, default []
            if empty, all columns will be selected

        Returns
        -------
        A Job object
        """
        return self.__cone_search(coordinate,
                                  radius=radius,
                                  table_name=table_name,
                                  ra_column_name=ra_column_name,
                                  dec_column_name=dec_column_name,
                                  async_job=False,
                                  background=False,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file, columns=columns)

    def cone_search_async(self, coordinate, radius=None,
                          table_name=MAIN_GAIA_TABLE,
                          ra_column_name=MAIN_GAIA_TABLE_RA,
                          dec_column_name=MAIN_GAIA_TABLE_DEC,
                          background=False,
                          output_file=None, output_format="votable",
                          verbose=False, dump_to_file=False, columns=[]):
        """Cone search sorted by distance (async)
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table
            table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag
            specifies whether
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
                                  table_name=table_name,
                                  ra_column_name=ra_column_name,
                                  dec_column_name=dec_column_name,
                                  async_job=True,
                                  background=background,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file, columns=columns)

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
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")

    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value,
                                                     commons.CoordClasses)):
            raise ValueError(
                str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value

    def load_user(self, user_id, verbose=False):
        """Loads the specified user
        TAP+ only

        Parameters
        ----------
        user_id : str, mandatory
            user id to load
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A user
        """

        return self.is_valid_user(user_id=user_id,
                                  verbose=verbose)

    def cross_match(self, full_qualified_table_name_a=None,
                    full_qualified_table_name_b=None,
                    results_table_name=None,
                    radius=1.0,
                    background=False,
                    verbose=False):
        """Performs a cross match between the specified tables
        The result is a join table (stored in the user storage area)
        with the identifies of both tables and the distance.
        TAP+ only

        Parameters
        ----------
        full_qualified_table_name_a : str, mandatory
            a full qualified table name (i.e. schema name and table name)
        full_qualified_table_name_b : str, mandatory
            a full qualified table name (i.e. schema name and table name)
        results_table_name : str, mandatory
            a table name without schema. The schema is set to the user one
        radius : float (arc. seconds), optional, default 1.0
            radius  (valid range: 0.1-10.0)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        Boolean indicating if the specified user is valid
        """
        if full_qualified_table_name_a is None:
            raise ValueError("Table name A argument is mandatory")
        if full_qualified_table_name_b is None:
            raise ValueError("Table name B argument is mandatory")
        if results_table_name is None:
            raise ValueError("Results table name argument is mandatory")
        if radius < 0.1 or radius > 10.0:
            raise ValueError("Invalid radius value. Found " + str(radius) +
                             ", valid range is: 0.1 to 10.0")
        schemaA = taputils.get_schema_name(full_qualified_table_name_a)
        if schemaA is None:
            raise ValueError("Not found schema name in " +
                             "full qualified table A: '" +
                             full_qualified_table_name_a + "'")
        tableA = taputils.get_table_name(full_qualified_table_name_a)
        schemaB = taputils.get_schema_name(full_qualified_table_name_b)
        if schemaB is None:
            raise ValueError("Not found schema name in " +
                             "full qualified table B: '" +
                             full_qualified_table_name_b + "'")
        tableB = taputils.get_table_name(full_qualified_table_name_b)
        if taputils.get_schema_name(results_table_name) is not None:
            raise ValueError("Please, do not specify schema for " +
                             "'results_table_name'")
        query = "SELECT crossmatch_positional(\
            '"+schemaA+"','"+tableA+"',\
            '"+schemaB+"','"+tableB+"',\
            "+str(radius)+",\
            '"+str(results_table_name)+"')\
            FROM dual;"
        name = str(results_table_name)
        return self.launch_job_async(query=query,
                                     name=name,
                                     output_file=None,
                                     output_format="votable",
                                     verbose=verbose,
                                     dump_to_file=False,
                                     background=background,
                                     upload_resource=None,
                                     upload_table_name=None)


Gaia = GaiaClass()
