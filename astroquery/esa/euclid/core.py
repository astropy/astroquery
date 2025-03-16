# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
Euclid TAP plus
===============
European Space Astronomy Centre (ESAC)
European Space Agency (ESA)
"""
import binascii
import os
import tarfile
import zipfile
from collections.abc import Iterable
from datetime import datetime

from astropy import units
from astropy import units as u
from astropy.coordinates import Angle
from astropy.units import Quantity
from requests.exceptions import HTTPError

from astroquery import log
from astroquery.utils import commons
from astroquery.utils.tap import TapPlus
from . import conf


class EuclidClass(TapPlus):
    __ERROR_MSG_REQUESTED_OBSERVATION_ID = "Missing required argument: 'observation_id'"
    __ERROR_MSG_REQUESTED_TILE_ID = "Missing required argument: 'tile_id'"
    __ERROR_MSG_REQUESTED_OBSERVATION_ID_AND_TILE_ID = "Incompatible: 'observation_id' and 'tile_id'. Use only one."
    __ERROR_MSG_REQUESTED_PRODUCT_TYPE = "Missing required argument: 'product_type'"
    __ERROR_MSG_REQUESTED_GENERIC = "Missing required argument"
    __ERROR_MSG_REQUESTED_RADIUS = "Radius cannot be greater than 30 arcminutes"
    EUCLID_MESSAGES = "notification?action=GetNotifications"

    """
    Proxy class to default TapPlus object (pointing to the Euclid archive)
    """
    ROW_LIMIT = conf.ROW_LIMIT

    __VALID_DATALINK_RETRIEVAL_TYPES = conf.VALID_DATALINK_RETRIEVAL_TYPES

    def __init__(self, *, environment='PDR', tap_plus_conn_handler=None, datalink_handler=None, cutout_handler=None,
                 verbose=False, show_server_messages=True):
        """Constructor for EuclidClass.

        Parameters
        ----------
        environment : str, mandatory if no tap, data or cutout hosts is specified, default 'PDR'
            The Euclid Science Archive environment: 'PDR', 'IDR', 'OTF' and 'REG'
        tap_plus_conn_handler : tap connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a new one is created.
        datalink_handler : dataliink connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a new one is created.
        cutout_handler : cutout connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a new one is created.
        verbose : bool, optional, default 'True'
            flag to display information about the process
        show_server_messages : bool, optional, default 'True'
            show the messages to inform users about the status of Euclid TAP
        """

        if environment not in conf.ENVIRONMENTS:
            raise ValueError(
                f"Invalid environment {environment}. Valid values: {list(conf.ENVIRONMENTS.keys())}")

        self.environment = environment
        self.main_table = conf.ENVIRONMENTS[self.environment]['main_table']
        self.main_table_ra = conf.ENVIRONMENTS[self.environment]['main_table_ra_column']
        self.main_table_dec = conf.ENVIRONMENTS[self.environment]['main_table_dec_column']

        url_server = conf.ENVIRONMENTS[environment]['url_server']

        super(EuclidClass, self).__init__(url=url_server,
                                          server_context='tap-server',
                                          tap_context="tap",
                                          upload_context="Upload",
                                          table_edit_context="TableTool",
                                          data_context="data",
                                          datalink_context="datalink",
                                          connhandler=tap_plus_conn_handler,
                                          verbose=verbose,
                                          client_id='ASTROQUERY',
                                          use_names_over_ids=conf.USE_NAMES_OVER_IDS)

        if datalink_handler is None:
            self.__eucliddata = TapPlus(url=url_server,
                                        server_context="sas-dd",
                                        tap_context="tap-server",
                                        upload_context="Upload",
                                        table_edit_context="TableTool",
                                        data_context="data",
                                        datalink_context="datalink",
                                        verbose=verbose,
                                        client_id='ASTROQUERY',
                                        use_names_over_ids=conf.USE_NAMES_OVER_IDS)
        else:
            self.__eucliddata = datalink_handler

        if cutout_handler is None:
            self.__euclidcutout = TapPlus(url=url_server,
                                          server_context="sas-cutout",
                                          tap_context="tap-server",
                                          upload_context="Upload",
                                          table_edit_context="TableTool",
                                          data_context="cutout",
                                          datalink_context="datalink",
                                          verbose=verbose,
                                          client_id='ASTROQUERY',
                                          use_names_over_ids=conf.USE_NAMES_OVER_IDS)
        else:
            self.__euclidcutout = cutout_handler

        if show_server_messages:
            self.get_status_messages()

    def launch_job(self, query, *, name=None, dump_to_file=False, output_file=None, output_format="csv", verbose=False,
                   upload_resource=None, upload_table_name=None):
        """
        Description
        -----------
        Launches a synchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional, default None
            custom name defined by the user for the job that is going to be created
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        output_file : str, optional, default None
            File name where the results are saved if dump_to_file is True.
            If this parameter is not provided, the job id is used instead
        output_format : str, optional, default 'csv'
            output format for the output file
        verbose : bool, optional, default 'False'
            flag to display information about the process
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        try:
            return super().launch_job(query=query, name=name,
                                      output_file=output_file,
                                      output_format=output_format,
                                      verbose=verbose,
                                      dump_to_file=dump_to_file,
                                      upload_resource=upload_resource,
                                      upload_table_name=upload_table_name,
                                      format_with_results_compressed=('votable_gzip',))

        except HTTPError as err:
            log.error(f'Query failed: {query}: HTTP error: {err}')
        except Exception as exx:
            log.error(f'Query failed: {query}, {str(exx)}')

    def launch_job_async(self, query, *, name=None, dump_to_file=False, output_file=None, output_format="csv",
                         verbose=False, background=False, upload_resource=None, upload_table_name=None, autorun=True):
        """
        Description
        -----------
        Launches an asynchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional, default None
            custom name defined by the user for the job that is going to be created
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        output_file : str, optional, default None
            file name where the results are saved if dump_to_file is True.
            if this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'csv'
            format of the results for the output file
        verbose : bool, optional, default 'False'
            flag to display information about the process
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies whether
            the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource
        autorun : boolean, optional, default True
            if 'True', sets 'phase' parameter to 'RUN',
            so the framework can start the job.

        Returns
        -------
        A Job object
        """
        try:
            return super().launch_job_async(query=query,
                                            name=name,
                                            output_file=output_file,
                                            output_format=output_format,
                                            verbose=verbose,
                                            dump_to_file=dump_to_file,
                                            background=background,
                                            upload_resource=upload_resource,
                                            upload_table_name=upload_table_name,
                                            autorun=autorun,
                                            format_with_results_compressed=('votable_gzip',))

        except HTTPError as err:
            log.error(f'Query failed: {query}: HTTP error: {err}')
        except Exception as exx:
            log.error(f'Query failed: {query}, {str(exx)}')

    def query_object(self, coordinate, *, radius=None, width=None, height=None,
                     async_job=False, verbose=False, columns=None):
        """
        Description
        -----------
        Searches for objects around a given position with the default catalog sascat_pvpr01.mer_final_cat_pvpr01

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
        columns: list, optional, default None
            if empty, all columns will be selected

        Returns
        -------
        The job results (astropy.table)
        """
        coord = commons.parse_coordinates(coordinate)

        if radius is not None:
            job = self.__cone_search(coord, radius, async_job=async_job, verbose=verbose, columns=columns)
        else:
            ra_hours, dec = commons.coord_to_radec(coord)
            ra = ra_hours * 15.0  # Converts to degrees
            width_quantity = self.__get_quantity_input(width, "width")
            height_quantity = self.__get_quantity_input(height, "height")
            width_deg = width_quantity.to(units.deg)
            height_deg = height_quantity.to(units.deg)
            query = ("SELECT DISTANCE(POINT('ICRS'," + self.main_table_ra + "," + self.main_table_dec + "), \
                POINT('ICRS'," + str(ra) + "," + str(dec) + ")) AS dist, * \
                FROM " + self.main_table + " WHERE CONTAINS(\
                POINT('ICRS'," + self.main_table_ra + "," + self.main_table_dec + "),\
                BOX('ICRS'," + str(ra) + "," + str(dec) + ", " + str(width_deg.value) + ", " + str(height_deg.value)
                     + "))=1 \
                ORDER BY dist ASC")

            if async_job:
                job = super().launch_job_async(query, verbose=verbose, format_with_results_compressed=('votable_gzip',))
            else:
                job = super().launch_job(query, verbose=verbose, format_with_results_compressed=('votable_gzip',))
        return job.get_results()

    def __cone_search(self, coordinate, radius, *, table_name=None, ra_column_name=None, dec_column_name=None,
                      async_job=False, verbose=False, columns=None):
        """Cone search sorted by distance
        TAP & TAP+

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
        async_job : bool, optional, default 'False'
            executes the job in asynchronous/synchronous mode (default
            synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        columns: list, optional, default None
            if empty, all columns will be selected
        Returns
        -------
        A Job object
        """

        if table_name is None:
            table_name = self.main_table
            ra_column_name = self.main_table_ra
            dec_column_name = self.main_table_dec

        radius_deg = None
        coord = commons.parse_coordinates(coordinate)
        ra_hours, dec = commons.coord_to_radec(coord)
        ra = ra_hours * 15.0  # Converts to degrees
        if radius is not None:
            radius_deg = Angle(self.__get_quantity_input(radius, "radius")).to_value(u.deg)

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
                """.format(**{'ra_column': ra_column_name,
                              'row_limit': "TOP {0}".format(self.ROW_LIMIT) if self.ROW_LIMIT > 0 else "",
                              'dec_column': dec_column_name, 'columns': columns, 'ra': ra, 'dec': dec,
                              'radius': radius_deg, 'table_name': table_name})

        if async_job:
            job = super().launch_job_async(query=query, verbose=verbose,
                                           format_with_results_compressed=('votable_gzip',))
        else:
            job = super().launch_job(query=query, verbose=verbose, format_with_results_compressed=('votable_gzip',))

        return job

    def cone_search(self, coordinate, radius, *,
                    table_name=None,
                    ra_column_name=None,
                    dec_column_name=None,
                    async_job=False,
                    background=False,
                    dump_to_file=False,
                    output_file=None,
                    output_format="csv",
                    verbose=False,
                    columns=None):
        """
        Description
        -----------
        Cone search for a given catalog and sky position, results sorted by distance

        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        table_name : str, optional, default the table defined for the selected environment
            Table to search
        ra_column_name : str, optional, default the column name defined for the selected environment
            Name of the RA column in the table
        dec_column_name : str, optional, default the column name defined for the selected environment
            Name of the DEC column in the table
        async_job : bool, optional, default 'False'
            executes the job in asynchronous/synchronous mode (default
            synchronous)
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        output_file : str, optional, default None
            file name where the results are saved if dump_to_file is True.
            If this parameter is not provided, the job id is used instead
        output_format : str, optional, default 'csv'
            Output format for the output file
        columns: list, optional, default None
            if empty, all columns will be selected
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """
        radius_deg = None
        coord = commons.parse_coordinates(coordinate)
        ra_hours, dec = commons.coord_to_radec(coord)
        ra = ra_hours * 15.0  # Converts to degrees
        if radius is not None:
            radius_deg = Angle(self.__get_quantity_input(radius, "radius")).to_value(u.deg)

        if table_name is None:
            table_name = self.main_table
            ra_column_name = self.main_table_ra
            dec_column_name = self.main_table_dec

        """
        if columns:
            columns = ','.join(map(str, columns))
        else:
            columns = "*"
        """

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
                """.format(**{'ra_column': ra_column_name,
                              'row_limit': "TOP {0}".format(self.ROW_LIMIT) if self.ROW_LIMIT > 0 else "",
                              'dec_column': dec_column_name, 'columns': columns, 'ra': ra, 'dec': dec,
                              'radius': radius_deg, 'table_name': table_name})

        if async_job:
            job = super().launch_job_async(query=query,
                                           output_file=output_file,
                                           output_format=output_format,
                                           verbose=verbose,
                                           dump_to_file=dump_to_file,
                                           background=background, format_with_results_compressed=('votable_gzip',))
        else:
            job = super().launch_job(query=query,
                                     output_file=output_file,
                                     output_format=output_format,
                                     verbose=verbose,
                                     dump_to_file=dump_to_file, format_with_results_compressed=('votable_gzip',))

        return job

    def login(self, *, user=None, password=None, credentials_file=None, verbose=False):
        """
        Description
        -----------
        Performs a login

        User and password can be used or a file that contains username and password
        (2 lines: one for username and the following one for the password)

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
        try:
            log.info(f"Login to Euclid TAP server: {self._TapPlus__getconnhandler().get_host_url()}")
            super().login(user=user, password=password, credentials_file=credentials_file, verbose=verbose)
        except HTTPError as err:
            log.error('Error logging in TAP server: %s' % (str(err)))
            return

        tap_user = self._TapPlus__user
        tap_password = self._TapPlus__pwd

        try:
            log.info(f"Login to Euclid data service: {self.__eucliddata._TapPlus__getconnhandler().get_host_url()}")
            self.__eucliddata.login(user=tap_user, password=tap_password, verbose=verbose)
            log.info(f"Login to Euclid cutout service: {self.__euclidcutout._TapPlus__getconnhandler().get_host_url()}")
            self.__euclidcutout.login(user=tap_user, password=tap_password, verbose=verbose)
        except HTTPError as err:
            log.error('Error logging in data or cutout services: %s' % (str(err)))
            log.error("Logging out from TAP server")
            TapPlus.logout(self, verbose=verbose)

    def login_gui(self, verbose=False):
        """
        Description
        -----------
        Performs a login using a GUI dialog

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        try:
            log.info(f"Login to Euclid TAP server: {self._TapPlus__getconnhandler().get_host_url()}")
            TapPlus.login_gui(self, verbose=verbose)
        except HTTPError as err:
            log.error('Error logging in TAP server: %s' % (str(err)))
            return

        tap_user = self._TapPlus__user
        tap_password = self._TapPlus__pwd

        try:
            log.info(f"Login to Euclid data server: {self.__eucliddata._TapPlus__getconnhandler().get_host_url()}")
            self.__eucliddata.login(user=tap_user, password=tap_password, verbose=verbose)
        except HTTPError as err:
            log.error('Error logging in data server: %s' % (str(err)))
            log.error("Logging out from TAP server")
            TapPlus.logout(self, verbose=verbose)

        try:
            log.info(f"Login to Euclid cutout server: {self.__euclidcutout._TapPlus__getconnhandler().get_host_url()}")
            self.__euclidcutout.login(user=tap_user, password=tap_password, verbose=verbose)
        except HTTPError as err:
            log.error('Error logging in cutout server: %s' % (str(err)))
            log.error("Logging out from TAP server")
            TapPlus.logout(self, verbose=verbose)

    def logout(self, verbose=False):
        """
        Description
        -----------
        Performs a logout

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        try:
            super().logout(verbose=verbose)
        except HTTPError as err:
            log.error('Error logging out TAP server: %s' % (str(err)))
            log.error("Error logging out TAP server")
            return
        log.info("Euclid TAP server logout OK")

        try:
            self.__eucliddata.logout(verbose=verbose)
            log.info("Euclid data server logout OK")
        except HTTPError as err:
            log.error('Error logging out data server: %s' % (str(err)))
            log.error("Error logging out data server")

        try:
            self.__euclidcutout.logout(verbose=verbose)
            log.info("Euclid cutout server logout OK")
        except HTTPError as err:
            log.error('Error logging out cutout server: %s' % (str(err)))

    @staticmethod
    def __get_quantity_input(value, msg):
        if value is None:
            raise ValueError(f"Missing required argument: '{msg}'")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(f"{msg} must be either a string or astropy.coordinates")
        if isinstance(value, str):
            return Quantity(value)
        else:
            return value

    @staticmethod
    def is_gz_file(filepath):
        with open(filepath, 'rb') as test_f:
            return binascii.hexlify(test_f.read(2)) == b'1f8b'

    def get_status_messages(self, verbose=False):
        """
        Description
        -----------
        Retrieve the messages to inform users about
        the status of Euclid TAP

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        """
        try:
            sub_context = self.EUCLID_MESSAGES
            conn_handler = self._TapPlus__getconnhandler()
            response = conn_handler.execute_tapget(sub_context, verbose=verbose)
            if response.status == 200:
                if isinstance(response, Iterable):
                    for line in response:

                        try:
                            print(line.decode("utf-8").split('=', 1)[1])
                        except ValueError as e:
                            print(e)
                        except IndexError:
                            print("Archive down for maintenance")

        except OSError:
            print("Status messages could not be retrieved")

    @staticmethod
    def __set_dirs(output_file, observation_id):
        if output_file is None:
            now = datetime.now()
            output_dir = os.getcwd() + os.sep + "temp_" + now.strftime("%Y%m%d_%H%M%S")
            output_file_full_path = output_dir + os.sep + str(observation_id)
        else:
            output_file_full_path = output_file
            output_dir = os.path.dirname(output_file_full_path)
        try:
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        except OSError as err:
            raise OSError("Creation of the directory %s failed: %s"
                          % (output_dir, err.strerror))
        return output_file_full_path, output_dir

    @staticmethod
    def __check_file_number(output_dir, output_file_name,
                            output_file_full_path, files):
        num_files_in_dir = len(os.listdir(output_dir))
        if num_files_in_dir == 1:
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

    @staticmethod
    def __extract_file(output_file_full_path, output_dir, files):
        if tarfile.is_tarfile(output_file_full_path):
            with tarfile.open(output_file_full_path) as tar_ref:
                tar_ref.extractall(path=output_dir)
        elif zipfile.is_zipfile(output_file_full_path):
            with zipfile.ZipFile(output_file_full_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
        elif not EuclidClass.is_gz_file(output_file_full_path):
            # single file: return it
            files.append(output_file_full_path)
            return files

    def get_observation_products(self, *, id=None, schema="sedm", product_type=None, product_subtype="STK",
                                 filter="VIS", output_file=None, verbose=False):
        """
        Description
        -----------
        Downloads the products for a given EUCLID observation_id (observations) or tile_index (mosaics)
        For big files the download may require a long time

        Parameters
        ----------
        id : str, mandatory
            observation identifier (observation id for observations, mosaic id for mosaics)
        schema : str, optional
            schema name. Default value is 'sedm'.
        product_type : str, mandatory, default None
            list only products of the given type.
            possible values: 'observation', 'mosaic'
        product_subtype : str, optional, default 'STK'
            list only products of the given subtype. Possible values: 'STK', 'ALL', 'PSF', 'BKG'
            for observations also 'DET', 'WGT'
            for mosaics also 'GRID_PSF', 'FLAG', 'RMS'.
        filter : str, optional, default 'VIS'
            list products for this instrument, only for observations. Possible values: 'VIS', 'NIR_J', 'NIR_H', 'NIR_Y'
        output_file : str, optional
            output file, use zip extension when downloading multiple files
            if no value is provided, a temporary one is created
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The fits file(s) are downloaded, and the local path where the product(s) are saved is returned
        """

        if id is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_OBSERVATION_ID)
        if product_type is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_PRODUCT_TYPE)
        if product_type not in conf.PRODUCT_TYPES:
            raise ValueError(f"Invalid product type {product_type}. Valid values: {conf.PRODUCT_TYPES}")

        params_dict = {'TYPE': product_subtype, 'RETRIEVAL_ACCESS': 'DIRECT', 'TAPCLIENT': 'ASTROQUERY',
                       'RELEASE': schema}
        if product_type == 'observation':
            params_dict['FILTER'] = filter
            params_dict['RETRIEVAL_TYPE'] = 'OBSERVATION'
            params_dict['OBS_ID'] = id
        if product_type == 'mosaic':
            params_dict['MSC_ID'] = id
            params_dict['RETRIEVAL_TYPE'] = 'MOSAIC'

        output_file_full_path, output_dir = self.__set_dirs(output_file=output_file, observation_id=id)
        try:
            self.__eucliddata.load_data(params_dict=params_dict, output_file=output_file_full_path, verbose=verbose)
        except HTTPError as err:
            log.error(f"Cannot retrieve products for observation {id}. HTTP error: {err}")
            return
        except Exception as exx:
            log.error(f'Cannot retrieve products for observation {id}: {str(exx)}')
            return

        files = []
        self.__extract_file(output_file_full_path=output_file_full_path, output_dir=output_dir, files=files)
        if files:
            return files

        self.__check_file_number(output_dir=output_dir, output_file_name=os.path.basename(output_file_full_path),
                                 output_file_full_path=output_file_full_path, files=files)

        return files

    def __get_tile_catalogue_list(self, *, tile_index, product_type, verbose=False):
        """
         Description
         -----------
         Get the list of products of a given EUCLID tile_index (mosaics)

        Parameters
        ----------
        tile_index : str, mandatory
            tile index for products searchable by tile.

        Searchable products by tile_index: 'DpdMerBksMosaic', 'dpdPhzPfOutputForL3', 'dpdPhzPfOutputCatalog',
            'dpdMerFinalCatalog','dpdSpePfOutputCatalog', 'dpdSheLensMcChains', 'dpdHealpixBitMaskVMPZ',
            'dpdHealpixFootprintMaskVMPZ', 'dpdHealpixCoverageVMPZ', 'dpdHealpixDepthMapVMPZ','dpdHealpixInfoMapVMPZ',
            'dpdSheBiasParams', 'dpdSheLensMcFinalCatalog', 'dpdSheLensMcRawCatalog', 'dpdSheMetaCalFinalCatalog',
            'dpdSheMetaCalRawCatalog', 'dpdSleDetectionOutput', 'dpdSleModelOutput', 'DpdSirCombinedSpectra',
            'DpdMerSegmentationMap'
        product_type : str, mandatory, default None
            Available product types:

                #. MER
                     DpdMerSegmentationMap: Segmentation Map Product
                     DpdMerBksMosaic: Background-Subtracted Mosaic Product
                     dpdMerFinalCatalog: Final Catalog Product
                #. PHZ
                    dpdPhzPfOutputCatalog: PHZ PF output catalog product for Deep tiles
                    dpdPhzPfOutputForL3: PHZ PF output catalog product for LE3
                #. SPE
                    dpdSpePfOutputCatalog: SPE PF output catalog product
                #. SHE
                    dpdSheLensMcChains: Shear LensMc Chains
                    dpdSheBiasParams: Shear Bias Parameters Data Product
                    dpdSheLensMcFinalCatalog: Shear LensMc Final Catalog
                    dpdSheMetaCalFinalCatalog: Shear MetaCal Final Catalog
                    dpdSheMetaCalRawCatalog: Shear LensMc Raw Catalog
                    dpdSheLensMcRawCatalog: Shear LensMc Raw Catalog
                #. VMPZ-ID
                    dpdHealpixBitMaskVMPZ: Input Product: Bit Mask Parameters
                    dpdHealpixFootprintMaskVMPZ: Output Product: HEALPix Footprint Mask
                    dpdHealpixCoverageVMPZ: Output Product: HEALPix Coverage Mask
                    dpdHealpixDepthMapVMPZ: Input Product: Depth Maps Parameters
                    dpdHealpixInfoMapVMPZ: Input Product: Information Map Parameters
                #. SLE
                    dpdSleDetectionOutput: SLE Detection Output
                    dpdSleModelOutput: SLE Model Output
                #. SIR
                    DpdSirCombinedSpectra: Combined Spectra Product
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The list of products (astropy.table)
        """

        if tile_index is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_TILE_ID)
        if product_type is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_PRODUCT_TYPE)

        query = None

        if product_type in conf.MOSAIC_PRODUCTS:
            query = (
                f"SELECT DISTINCT mosaic_product.file_name, mosaic_product.mosaic_product_oid, "
                f"mosaic_product.tile_index, mosaic_product.instrument_name, mosaic_product.filter_name, "
                f"mosaic_product.category, mosaic_product.second_type, mosaic_product.ra, mosaic_product.dec, "
                f"mosaic_product.release_name, "
                f"mosaic_product.technique FROM sedm.mosaic_product WHERE mosaic_product.tile_index = '{tile_index}' "
                f"AND "
                f"mosaic_product.product_type = '{product_type}';")

        if product_type in conf.BASIC_DOWNLOAD_DATA_PRODUCTS:
            query = (
                f"SELECT basic_download_data.basic_download_data_oid, basic_download_data.product_type, "
                f"basic_download_data.product_id, CAST(basic_download_data.observation_id_list as text) AS "
                f"observation_id_list, CAST(basic_download_data.tile_index_list as text) AS tile_index_list, "
                f"CAST(basic_download_data.patch_id_list as text) AS patch_id_list, "
                f"CAST(basic_download_data.filter_name as text) AS filter_name, basic_download_data.release_name FROM "
                f"sedm.basic_download_data WHERE '{tile_index}'=ANY(tile_index_list) AND product_type = '"
                f"{product_type}' "
                f"ORDER BY observation_id_list ASC;")

        if product_type in conf.COMBINED_SPECTRA_PRODUCTS:
            query = (
                f"SELECT combined_spectra.combined_spectra_oid, combined_spectra.lambda_range, "
                f"combined_spectra.tile_index, combined_spectra.stc_s, combined_spectra.product_type, "
                f"combined_spectra.product_id, combined_spectra.observation_id_list FROM sedm.combined_spectra "
                f"WHERE combined_spectra.tile_index = '{tile_index}' AND combined_spectra.product_type = '"
                f"{product_type}';")

        if product_type in conf.MER_SEGMENTATION_MAP_PRODUCTS:
            query = (
                f"SELECT mer_segmentation_map.file_name, mer_segmentation_map.segmentation_map_oid, "
                f"mer_segmentation_map.ra, mer_segmentation_map.dec, mer_segmentation_map.stc_s, "
                f"mer_segmentation_map.tile_index, "
                f"CAST(mer_segmentation_map.observation_id_list as TEXT) AS observation_id_list, "
                f"mer_segmentation_map.product_type, mer_segmentation_map.product_id FROM sedm.mer_segmentation_map "
                f"WHERE mer_segmentation_map.tile_index = '{tile_index}' AND "
                f"mer_segmentation_map.product_type = '{product_type}';")

        if query is None:
            raise ValueError(f"Invalid product type {product_type}.")

        job = super().launch_job(query=query, output_format='votable_plain', verbose=verbose,
                                 format_with_results_compressed=('votable_gzip',))
        return job.get_results()

    def get_product_list(self, *, observation_id=None, tile_index=None, product_type, verbose=False):
        """
        Description
        -----------
        Get the list of products of a given EUCLID id searching by observation_id or tile_index.

        Parameters
        ----------
        observation_id : str, mandatory
            observation id for observations. It is not compatible with parameter tile_index.

            Searchable products by observation_id: 'dpdVisRawFrame', 'dpdNispRawFrame',
            ,'DpdVisCalibratedQuadFrame','DpdVisCalibratedFrameCatalog', 'DpdVisStackedFrame',
            'DpdVisStackedFrameCatalog',
            'DpdNirCalibratedFrame', 'DpdNirCalibratedFrameCatalog', 'DpdNirStackedFrameCatalog', 'DpdNirStackedFrame',
            'DpdMerSegmentationMap', 'dpdMerFinalCatalog',
            'dpdPhzPfOutputCatalog', 'dpdPhzPfOutputForL3',
            'dpdSpePfOutputCatalog',
            'dpdSheLensMcChains','dpdSheBiasParams', 'dpdSheLensMcFinalCatalog','dpdSheLensMcRawCatalog',
            'dpdSheMetaCalFinalCatalog', 'dpdSheMetaCalRawCatalog',
            'dpdHealpixBitMaskVMPZ', 'dpdHealpixFootprintMaskVMPZ', 'dpdHealpixCoverageVMPZ',
            'dpdHealpixDepthMapVMPZ', 'dpdHealpixInfoMapVMPZ',
            'dpdSleDetectionOutput','dpdSleModelOutput',
            'DpdSirCombinedSpectra','dpdSirScienceFrame'

        tile_index : str, mandatory
            tile index for products searchable by tile. It is not compatible with parameter observation_id.

            Searchable products by tile_index:
            'DpdMerSegmentationMap', 'dpdMerFinalCatalog', 'DpdMerBksMosaic',
            'dpdPhzPfOutputCatalog','dpdPhzPfOutputForL3',
            'dpdSpePfOutputCatalog',
            'dpdSheLensMcChains', 'dpdSheBiasParams',  'dpdSheLensMcFinalCatalog', 'dpdSheLensMcRawCatalog',
            'dpdSheMetaCalFinalCatalog', 'dpdSheMetaCalRawCatalog',
            'dpdHealpixBitMaskVMPZ', 'dpdHealpixFootprintMaskVMPZ', 'dpdHealpixCoverageVMPZ',
            'dpdHealpixDepthMapVMPZ','dpdHealpixInfoMapVMPZ',
            dpdSleDetectionOutput', 'dpdSleModelOutput',
            'DpdSirCombinedSpectra'

        product_type : str, mandatory, default None
            Available product types:

            #. Euclid LE1 observations:

                #. VIS
                    DpdVisRawFrame: Vis Raw Frame Product
                #. NISP
                    DpdNispRawFrame: NISP Raw Frame Product

            #. Euclid LE2/LE3 products:

                #. VIS
                    DpdVisCalibratedQuadFrame: VIS Calibrated Frame Product
                    DpdVisCalibratedFrameCatalog: VIS Calibrated Frame Catalog
                    DpdVisStackedFrame: Vis Stacked Frame Product   - This product is not available in Q1
                    DpdVisStackedFrameCatalog: Vis Stacked Catalogue Product    - This product is not available in Q1
                #. NIR
                    DpdNirCalibratedFrame: NIR Calibrated Frame
                    DpdNirCalibratedFrameCatalog: NIR Calibrated Frame Catalog
                    DpdNirStackedFrame: NIR Stacked Frame   - This product is not available in Q1
                    DpdNirStackedFrameCatalog: NIR Stacked Frame Catalog    - This product is not available in Q1
                #. MER
                     DpdMerSegmentationMap: Segmentation Map Product
                     DpdMerBksMosaic: Background-Subtracted Mosaic Product
                     dpdMerFinalCatalog: Final Catalog Product   \
                                         - We suggest to use ADQL to retrieve data from this dataset.
                #. PHZ      - We suggest to use ADQL to retrieve data from these products.
                    dpdPhzPfOutputCatalog: PHZ PF output catalog product for weak lensing
                    dpdPhzPfOutputForL3: PHZ PF output catalog product for LE3
                #. SPE      - We suggest to use ADQL to retrieve data from this product.
                    dpdSpePfOutputCatalog: SPE PF output catalog product
                #. SHE      - None of these product are available in Q1
                    dpdSheLensMcChains: Shear LensMc Chains
                    dpdSheBiasParams: Shear Bias Parameters Data Product
                    dpdSheLensMcFinalCatalog: Shear LensMc Final Catalog
                    dpdSheLensMcRawCatalog: Shear LensMc Raw Catalog
                    dpdSheMetaCalFinalCatalog: Shear MetaCal Final Catalog
                    dpdSheMetaCalRawCatalog: Shear LensMc Raw Catalog
                #. VMPZ-ID
                    dpdHealpixBitMaskVMPZ: Input Product: Bit Mask Parameters
                    dpdHealpixFootprintMaskVMPZ: Output Product: HEALPix Footprint Mask
                    dpdHealpixCoverageVMPZ: Output Product: HEALPix Coverage Mask
                    dpdHealpixDepthMapVMPZ: Input Product: Depth Maps Parameters
                    dpdHealpixInfoMapVMPZ: Input Product: Information Map Parameters
                #. SLE      - None of these product are available in Q1
                    dpdSleDetectionOutput: SLE Detection Output
                    dpdSleModelOutput: SLE Model Output
                #. SIR
                    DpdSirCombinedSpectra: Combined Spectra Product \
                                           - We suggest to use ADQL to retrieve data (spectra) from this dataset.
                    dpdSirScienceFrame: Science Frame Product
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The list of products (astropy.table)
        """
        if product_type is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_PRODUCT_TYPE)

        if observation_id is not None and tile_index is not None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_OBSERVATION_ID_AND_TILE_ID)

        if observation_id is None and tile_index is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_OBSERVATION_ID + "; " + self.__ERROR_MSG_REQUESTED_TILE_ID)

        if tile_index is not None:
            return self.__get_tile_catalogue_list(tile_index=tile_index, product_type=product_type, verbose=verbose)

        query = None
        if product_type in conf.OBSERVATION_STACK_PRODUCTS:
            query = (f"SELECT observation_stack.file_name, observation_stack.observation_stack_oid, "
                     f"observation_stack.observation_id, observation_stack.ra, observation_stack.dec, "
                     f"observation_stack.instrument_name, observation_stack.filter_name, "
                     "observation_stack.release_name, observation_stack.category, observation_stack.second_type, "
                     f"observation_stack.technique, observation_stack.product_type, observation_stack.start_time, "
                     f"observation_stack.duration FROM sedm.observation_stack WHERE "
                     f" observation_stack.observation_id = '{observation_id}' AND observation_stack.product_type = '"
                     f"{product_type}';")

        if product_type in conf.BASIC_DOWNLOAD_DATA_PRODUCTS:
            query = (
                f"SELECT basic_download_data.basic_download_data_oid, basic_download_data.product_type, "
                f"basic_download_data.product_id, CAST(basic_download_data.observation_id_list as text) AS "
                f"observation_id_list, CAST(basic_download_data.tile_index_list as text) AS tile_index_list, "
                f"CAST(basic_download_data.patch_id_list as text) AS patch_id_list, "
                f"CAST(basic_download_data.filter_name as text) AS filter_name, basic_download_data.release_name FROM "
                f"sedm.basic_download_data WHERE '{observation_id}'=ANY(observation_id_list) AND product_type = '"
                f"{product_type}' "
                f"ORDER BY observation_id_list ASC;")

        if product_type in conf.MER_SEGMENTATION_MAP_PRODUCTS:
            query = (
                f"SELECT mer_segmentation_map.file_name, mer_segmentation_map.segmentation_map_oid, "
                f"mer_segmentation_map.ra, mer_segmentation_map.dec, mer_segmentation_map.stc_s, "
                f"mer_segmentation_map.tile_index, "
                f"mer_segmentation_map.product_type, mer_segmentation_map.product_id FROM sedm.mer_segmentation_map "
                f"WHERE ( observation_id_list = '{observation_id}' OR observation_id_list like '{observation_id},"
                f"%' OR observation_id_list "
                f"like '%,{observation_id}' OR CAST(observation_id_list as TEXT) like '%,{observation_id},%' ) AND "
                f"mer_segmentation_map.product_type = '{product_type}';")

        if product_type in conf.RAW_FRAME_PRODUCTS:

            if product_type == "dpdNispRawFrame":
                instrument_name = "NISP"
            else:
                instrument_name = "VIS"

            query = (
                f"SELECT raw_frame.file_name, raw_frame.rawframe_oid, raw_frame.observation_id, "
                f"raw_frame.instrument_name, raw_frame.data_set_release, raw_frame.filter_name, "
                f"raw_frame.observation_mode, raw_frame.grism_wheel_pos, raw_frame.cal_block_id, "
                f"raw_frame.cal_block_variant, raw_frame.ra, raw_frame.dec, raw_frame.obs_time_utc, "
                f"raw_frame.exposure_time FROM sedm.raw_frame WHERE raw_frame.observation_id = '{observation_id}' "
                f"AND raw_frame.instrument_name = '{instrument_name}';")

        if product_type in conf.CALIBRATED_FRAME_PRODUCTS:
            query = (
                f"SELECT calibrated_frame.file_name, calibrated_frame.calibrated_frame_oid, "
                f"calibrated_frame.observation_id, calibrated_frame.instrument_name, calibrated_frame.filter_name, "
                f"calibrated_frame.ra, calibrated_frame.dec, calibrated_frame.stc_s, calibrated_frame.start_time, "
                f"calibrated_frame.end_time, calibrated_frame.duration "
                f"FROM sedm.calibrated_frame WHERE calibrated_frame.observation_id = '{observation_id}' AND "
                f"calibrated_frame.product_type = '{product_type}';")

        if product_type in conf.FRAME_CATALOG_PRODUCTS:
            query = (
                f"SELECT frame_catalog.file_name, frame_catalog.catalog_oid, frame_catalog.observation_id, "
                f"frame_catalog.instrument_name, frame_catalog.filter_name, frame_catalog.ra, frame_catalog.dec, "
                f"frame_catalog.datarange_start_time, frame_catalog.datarange_end_time, "
                f"frame_catalog.product_type, frame_catalog.product_id FROM sedm.frame_catalog "
                f"WHERE frame_catalog.observation_id = '{observation_id}' AND frame_catalog.product_type = '"
                f"{product_type}';")

        if product_type in conf.COMBINED_SPECTRA_PRODUCTS:
            query = (
                f"SELECT combined_spectra.combined_spectra_oid, combined_spectra.lambda_range, "
                f"combined_spectra.tile_index, combined_spectra.stc_s, combined_spectra.product_type, "
                f"combined_spectra.product_id FROM sedm.combined_spectra "
                f"WHERE ( observation_id_list = '{observation_id}' OR observation_id_list like '{observation_id} %' "
                f"OR observation_id_list "
                f"like '% {observation_id}' OR observation_id_list like '% {observation_id} %' ) AND "
                f"combined_spectra.product_type = '{product_type}';")

        if product_type in conf.SIR_SCIENCE_FRAME_PRODUCTS:
            instrument_name = "NISP"

            query = (
                f"SELECT sir_science_frame.file_name, sir_science_frame.science_frame_oid, "
                f"sir_science_frame.observation_id, sir_science_frame.instrument_name, sir_science_frame.stc_s, "
                f"sir_science_frame.prod_sdc FROM sedm.sir_science_frame "
                f"WHERE sir_science_frame.observation_id = '{observation_id}' AND sir_science_frame.instrument_name = '"
                f"{instrument_name}';")

        if query is None:
            raise ValueError(f"Invalid product type {product_type}.")

        job = super().launch_job(query=query, output_format='votable_plain', verbose=verbose,
                                 format_with_results_compressed=('votable_gzip',))
        return job.get_results()

    def get_product(self, *, file_name=None, product_id=None, schema='sedm', output_file=None, verbose=False):
        """
        Description
        -----------
        Downloads a product given its file name or product id

        Parameters
        ----------
        file_name : str, optional, default None
            file name for the product. More than one can be specified between comma. Either file_name or product_id
            is mandatory
        product_id : str, optional, default None
            product id. More than one can be specified between comma. Either file_name or product_id is mandatory
        schema : str, optional, default 'sedm'
            the data release name (schema) in which the product should be searched
        output_file : str, optional
            output file, use zip extension when downloading multiple files
            if no value is provided, a temporary one is created
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The fits file(s) are downloaded, and the local path where the product(s) are saved is returned
        """

        if file_name is None and product_id is None:
            raise ValueError("'file_name' and 'product_id' are both None")

        params_dict = {'TAPCLIENT': 'ASTROQUERY', 'RELEASE': schema}
        if file_name is not None:
            params_dict['FILE_NAME'] = file_name
            params_dict['RETRIEVAL_TYPE'] = 'FILE'
        if product_id is not None:
            params_dict['PRODUCT_ID'] = product_id
            params_dict['RETRIEVAL_TYPE'] = 'PRODUCT_ID'

        output_file_full_path, output_dir = self.__set_dirs(output_file=output_file, observation_id='temp')
        try:
            self.__eucliddata.load_data(params_dict=params_dict, output_file=output_file_full_path, verbose=verbose)
        except HTTPError as err:
            log.error(
                f"Cannot retrieve products for file_name {file_name} or product_id {product_id}. HTTP error: {err}")
            return
        except Exception as exx:
            log.error(f"Cannot retrieve products for file_name {file_name} or product_id {product_id}: {str(exx)}")
            return

        files = []
        self.__extract_file(output_file_full_path=output_file_full_path, output_dir=output_dir, files=files)
        if files:
            return files

        self.__check_file_number(output_dir=output_dir, output_file_name=os.path.basename(output_file_full_path),
                                 output_file_full_path=output_file_full_path, files=files)

        return files

    def get_cutout(self, *, file_path=None, instrument=None, id=None, coordinate, radius, output_file=None,
                   verbose=False):
        """
        Description
        -----------
        Downloads a cutout given its file path, instrument and obs_id, and the cutout region

        Parameters
        ----------
        file_path : str, mandatory, default None
            file path for the product on the server
        instrument : str, mandatory, default None
            instrument for the product, can be 'VIS' or 'NISP'
        id : str, mandatory, default None
            the observation id or tile index for MER products
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            the radius of the cutout to generate
        output_file : str, optional
            output file. If no value is provided, a temporary one is created
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The fits file is downloaded, and the local path where the cutout is saved is returned
        """

        if file_path is None or instrument is None or id is None or coordinate is None or radius is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_GENERIC)

        # Parse POS
        radius_deg = Angle(self.__get_quantity_input(radius, "radius")).to_value(u.deg)
        if radius_deg > 0.5:
            raise ValueError(self.__ERROR_MSG_REQUESTED_RADIUS)
        coord = commons.parse_coordinates(coordinate)
        ra_hours, dec = commons.coord_to_radec(coord)
        ra = ra_hours * 15.0  # Converts to degrees
        pos = """CIRCLE,{ra},{dec},{radius}""".format(**{'ra': ra, 'dec': dec, 'radius': radius_deg})

        params_dict = {'TAPCLIENT': 'ASTROQUERY', 'FILEPATH': file_path, 'COLLECTION': instrument, 'OBSID': id,
                       'POS': pos}

        output_file_full_path, output_dir = self.__set_dirs(output_file=output_file, observation_id='temp')
        try:
            self.__euclidcutout.load_data(params_dict=params_dict, output_file=output_file_full_path, verbose=verbose)
        except HTTPError as err:
            log.error(
                f"Cannot retrieve the product for file_path {file_path}, obsId {id}, and collection {instrument}. "
                f"HTTP error: {err}")
            return
        except Exception as exx:
            log.error(
                f"Cannot retrieve the product for file_path {file_path}, obsId {id}, and collection {instrument}: "
                f"{str(exx)}")
            return

        files = []
        self.__extract_file(output_file_full_path=output_file_full_path, output_dir=output_dir, files=files)
        if files:
            return files

        self.__check_file_number(output_dir=output_dir, output_file_name=os.path.basename(output_file_full_path),
                                 output_file_full_path=output_file_full_path, files=files)

        return files

    def get_spectrum(self, *, source_id, schema='sedm', retrieval_type="ALL", output_file=None, verbose=False):
        """
        Description
        -----------
        Downloads a spectrum with datalink.

        The spectrum associated with the source_id is downloaded as a compressed fits file, and the files it contains
        are returned in a list. The compressed fits file is saved in the local path given by output_file. If this
        parameter is not set, the result is saved in the file "<working
        directory>/temp_<%Y%m%d_%H%M%S>/<source_id>.fits.zip". In any case, the content of the zip file is
        automatically extracted.

        Parameters
        ----------
        source_id : str, mandatory, default None
            source id for the spectrum
        schema : str, mandatory, default 'sedm'
            the data release
        retrieval_type : str, optional, default 'ALL' to retrieve all data from the list of sources
            retrieval type identifier. Possible values are: 'SPECTRA_BGS' for the blue spectrum and 'SPECTRA_RGS' for
            the red one.
        output_file : str, optional
            output file name. If no value is provided, a temporary one is created with the name
            "<working directory>/temp_<%Y%m%d_%H%M%S>/<source_id>.fits"
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of files: the files contained in the downloaded compressed fits file. The format of the file is
        SPECTRA_<colour>-<schema> <source_id>.fits', where <colour> is BGS or RGS, and <schema> and <source_id> are
        taken from the input parameters.

        """

        if source_id is None or schema is None:
            raise ValueError(self.__ERROR_MSG_REQUESTED_GENERIC)

        rt = str(retrieval_type).upper()
        if rt != 'ALL' and rt not in self.__VALID_DATALINK_RETRIEVAL_TYPES:
            raise ValueError(f"Invalid argument value for 'retrieval_type'. Found {retrieval_type}, "
                             f"expected: 'ALL' or any of {self.__VALID_DATALINK_RETRIEVAL_TYPES}")

        params_dict = {}

        id_value = """{schema} {source_id}""".format(**{'schema': schema, 'source_id': source_id})
        params_dict['ID'] = id_value
        params_dict['SCHEMA'] = schema
        params_dict['RETRIEVAL_TYPE'] = str(retrieval_type)
        params_dict['USE_ZIP_ALWAYS'] = 'true'
        params_dict['TAPCLIENT'] = 'ASTROQUERY'

        fits_file = source_id + '.fits.zip'

        if output_file is not None:
            if not output_file.endswith('.zip'):
                output_file = output_file + '.zip'

            if os.path.dirname(output_file) == '':
                output_file = os.path.join(os.getcwd(), output_file)

            if verbose:
                print(f"output file: {output_file}")

        output_file_full_path, output_dir = self.__set_dirs(output_file=output_file, observation_id=fits_file)

        if os.listdir(output_dir):
            raise IOError(f'The directory is not empty: {output_dir}')

        try:
            self.__eucliddata.load_data(params_dict=params_dict, output_file=output_file_full_path, verbose=verbose)
        except HTTPError as err:
            log.error(f'Cannot retrieve spectrum for source_id {source_id}, schema {schema}. HTTP error: {err}')
            return
        except Exception as exx:
            log.error(f'Cannot retrieve spectrum for source_id {source_id}, schema {schema}: {str(exx)}')
            return

        files = []
        self.__extract_file(output_file_full_path=output_file_full_path, output_dir=output_dir, files=files)

        if files:
            return files

        self.__check_file_number(output_dir=output_dir,
                                 output_file_name=os.path.basename(output_file_full_path),
                                 output_file_full_path=output_file_full_path,
                                 files=files)

        return files

    def get_datalinks(self, ids, *, linking_parameter='SOURCE_ID', verbose=False):
        """Gets datalinks associated to the provided identifiers
        TAP+ only

        Parameters
        ----------
        ids : str, int, list of str or list of int, mandatory
            list of identifiers
        linking_parameter : str, optional, default SOURCE_ID, valid values: SOURCE_ID
            By default, all the identifiers are considered as source_id
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object

        """

        return self.__eucliddata.get_datalinks(ids=ids, linking_parameter=linking_parameter, verbose=verbose)


Euclid = EuclidClass()
