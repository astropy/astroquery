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
Modified on 18 Ene. 2022 by mhsarmiento
"""
import datetime
import json
import os
import shutil
import zipfile
from collections.abc import Iterable

from astropy import units
from astropy import units as u
from astropy.coordinates import Angle
from astropy.io import fits
from astropy.io import votable
from astropy.table import Table
from astropy.units import Quantity
from astropy.utils.decorators import deprecated_renamed_argument
from requests import HTTPError

from astroquery import log
from astroquery.utils import commons
from astroquery.utils.tap import TapPlus
from astroquery.utils.tap import taputils
from . import conf


class GaiaClass(TapPlus):
    """
    Proxy class to default TapPlus object (pointing to Gaia Archive)
    """
    MAIN_GAIA_TABLE = None
    MAIN_GAIA_TABLE_RA = conf.MAIN_GAIA_TABLE_RA
    MAIN_GAIA_TABLE_DEC = conf.MAIN_GAIA_TABLE_DEC
    ROW_LIMIT = conf.ROW_LIMIT
    VALID_DATALINK_RETRIEVAL_TYPES = conf.VALID_DATALINK_RETRIEVAL_TYPES
    VALID_LINKING_PARAMETERS = conf.VALID_LINKING_PARAMETERS
    GAIA_MESSAGES = "notification?action=GetNotifications"
    USE_NAMES_OVER_IDS = True
    """When `True` use the ``name`` attributes of columns as the names of columns in the `astropy.table.Table` instance.
       Since names are not guaranteed to be unique, this may cause  some columns to be renamed by appending numbers to
       the end. Otherwise, use the ID attributes as the column names.
    """

    def __init__(self, *, tap_plus_conn_handler=None,
                 datalink_handler=None,
                 gaia_tap_server='https://gea.esac.esa.int/',
                 gaia_data_server='https://gea.esac.esa.int/',
                 tap_server_context="tap-server",
                 data_server_context="data-server",
                 verbose=False, show_server_messages=True):
        super(GaiaClass, self).__init__(url=gaia_tap_server,
                                        server_context=tap_server_context,
                                        tap_context="tap",
                                        upload_context="Upload",
                                        table_edit_context="TableTool",
                                        data_context="data",
                                        datalink_context="datalink",
                                        connhandler=tap_plus_conn_handler,
                                        verbose=verbose,
                                        use_names_over_ids=self.USE_NAMES_OVER_IDS)
        # Data uses a different TapPlus connection
        if datalink_handler is None:
            self.__gaiadata = TapPlus(url=gaia_data_server,
                                      server_context=data_server_context,
                                      tap_context="tap",
                                      upload_context="Upload",
                                      table_edit_context="TableTool",
                                      data_context="data",
                                      datalink_context="datalink",
                                      verbose=verbose,
                                      use_names_over_ids=self.USE_NAMES_OVER_IDS)
        else:
            self.__gaiadata = datalink_handler

        # Enable notifications
        if show_server_messages:
            self.get_status_messages()

    def login(self, *, user=None, password=None, credentials_file=None, verbose=False):
        """Performs a login.
        User and password arguments can be used or a file that contains
        username and password
        (2 lines: one for username and the following one for the password).
        If no arguments are provided, a prompt asking for username and
        password will appear.

        Parameters
        ----------
        user : str, default None
            login name
        password : str, default None
            user password
        credentials_file : str, default None
            file containing user and password in two lines
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        try:
            log.info("Login to gaia TAP server")
            TapPlus.login(self, user=user, password=password, credentials_file=credentials_file, verbose=verbose)
        except HTTPError:
            log.error("Error logging in TAP server")
            return
        new_user = self._TapPlus__user
        new_password = self._TapPlus__pwd
        try:
            log.info("Login to gaia data server")
            TapPlus.login(self.__gaiadata, user=new_user, password=new_password, verbose=verbose)
        except HTTPError:
            log.error("Error logging in data server")
            log.error("Logging out from TAP server")
            TapPlus.logout(self, verbose=verbose)

    def login_gui(self, *, verbose=False):
        """Performs a login using a GUI dialog

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        try:
            log.info("Login to gaia TAP server")
            TapPlus.login_gui(self, verbose=verbose)
        except HTTPError:
            log.error("Error logging in TAP server")
            return
        new_user = self._TapPlus__user
        new_password = self._TapPlus__pwd
        try:
            log.info("Login to gaia data server")
            TapPlus.login(self.__gaiadata, user=new_user, password=new_password, verbose=verbose)
        except HTTPError:
            log.error("Error logging in data server")
            log.error("Logging out from TAP server")
            TapPlus.logout(self, verbose=verbose)

    def logout(self, *, verbose=False):
        """Performs a logout

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        try:
            TapPlus.logout(self, verbose=verbose)
        except HTTPError:
            log.error("Error logging out TAP server")
            return
        log.info("Gaia TAP server logout OK")
        try:
            TapPlus.logout(self.__gaiadata, verbose=verbose)
            log.info("Gaia data server logout OK")
        except HTTPError:
            log.error("Error logging out data server")

    @deprecated_renamed_argument("output_file", None, since="0.4.8")
    def load_data(self, ids, *, data_release=None, data_structure='INDIVIDUAL', retrieval_type="ALL",
                  linking_parameter='SOURCE_ID', valid_data=False, band=None, avoid_datatype_check=False,
                  format="votable", dump_to_file=False, overwrite_output_file=False, verbose=False,
                  output_file=None):
        """Loads the specified table
        TAP+ only

        Parameters
        ----------
        ids :  str, int, str list or int list, mandatory
            list of identifiers
        data_release: str, optional, default None
            data release from which data should be taken. E.g. 'Gaia DR3'
            By default, it takes the current default one.
        data_structure: str, optional, default 'INDIVIDUAL'
            it can be 'INDIVIDUAL' or 'RAW':
            'INDIVIDUAL' means products are provided in separate files for each sourceId. All files are zipped
            in a single bundle, even if only one source/file is considered
            'RAW' means products are provided following a Data Model similar to that used in the MDB, meaning in
            particular that parameters stored as arrays will remain as such. A single file is provided for the data of
            all sourceIds together, but in this case there will be always be one row per sourceId
        retrieval_type : str, optional, default 'ALL' to retrieve all data  from the list of sources
            retrieval type identifier. For GAIA DR2 possible values are ['EPOCH_PHOTOMETRY']
            For GAIA DR3, possible values are ['EPOCH_PHOTOMETRY', 'RVS', 'XP_CONTINUOUS', 'XP_SAMPLED',
            'MCMC_GSPPHOT' or 'MCMC_MSC']
            For GAIA DR4, possible values will be ['EPOCH_PHOTOMETRY', 'RVS', 'XP_CONTINUOUS', 'XP_SAMPLED',
            'MCMC_GSPPHOT', 'MCMC_MSC', 'EPOCH_ASTROMETRY', 'RVS_EPOCH_DATA_SINGLE',
            'RVS_EPOCH_DATA_DOUBLE','RVS_EPOCH_SPECTRUM', 'RVS_TRANSIT', 'EPOCH_ASTROMETRY_CROWDED_FIELD',
            'EPOCH_IMAGE', 'EPOCH_PHOTOMETRY_CCD', 'XP_EPOCH_SPECTRUM_SSO', 'XP_EPOCH_CROWDING', 'XP_MEAN_SPECTRUM',
            'XP_EPOCH_SPECTRUM', 'CROWDED_FIELD_IMAGE', 'EPOCH_ASTROMETRY_BRIGHT']. Note that for
            'CROWDED_FIELD_IMAGE' only the format 'fits' can be used, and that its image, in the principal header, will
            not be available in the returned dictionary. Set 'output_file' to retrieve all data: image + tables.
        linking_parameter : str, optional, default SOURCE_ID, valid values: SOURCE_ID, TRANSIT_ID, IMAGE_ID
            By default, all the identifiers are considered as source_id
            SOURCE_ID: the identifiers are considered as source_id
            TRANSIT_ID: the identifiers are considered as transit_id
            IMAGE_ID: the identifiers are considered as sif_observation_id
        valid_data : bool, optional, default False
            By default, the epoch photometry service returns all available data, including
            data rows where flux is null and/or the rejected_by_photometry flag is set to True.
            In order to retrieve only valid data (data rows where flux is not null and/or the
            rejected_by_photometry flag is set to False) this request parameter should be included
            with valid_data=True.
        band : str, optional, default None, valid values: G, BP, RP
            By default, the epoch photometry service returns all the
            available photometry bands for the requested source.
            This parameter allows to filter the output lightcurve by its band.
        avoid_datatype_check: boolean, optional, default False.
            By default, this value will be set to False. If it is set to 'true'
            the Datalink items tags will not be checked.
        format : str, optional, default 'votable'
            loading format. Other available formats are 'csv', 'ecsv','votable_plain', 'json' and 'fits'
        dump_to_file: boolean, optional, default False.
            If it is true, a compressed directory named "datalink_output_<time_stamp>.zip" with all the DataLink
            files is made in the current working directory. The <time_stamp> format follows the ISO 8601 standard:
            "YYYYMMDD_HHMMSS.mmmmmm".
        overwrite_output_file : boolean, optional, default False
            To overwrite the output file ("datalink_output.zip") if it already exists.
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A dictionary where the keys are the file names and its value is a list of astropy.table.table.Table objects
        """

        output_file_specified = False

        now = datetime.datetime.now(datetime.timezone.utc)
        if not dump_to_file:
            now_formatted = now.strftime("%Y%m%d_%H%M%S.%f")
            temp_dirname = "temp_" + now_formatted
            downloadname_formated = "download_" + now_formatted
            output_file = os.path.join(os.getcwd(), temp_dirname, downloadname_formated)

        else:
            output_file = 'datalink_output_' + now.strftime("%Y%m%dT%H%M%S.%f") + '.zip'
            output_file_specified = True
            output_file = os.path.abspath(output_file)
            log.info(f"DataLink products will be stored in the {output_file} file")

            if not overwrite_output_file and os.path.exists(output_file):
                raise ValueError(f"{output_file} file already exists. Please use overwrite_output_file='True' to "
                                 f"overwrite output file.")

        path = os.path.dirname(output_file)

        log.debug(f"Directory where the data will be saved: {path}")

        if path:
            if not os.path.isdir(path):
                try:
                    os.mkdir(path)
                except FileExistsError:
                    log.warn("Path %s already exist" % path)
                except OSError:
                    log.error("Creation of the directory %s failed" % path)

        if avoid_datatype_check is False:
            # we need to check params
            rt = str(retrieval_type).upper()
            if rt != 'ALL' and rt not in self.VALID_DATALINK_RETRIEVAL_TYPES:
                raise ValueError(f"Invalid mandatory argument 'retrieval_type'. Found {retrieval_type}, "
                                 f"expected: 'ALL' or any of {self.VALID_DATALINK_RETRIEVAL_TYPES}")

        params_dict = {}

        if not valid_data or str(retrieval_type) == 'ALL':
            params_dict['VALID_DATA'] = "false"
        elif valid_data:
            params_dict['VALID_DATA'] = "true"

        if band is not None:
            if band != 'G' and band != 'BP' and band != 'RP':
                raise ValueError(f"Invalid band value '{band}' (Valid values: 'G', 'BP' and 'RP)")
            else:
                params_dict['BAND'] = band
        if isinstance(ids, str):
            ids_arg = ids
        else:
            if isinstance(ids, int):
                ids_arg = str(ids)
            else:
                ids_arg = ','.join(str(item) for item in ids)
        params_dict['ID'] = ids_arg
        if data_release is not None:
            params_dict['RELEASE'] = data_release
        params_dict['DATA_STRUCTURE'] = data_structure
        params_dict['FORMAT'] = str(format)
        params_dict['RETRIEVAL_TYPE'] = str(retrieval_type)
        params_dict['USE_ZIP_ALWAYS'] = 'true'

        if linking_parameter not in self.VALID_LINKING_PARAMETERS:
            raise ValueError(
                f"Invalid linking_parameter value '{linking_parameter}' (Valid values: "
                f"{', '.join(self.VALID_LINKING_PARAMETERS)})")
        else:
            if linking_parameter != 'SOURCE_ID':
                params_dict['LINKING_PARAMETER'] = linking_parameter

        files = dict()
        try:
            self.__gaiadata.load_data(params_dict=params_dict, output_file=output_file, verbose=verbose)
            files = Gaia.__get_data_files(output_file=output_file, path=path)
        except Exception as err:
            raise err
        finally:
            if not output_file_specified:
                shutil.rmtree(path)
            else:
                for file in files.keys():
                    os.remove(os.path.join(os.getcwd(), path, file))

        if verbose:
            if output_file_specified:
                log.info("output_file = %s" % output_file)

        if log.isEnabledFor(20):
            log.debug("List of products available:")
            for item in sorted([key for key in files.keys()]):
                log.debug("Product = " + item)

        return files

    @staticmethod
    def __get_data_files(output_file, path):
        files = {}
        extracted_files = []

        with zipfile.ZipFile(output_file, "r") as zip_ref:
            extracted_files.extend(zip_ref.namelist())
            zip_ref.extractall(os.path.dirname(output_file))

        # r=root, d=directories, f = files
        for r, d, f in os.walk(path):
            for file in f:
                if file in extracted_files:
                    files[file] = os.path.join(r, file)

        for key, value in files.items():

            if key.endswith('.fits'):
                tables = []
                with fits.open(value) as hduList:
                    num_hdus = len(hduList)
                    for i in range(1, num_hdus):
                        table = Table.read(hduList[i], format='fits')
                        Gaia.correct_table_units(table)
                        tables.append(table)
                    files[key] = tables

            elif key.endswith('.xml'):
                tables = []
                for table in votable.parse(value).iter_tables():
                    tables.append(table)
                files[key] = tables

            elif key.endswith('.csv'):
                tables = []
                table = Table.read(value, format='ascii.csv', fast_reader=False)
                tables.append(table)
                files[key] = tables

            elif key.endswith('.json'):
                tables = []
                with open(value) as f:
                    data = json.load(f)

                    if data.get('data') and data.get('metadata'):

                        column_name = []
                        for name in data['metadata']:
                            column_name.append(name['name'])

                        result = Table(rows=data['data'], names=column_name, masked=True)

                        for v in data['metadata']:
                            col_name = v['name']
                            result[col_name].unit = v['unit']
                            result[col_name].description = v['description']
                            result[col_name].meta = {'metadata': v}

                        files[key] = result
                    else:
                        tables.append(Table.read(value, format='pandas.json'))
                        files[key] = tables

        return files

    def get_datalinks(self, ids, *, linking_parameter='SOURCE_ID', verbose=False):
        """Gets datalinks associated to the provided identifiers
        TAP+ only

        Parameters
        ----------
        ids : str, int, str list or int list, mandatory
            list of identifiers
        linking_parameter : str, optional, default SOURCE_ID, valid values: SOURCE_ID, TRANSIT_ID, IMAGE_ID
            By default, all the identifiers are considered as source_id
            SOURCE_ID: the identifiers are considered as source_id
            TRANSIT_ID: the identifiers are considered as transit_id
            IMAGE_ID: the identifiers are considered as sif_observation_id
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object

        Examples
        --------
        Id formats.

        -- Gaia.get_datalinks(iids=1104405489608579584) # single id as an int

        -- Gaia.get_datalinks(ids='1104405489608579584, 1809140662896080256') # multiple ids as a str

        -- Gaia.get_datalinks(ids=(1104405489608579584, 1809140662896080256)) # multiple ids as an int list

        -- Gaia.get_datalinks(ids=('1104405489608579584','1809140662896080256')) # multiple ids as str list

        -- Gaia.get_datalinks(ids='4295806720-38655544960') # range of ids as a str

        -- Gaia.get_datalinks(ids='4295806720-38655544960, 549755818112-1275606125952') # multiple ranges of ids as
        a str

        -- Gaia.get_datalinks(ids=('4295806720-38655544960', '549755818112-1275606125952') # multiple ranges of ids
        as a str list

        -- Gaia.get_datalinks(ids='Gaia DR3 1104405489608579584') # single designator

        -- Gaia.get_datalinks(ids='Gaia DR3 1104405489608579584, Gaia DR3 1809140662896080256') # multiple
        designators as a str

        -- Gaia.get_datalinks(ids=('Gaia DR3 1104405489608579584','Gaia DR3 1809140662896080256')) # multiple
        designators as a str list

        -- Gaia.get_datalinks(ids='Gaia DR3 4295806720-Gaia DR3 38655544960') # range of designators as a str

        -- Gaia.get_datalinks(ids='Gaia DR3 4295806720-Gaia DR3 38655544960, Gaia DR3 549755818112-Gaia DR3
        1275606125952') # multiple ranges of designators as a str

        -- Gaia.get_datalinks(ids=('Gaia DR3 4295806720-Gaia DR3 38655544960', 'Gaia DR3 549755818112-Gaia DR3
        1275606125952')) # multiple ranges of designators as a str list

        -- Gaia.get_datalinks(ids='Gaia DR3 4295806720-Gaia DR3 38655544960, Gaia DR2 549755818112-Gaia DR2
        1275606125952') # multiple ranges of designators with different releases as a str

        -- Gaia.get_datalinks(ids=('Gaia DR3 4295806720-Gaia DR3 38655544960', 'Gaia DR2 549755818112-Gaia DR2
        1275606125952')) # multiple ranges of designators with different releases as a str list
        """

        if linking_parameter not in self.VALID_LINKING_PARAMETERS:
            raise ValueError(
                f"Invalid linking_parameter value '{linking_parameter}' (Valid values: "
                f"{', '.join(self.VALID_LINKING_PARAMETERS)})")

        final_linking_parameter = None
        if linking_parameter != 'SOURCE_ID':
            final_linking_parameter = linking_parameter

        return self.__gaiadata.get_datalinks(ids=ids, linking_parameter=final_linking_parameter, verbose=verbose)

    def __query_object(self, coordinate, *, radius=None, width=None, height=None,
                       async_job=False, verbose=False, columns=()):
        """Launches a job
        TAP & TAP+

        Parameters
        ----------
        coordinate : str or astropy.coordinate, mandatory
            coordinates center point
        radius : str or astropy.units if no 'width' nor 'height' are provided
            radius (deg)
        width : str or astropy.units if no 'radius' is provided
            box width
        height : str or astropy.units if no 'radius' is provided
            box height
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        verbose : bool, optional, default 'False'
            flag to display information about the process
        columns: list, optional, default ()
            if empty, all columns will be selected

        Returns
        -------
        The job results (astropy.table).
        """
        coord = self.__getCoordInput(coordinate, "coordinate")

        if radius is not None:
            job = self.__cone_search(coord, radius, async_job=async_job, verbose=verbose, columns=columns)
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
                    """.format(**{'row_limit': "TOP {0}".format(self.ROW_LIMIT) if self.ROW_LIMIT > 0 else "",
                                  'ra_column': self.MAIN_GAIA_TABLE_RA, 'dec_column': self.MAIN_GAIA_TABLE_DEC,
                                  'columns': columns, 'table_name': self.MAIN_GAIA_TABLE or conf.MAIN_GAIA_TABLE,
                                  'ra': ra, 'dec': dec,
                                  'width': widthDeg.value, 'height': heightDeg.value})
            if async_job:
                job = self.launch_job_async(query, verbose=verbose)
            else:
                job = self.launch_job(query, verbose=verbose)
        return job.get_results()

    def query_object(self, coordinate, *, radius=None, width=None, height=None, verbose=False, columns=()):
        """Launches a synchronous cone search for the input search radius or the box on the sky, sorted by angular
        separation
        TAP & TAP+

        Parameters
        ----------
        coordinate : str or astropy.coordinates, mandatory
            coordinates center point
        radius : str or astropy.units if no 'width'/'height' are provided
            radius (deg)
        width : str or astropy.units if no 'radius' is provided
            box width
        height : str or astropy.units if no 'radius' is provided
            box height
        verbose : bool, optional, default 'False'
            flag to display information about the process
        columns: list, optional, default ()
            if empty, all columns will be selected

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius=radius, width=width, height=height, async_job=False,
                                   verbose=verbose, columns=columns)

    def query_object_async(self, coordinate, *, radius=None, width=None, height=None, verbose=False, columns=()):
        """Launches an asynchronous cone search for the input search radius or the box on the sky, sorted by angular
        separation
        TAP & TAP+

        Parameters
        ----------
        coordinate : str or astropy.coordinates, mandatory
            coordinates center point
        radius : str or astropy.units if no 'width'/'height' are provided
            radius
        width : str or astropy.units if no 'radius' is provided
            box width
        height : str or astropy.units if no 'radius' is provided
            box height
        verbose : bool, optional, default 'False'
            flag to display information about the process
        columns: list, optional, default ()
            if empty, all columns will be selected

        Returns
        -------
        The job results (astropy.table).
        """
        return self.__query_object(coordinate, radius=radius, width=width, height=height, async_job=True,
                                   verbose=verbose, columns=columns)

    def __cone_search(self, coordinate, radius, *, table_name=None,
                      ra_column_name=MAIN_GAIA_TABLE_RA,
                      dec_column_name=MAIN_GAIA_TABLE_DEC,
                      async_job=False,
                      background=False,
                      output_file=None, output_format="votable_gzip", verbose=False,
                      dump_to_file=False,
                      columns=()):
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
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        output_file : str, optional, default None
            file name where the results are saved if ``dump_to_file`` is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable_gzip'
            results format. Available formats are: 'votable', 'votable_plain',
             'fits', 'csv', 'ecsv' and 'json', default is 'votable'.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        columns: list, optional, default ()
            if empty, all columns will be selected

        Returns
        -------
        A Job object
        """
        radiusDeg = None
        coord = self.__getCoordInput(coordinate, "coordinate")
        raHours, dec = commons.coord_to_radec(coord)
        ra = raHours * 15.0  # Converts to degrees
        if radius is not None:
            radiusDeg = Angle(self.__getQuantityInput(radius, "radius")).to_value(u.deg)

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
                              'radius': radiusDeg,
                              'table_name': table_name or self.MAIN_GAIA_TABLE or conf.MAIN_GAIA_TABLE})

        if async_job:
            return self.launch_job_async(query=query, output_file=output_file, output_format=output_format,
                                         verbose=verbose, dump_to_file=dump_to_file, background=background)
        else:
            return self.launch_job(query=query, output_file=output_file, output_format=output_format, verbose=verbose,
                                   dump_to_file=dump_to_file)

    def cone_search(self, coordinate, *, radius=None,
                    table_name=None,
                    ra_column_name=MAIN_GAIA_TABLE_RA,
                    dec_column_name=MAIN_GAIA_TABLE_DEC,
                    output_file=None,
                    output_format="votable_gzip", verbose=False,
                    dump_to_file=False,
                    columns=()):
        """Cone search sorted by distance (sync.)
        TAP & TAP+

        Parameters
        ----------
        coordinate : str or astropy.coordinate, mandatory
            coordinates center point
        radius : str or astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
        output_file : str, optional, default None
            file name where the results are saved if ``dump_to_file`` is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable_gzip'
            results format. Available formats are: 'votable', 'votable_plain',
             'fits', 'csv', 'ecsv' and 'json', default is 'votable'.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        columns: list, optional, default ()
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

    def cone_search_async(self, coordinate, *, radius=None,
                          table_name=None,
                          ra_column_name=MAIN_GAIA_TABLE_RA,
                          dec_column_name=MAIN_GAIA_TABLE_DEC,
                          background=False,
                          output_file=None, output_format="votable_gzip",
                          verbose=False, dump_to_file=False, columns=()):
        """Cone search sorted by distance (async)
        TAP & TAP+

        Parameters
        ----------
        coordinate : str or astropy.coordinate, mandatory
            coordinates center point
        radius : str or astropy.units, mandatory
            radius
        table_name : str, optional, default main gaia table name doing the cone search against
        ra_column_name : str, optional, default ra column in main gaia table
            ra column doing the cone search against
        dec_column_name : str, optional, default dec column in main gaia table
            dec column doing the cone search against
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag
            specifies whether
            the execution will wait until results are available
        output_file : str, optional, default None
            file name where the results are saved if ``dump_to_file`` is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable_gzip'
            results format. Available formats are: 'votable', 'votable_plain',
             'fits', 'csv', 'ecsv' and 'json', default is 'votable'.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        columns: list, optional, default ()
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
                                  async_job=True,
                                  background=background,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file, columns=columns)

    def __checkQuantityInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(f"{msg} must be either a string or astropy coordinates")

    def __getQuantityInput(self, value, msg):
        if value is None:
            raise ValueError(f"Missing required argument: {msg}")
        if not (isinstance(value, str) or isinstance(value, units.Quantity)):
            raise ValueError(f"{msg} must be either a string or astropy.coordinates")

        if isinstance(value, str):
            return Quantity(value)
        else:
            return value

    def __checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(f"{msg} must be either a string or astropy.coordinates")

    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(f"{msg} must be either a string or astropy.coordinates")
        if isinstance(value, str):
            return commons.parse_coordinates(value)
        else:
            return value

    @staticmethod
    def correct_table_units(table):
        """Correct format in the units of the columns
        TAP & TAP+

        Parameters
        ----------
        table : `~astropy.table.Table`, mandatory
            change the format of the units in the columns of the input table: '.' by ' ' and "'" by ""
        """

        for cn in table.colnames:
            col = table[cn]
            if isinstance(col.unit, u.UnrecognizedUnit):
                try:
                    col.unit = u.Unit(col.unit.name.replace(".", " ").replace("'", ""))
                except Exception:
                    pass
            elif isinstance(col.unit, str):
                col.unit = col.unit.replace(".", " ").replace("'", "")

    def load_user(self, user_id, *, verbose=False):
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

        return self.is_valid_user(user_id=user_id, verbose=verbose)

    def cross_match(self, *, full_qualified_table_name_a,
                    full_qualified_table_name_b,
                    results_table_name,
                    radius=1.0,
                    background=False,
                    verbose=False):
        """Performs a cross-match between the specified tables
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
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """
        if radius < 0.1 or radius > 10.0:
            raise ValueError(f"Invalid radius value. Found {radius}, valid range is: 0.1 to 10.0")

        schemaA = taputils.get_schema_name(full_qualified_table_name_a)
        if schemaA is None:
            raise ValueError(f"Not found schema name in full qualified table A: '{full_qualified_table_name_a}'")
        tableA = taputils.get_table_name(full_qualified_table_name_a)
        schemaB = taputils.get_schema_name(full_qualified_table_name_b)

        if schemaB is None:
            raise ValueError(f"Not found schema name in full qualified table B: '{full_qualified_table_name_b}'")

        tableB = taputils.get_table_name(full_qualified_table_name_b)

        if taputils.get_schema_name(results_table_name) is not None:
            raise ValueError("Please, do not specify schema for 'results_table_name'")

        query = f"SELECT crossmatch_positional('{schemaA}','{tableA}','{schemaB}','{tableB}',{radius}, " \
                f"'{results_table_name}') FROM dual;"

        name = str(results_table_name)

        return self.launch_job_async(query=query,
                                     name=name,
                                     output_file=None,
                                     output_format="votable_gzip",
                                     verbose=verbose,
                                     dump_to_file=False,
                                     background=background,
                                     upload_resource=None,
                                     upload_table_name=None)

    def launch_job(self, query, *, name=None, output_file=None,
                   output_format="votable_gzip", verbose=False,
                   dump_to_file=False, upload_resource=None,
                   upload_table_name=None):
        """Launches a synchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional, default None
            custom name defined by the user for the job that is going to be created
        output_file : str, optional, default None
            file name where the results are saved if ``dump_to_file`` is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable_gzip'
            results format. Available formats are: 'votable_gzip', 'votable', 'votable_plain',
             'fits', 'csv', 'ecsv' and 'json', default is 'votable_gzip'.
             Returned results for 'votable_gzip', 'ecsv' and 'fits' formats are compressed
             gzip files.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        upload_resource : str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name : str, optional, default None
            resource temporary table name associated to the uploaded resource.
            This argument is required if ``upload_resource`` is provided.

        Returns
        -------
        A Job object
        """

        return TapPlus.launch_job(self, query=query, name=name,
                                  output_file=output_file,
                                  output_format=output_format,
                                  verbose=verbose,
                                  dump_to_file=dump_to_file,
                                  upload_resource=upload_resource,
                                  upload_table_name=upload_table_name,
                                  format_with_results_compressed=('votable_gzip',))

    def launch_job_async(self, query, *, name=None, output_file=None,
                         output_format="votable_gzip", verbose=False,
                         dump_to_file=False, background=False,
                         upload_resource=None, upload_table_name=None,
                         autorun=True):
        """Launches an asynchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional, default None
            custom name defined by the user for the job that is going to be created
        output_file : str, optional, default None
            file name where the results are saved if ``dump_to_file`` is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable_gzip'
            results format. Available formats are: 'votable_gzip', 'votable', 'votable_plain',
             'fits', 'csv' and 'json', default is 'votable_gzip'.
             Returned results for 'votable_gzip' 'ecsv' and 'fits' format are compressed
             gzip files.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        upload_resource : str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name : str, optional, default None
            resource temporary table name associated to the uploaded resource.
            This argument is required if ``upload_resource`` is provided.
        autorun : boolean, optional, default True
            if 'True', sets 'phase' parameter to 'RUN',
            so the framework can start the job.

        Returns
        -------
        A Job object
        """
        return TapPlus.launch_job_async(self, query=query,
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

    def get_status_messages(self):
        """Retrieve the messages to inform users about
        the status of Gaia TAP
        """
        try:
            sub_context = self.GAIA_MESSAGES
            conn_handler = self._TapPlus__getconnhandler()
            response = conn_handler.execute_tapget(sub_context, verbose=False)
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


Gaia = GaiaClass()
