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
from pyvo.auth.authsession import AuthSession


TARGET_RESOLVERS = ['ALL', 'SIMBAD', 'NED', 'VIZIER']


# We do trust the ESA tar files, this is to avoid the new to Python 3.12 deprecation warning
# https://docs.python.org/3.12/library/tarfile.html#tarfile-extraction-filter
if hasattr(esatar, "fully_trusted_filter"):
    esatar.TarFile.extraction_filter = staticmethod(esatar.fully_trusted_filter)


# Subclass AuthSession to customize requests
class ESAAuthSession(AuthSession):
    """
    Session to login/logout an ESA TAP using PyVO
    """

    def __init__(self: str):
        """
        Initialize the custom authentication session.

        Parameters:
            login_url (str): The login endpoint URL.
        """
        super().__init__()

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
        additional_params = {'TAPCLIENT': 'ASTROQUERY',
                             'format': 'votable_plain'}
        if kwargs is not None and 'params' in kwargs:
            kwargs['params'].update(additional_params)
        elif kwargs is not None:
            kwargs['params'] = additional_params
        return super()._request(method, url, **kwargs)


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


def execute_servlet_request(url, tap, *, query_params=None):
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

    Returns
    -------
    The request with the modified url
    """

    if 'TAPCLIENT' not in query_params:
        query_params['TAPCLIENT'] = 'ASTROQUERY'

    # Use the TAPService session to perform a custom GET request
    response = tap._session.get(url=url, params=query_params)
    if response.status_code == 200:
        return response.json()
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
    Download a file in streaming mode using a existing session

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
