"""
==============================
ESA Utils for common functions
==============================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import datetime
import getpass
import os
import binascii
import shutil

import tarfile as esatar
import zipfile
from astropy import log
from astropy.coordinates import SkyCoord
from astropy import units as u

from astropy.units import Quantity
from astropy.io import fits
from astropy.table import Table
import pyvo

from PIL import Image
import requests
from io import BytesIO

import numbers

from astroquery.query import BaseVOQuery, BaseQuery

TARGET_RESOLVERS = ['ALL', 'SIMBAD', 'NED', 'VIZIER']


# We do trust the ESA tar files, this is to avoid the new to Python 3.12 deprecation warning
# https://docs.python.org/3.12/library/tarfile.html#tarfile-extraction-filter
if hasattr(esatar, "fully_trusted_filter"):
    esatar.TarFile.extraction_filter = staticmethod(esatar.fully_trusted_filter)


# Subclass AuthSession to customize requests
class ESAAuthSession(pyvo.auth.authsession.AuthSession):
    """
    Session to login/logout an ESA TAP using PyVO
    """

    def __init__(self, request_parameters=None):
        """
        Initialize the custom authentication session.

        Parameters:
            login_url (str): The login endpoint URL.
        """
        super().__init__()
        self.request_parameters = request_parameters or {}

    def login(self, login_url, *, user=None, password=None):
        """
        Performs a login.
        TAP+ only
        User and password shall be used

        Parameters
        ----------
        login_url: str, mandatory
            URL to execute the login request
        user : str, mandatory, default None
            Username. If no value is provided, a prompt to type it will appear
        password : str, mandatory, default None
            User password. If no value is provided, a prompt to type it will appear
        """

        if user is None:
            user = input("Username:")
        if password is None:
            password = getpass.getpass("Password:")

        if user and password:
            args = {
                "username": str(user),
                "password": str(password)}
            header = {
                "Content-type": "application/x-www-form-urlencoded",
                "Accept": "text/plain"
            }

            try:
                response = self.post(url=login_url, data=args, headers=header)
                response.raise_for_status()
                log.info('User has been logged successfully.')
            except Exception as e:
                log.error('Logging error: {}'.format(e))
                raise e

    def logout(self, logout_url):
        """
        Performs a logout.
        TAP+ only
        User and password shall be used

        Parameters
        ----------
        logout_url: str, mandatory
            URL to execute the logout request
        """
        header = {
            "Content-type": "application/x-www-form-urlencoded",
            "Accept": "text/plain"
        }

        try:
            response = self.post(url=logout_url, headers=header)
            response.raise_for_status()
            log.info('Logout executed successfully.')
        except Exception as e:
            log.error('Logout error: {}'.format(e))
            raise e

    def _request(self, method, url, *args, **kwargs):
        """
        Intercept the request method and add TAPCLIENT=ASTROQUERY

        Parameters
        ----------
        method: str, mandatory
            method to be executed
        url: str, mandatory
            url for the request

        Returns
        -------
        The request with the modified url
        """

        # Add the custom query parameter to the URL
        additional_params = {'TAPCLIENT': 'ASTROQUERY'}
        # Merge the default parameters with the additional request parameters
        additional_params = additional_params | self.request_parameters
        if kwargs is not None and 'params' in kwargs:
            kwargs['params'].update(additional_params)
        elif kwargs is not None:
            kwargs['params'] = additional_params
        return super()._request(method, url, **kwargs)


def check_initial_params(**kwargs):
    """
    Verify that the initial parameters for an ESA TAP class are initialized

    Returns
    -------
    A value error in case a parameter has not been defined
    """
    null_vars = [name for name, value in kwargs.items() if value is None]
    if null_vars:
        raise ValueError(f"Null elements found: {', '.join(null_vars)}")


class EsaTap(BaseVOQuery, BaseQuery):

    ESA_ARCHIVE_NAME: str  # must be defined for each module
    TAP_URL: str  # must be defined for each module
    LOGIN_URL: str  # must be defined for each module
    LOGOUT_URL: str  # must be defined for each module
    TIMEOUT = 60
    REQUEST_PARAMETERS = {}  # Additional parameters to be added to all requests

    """
    Class to init ESA TAP Module to communicate with {ESA_ARCHIVE_NAME} Science Archive

    Subclasses must define:
        ESA_ARCHIVE_NAME: str
        TAP_URL: str
        LOGIN_URL: str
        LOGOUT_URL: str
        TIMEOUT (Optional) =  60
        REQUEST_PARAMETERS = {}
    """

    def __init__(self, auth_session=None, tap_url=None):
        """
        Set the session, alternative TAP url, initial parameter for the TAP connection

        Parameters
        ----------
        auth_session : pyvo.auth.authsession.AuthSession, optional, default None
            Authentication session to manage login
        tap_url : str, optional, default None
            In case an alternative URL for the TAP needs to be defined

        Returns
        -------
        A list of table objects
        """

        super().__init__()

        # Checks if auth session has been defined. If not, create a new session
        if auth_session:
            self._auth_session = auth_session
        else:
            self._auth_session = ESAAuthSession(self.REQUEST_PARAMETERS)

        # Checks if a different URL need to be defined
        if tap_url:
            self.TAP_URL = tap_url

        self._auth_session.timeout = self.TIMEOUT
        self._tap = None
        self._tap_url = self.TAP_URL

    def __init_subclass__(cls, **kwargs):
        """
        Include the name of the ESA Science Archive within the docstrings
        """

        super().__init_subclass__(**kwargs)

        # Check if all mandatory attributes are defined
        mandatory_attrs = ['ESA_ARCHIVE_NAME', 'TAP_URL', 'LOGIN_URL', 'LOGOUT_URL']
        null_attrs = [name for name in mandatory_attrs if getattr(cls, name, None) is None]

        # Automatically add default value to optional attributes if not set
        if not hasattr(cls, "TIMEOUT") or cls.TIMEOUT is None:
            cls.TIMEOUT = EsaTap.TIMEOUT
        if not hasattr(cls, "REQUEST_PARAMETERS") or cls.REQUEST_PARAMETERS is None:
            cls.REQUEST_PARAMETERS = EsaTap.REQUEST_PARAMETERS

        if null_attrs:
            raise ValueError(f" The following parameters for {cls.__name__} are mandatory: {', '.join(null_attrs)}")

        archive = getattr(cls, "ESA_ARCHIVE_NAME", None)

        # Only iterate over non-special attributes
        for name in dir(cls):
            if name.startswith("__") and name.endswith("__"):
                continue  # skip dunder attributes
            try:
                attr = getattr(cls, name)
            except AttributeError:
                continue  # skip inaccessible attributes
            if callable(attr) and hasattr(attr, "__doc__") and attr.__doc__:
                if "{ESA_ARCHIVE_NAME}" in attr.__doc__:
                    attr.__doc__ = attr.__doc__.format(ESA_ARCHIVE_NAME=archive)

    @property
    def tap(self) -> pyvo.dal.TAPService:
        """
        Initialize {ESA_ARCHIVE_NAME} TAP connection

        Returns
        -------
        A pyvo.dal.TAPService object connected to {ESA_ARCHIVE_NAME} TAP
        """
        if self._tap is None:
            self._tap = pyvo.dal.TAPService(
                self.TAP_URL, session=self._auth_session)

        return self._tap

    def get_tables(self, *, only_names=False):
        """
        Gets all public tables within {ESA_ARCHIVE_NAME} TAP

        Parameters
        ----------
        only_names : bool, optional, default False
            True to load table names only

        Returns
        -------
        A list of table objects
        """
        table_set = self.tap.tables
        if only_names:
            return list(table_set.keys())
        else:
            return list(table_set.values())

    def get_table(self, table):
        """
        Gets the specified table from {ESA_ARCHIVE_NAME} TAP

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)

        Returns
        -------
        A table object
        """
        tables = self.get_tables()
        for t in tables:
            if table == t.name:
                return t

    def get_metadata(self, table):
        """
        Gets the specified table from {ESA_ARCHIVE_NAME} TAP

        Parameters
        ----------
        table : str, mandatory
        full qualified table name (i.e. schema name.table name)

        Returns
        -------
        A table object
        """
        tap_table = self.get_table(table)
        if tap_table is None:
            raise ValueError(f'Table {tap_table} does not exist.')

        columns = tap_table.columns
        metadata_table = Table(names=('Column', 'Description', 'Unit', 'Data Type', 'UCD', 'UType'),
                               dtype=(str, object, object, str, object, object), masked=True)
        for column in columns:
            metadata_table.add_row([column.name, column.description, column.unit, column.datatype.content,
                                    column.ucd, column.utype])

        return metadata_table

    def get_job(self, jobid):
        """
        Returns the job corresponding to an ID from {ESA_ARCHIVE_NAME} TAP.
        Note that the user must be able to see the job in the current security context.

        Parameters
        ----------
        jobid : str, mandatory
            ID of the job to view

        Returns
        -------
        JobSummary corresponding to the job ID
        """

        return self.tap.get_job(job_id=jobid)

    def get_job_list(self, *, phases=None, after=None, last=None,
                     short_description=True):
        """
        Returns all the asynchronous jobs stored in {ESA_ARCHIVE_NAME} TAP.
        Note that the user must be able to see the job in the current security context.

        Parameters
        ----------
        phases : list of str
            Union of job phases to filter the results by.
        after : datetime
            Return only jobs created after this datetime
        last : int
            Return only the most recent number of jobs
        short_description : flag - True or False
            If True, the jobs in the list will contain only the information
            corresponding to the TAP ShortJobDescription object (job ID, phase,
            run ID, owner ID and creation ID) whereas if False, a separate GET
            call to each job is performed for the complete job description

        Returns
        -------
        A list of Job objects
        """

        return self.tap.get_job_list(phases=phases, after=after, last=last,
                                     short_description=short_description)

    def login(self, *, user=None, password=None):
        """
        Performs a login in {ESA_ARCHIVE_NAME} TAP.
        TAP+ only
        User and password shall be used

        Parameters
        ----------
        user : str, mandatory, default None
            Username. If no value is provided, a prompt to type it will appear
        password : str, mandatory, default None
            User password. If no value is provided, a prompt to type it will appear
        """
        self._auth_session.login(login_url=self.LOGIN_URL, user=user, password=password)

    def logout(self):
        """
        Performs a logout in {ESA_ARCHIVE_NAME} TAP.
        TAP+ only
        """
        self._auth_session.logout(logout_url=self.LOGOUT_URL)

    def query_tap(self, query, *, async_job=False, output_file=None, output_format='votable', verbose=False):
        """
        Launches a synchronous or asynchronous job to query the {ESA_ARCHIVE_NAME} TAP

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided
        output_format : str, optional, default 'votable'
            results format
        verbose: bool, optional, default False
            To log the query when executing this method.

        Returns
        -------
        An astropy.table object containing the results
        """
        if async_job:
            query_result = self.tap.run_async(query)
            result = query_result.to_table()
        else:
            result = self.tap.search(query).to_table()

        if output_file:
            download_table(result, output_file, output_format)

        if verbose:
            print(f"Executed query:{query}")

        return result

    def create_cone_search_query(self, ra, dec, ra_column, dec_column, radius):
        return f"1=CONTAINS(POINT('ICRS', {ra_column}, {dec_column}),CIRCLE('ICRS', {ra}, {dec}, {radius}))"

    def query_table(self, table_name, *, columns=None, custom_filters=None, get_metadata=False, async_job=False,
                    output_file=None, output_format='votable', **filters):
        """
        Query a set of columns from a specific table in {ESA_ARCHIVE_NAME} TAP, using filters defined by the user

        Parameters
        ----------
        table_name : str, mandatory
            name of the table where this query will be executed
        columns : list of str or str, optional, default 'None'
            columns from the table to be retrieved
        custom_filters : str, optional, default 'None'
            No SQL filters defined by the user
            E.g. ADQL Intersect filter
        get_metadata: bool, optional, default False
            If set to true, the method will return an astropy.Table
            containing the available columns for this table, including
            the description, units, ucd, utype and data type
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_file : str, optional, default None
            file name where the results are saved
        output_format : str, optional, default 'votable'
            results format
        Users can defined more parameters, using the column names. They will be
        used to generate the SQL filters for the query. Some examples are described below,
        where the left side is the parameter defined for this method and the right side the
        SQL filter generated:
        StarName='star1' -> StarName = 'star1'
        StarName='star*' -> StarName ILIKE 'star%'
        StarName='star%' -> StarName ILIKE 'star%'
        StarName=['star1', 'star2'] -> StarName = 'star1' OR StarName - 'star2'
        ra=('>', 30) -> ra > 30
        ra=(20, 30) -> ra >= 20 AND ra <= 30

        Returns
        -------
        An astropy.table object containing the results
        """
        if get_metadata:
            return self.get_metadata(table_name)

        # If columns is defined and a list, join them.
        # If it is a simple value, use it
        # If not defined, the columns are '*'
        result_columns = (
            (lambda c: ', '.join(c) if isinstance(c, list) else c)(columns)
            if columns else '*'
        )

        # If filters are defined, generate the associated query criteria
        query_filters = (
            self.__create_sql_criteria(filters)
            if filters and len(filters) > 0 else ''
        )

        # If custom filters are added, if query filters exists, add a new condition
        # If they don't exist, this is the WHERE clause
        # If custom_filters filters are not defined, this is an empty string
        additional_filters = (
            (lambda has_qf: f" AND {custom_filters}" if has_qf else f"WHERE {custom_filters}")
            (bool(query_filters))
            if custom_filters else ''
        )

        query = f"SELECT {result_columns} FROM {table_name} {query_filters}{additional_filters}"
        return self.query_tap(query=query, async_job=async_job, output_file=output_file,
                              output_format=output_format, verbose=True)

    def __create_sql_criteria(self, filters):
        """
        Create the SQL clause associated to the query_criteria filters

        Parameters
        ----------
        query_criteria : str, mandatory
            table name where the query will be executed
        Returns
        -------
        A string containing the list of SQL filters
        """
        sql_clauses = []
        for key, value in filters.items():
            # Checks if the value is not defined NULL
            if value is None:
                sql_clauses.append(f"{key} IS NULL")

            # Detect if the value is a list
            elif isinstance(value, list):
                sql_clauses.append(self.__create_multiple_criteria(column=key, value_list=value))

            else:
                sql_clauses.append(self.__create_single_criteria(column=key, value=value))

        where_sql = f" WHERE {' AND '.join(sql_clauses)}"
        return where_sql

    def __create_string_criteria(self, column, value):
        """
        Create the filter for a string value
        Parameters
        ----------
        column : str, mandatory
            column where this filter is applied
        value : str, mandatory
            value to be used to compare. Wildcards can be used
        Returns
        -------
        The SQL filter for a string column
        """
        if '*' in value or '%' in value:
            return f"{column} ILIKE '{value.replace('*', '%')}'"
        else:
            return f"{column} = '{value}'"

    def __create_boolean_criteria(self, column, value):
        """
        Create the filter for a boolean value
        Parameters
        ----------
        column : str, mandatory
            column where this filter is applied
        value : bool, mandatory
            value to be used to compare.
        Returns
        -------
        The SQL filter for a boolean column
        """
        return f"{column} = '{value}'"

    def __create_number_criteria(self, column, value, comparator='='):
        """
        Create the filter for a numeric value
        Parameters
        ----------
        column : str, mandatory
            column where this filter is applied
        value : number, mandatory
            value to be used to compare
        Returns
        -------
        The SQL filter for a numeric column
        """
        # For exact searches in not integer values, check the number is
        # within a threshold of 1e-5
        threshold = 1e-5
        if not isinstance(value, numbers.Integral) and comparator == '=':
            return (f"({column} >= {value - threshold} and "
                    f"{column} <= {value + threshold})")
        else:
            return f"{column} {comparator} {value}"

    def __create_single_criteria(self, column, value):
        """
        Create the filter for a single value of different types
        Parameters
        ----------
        column : str, mandatory
            column where this filter is applied
        value : object, mandatory
            value to be used to compare
        Returns
        -------
        The SQL filter for the column
        """
        if isinstance(value, str):
            return self.__create_string_criteria(column, value)
        if isinstance(value, bool):
            return self.__create_boolean_criteria(column, value)
        if isinstance(value, numbers.Number):
            return self.__create_number_criteria(column, value, "=")
        # For numeric values, a tuple shall be provided
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError('For numeric values, a tuple (comparator, value) shall be provided')
            # First value can be a comparator or a minimum value
            # Second value should always be a number
            first_value, second_value = value
            if not isinstance(second_value, numbers.Number):
                raise ValueError('Comparator can only be applied to numeric values.')
            # If first value is also a number, the filter is between two numbers
            if isinstance(first_value, numbers.Number):
                min_value_filter = self.__create_number_criteria(column, first_value, ">=")
                max_value_filter = self.__create_number_criteria(column, second_value, "<=")
                return f"{min_value_filter} AND {max_value_filter}"
            else:
                return self.__create_number_criteria(column, second_value, first_value)

    def __create_multiple_criteria(self, column, value_list):
        """
        Create the filter for a single value of different types
        Parameters
        ----------
        column : str, mandatory
            column where this filter is applied
        value_list : list of objects, mandatory
            values to be used to compare
        Returns
        -------
        The SQL filter for the column including all the values
        """
        if isinstance(value_list[0], str):
            string_criteria_list = [self.__create_string_criteria(column=column, value=val) for val in value_list]
            return f"({' OR '.join(string_criteria_list)})"
        if isinstance(value_list[0], numbers.Number):
            min_value_clause = self.__create_number_criteria(column, value_list[0], ">=")
            max_value_clause = self.__create_number_criteria(column, value_list[1], "<=")
            return f"({min_value_clause} AND {max_value_clause})"


def get_degree_radius(radius):
    """
    Method to parse the radius and retrieve it in degrees

    Parameters
    ----------
    radius: number or Quantity, mandatory
        radius to be transformed to degrees

    Returns
    -------
    The radius in degrees
    """
    if radius is not None:
        if isinstance(radius, Quantity):
            return radius.to(u.deg).value
        elif isinstance(radius, float):
            return radius
        elif isinstance(radius, int):
            return float(radius)
    raise ValueError('Radius must be either a Quantity or float value')


def download_table(astropy_table, output_file=None, output_format=None):
    """
    Auxiliary method to download an astropy table

    Parameters
    ----------
    astropy_table: Table, mandatory
        Input Astropy Table
    output_file: str, optional
        File where the table will be saved
    output_format: str, optional
        Format of the file to be exported
    """
    astropy_table.write(output_file, format=output_format, overwrite=True)


def execute_servlet_request(url, tap, *, query_params=None, parser_method=None):
    """
    Method to execute requests to the servlets on a server

    Parameters
    ----------
    url: str, mandatory
        Url of the servlet
    tap: PyVO TAP, mandatory
        TAP instance from where the session will be extracted
    query_params: dict, optional
        Parameters to be included in the request
    parser_method: dict, optional
        Method to parse the response

    Returns
    -------
    The request with the modified url
    """

    if 'TAPCLIENT' not in query_params:
        query_params['TAPCLIENT'] = 'ASTROQUERY'

    # Use the TAPService session to perform a custom GET request
    response = tap._session.get(url=url, params=query_params)
    if response.status_code == 200:
        if parser_method is None:
            return response.json()
        else:
            return parser_method(response)
    else:
        response.raise_for_status()


def download_file(url, session, *, params=None, path='', filename=None, cache=False, cache_folder=None, verbose=False):
    """
    Download a file in streaming mode using an existing session

    Parameters
    ----------
    url: str, mandatory
        URL to be downloaded
    session: ESAAuthSession, mandatory
        session to download the file, including the cookies from ESA login
    params: dict, optional
        Additional params for the request
    path: str, optional
        Path where the file will be stored
    filename: str, optional
        filename to be given to the final file
    cache: bool, optional, default False
        flag to store the file in the Astroquery cache
    cache_folder: str, optional
        folder to store the cached file
    verbose: boolean, optional, default False
        Write the outputs in console

    Returns
    -------
    The request with the modified url
    """
    if params is None or len(params) == 0:
        params = {}
    if 'TAPCLIENT' not in params:
        params['TAPCLIENT'] = 'ASTROQUERY'
    with session.get(url, stream=True, params=params) as response:
        response.raise_for_status()

        if filename is None:
            content_disposition = response.headers.get('Content-Disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = os.path.basename(url.split('?')[0])
        if cache:
            filename = get_cache_filepath(filename, cache_folder)
            path = ''
        # Open a local file in binary write mode
        if verbose:
            log.info('Downloading: ' + filename)
        file_path = os.path.join(path, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        if verbose:
            log.info(f"File {file_path} has been downloaded successfully")
        return file_path


def get_cache_filepath(filename=None, cache_path=None):
    """
    Stores the content from a response as an Astroquery cache object.

    Parameters:
    response (requests.Response):
        The HTTP response object with iterable content.
    filename: str, optional
        filename to be given to the final file
    cache_filename (str, optional):
        The desired filename in the cache. If None, a default name is used.

    Returns:
        str: Path to the cached file.
    """
    # Determine the cache path
    cache_file_path = os.path.join(cache_path, filename)
    # Create the cache directory if it doesn't exist
    os.makedirs(cache_path, exist_ok=True)

    return cache_file_path


def read_downloaded_fits(files):
    extracted_files = []
    for file in files:
        extracted_files.extend(extract_file(file))

    fits_files = []
    for file in extracted_files:
        fits_file = safe_open_fits(file)
        if fits_file:
            fits_files.append({
                'filename': os.path.basename(file),
                'path': file,
                'fits': fits_file
            })

    return fits_files


def safe_open_fits(file_path):
    """
    Safely open a FITS file using astropy.io.fits.

    Parameters:
    file_path: string
        The path to the file to be opened.

    Returns:
    fits.HDUList or None
    Returns the HDUList object if the file is a valid FITS file, otherwise None.
    """
    try:
        hdu_list = fits.open(file_path)
        return hdu_list
    except (OSError, fits.VerifyError) as e:
        print(f"Skipping file {file_path}: {e}")
        return None


def extract_file(file_path, output_dir=None):
    """
    Extracts a .tar, .tar.gz, or .zip file. If the file is in a different format,
    returns the path of the original file.

    Parameters:
        file_path (str):
            Path to the archive file (.tar, .tar.gz, or .zip).
        output_dir (str, optional):
            Directory to store the extracted files. If None, a directory
            with the same name as the archive file (minus the extension)
            is created.

    Returns:
        list: List of paths to the extracted files.
    """
    if not output_dir:
        output_dir = os.path.abspath(file_path)
    if esatar.is_tarfile(file_path):
        with esatar.open(file_path, "r") as tar_ref:
            return extract_from_tar(tar_ref, file_path, output_dir)
    elif is_gz_file(file_path):
        with esatar.open(file_path, "r:gz") as tar:
            return extract_from_tar(tar, file_path, output_dir)
    elif zipfile.is_zipfile(file_path):
        return extract_from_zip(file_path, output_dir)
    elif not is_gz_file(file_path):
        return [str(file_path)]


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'


def extract_from_tar(tar, file_path, output_dir=None):
    """
    Extract files from a tar file (both .tar and .tar.gz formats).
    """
    # Prepare the output directory
    output_dir = prepare_output_dir(file_path)

    # Extract all files into the specified directory
    tar.extractall(output_dir)

    # Get the paths of the extracted files
    extracted_files = [os.path.join(output_dir, member.name) for member in tar.getmembers()]
    return extracted_files


def extract_from_zip(file_path, output_dir=None):
    """
    Handle extraction of .zip files.
    """
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        # Prepare the output directory
        output_dir = prepare_output_dir(file_path)

        # Extract all files into the specified directory
        zip_ref.extractall(output_dir)

        # Get the paths of the extracted files
        extracted_files = [os.path.join(output_dir, file) for file in zip_ref.namelist()]
        return extracted_files


def check_rename_to_gz(filename):
    """
    Check if the file is compressed as gz and rename it
    Parameters
    ----------
    filename: str, mandatory
        filename to verify

    Returns
    -------
    The renamed file
    """

    rename = False
    if os.path.exists(filename):
        with open(filename, 'rb') as test_f:
            if test_f.read(2) == b'\x1f\x8b' and not filename.endswith('.fits.gz'):
                rename = True

    if rename:
        output = os.path.splitext(filename)[0] + '.fits.gz'
        os.rename(filename, output)
        return os.path.basename(output)
    else:
        return os.path.basename(filename)


def prepare_output_dir(file_path):
    """
    Prepare the output directory. If output_dir is provided, use it. Otherwise,
    create a new directory with the name of the file (without the extension).
    """
    # Create a directory based on the file name without extension
    base_path = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)
    file_name_without_extensions = base_name.split('.')[0]
    current_time = datetime.datetime.now().strftime("%y%m%d%H%M%S")

    output_dir = os.path.join(base_path, f"{file_name_without_extensions}_{current_time}")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def resolve_target(url, session, target_name, target_resolver):
    """
    Download a file in streaming mode using an existing session

    Parameters
    ----------
    url: str, mandatory
        URL to be downloaded
    session: ESAAuthSession, mandatory
        session to download the file, including the cookies from ESA login
    target_name: str, mandatory
        Name of the target
    target_resolver: str, mandatory
        Name of the resolver. Possible values: ALL, SIMBAD, NED, VIZIER

    Returns
    -------
    The request with the modified url
    """

    if target_resolver not in TARGET_RESOLVERS:
        raise ValueError("This target resolver is not allowed")

    resolver_url = url.format(target_name, target_resolver)
    try:
        with session.get(resolver_url, stream=True) as response:
            response.raise_for_status()
            target_result = response.json()
            if target_result['objects']:
                ra = target_result['objects'][0]['raDegrees']
                dec = target_result['objects'][0]['decDegrees']
            return SkyCoord(ra=ra, dec=dec, unit="deg")
    except (ValueError, KeyError) as err:
        raise ValueError('This target cannot be resolved. {}'.format(err))


def load_image_from_url(url):
    response = requests.get(url)
    response.raise_for_status()        # raise an error if download failed
    return Image.open(BytesIO(response.content))
