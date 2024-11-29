"""
==============================
ESA Utils for common functions
==============================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import os

import numpy as np
import requests

from astropy.units import Quantity
from pyvo.auth.authsession import AuthSession
from astroquery.utils import commons

import matplotlib.pyplot as plt


# Subclass AuthSession to customize requests
class ESAAuthSession(AuthSession):
    def request(self, method, url, *args, **kwargs):
        # Add the custom query parameter to the URL
        if '?' in url:
            url += "&TAPCLIENT=ASTROQUERY"
        else:
            url += "?TAPCLIENT=ASTROQUERY"
        return super()._request(method, url, **kwargs)


def get_coord_input(value, msg):
    if not (isinstance(value, str) or isinstance(value,
                                                 commons.CoordClasses)):
        raise ValueError(f"{msg} must be either a string or astropy.coordinates")
    if isinstance(value, str):
        c = commons.parse_coordinates(value)
        return c
    else:
        return value


def get_degree_radius(radius):
    if radius is not None:
        if isinstance(radius, Quantity):
            return radius.degree
        elif isinstance(radius, float):
            return radius
        elif isinstance(radius, int):
            return float(radius)
    raise ValueError(f"Radius must be either a Quantity or float value")


def download_table(astropy_table, output_file=None, output_format=None):
    astropy_table.write(output_file, format=output_format, overwrite=False)


def execute_servlet_request(url, tap, *, query_params=None):
    # Use the TAPService session to perform a custom GET request
    response = tap._session.get(url=url, params=query_params)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def plot_result(x, y, x_title, y_title, plot_title, *, error_x=None, error_y=None, log_scale=False):
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


def plot_image(z, plot_title, height, width, *, x_title=None, y_title=None, z_title=None, z_min=2, z_max=10):

    z_reshaped = z.reshape(width, height)
    z_clipped = np.clip(z_reshaped, z_min, z_max)

    # Plot the heatmap
    plt.imshow(z_clipped, origin='lower', cmap='hot')
    plt.colorbar(label=z_title)
    plt.xlabel(x_title)
    plt.ylabel(y_title)
    plt.title(plot_title)
    plt.show(block=False)


def download_file(url, session, *, filename=None, params=None, verbose=False):
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
            print('Downloading: ' + filename)
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        if verbose:
            print(f"File {filename} has been downloaded successfully")


def check_rename_to_gz(filename):
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
