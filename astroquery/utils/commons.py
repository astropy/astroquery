# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This submodule contains some common functions that are required
by all query classes
"""
import requests
import astropy.units as u
from astropy import coordinates as coord
#from ..exceptions import TimeoutError
from astroquery.exceptions import TimeoutError
__all__ = ['send_request']

def send_request(url, data, timeout):
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

    Returns
    -------
    response : `requests.Response`
    Response object returned by the remote server
    """
    try:
        response = requests.post(url, data=data, timeout=timeout)
        return response
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
    AssertionError
    """
    if isinstance(coordinates, basestring):
        try:
            c = coord.ICRSCoordinates.from_name(coordinates)
        except coord.name_resolve.NameResolveError:
            # check if they are coordinates expressed as a string
            # otherwise UnitsException will be raised
            c = coord.ICRSCoordinates(coordinates, unit=(None, None))
    else:
        # it must be an astropy.coordinates coordinate object
        assert isinstance(coordinates, coord.SphericalCoordinatesBase)
        c = coordinates
    return c

