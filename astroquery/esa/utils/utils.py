"""
==============================
ESA Utils for common functions
==============================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import getpass
import os

import numpy as np
from astropy import log
from astropy.coordinates import SkyCoord

from astropy.units import Quantity
from pyvo.auth.authsession import AuthSession
from astroquery.utils import commons

import matplotlib.pyplot as plt
from requests import Response


TARGET_RESOLVERS = ['ALL', 'SIMBAD', 'NED', 'VIZIER']


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
            response = self.post(url=login_url, data=args, headers=header)
            try:
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
        response = self.post(url=logout_url, headers=header)
        try:
            response.raise_for_status()
            log.info('Logout executed successfully.')
        except Exception as e:
            log.error('Logout error: {}'.format(e))
            raise e

    def _send_login_request(self, username: str, password: str) -> Response:
        """
        Send a POST request to the login URL with username and password.

        Parameters:
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            Response: The response object from the login request.
        """
        import requests  # Use requests for handling HTTP interactions

        # Login payload
        payload = {"username": username, "password": password}

        # Perform the POST request
        response = requests.post(self.login_url, data=payload)

        # Raise an error if the request failed
        response.raise_for_status()
        return response

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
        if '?' in url:
            url += "&TAPCLIENT=ASTROQUERY&format=votable_plain"
        else:
            url += "?TAPCLIENT=ASTROQUERY&format=votable_plain"
        return super()._request(method, url, **kwargs)


def get_coord_input(value, msg):
    """
    Auxiliary method to parse the coordinates

    Parameters
    ----------
    value: str or SkyCoord, mandatory
        coordinates to be parsed
    msg: str, mandatory
        Value to be shown in the error message

    Returns
    -------
    The coordinates parsed
    """
    if not (isinstance(value, str) or isinstance(value,
                                                 commons.CoordClasses)):
        raise ValueError(f"{msg} must be either a string or astropy.coordinates")
    if isinstance(value, str):
        c = commons.parse_coordinates(value)
        return c
    else:
        return value


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
            return radius.degree
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
    astropy_table.write(output_file, format=output_format, overwrite=False)


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


def execute_post_request(url, tap, *, query_params=None):
    response = tap._session.post(url=url, params=query_params)
    response.raise_for_status()

    return response


def plot_result(x, y, x_title, y_title, plot_title, *, error_x=None, error_y=None, log_scale=False):
    """
    Draw series in a 2D plot

    Parameters
    ----------
    x: array of numbers, mandatory
        values for the X series
    y: array of numbers, mandatory
        values for the Y series
    x_title: str, mandatory
        title of the X axis
    y_title: str, mandatory
        title of the Y axis
    plot_title: str, mandatory
        title of the plot
    error_x: array of numbers, optional
        error on the X series
    error_y: array of numbers, optional
        error on the Y series
    log_scale: boolean, optional, default False
        Draw X and Y axes using log scale
    """

    plt.figure(figsize=(8, 6))
    plt.scatter(x, y, color='blue')
    plt.xlabel(x_title)
    plt.ylabel(y_title)

    if log_scale:
        plt.xscale('log')
        plt.yscale('log')

    plt.title(plot_title)

    if error_x is not None or error_y is not None:
        plt.errorbar(x, y, xerr=error_x, yerr=error_y, fmt='o')

    plt.show(block=False)


def plot_concatenated_results(x, y1, y2, x_title, y1_title, y2_title, plot_title, *,
                              x_label=None, y_label=None):
    """
    Draw two plots concatenated on the X axis

    Parameters
    ----------
    x: array of numbers, mandatory
        values for the X series
    y1: array of numbers, mandatory
        values for the first Y series
    y2: array of numbers, mandatory
        values for the second Y series
    x_title: str, mandatory
        title of the X axis
    y1_title: str, mandatory
        title of the first Y axis
    y2_title: str, mandatory
        title of the second Y axis
    plot_title: str, mandatory
        title of the plot
    x_label: str, optional
        label for the X series
    y_label: str, optional
        label for the Y series
    """
    # Create a figure with two subplots that share the x-axis
    fig = plt.figure()
    gs = fig.add_gridspec(2, hspace=0)
    axs = gs.subplots(sharex=True, sharey=True)

    # Plot the first dataset on the first subplot
    axs[0].scatter(x, y1, color='blue', label=x_label)
    axs[0].set_ylabel(y1_title)
    axs[0].grid(True, which='both')

    # Plot the second dataset on the second subplot
    axs[1].scatter(x, y2, label=y_label, color='#DB4052')
    axs[1].set_xlabel(x_title)
    axs[1].set_ylabel(y2_title)
    axs[1].grid(True, which='both')

    # Show the combined plot
    fig.suptitle(plot_title)
    for ax in axs:
        ax.label_outer()
    plt.show(block=False)


def plot_image(z, height, width, *, x_title=None, y_title=None, z_title=None, plot_title=None, z_min=2, z_max=10):
    """
    Method to draw images and mosaics as heatmaps

    Parameters
    ----------
    z: array of numbers, mandatory
        values for the heatmap series
    height: number, mandatory
        height dimension for the heatmap
    width: number, mandatory
        width dimension for the heatmap
    x_title: str, optional
        title of the X axis
    y_title: str, optional
        title of the Y axis
    z_title: str, optional
        title of the Z axis (heatmap values)
    plot_title: str, optional
        title of the plot
    z_min: number, optional, default 2
        Min value to show in the plot
    z_max: number, optional, default 10
        Max value to show in the plot
    """
    z_reshaped = z.reshape(width, height)

    if z_min is not None and z_max is not None:
        z_clipped = np.clip(z_reshaped, z_min, z_max)
        plt.imshow(z_clipped, origin='lower', cmap='hot')
    else:
        plt.imshow(z, origin='lower', cmap='hot')

    # Plot the heatmap

    plt.colorbar(label=z_title)
    plt.xlabel(x_title)
    plt.ylabel(y_title)
    plt.title(plot_title)
    plt.show(block=False)


def download_file(url, session, *, filename=None, params=None, verbose=False):
    """
    Download a file in streaming mode using a existing session

    Parameters
    ----------
    url: str, mandatory
        URL to be downloaded
    session: ESAAuthSession, mandatory
        session to download the file, including the cookies from ESA login
    filename: str, optional
        filename to be given to the final file
    params: dict, optional
        Additional params for the request
    verbose: boolean, optional, default False
        Write the outputs in console

    Returns
    -------
    The request with the modified url
    """

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

        # Open a local file in binary write mode
        if verbose:
            log.info('Downloading: ' + filename)
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        if verbose:
            log.info(f"File {filename} has been downloaded successfully")
        return filename


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

    params = {'TAPCLIENT': 'ASTROQUERY'}
    resolver_url = url.format(target_name, target_resolver)

    with session.get(resolver_url, stream=True, params=params) as response:
        response.raise_for_status()

        try:
            target_result = response.json()
            if target_result['objects']:
                ra = target_result['objects'][0]['raDegrees']
                dec = target_result['objects'][0]['decDegrees']
            return SkyCoord(ra=ra, dec=dec, unit="deg")
        except (ValueError, KeyError):
            raise ValueError("This target cannot be resolved")
