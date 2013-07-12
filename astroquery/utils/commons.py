# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This submodule contains some common functions that are required
by all query classes
"""
import requests
import warnings
import astropy.units as u
from astropy import coordinates as coord
from ..exceptions import TimeoutError

__all__ = ['send_request',
           'parse_coordinates',
           'parse_radius']

def send_request(url, data, timeout, request_type='POST'):
    """
    A utility function that post HTTP requests to remote server
    and returns the HTTP response.

    Parameters
    ----------
    url : str
        The URL of the remote server
    data : dict
        A dictionary representing the payload to be posted via the HTTP request
    timeout : int
        Time limit for establishing successful connection with remote server
    request_type : str
        options are 'POST' (default) and 'GET'. Determines whether to perform
        an HTTP POST or an HTTP GET request
    Returns
    -------
    response : `requests.Response`
        Response object returned by the remote server
    """
    try:
        if request_type == 'GET':
            response = requests.get(url, params=data, timeout=timeout)
            return response
        elif request_type == 'POST':
            response = requests.post(url, data=data, timeout=timeout)
            return response
        else:
            raise ValueError("request_type must be either 'GET' or 'POST'.")
    except requests.exceptions.Timeout:
            raise TimeoutError("Query timed out, time elapsed {time}s".
                               format(time=timeout))
    except requests.exceptions.RequestException:
            raise Exception("Query failed\n")


def parse_radius(radius):
    """
    Given a radius checks that it is either parsable as an
    `astropy.coordinates.angle` or an `astropy.units.Quantity`
    and returns an `astropy.coordinates.Angle` object

    Parameters
    ----------
    radius : str/astropy.units.Quantity
        The radius of a region

    Returns
    -------
    `astropy.coordinates.Angle` object

    Raises
    ------
    astropy.units.UnitsException
    astropy.coordinates.errors.UnitsError
    AttributeError
    """
    # check if its a string parsable as Angle
    if isinstance(radius, basestring):
        return coord.Angle(radius)
    # else must be a quantity
    else:
        return coord.Angle(radius.value, unit=radius.unit)

def parse_coordinates(coordinates):
    """
    Takes a string or astropy.coordinates object. Checks if the
    string is parsable as an astropy.coordinates.ICRSCoordinates
    object or is a name that is resolvable. Otherwise asserts
    that the argument is an astropy.coordinates object.

    Parameters
    ----------
    coordinates : str/astropy.coordinates object
        Astronomical coordinate

    Returns
    -------
    a subclass of `astropy.coordinates.SphericalCoordinatesBase`

    Raises
    ------
    astropy.units.UnitsException
    TypeError
    """
    if isinstance(coordinates, basestring):
        try:
            c = coord.ICRSCoordinates.from_name(coordinates)
        except coord.name_resolve.NameResolveError:
            try:
                c = coord.ICRSCoordinates(coordinates)
                warnings.warn("Coordinate string is being interpreted as an ICRS coordinate.")
            except u.UnitsException:
                warnings.warn("Only ICRS coordinates can be entered as strings\n"
                              "For other systems please use the appropriate "
                              "astropy.coordinates object")
                raise u.UnitsException
    elif isinstance(coordinates, coord.SphericalCoordinatesBase):
        c = coordinates
    else:
        raise TypeError("Argument cannot be parsed as a coordinate")
    return c
